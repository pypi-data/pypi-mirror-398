from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import os
from dotenv import load_dotenv

load_dotenv()


class KeyVaultClient:
    def __init__(
        self,
        tenant_id: str = None,
        client_id: str = None,
        client_secret: str = None,
        key_vault_name: str = "kv-pi-001",
    ):
        """
        Initialize the KeyVaultClient with Azure credentials and Key Vault URL.

        :param tenant_id: Azure Tenant ID
        :param client_id: Service Principal Client ID
        :param client_secret: Service Principal Client Secret
        :param key_vault_url: The URL of the Azure Key Vault
        """
        # If user didn't pass any of the credentials, retrieve from environment
        if not all([tenant_id, client_id, client_secret]):
            tenant_id = tenant_id or os.getenv("AZURE_SPN_PI01_TENANT_ID")
            client_id = client_id or os.getenv("AZURE_SPN_PI01_CLIENT_ID")
            client_secret = client_secret or os.getenv("AZURE_SPN_PI01_CLIENT_SECRET")
            if not all([tenant_id, client_id, client_secret]):
                raise ValueError("Azure credentials must be provided.")

        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret

        self.credential = ClientSecretCredential(
            tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
        )
        self.key_vault_url = key_vault_name
        self.secret_client = SecretClient(
            vault_url=f"https://{key_vault_name}.vault.azure.net/",
            credential=self.credential,
        )

    def get_secret(self, secret_name: str):
        """
        Fetch a secret from the Azure Key Vault.

        :param secret_name: Name of the secret to fetch
        :return: The value of the secret
        """
        try:
            secret = self.secret_client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            print(f"Error fetching secret '{secret_name}': {e}")
            return None
