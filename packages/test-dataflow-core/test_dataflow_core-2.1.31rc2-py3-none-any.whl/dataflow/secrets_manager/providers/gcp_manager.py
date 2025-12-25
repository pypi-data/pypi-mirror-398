import os, base64, json, atexit
from pathlib import Path
from google.cloud import secretmanager
from google.cloud.secretmanager_v1 import SecretManagerServiceClient
from google.cloud.secretmanager_v1.types import Secret, SecretPayload
from google.api_core.exceptions import (
    AlreadyExists,
    NotFound,
    PermissionDenied,
    Forbidden,
    ResourceExhausted,
    InvalidArgument,
    FailedPrecondition
)
import json
from ..interface import SecretManager
from ...utils.exceptions import (
    SecretNotFoundException,
    SecretAlreadyExistsException,
    SecretManagerAuthException,
    SecretManagerServiceException
)

def _setup_gcp_credentials():
    """Setup GCP credentials from base64 encoded JSON environment variable"""
    
    # Only run if GOOGLE_APPLICATION_CREDENTIALS is not already set
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        return
    
    # Get base64 encoded JSON credentials
    encoded_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    
    if encoded_json:
        try:
            # Decode base64 to JSON string
            json_credentials = base64.b64decode(encoded_json).decode('utf-8')
            
            # Validate it's valid JSON
            json.loads(json_credentials)  # Just to validate
            
            # Create credentials file in home directory
            home_dir = Path.home()
            credentials_dir = home_dir / '.gcp'
            credentials_dir.mkdir(exist_ok=True)  # Create .gcp directory if it doesn't exist
            
            credentials_path = credentials_dir / 'credentials.json'
            
            # Write JSON string to credentials file
            with open(credentials_path, 'w') as f:
                f.write(json_credentials)
            
            # Set the standard Google environment variable that the SDK looks for
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
            
            # Clean up file on exit
            atexit.register(lambda: credentials_path.unlink() if credentials_path.exists() else None)
            
            print(f"GCP credentials decoded and configured at {credentials_path}")
            
        except Exception as e:
            print(f"Error setting up GCP credentials: {e}")


