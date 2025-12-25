from aas_python_http_client import (
    ApiClient,
    Configuration,
    AssetAdministrationShellRepositoryAPIApi
)
from aas_python_http_client.util import string_to_base64url
import json

class S3IRepositoryClient:
    def __init__(self, repo_url: str):
        """Initializes the connection to the S³I Repository, which is realized using AAS Environment

        :param repo_url: The URL of the S³I Repository, e.g., http://repo.mmi-0.s3i.mmi-services.de/ for the global instance
        """
        # Create a configuration for the API client
        configuration = Configuration()
        # Set the host URL of the API client to the given repository URL
        configuration.host = repo_url
        # Create an API client with the given configuration
        api_client = ApiClient(configuration=configuration)
        # Create an instance of the AssetAdministrationShellRepositoryAPIApi
        # with the given API client
        self.api_client = AssetAdministrationShellRepositoryAPIApi(
            api_client=api_client
        )

    def get_repo_all_aas(self) -> list:
        """Returns all Asset Administration Shells from the Repository

        This method returns a list of all Asset Administration Shells from the
        S³I Repository.

        :return: A list of all Asset Administration Shells
        """
        return self.api_client.get_all_asset_administration_shells()


    def get_repo_aas_by_id(self, aas_id: str):
        """Returns a specific Asset Administration Shell from the Repository

        This method returns a specific Asset Administration Shell from the
        S³I Repository. The AAS is identified by the given id.

        :param str aas_id: The AAS's unique id (required)
        :return: The Asset Administration Shell with the given id
        """
        return self.api_client.get_asset_administration_shell_by_id(
            string_to_base64url(aas_id)
        )

    def update_repo_aas(self, aas_id: str, aas_json: dict):
        """Updates a specific Asset Administration Shell from the Repository

        This method updates a specific Asset Administration Shell from the
        S³I Repository. The AAS is identified by the given id.

        :param str aas_id: The AAS's unique id, that you want to update (required)
        :param dict aas_json: The AAS Json file (required)
        :return: None
        """
        self.api_client.put_asset_administration_shell_by_id(
            json.dumps(aas_json),
            string_to_base64url(aas_id),
        )

    def get_asset_information(self, aas_id):
        """Returns the Asset Information of a specified AAS

        This method returns the Asset Information of an Asset Administration
        Shell from the S³I Repository. The AAS is identified by the given id.

        :param str aas_id: The Asset Administration Shell’s unique id (required)
        :return: The Asset Information of the specified AAS
        """
        return self.api_client.get_asset_information_aas_repository(
            string_to_base64url(aas_id)
        )

    def get_all_submodel_refs(self, aas_id: str, limit: str = None):
        """Returns the References of all submodels of an AAS

        This method returns the References of all submodels of an Asset
        Administration Shell from the S³I Repository. The AAS is identified
        by the given id.

        :param str aas_id: The Asset Administration Shell's unique id (required)
        :param str limit: The maximum number of elements in the response array
        :return: The submodel references of the specified AAS
        """
        if limit is None:
            sm_ref = self.api_client.get_all_submodel_references_aas_repository(
                string_to_base64url(aas_id)
            )
        else:
            sm_ref = self.api_client.get_all_submodel_references_aas_repository(
                string_to_base64url(aas_id), limit=limit
            )
        return sm_ref

    def delete_submodel_ref(self, aas_id: str, submodel_id: str):
        """Deletes the submodel reference from the Asset Administration Shell. Does not delete the submodel itself!

        This method deletes the submodel reference from the Asset Administration
        Shell. The AAS is identified by the given id and the submodel is
        identified by the given submodel id.

        :param str aas_id: The Asset Administration Shell's unique id (required)
        :param str submodel_id: The Submodel's unique id (required)
        :return: None
        """

        self.api_client.delete_submodel_reference_by_id_aas_repository(
            string_to_base64url(aas_id), string_to_base64url(submodel_id)
        )

