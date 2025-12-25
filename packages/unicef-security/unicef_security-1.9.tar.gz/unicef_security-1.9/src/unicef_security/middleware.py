from typing import Iterable

from django.conf import settings

from social_core.backends.azuread_b2c import AzureADB2COAuth2
from social_core.exceptions import AuthCanceled, AuthMissingParameter
from social_django.middleware import SocialAuthExceptionMiddleware

from . import config


class UNICEFSocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    """Middleware to ignore Forgot Password Exceptions."""

    def process_exception(self, request, exception):
        if exception in [AuthCanceled, AuthMissingParameter]:
            return self.get_redirect_uri(request, exception)
        return super().process_exception(request, exception)  # pragma: no cover

    def get_redirect_uri(self, request, exception):
        strategy = getattr(request, "social_strategy", None)
        error = request.GET.get("error", None)

        # This is what we should expect:
        # ['AADB2C90118: The user has forgotten their password.\r\n
        # Correlation ID: 7e8c3cf9-2fa7-47c7-8924-a1ea91137ba9\r\n
        # Timestamp: 2018-11-13 11:37:56Z\r\n']
        error_description = request.GET.get("error_description", None)
        if (
            error == "access_denied" and isinstance(error_description, Iterable) and "AADB2C90118" in error_description
        ):  # pragma: no cover
            auth_class = AzureADB2COAuth2()
            redirect_home = auth_class.get_redirect_uri()
            reset_policy = config.AZURE_RESET_POLICY
            return "".join(
                [
                    auth_class.base_url,
                    "/oauth2/v2.0/",
                    f"authorize?p={reset_policy}",
                    f"&client_id={strategy.setting('KEY')}",
                    f"&nonce=defaultNonce&redirect_uri={redirect_home}",
                    "&scope=openid+email&response_type=code",
                ]
            )

        # TODO: In case of password reset the state can't be verified figure out a way to log the user in after reset
        if error is None:  # pragma: no cover
            return settings.LOGIN_URL

        strategy = getattr(request, "social_strategy", None)
        return strategy.setting("LOGIN_ERROR_URL") + "?msgc=loginerror"
