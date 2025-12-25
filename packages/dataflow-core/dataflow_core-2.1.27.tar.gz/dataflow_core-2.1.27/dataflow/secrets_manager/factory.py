# secrets_manager/factory.py
import os
from .interface import SecretManager
from .providers.aws_manager import AWSSecretsManager
from .providers.azure_manager import AzureKeyVault
from .providers.gcp_manager import GCPSecretsManager
from ..configuration import ConfigurationManager

# A custom exception for clear error messages
class SecretProviderError(Exception):
    pass

def get_secret_manager() -> SecretManager:

    """Factory function to get the configured secret manager instance.

    Reads the cloud provider configuration from dataflow_auth.cfg
    to determine which cloud provider's secret manager to instantiate.

    Returns:
        SecretManager: An instance of the appropriate SecretManager subclass.
    """

    try:
        dataflow_config = ConfigurationManager('/dataflow/app/config/dataflow.cfg')
    except Exception as e:
        raise SecretProviderError(
            f"Failed to read cloud provider configuration: {str(e)}. "
            "Please check that the configuration file exists and contains the 'cloud' section."
        )

    provider = dataflow_config.get_config_value('cloudProvider', 'cloud')
    if not provider:
        raise SecretProviderError(
            "The cloud provider is not configured in config file. "
            "Please set the 'cloud' value in the 'cloud' section to 'aws' or 'azure'."
        )

    provider = provider.lower()
    print(f"Initializing secret manager for provider: {provider}")

    if provider == "aws":
        return AWSSecretsManager()

    elif provider == "azure":
        vault_url = dataflow_config.get_config_value('cloudProvider', 'key_vault')
        if not vault_url:
            raise SecretProviderError(
                "AZURE_VAULT_URL must be set when using the Azure provider."
            )
        return AzureKeyVault(vault_url=vault_url)

    elif provider == "gcp":
        project_id = dataflow_config.get_config_value('cloudProvider', 'gcp_project_id')
        region = dataflow_config.get_config_value('cloudProvider', 'gcp_region')
        if not project_id:
            raise SecretProviderError(
                "GCP_PROJECT_ID must be set when using the GCP provider."
            )
        if not region:
            raise SecretProviderError(
                "GCP_REGION must be set when using the GCP provider."
            )
        return GCPSecretsManager(project_id=project_id, region=region)

    else:
        raise SecretProviderError(
            f"Unsupported secret provider: '{provider}'. Supported providers are: aws, azure and gcp"
        )