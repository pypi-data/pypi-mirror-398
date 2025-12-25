import os

from jwt import decode, DecodeError, ExpiredSignatureError, get_unverified_header
from social_core.backends.azuread_tenant import AzureADTenantOAuth2
from social_core.exceptions import AuthTokenError


class UNICEFAzureADTenantOAuth2Ext(AzureADTenantOAuth2):
    name = "unicef-azuread-tenant-oauth2"

    def user_data(self, access_token, *args, **kwargs):
        response = kwargs.get("response")
        id_token = response.get("id_token")

        # get key id and algorithm
        key_id = get_unverified_header(id_token)["kid"]
        key = ""
        verify = os.environ.get("OAUTH2_VERIFY", "")
        try:
            # retrieve certificate for key_id
            if verify:  # pragma: no cover
                certificate = self.get_certificate(key_id)
                key = certificate.public_key()

            options = {"verify_signature": verify}
            return decode(
                id_token,
                key=key,
                algorithms=["RS256"],
                audience=self.setting("KEY"),
                options=options,
            )
        except (DecodeError, ExpiredSignatureError) as error:  # pragma: no cover
            raise AuthTokenError(self, error)