class GCPSecretsManager(SecretManager):
    """Google Cloud Platform Secrets Manager implementation."""

    def __init__(self, project_id: str, region: str):
        """Initialize the GCP Secret Manager client.
        
        Args:
            project_id: The GCP project ID where secrets will be stored.
            region: The GCP region where secrets will be stored.
        """
        self.project_id = project_id
        self.region = region
        try:
            _setup_gcp_credentials()
            self.client = secretmanager.SecretManagerServiceClient()
        except PermissionDenied as e:
            raise SecretManagerAuthException("initialize_gcp_client", original_error=str(e))
        except Exception as e:
            raise SecretManagerServiceException("initialize_gcp_client", original_error=str(e))
    
    def _get_secret_path(self, vault_path: str) -> str:
        """Get the full secret path in GCP format.
        
        Args:
            vault_path: The path/name of the secret.
            
        Returns:
            The full path to the secret in GCP format.
        """
        return f"projects/{self.project_id}/secrets/{vault_path}"
    
    def _get_secret_version_path(self, vault_path: str, version: str = "latest") -> str:
        """Get the full path to a specific secret version.
        
        Args:
            vault_path: The path/name of the secret.
            version: The version of the secret (default is "latest").
            
        Returns:
            The full path to the secret version in GCP format.
        """
        return f"{self._get_secret_path(vault_path)}/versions/{version}"
    
    def create_secret(self, vault_path: str, secret_data: dict) -> str:
        """Create a new secret.
        
        Args:
            vault_path: The path/name of the secret.
            region: The region where the secret will be stored.
            secret_data: The data to store in the secret.
            
        Returns:
            A success message.
            
        Raises:
            SecretAlreadyExistsException: If the secret already exists.
            SecretManagerAuthException: If there are permission issues.
            SecretManagerServiceException: For other service errors.
        """
        try:
            # Convert dictionary to JSON string before saving
            secret_string = json.dumps(secret_data)
            
            # First create the secret
            parent = f"projects/{self.project_id}"
            secret = Secret(
                replication={
                    "user_managed": {
                        "replicas": [
                            {"location": self.region }
                        ]
                    }
                }
            )
            
            self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": vault_path,
                    "secret": secret
                }
            )
            
            # Then add the secret version with the data
            secret_path = self._get_secret_path(vault_path)
            self.client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {"data": secret_string.encode("UTF-8")}
                }
            )
            
            return "Secret created successfully"
        except AlreadyExists as e:
            raise SecretAlreadyExistsException("secret", vault_path, original_error=str(e))
        except PermissionDenied as e:
            raise SecretManagerAuthException("create_secret", original_error=str(e))
        except Forbidden as e:
            raise SecretManagerAuthException("create_secret", original_error=str(e))
        except FailedPrecondition as e:
            # Handle case where secret might be in recovery/deleted state
            if "pending deletion" in str(e).lower() or "scheduled for deletion" in str(e).lower():
                raise SecretAlreadyExistsException("secret", vault_path, original_error=str(e), is_scheduled_for_deletion=True)
            else:
                raise SecretManagerServiceException("create_secret", original_error=str(e))
        except ResourceExhausted as e:
            raise SecretManagerServiceException("create_secret", original_error=str(e))
        except Exception as e:
            raise SecretManagerServiceException("create_secret", original_error=str(e))
    
    def get_secret_by_key(self, vault_path: str) -> dict:
        """Get a secret by its key.
        
        Args:
            vault_path: The path/name of the secret.
            
        Returns:
            The secret data as a dictionary.
            
        Raises:
            SecretNotFoundException: If the secret doesn't exist.
            SecretManagerAuthException: If there are permission issues.
            SecretManagerServiceException: For other service errors.
        """
        try:
            # Get the latest version of the secret
            name = self._get_secret_version_path(vault_path)
            response = self.client.access_secret_version(request={"name": name})
            
            # Decode the payload and convert JSON string back to dictionary
            secret_string = response.payload.data.decode("UTF-8")
            secret_data = json.loads(secret_string)
            return secret_data
        except NotFound as e:
            raise SecretNotFoundException("secret", vault_path, original_error=str(e))
        except PermissionDenied as e:
            raise SecretManagerAuthException("get_secret", original_error=str(e))
        except Forbidden as e:
            raise SecretManagerAuthException("get_secret", original_error=str(e))
        except InvalidArgument as e:
            raise SecretManagerServiceException("get_secret", original_error=str(e))
        except json.JSONDecodeError as e:
            raise SecretManagerServiceException("get_secret", original_error=str(e))
        except Exception as e:
            raise SecretManagerServiceException("get_secret", original_error=str(e))
    
    def update_secret(self, vault_path: str, update_data: dict) -> str:
        """
        Update a secret and delete all previous versions so only the latest remains.
        """
        try:
            current_data = self.get_secret_by_key(vault_path)
            current_data.update(update_data)
            updated_string = json.dumps(current_data)

            secret_path = self._get_secret_path(vault_path)
            new_version = self.client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {"data": updated_string.encode("UTF-8")}
                }
            )

            new_version_name = new_version.name
            versions = self.client.list_secret_versions(request={"parent": secret_path})

            for version in versions:
                # Skip the newly created version
                if version.name == new_version_name:
                    continue

                # Disable the version before destroying
                if version.state.name != "DISABLED":
                    self.client.disable_secret_version(
                        request={"name": version.name}
                    )
                self.client.destroy_secret_version(
                    request={"name": version.name}
                )

            return "Secret updated successfully (old versions removed)"

        except SecretNotFoundException:
            raise
        except PermissionDenied as e:
            raise SecretManagerAuthException("update_secret", original_error=str(e))
        except Forbidden as e:
            raise SecretManagerAuthException("update_secret", original_error=str(e))
        except NotFound as e:
            raise SecretNotFoundException("secret", vault_path, original_error=str(e))
        except InvalidArgument as e:
            raise SecretManagerServiceException("update_secret", original_error=str(e))
        except json.JSONDecodeError as e:
            raise SecretManagerServiceException("update_secret", original_error=str(e))
        except Exception as e:
            raise SecretManagerServiceException("update_secret", original_error=str(e))

    
    def delete_secret(self, vault_path: str) -> str:
        """Delete a secret.
        
        Args:
            vault_path: The path/name of the secret.
            
        Returns:
            A success message.
            
        Raises:
            SecretNotFoundException: If the secret doesn't exist.
            SecretManagerAuthException: If there are permission issues.
            SecretManagerServiceException: For other service errors.
        """
        try:
            # Get the full path to the secret
            name = self._get_secret_path(vault_path)
            
            # Get all versions to destroy them permanently
            versions = self.client.list_secret_versions(request={"parent": name})
            for version in versions:
                if version.state == secretmanager.SecretVersion.State.ENABLED:
                    version_name = f"{name}/versions/{version.name.split('/')[-1]}"
                    self.client.destroy_secret_version(request={"name": version_name})
            
            # Delete the secret itself
            self.client.delete_secret(request={"name": name})
            
            return "Secret deleted successfully"
        except NotFound as e:
            raise SecretNotFoundException("secret", vault_path, original_error=str(e))
        except PermissionDenied as e:
            raise SecretManagerAuthException("delete_secret", original_error=str(e))
        except Forbidden as e:
            raise SecretManagerAuthException("delete_secret", original_error=str(e))
        except InvalidArgument as e:
            raise SecretManagerServiceException("delete_secret", original_error=str(e))
        except Exception as e:
            raise SecretManagerServiceException("delete_secret", original_error=str(e))
    
    def test_connection(self, vault_path: str) -> str:
        """Test the connection to the secret manager by attempting to access a secret.
        
        Args:
            vault_path: The path/name of the secret to test.
            
        Returns:
            The status of the secret.
            
        Raises:
            SecretNotFoundException: If the secret doesn't exist.
            SecretManagerAuthException: If there are permission issues.
            SecretManagerServiceException: For other service errors.
        """
        try:
            secret = self.get_secret_by_key(vault_path)
            return secret.get('status', 'Unknown')
        except SecretNotFoundException:
            raise
        except (SecretManagerAuthException, SecretManagerServiceException):
            raise
        except Exception as e:
            raise SecretManagerServiceException("test_connection", original_error=str(e))
