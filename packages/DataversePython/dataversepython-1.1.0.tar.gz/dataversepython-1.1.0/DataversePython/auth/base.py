from abc import ABC, abstractmethod
import requests


class AuthenticationProvider(ABC):
    """
    Abstract base class for authentication providers.
    All authentication methods must inherit from this class and implement the authenticate method.
    """
    
    @abstractmethod
    def authenticate(self, config: dict) -> tuple[requests.Session, str]:
        """
        Authenticates with Azure Entra ID and returns an authenticated session.
        
        Args:
            config (dict): Configuration dictionary containing authentication parameters.
                Required keys depend on the specific authentication provider implementation.
        
        Returns:
            tuple[requests.Session, str]: A tuple containing:
                - An authenticated requests.Session with appropriate headers set
                - The environment URI string
        
        Raises:
            Exception: If authentication fails or an access token cannot be obtained.
        """
        pass
