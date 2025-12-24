import logging
import requests
import msal
from .base import AuthenticationProvider


class MSALClientSecretAuth(AuthenticationProvider):
    """
    Authentication provider using MSAL client secret flow.
    Enables non-interactive authentication using application credentials.
    """
    
    def authenticate(self, config: dict) -> tuple[requests.Session, str]:
        """
        Authenticates with Azure Entra ID using client secret (application credentials).
        
        Args:
            config (dict): Configuration dictionary containing:
                - environmentURI (str): The base URI of the environment.
                - scopeSuffix (str): The suffix to append to the environment URI for the scope.
                - clientID (str): The client (application) ID registered in Azure.
                - clientSecret (str): The client secret for the application.
                - authorityBase (str): The base authority URL (e.g., "https://login.microsoftonline.com/").
                - tenantID (str): The Azure tenant ID.
        
        Returns:
            tuple[requests.Session, str]: Authenticated session and environment URI.
        
        Raises:
            Exception: If authentication fails or an access token cannot be obtained.
        
        Notes:
            - This method uses client credentials flow, suitable for server-to-server authentication.
            - The application must be registered in Azure as a confidential client with a client secret.
            - No user interaction is required.
        """
        environmentURI = config['environmentURI']
        scope = [environmentURI + '/' + config['scopeSuffix']]
        clientID = config['clientID']
        clientSecret = config['clientSecret']
        authority = config['authorityBase'] + config['tenantID']

        app = msal.ConfidentialClientApplication(
            clientID,
            authority=authority,
            client_credential=clientSecret
        )

        logging.info('Obtaining new token from Azure Entra ID using client secret...')

        result = app.acquire_token_for_client(scopes=scope)

        if 'access_token' in result:
            logging.info('Token obtained successfully.')
            session = requests.Session()
            session.headers.update(dict(Authorization='Bearer {}'.format(result.get('access_token'))))
            session.headers.update({'OData-MaxVersion': '4.0', 'OData-Version': '4.0', 'Accept': 'application/json'})
            return session, environmentURI
        else:
            error_msg = f"Failed to obtain token: {result.get('error')}\nDescription: {result.get('error_description')}\nCorrelation ID: {result.get('correlation_id')}"
            logging.error(error_msg)
            raise Exception(f"Authentication failed: {result.get('error')}, {result.get('error_description')}")
