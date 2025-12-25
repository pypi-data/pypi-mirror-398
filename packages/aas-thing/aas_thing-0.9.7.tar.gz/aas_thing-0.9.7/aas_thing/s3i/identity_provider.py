from keycloak import KeycloakOpenID


class S3IIdentityProviderClient:
    def __init__(self, client_id, client_secret, realm, idp_url, logger, username=None, password=None) -> None:
        """
        Initialize the connection to S3I Identity Provider.

        The S3I Identity Provider is used to authenticate with the S³I services.
        It requires a client ID, client secret, realm, and IDP URL to connect to the
        S³I Identity Provider. Additionally, it can accept a username and password
        to use for authentication.

        :param client_id: Client ID from S³I Identity Provider
        :param client_secret: Client secret from S³I Identity Provider
        :param realm: Realm name from S³I Identity Provider
        :param idp_url: URL of the S³I Identity Provider
        :param logger: Logger for the S3I Identity Provider
        :param username: Username for the S³I Identity Provider, defaults to None
        :param password: Password for the S³I Identity Provider, defaults to None
        :raises Exception: If the client ID, client secret, realm, or IDP URL are invalid
        """
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__realm = realm
        self.__idp_url = idp_url
        self.__username = username
        self.__password = password

        # Initialize the connection to the Keycloak server
        self.__connection = None

        # Initialize the token set returned from the Keycloak server
        self.__token_set = None

        # Initialize the access token returned from the Keycloak server
        self.__access_token = None

        # Initialize the refresh token returned from the Keycloak server
        self.__refresh_token = None

        # Initialize the logger for the S3I Identity Provider
        self.__logger = logger

    @property
    def client_id(self):
        """
        Client ID from S³I Identity Provider

        :return: Client ID
        """

        return self.__client_id

    @property
    def token_set(self):
        """
        Token set from S³I Identity Provider

        :return: Token set
        """

        return self.__token_set

    @property
    def access_token(self):
        """
        Access token from S³I Identity Provider

        :return: Access token
        """

        return self.__access_token

    @property
    def refresh_token(self):
        """
        Refresh token from S³I Identity Provider

        :return: Refresh token
        """

        return self.__refresh_token

    def connect(self):
        """
        Connect to the S³I Identity Provider

        Connects to the S³I Identity Provider with the given client ID, client secret, realm, and IDP URL.

        :raises Exception: If the client ID, client secret, realm, or IDP URL are invalid
        """
        self.__logger.info("Connect to the Identity Provider")
        self.__connection = KeycloakOpenID(
            server_url=self.__idp_url,
            realm_name=self.__realm,
            client_id=self.__client_id,
            client_secret_key=self.__client_secret
        )

    def get_token_set(self):
        """
        Get a token set from the S³I Identity Provider

        Retrieves a token set from the S³I Identity Provider using the client ID, client secret, realm, and IDP URL.
        If a username and password are provided, the token set is retrieved using the username and password.
        If not, the token set is retrieved using the client credentials.

        :return: Token set
        """
        if self.__username and self.__password:
            self.__token_set = self.__connection.token(
                username=self.__username,
                password=self.__password
            )
        else:
            self.__token_set = self.__connection.token(
                grant_type=["client_credentials"]
            )
        if self.__token_set:
            self.__logger.info("Token set obtained")
            self.__access_token = self.__token_set["access_token"]
            self.__refresh_token = self.__token_set.get("refresh_token")
            return self.__token_set
        else:
            self.__logger.info("Token set not obtained")
            return None
        
    def refresh_token_set(self):
        """
        Refresh the token set from the S³I Identity Provider

        Refreshes the token set from the S³I Identity Provider by gathering a new access token.
        The refresh token is not used for client credentials grant type.

        TODO: Remove this method and used get_token_set() directly since refresh is not applicable for client credentials.
        """
        self.get_token_set()
        self.__logger.info("Token set refreshed")

    def disconnect(self):
        """
        Disconnect from the S³I Identity Provider

        Disconnects from the S³I Identity Provider by logging out the refresh token.
        """
        self.__logger.info("Disconnect from the Identity Provider")
        if isinstance(self.__connection, KeycloakOpenID):
            # Logout the refresh token
            self.__connection.logout(
                self.__refresh_token
            )
