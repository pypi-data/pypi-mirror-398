from urllib.parse import quote

from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse

from social_core.pipeline import social_auth, user as social_core_user
from social_core.pipeline.user import USER_FIELDS

from .config import UNICEF_EMAIL


def social_details(backend, details, response, *args, **kwargs):
    resp = social_auth.social_details(backend, details, response, *args, **kwargs)
    user = kwargs.get("user")
    if user:
        # here we are preventing messing up between current us and social user
        unauthorized = reverse("unicef_security:unauthorized")
        return HttpResponseRedirect(f"{unauthorized}?eu={user.email}&msgc=alreadyauthenticated")

    resp["details"]["idp"] = response.get("idp")

    if not resp["details"].get("email"):  # pragma: no cover
        resp["details"]["email"] = (
            response.get("email") if response.get("email") else response["signInNames.emailAddress"]
        )
    email = resp["details"].get("email")
    resp["details"]["email"] = email.lower().strip()
    return resp


def get_username(strategy, details, backend, user=None, *args, **kwargs):
    username = details.get("email")

    try:
        get_user_model().objects.get(username=username)

    except get_user_model().DoesNotExist:
        email = quote(username)
        unauthorized = reverse("unicef_security:unauthorized")
        return HttpResponseRedirect(f"{unauthorized}?eu={email}&msgc=nouser")

    return {"username": details.get("email")}


def create_unicef_user(strategy, details, backend, user=None, *args, **kwargs):
    """Override create_user, to create only UNICEF users."""
    if user:
        return {"is_new": False}

    fields = {name: kwargs.get(name, details.get(name)) for name in backend.setting("USER_FIELDS", USER_FIELDS)}

    if not (fields and details.get("email", "").endswith(UNICEF_EMAIL)):
        return None

    response = kwargs.get("response")
    if response:
        email = response.get("email") or response.get("signInNames.emailAddress")
        if email and not email.endswith(UNICEF_EMAIL):
            return None

    return {"is_new": True, "user": strategy.create_user(**fields)}


def user_details(strategy, details, backend, user=None, *args, **kwargs):
    """Update the user see what the property to map by is here updates_available = False."""
    if user:
        user.username = user.email
        user.first_name = details["first_name"]
        user.last_name = details["last_name"]
        user.set_unusable_password()
        user.save()

    return social_core_user.user_details(strategy, details, backend, user, *args, **kwargs)
