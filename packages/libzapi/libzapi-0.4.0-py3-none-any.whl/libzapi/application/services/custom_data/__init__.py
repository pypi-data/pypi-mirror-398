from libzapi.application.services.custom_data.custom_objects_service import CustomObjectsService
from libzapi.application.services.custom_data.custom_object_fields_service import CustomObjectFieldsService
from libzapi.application.services.custom_data.custom_object_records import CustomObjectRecordsService
from libzapi.infrastructure.http.auth import oauth_headers, api_token_headers
from libzapi.infrastructure.http.client import HttpClient
import libzapi.infrastructure.api_clients.custom_data as api


class CustomData:
    def __init__(
        self, base_url: str, oauth_token: str | None = None, email: str | None = None, api_token: str | None = None
    ):
        if oauth_token:
            headers = oauth_headers(oauth_token)
        elif email and api_token:
            headers = api_token_headers(email, api_token)
        else:
            raise ValueError("Provide oauth_token or email+api_token")

        http = HttpClient(base_url, headers=headers)

        # Initialize services
        self.custom_objects = CustomObjectsService(api.CustomObjectApiClient(http))
        self.custom_object_fields = CustomObjectFieldsService(api.CustomObjectFieldApiClient(http))
        self.custom_object_records = CustomObjectRecordsService(api.CustomObjectRecordApiClient(http))

