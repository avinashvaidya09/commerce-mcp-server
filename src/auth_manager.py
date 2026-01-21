import httpx
import os

# Load environment variables
CAP_API_USERNAME = os.getenv("CAP_API_USERNAME", "user")
CAP_API_PASSWORD = os.getenv("CAP_API_PASSWORD", "password")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

class AuthManager:
    """Manages the authentication object."""
    _auth = None

    @classmethod
    def initialize_auth(cls):
        """Initialize the authentication object for local environment."""
        if ENVIRONMENT == "local" and CAP_API_USERNAME and CAP_API_PASSWORD:
            cls._auth = httpx.BasicAuth(CAP_API_USERNAME, CAP_API_PASSWORD)

    @classmethod
    def get_auth(cls):
        """Retrieve the authentication object."""
        return cls._auth