import os, uuid, re, hashlib, secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from traitlets import Bool, Unicode
from jupyterhub.auth import Authenticator
from oauthenticator.google import GoogleOAuthenticator
from oauthenticator.azuread import AzureAdOAuthenticator
from dataflow.db import get_db
from dataflow.models import user as m_user, session as m_session, otp as m_otp
from sqlalchemy import  func
from dataflow.configuration import ConfigurationManager
import asyncio
import httpx

class DataflowBaseAuthenticator(Authenticator):
    """Base Authenticator to handle Dataflow authentication and session management.
    Provides methods to authenticate users via Dataflow credentials, manage sessions.
    
    Overrides JupyterHub's Authenticator class.
    """
    
    enable_dataflow_auth = Bool(True, config=True, help="Enable username/password authentication")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.db = next(get_db())
            m_user.Base.metadata.create_all(bind=self.db.get_bind(), checkfirst=True)
            m_session.Base.metadata.create_all(bind=self.db.get_bind(), checkfirst=True)
            self.log.info("Dataflow database initialized successfully")
        except Exception as e:
            self.log.error(f"Failed to initialize Dataflow database: {str(e)}")
            raise

    def generate_session_id(self):

        """Generate and return a unique session ID using UUID4."""

        return str(uuid.uuid4())

    def set_session_cookie(self, handler, session_id):

        """Set the dataflow_session cookie in the user's browser.
        
        Args:
            handler: The request handler to set the cookie on.
            session_id: The session ID to set in the cookie."""
        dataflow_config = ConfigurationManager('/dataflow/app/config/dataflow.cfg')
        idle_timeout = dataflow_config.get_config_value('session', 'idle_timeout_days')
        expires = datetime.now(ZoneInfo("UTC")) + timedelta(days=int(idle_timeout))
        host = handler.request.host
        domain = '.'.join(host.split('.')[-2:]) if len(host.split('.')) >= 2 else host
        handler.set_cookie(
            "dataflow_session",
            session_id,
            domain=f".{domain}",
            path="/",
            expires=expires,
            secure=True,
            httponly=True,
            samesite="None"
        )
        self.log.info(f"Set session cookie: dataflow_session={session_id} for host={host}")

    def create_session(self, user_id):

        """Create a new session ID for user.
        
        Args:
            user_id: The ID of the user to get or create a session for.
        
        Returns:
            session_id (str): The newly created session ID.
        """

        from datetime import timedelta
        session_id = self.generate_session_id()
        while self.db.query(m_session.Session).filter(
            m_session.Session.session_id == session_id
        ).first():
            session_id = self.generate_session_id()

        now = datetime.now(ZoneInfo("UTC"))
        expires_at = now + timedelta(days=7)
        
        db_item = m_session.Session(
            user_id=user_id, 
            session_id=session_id,
            last_seen=now,
            expires_at=expires_at,
            revoked=False
        )
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        self.log.info(f"Created new session: {session_id}")
        return session_id
    
    def check_blocked_users(self, username, authenticated):
        
        """Check if the authenticated user is blocked based on allowed_users list.
        
        Args:
            username (str): The username of the authenticated user.
            authenticated (dict|None): The authentication data returned from authenticate method.
        
        Returns:
            username (str|None): The username if not blocked, else None."""
        
        self.log.info(f"Checking blocked users for {username}: authenticated={authenticated}, allowed_users={self.allowed_users}")

        if not authenticated:
            self.log.warning(f"No authenticated data for user: {username}")
            return None

        if isinstance(authenticated, dict) and "session_id" in authenticated:
            self.log.info(f"Allowing Dataflow authentication for user: {username}")
            return username

        return super().check_blocked_users(username, authenticated)

    def extract_username_from_email(self, email):

        """Extract username from email by removing domain
        
        Args:
            email (str): User's email address
        
        Returns:
            username (str): Extracted username after removing domain
        """
        
        if '@' in email:
            return email.split('@')[0]
        return email

    def generate_secure_password(self):
        
        """Generate secure random password hash
        
        Returns:
            password_hash (str): Securely hashed password
        """
        
        salt = secrets.token_hex(16)
        random_uuid = str(uuid.uuid4())
        hash_obj = hashlib.sha256((random_uuid + salt).encode())
        return hash_obj.hexdigest()

    async def send_user_creation_email_async(self, email, user_name, first_name, last_name, secure_password):
        """Send user creation email via API asynchronously without blocking.
        
        Args:
            email (str): User's email address
            user_name (str): User's username
            first_name (str): User's first name
            last_name (str): User's last name
            secure_password (str): Generated secure password
        """
        try:
            url = "http://ui-svc:8000/private/api/email/user-creation"
            payload = {
                "email": email,
                "password": secure_password,
                "user_name": first_name or user_name
            }
            
            timeout = httpx.Timeout(15.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    self.log.info(f"User creation email sent successfully for {email}")
                else:
                    self.log.warning(f"Failed to send user creation email for {email}: Status {response.status_code}")
        except httpx.TimeoutException:
            self.log.warning(f"Timeout while sending user creation email for {email}")
        except Exception as e:
            self.log.warning(f"Error sending user creation email for {email}: {str(e)}")

    def create_new_user(self, email, first_name=None, last_name=None):

        """Create a new user with Applicant role
        
        Args:
            email (str): User's email address
            first_name (str): User's first name
            last_name (str): User's last name
        
        Returns:
            new_user (m_user.User|None): Created user object or None if creation failed
        """
        
        try:
            # Normalize email to lowercase for consistency
            email = email.lower()
            
            username = self.extract_username_from_email(email)
            username = re.sub(r'[^a-z0-9]', '', username.lower())
            if not username:
                self.log.error("Cannot create user: Username is empty")
                return None
            
            existing_user = (
                self.db.query(m_user.User)
                .filter(m_user.User.user_name == username)
                .first()
            )
            if existing_user:
                counter = 1
                original_username = username
                while existing_user:
                    username = f"{original_username}{counter}"
                    existing_user = (
                        self.db.query(m_user.User)
                        .filter(m_user.User.user_name == username)
                        .first()
                    )
                    counter += 1

            secure_password = self.generate_secure_password()
            new_user = m_user.User(
                user_name=username,
                first_name=first_name or username,
                last_name=last_name or "",
                email=email,
                password=secure_password,
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            self.log.info(f"Created new user: {username} with email: {email}")
            
            # Send email notification asynchronously without blocking
            try:
                asyncio.create_task(self.send_user_creation_email_async(email, username, first_name or username, last_name or "",secure_password))
            except Exception as e:
                self.log.warning(f"Failed to schedule email task for {email}: {str(e)}")
            
            return new_user
            
        except Exception as e:
            self.log.error(f"Error creating new user: {str(e)}")
            self.db.rollback()
            return None

    def check_user_and_org_active(self, user):
        """Check if user is active and has at least one active organization
        
        Args:
            user: User object from database
            
        Returns:
            bool: True if user is active and has at least one active org or no orgs, False if user is inactive or all orgs are inactive
        """
        
        # Check if user is active
        if not user.active:
            self.log.warning(f"User {user.user_name} is inactive")
            return False
        
        # Check if user has at least one active organization (commented out for now)
        # active_org_count = (
        #     self.db.query(m_org_assocs.OrganizationUser)
        #     .join(m_organization.Organization)
        #     .filter(
        #         m_org_assocs.OrganizationUser.user_id == user.user_id,
        #         m_organization.Organization.active == True
        #     )
        #     .count()
        # )
        
        # if active_org_count == 0:
        #     self.log.warning(f"User {user.user_name} has organizations but none are active")
        #     return False
        
        return True

    async def authenticate_dataflow(self, handler, data):

        """Authenticate user using Dataflow username/password.

        Args:
            handler: The request handler.
            data: The authentication data containing username and password.
        
        Returns:
            dict|None: Authentication result with username and session_id if successful, else None.
        """

        if not (self.enable_dataflow_auth and isinstance(data, dict) and data.get("username") and data.get("password")):
            return None
        user_email = data["username"].lower()  # Normalize email for comparison
        password = data["password"]
        self.log.info(f"Attempting Dataflow authentication for user: {user_email}")
        
        try:
            otp_value = int(password)
            current_time = datetime.now(ZoneInfo("UTC"))
            valid_user = (
                self.db.query(m_otp.UserOtp)
                .filter(
                    func.lower(m_otp.UserOtp.email) == user_email, 
                    m_otp.UserOtp.otp == otp_value,
                    m_otp.UserOtp.expires_at > current_time
                )
                .first()
            )

            user = (
                self.db.query(m_user.User)
                .filter(func.lower(m_user.User.email) == user_email)  
                .first()
            )

            if not valid_user:
                if user:
                    self.log.warning(f"Invalid OTP for user: {user_email}")
                    self.login_error(handler, f"Invalid OTP provided for {user_email}. Please try again.")
                else:
                    self.log.warning(f"User not found: {user_email}")
                    self.login_error(handler, f"User not found: {user_email}. Please sign up.")
                return None

            self.db.delete(valid_user)
            self.db.commit()
            self.log.info(f"OTP validated and deleted for user: {user_email}")
            if not user:
                try:
                    db_user = self.create_new_user(user_email)
                    if not db_user:
                        self.log.error(f"Failed to create new user for email: {user_email}")
                        self.login_error(handler, "Authentication error occurred. Please try again.")
                        return None
                    user = db_user
                except Exception as e:
                    self.log.error(f"Error during user creation: {str(e)}")
                    self.login_error(handler, "Authentication error occurred. Please try again.")
                    return None
            else:
                # Check if existing user and their organizations are active
                if not self.check_user_and_org_active(user):
                    self.login_error(
                        handler, 
                        "Your account has been disabled. Please contact your administrator for assistance.",
                        "Account Disabled"
                    )
                    return None
                        
            session_id = self.create_session(user.user_id)
            self.set_session_cookie(handler, session_id)
            self.log.info(f"Dataflow authentication successful for user: {user.user_name}")
            return {"name": user.user_name, "session_id": session_id, "auth_state": {}}
            
        except Exception as e:
            self.log.error(f"Dataflow authentication error: {str(e)}", exc_info=True)
            self.db.rollback() 
            self.login_error(handler, "Authentication error occurred. Please try again.")
            return None

class DataflowGoogleAuthenticator(DataflowBaseAuthenticator, GoogleOAuthenticator):

    """Authenticator to handle Google OAuth authentication with Dataflow integration.
    
    Overrides
      - DataflowBaseAuthenticator
      - GoogleOAuthenticator
    
    Requires Google OAuth credentials.
      - google_client_id
      - google_client_secret
    """

    dataflow_oauth_type = Unicode(
        default_value="google",
        config=True,
        help="The OAuth provider type for DataflowHub (e.g., github, google)"
    )
    google_client_id = Unicode(config=True, help="Google OAuth client ID")
    google_client_secret = Unicode(config=True, help="Google OAuth client secret")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_id = self.google_client_id
        self.client_secret = self.google_client_secret
        self.dataflow_oauth_type = self.dataflow_oauth_type
        self.log.info(f"DataflowGoogleAuthenticator initialized with google_client_id={self.google_client_id}, "
                      f"oauth_callback_url={self.oauth_callback_url}, "
                      f"enable_dataflow_auth={self.enable_dataflow_auth}")

    def login_error(self, handler, message, title="Authentication Failed"):
        """Custom error handler with simple centered design"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <link href='https://fonts.googleapis.com/css?family=Lato:400,600' rel='stylesheet'>
        </head>
        <body style="margin: 0; padding: 20px; font-family: 'Lato', Arial, sans-serif; background-color: #f8fafc; min-height: 100vh; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 450px; width: 100%; padding: 40px; text-align: center;">
                <div style="width: 60px; height: 60px; background-color: #ffebee; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 30px; color: #d32f2f;">!</div>
                
                <h1 style="font-size: 24px; font-weight: 600; color: #121926; margin: 0 0 12px 0;">{title}</h1>
                
                <p style="font-size: 15px; color: #697586; line-height: 1.5; margin: 0 0 24px 0;">{message}</p>
                
                <a href="/hub/login" style="display: inline-block; padding: 12px 32px; background-color: #30baba; color: white; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600; transition: background-color 0.3s;">Try Again</a>
            </div>
        </body>
        </html>
        """
        handler.set_status(403)
        handler.finish(html)



    async def authenticate(self, handler, data):

        """Authenticate user using Google OAuth with Dataflow integration.

        Args:
            handler: The request handler.
            data: The authentication data.
        
        Returns:
            dict|None: Authentication result with username and session_id if successful, else None.
        """

        self.log.info(f"Authenticate called with data: {data}, request_uri: {handler.request.uri}")
        result = await self.authenticate_dataflow(handler, data)
        if result:
            return result
        try:
            user = await super().authenticate(handler, data)
            self.log.info(f"Google OAuth authentication returned: {user}")
            if not user:
                self.log.warning("Google OAuth authentication failed: No user data returned")
                return None
            
            email = user["name"]
                
            db_user = (
                self.db.query(m_user.User)
                .filter(m_user.User.email == email)
                .first()
            )
            
            if not db_user:
                self.log.info(f"User with email {email} not found in Dataflow database, creating new user")
                # Extract additional info from user data if available
                auth_state = user.get("auth_state", {})
                user_info = auth_state.get("user", {}) if auth_state else {}
                
                # Get name information from Google OAuth response
                full_name = user_info.get("name", "")
                given_name = user_info.get("given_name", "")
                family_name = user_info.get("family_name", "")
                
                # Use given_name and family_name if available, otherwise parse full name
                first_name = given_name
                last_name = family_name
                
                if not first_name and full_name:
                    # Fallback: parse full name if given_name is not available
                    name_parts = full_name.strip().split(' ', 1)
                    first_name = name_parts[0] if name_parts else ""
                    last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                # Log the extracted names for debugging
                self.log.info(f"Creating user with first_name='{first_name}', last_name='{last_name}' from Google data: {user_info}")
                
                try:
                    db_user = self.create_new_user(email, first_name, last_name)
                    if not db_user:
                        self.log.error(f"Failed to create new user for email: {email}")
                        self.login_error(handler, "Authentication error occurred. Please try again.")
                        return None
                except Exception as e:
                    self.log.error(f"Error during user creation: {str(e)}")
                    self.login_error(handler, "Authentication error occurred. Please try again.")
                    return None
            else:
                # Check if existing user and their organizations are active
                if not self.check_user_and_org_active(db_user):
                    self.login_error(
                        handler, 
                        "Your account has been disabled. Please contact your administrator for assistance.",
                        "Account Disabled"
                    )
                    return None

            username = db_user.user_name
            session_id = self.create_session(db_user.user_id)
            self.set_session_cookie(handler, session_id)
            self.log.info(f"Google OAuth completed for user: {username}, session_id={session_id}")
            return {
                "name": username,
                "session_id": session_id,
                "auth_state": user.get("auth_state", {})
            }
        except Exception as e:
            self.login_error(handler, str(e))
            self.log.error(f"Google OAuth authentication error: {str(e)}", exc_info=True)
            return None
        finally:
            self.db.close()

class DataflowAzureAuthenticator(DataflowBaseAuthenticator, AzureAdOAuthenticator):

    """Authenticator to handle Azure AD OAuth authentication with Dataflow integration.

    Overrides
      - DataflowBaseAuthenticator
      - AzureAdOAuthenticator

    Requires Azure AD OAuth credentials.
      - azure_client_id
      - azure_client_secret
      - azure_tenant_id
    """

    azure_client_id = Unicode(config=True, help="Azure AD OAuth client ID")
    azure_client_secret = Unicode(config=True, help="Azure AD OAuth client secret")
    azure_tenant_id = Unicode(config=True, help="Azure AD tenant ID")
    azure_scope = Unicode("openid profile email", config=True, help="Azure AD OAuth scopes")
    dataflow_oauth_type = Unicode(
        default_value="google",
        config=True,
        help="The OAuth provider type for DataflowHub (e.g., github, google)"
    )
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_id = self.azure_client_id
        self.client_secret = self.azure_client_secret
        self.tenant_id = self.azure_tenant_id
        self.scope = self.azure_scope.split()
        self.dataflow_oauth_type = self.dataflow_oauth_type
        self.log.info(f"DataflowAzureAuthenticator initialized with azure_client_id={self.azure_client_id}, "
                      f"oauth_callback_url={self.oauth_callback_url}, "
                      f"enable_dataflow_auth={self.enable_dataflow_auth}")

    def login_error(self, handler, message, title="Authentication Failed"):
        """Custom error handler with simple centered design"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <link href='https://fonts.googleapis.com/css?family=Lato:400,600' rel='stylesheet'>
        </head>
        <body style="margin: 0; padding: 20px; font-family: 'Lato', Arial, sans-serif; background-color: #f8fafc; min-height: 100vh; display: flex; align-items: center; justify-content: center;">
            <div style="background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 450px; width: 100%; padding: 40px; text-align: center;">
                <div style="width: 60px; height: 60px; background-color: #ffebee; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 30px; color: #d32f2f;">!</div>
                
                <h1 style="font-size: 24px; font-weight: 600; color: #121926; margin: 0 0 12px 0;">{title}</h1>
                
                <p style="font-size: 15px; color: #697586; line-height: 1.5; margin: 0 0 24px 0;">{message}</p>
                
                <a href="/hub/login" style="display: inline-block; padding: 12px 32px; background-color: #30baba; color: white; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600; transition: background-color 0.3s;">Try Again</a>
            </div>
        </body>
        </html>
        """
        handler.set_status(403)
        handler.finish(html)

    async def authenticate(self, handler, data):
        """Authenticate user using Azure AD OAuth with Dataflow integration.

        Args:
            handler: The request handler.
            data: The authentication data.
        
        Returns:
            dict|None: Authentication result with username and session_id if successful, else None.
        """
        
        result = await self.authenticate_dataflow(handler, data)
        if result:
            return result
        try:
            user = await super().authenticate(handler, data)
            self.log.info(f"Azure AD OAuth authentication returned: {user}")
            if not user:
                self.log.warning("Azure AD OAuth authentication failed: No user data returned")
                return None

            auth_state = user.get("auth_state", {})
            user_info = auth_state.get("user", {}) if auth_state else {}
            email = user_info.get("upn")
            if not email:
                self.log.warning("Azure AD OAuth authentication failed: No upn in user data")
                return None

            db_user = (
                self.db.query(m_user.User)
                .filter(m_user.User.email == email)
                .first()
            )

            if not db_user:
                self.log.info(f"User with email {email} not found in Dataflow database, creating new user")
                
                # Extract name information from Azure AD response
                display_name = user_info.get("displayName", "") or user_info.get("name", "") or user.get("name", "")
                given_name = user_info.get("givenName", "")
                surname = user_info.get("surname", "")
                
                # Use givenName and surname if available, otherwise parse displayName
                first_name = given_name
                last_name = surname
                
                if not first_name and display_name:
                    # Fallback: parse display name if givenName is not available
                    name_parts = display_name.strip().split(' ', 1)
                    first_name = name_parts[0] if name_parts else ""
                    last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                # Log the extracted names for debugging
                self.log.info(f"Creating user with first_name='{first_name}', last_name='{last_name}' from Azure data: {user_info}")
                
                try:
                    db_user = self.create_new_user(email, first_name, last_name)
                    if not db_user:
                        self.log.error(f"Failed to create new user for email: {email}")
                        self.login_error(handler, "Authentication error occurred. Please try again.")
                        return None
                except Exception as e:
                    self.log.error(f"Error during user creation: {str(e)}")
                    self.login_error(handler, "Authentication error occurred. Please try again.")
                    return None
            else:
                # Check if existing user and their organizations are active
                if not self.check_user_and_org_active(db_user):
                    self.login_error(
                        handler, 
                        "Your account has been disabled. Please contact your administrator for assistance.",
                        "Account Disabled"
                    )
                    return None

            username = db_user.user_name
            session_id = self.create_session(db_user.user_id)
            self.set_session_cookie(handler, session_id)
            self.log.info(f"Azure AD OAuth completed for user: {username}, session_id={session_id}")
            return {
                "name": username,
                "session_id": session_id,
                "auth_state": user.get("auth_state", {})
            }

        except Exception as e:
            # self.login_error(handler, str(e))
            self.log.error(f"Azure AD OAuth authentication error: {str(e)}", exc_info=True)
            return None
        finally:
            self.db.close()

auth_type = os.environ.get("DATAFLOW_OAUTH_TYPE", "google")

if auth_type == "google":
    BaseAuthenticator = DataflowGoogleAuthenticator
else:
    BaseAuthenticator = DataflowAzureAuthenticator

class DataflowHubAuthenticator(BaseAuthenticator):
    pass