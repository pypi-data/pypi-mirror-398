"""
Utility functions for secrets manager.
"""


def encode_vault_key(key: str) -> str:
    """
    Encode key for cloud-safe storage.
    
    Converts to lowercase and replaces underscores with hyphens
    to ensure compatibility with all cloud providers (AWS, Azure, GCP).
    
    Cloud providers have different naming restrictions:
    - AWS: Allows a-z, A-Z, 0-9, /_+=.@-
    - Azure: Only lowercase letters, digits, and hyphens (a-z, 0-9, -)
            Must START with letter, END with letter or digit
    - GCP: Lowercase letters, digits, hyphens, and underscores (a-z, 0-9, -, _)
           Must START with letter or underscore
    
    This encoding ensures compatibility with the most restrictive provider (Azure).
    
    Input validation (done in schemas) ensures:
    - Key starts with a letter (A-Z, a-z)
    - Key ends with a letter or digit (A-Z, a-z, 0-9)
    - Key contains only letters, numbers, and underscores
    
    After encoding (lowercase + underscore→hyphen):
    - Starts with lowercase letter (a-z) ✓
    - Ends with lowercase letter or digit (a-z, 0-9) ✓
    - Contains only lowercase letters, digits, and hyphens ✓
    
    Args:
        key: Original key name (e.g., "My_Secret", "DB_CONNECTION")
             Must start with letter and end with letter/digit
    
    Returns:
        Encoded key in lowercase with hyphens (e.g., "my-secret", "db-connection")
    
    Examples:
        >>> encode_vault_key("My_Secret")
        'my-secret'
        >>> encode_vault_key("DB_CONNECTION")
        'db-connection'
        >>> encode_vault_key("apiKey123")
        'apikey123'
        >>> encode_vault_key("test_API_v2")
        'test-api-v2'
        >>> encode_vault_key("A")
        'a'
    
    Note:
        This encoding is case-insensitive. Both "My_Secret" and "my_secret"
        will map to the same vault path. The original key (with case) is 
        preserved in the secret's data payload for reference.
    """
    # Simple encoding: lowercase and replace underscores with hyphens
    # No need for prefix/suffix handling since validation ensures correct start/end
    return key.lower().replace('_', '-')
