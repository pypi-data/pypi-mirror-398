from aas_python_http_client import (
    ApiClient,
    Configuration,
    AssetAdministrationShellRegistryAPIApi,
    SubmodelRegistryAPIApi,
)
from aas_python_http_client.util import string_to_base64url
import json


class S3IDirectoryClient:

    """
    This class is used to interact with the S³I Directory, which is realized using an AAS Registry.
    """

    def __init__(self, dir_url: str):
        """Initializes the connection to the S³I Directory that is realized using AAS Registry

        :param str dir_url: The URL of the S³I Directory, e.g., http://dir.mmi-0.s3i.mmi-services.de/ for the global instance
        """

        # Create a configuration for the API client
        configuration = Configuration()
        # Set the host URL of the API client to the given directory URL
        configuration.host = dir_url
        # Create an API client with the given configuration
        api_client = ApiClient(configuration=configuration)
        # Create an instance of the AssetAdministrationShellRegistryAPIApi
        # with the given API client
        self.api_client = AssetAdministrationShellRegistryAPIApi(
            api_client=api_client
        )

    def get_all_aas(self) -> list:
        """Returns all AAS Descriptors from the S³I Directory

        This function queries the S³I Directory and returns a list of all AAS
        Descriptors, which are stored in the directory.

        :return: A list of all AAS Descriptors
        """
        return self.api_client.get_all_asset_administration_shell_descriptors()

    def get_aas_by_id(self, aas_id: str) -> dict:
        """
        Returns a specific AAS Descriptor

        This function queries the S³I Directory and returns the AAS
        Descriptor, which is stored in the directory and has the given id.

        :param str aas_id: The AAS's unique id
        :return: The AAS Descriptor with the given id
        """

        # Get the AAS Descriptor by id
        aas_descriptor = self.api_client.get_asset_administration_shell_descriptor_by_id(
            string_to_base64url(aas_id)
        )

        # Return the AAS Descriptor
        return aas_descriptor

    def update_aas(self, aas_id: str, aas_json: dict):
        """Updates a specific AAS Descriptor

        This function updates a specific AAS Descriptor in the S³I Directory.
        The AAS Descriptor is identified by the given id.

        :param str aas_id: The AAS's unique id, that you want to update
        :param dict aas_json: The AAS Json file
        :raises ValueError: If the given aas_id does not match the id in the aas_json
        :return: Registers a new AAS Descriptor and prints a message, if successful
        """
        # Check if the given aas_id matches the id in the aas_json
        if aas_id != aas_json.get("id"):
            raise ValueError("The given aas_id does not match the id in the aas_json")

        # Update the AAS Descriptor
        self.api_client.put_asset_administration_shell_descriptor_by_id(
            json.dumps(aas_json),
            string_to_base64url(aas_id),
        )





