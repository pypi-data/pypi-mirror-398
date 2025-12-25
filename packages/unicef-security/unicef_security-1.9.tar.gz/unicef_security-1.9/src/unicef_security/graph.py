import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

import requests
from constance import config as constance
from social_django.models import UserSocialAuth

from unicef_security.config import GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET

from . import config

AZURE_GRAPH_API_TOKEN_CACHE_KEY = "azure_graph_api_token_cache_key"  # noqa
AZURE_GRAPH_DELTA_LINK_KEY = "azure_graph_delta_link_key"

logger = logging.getLogger(__name__)

DJANGOUSERMAP = {
    "_pk": ["username"],
    "username": "userPrincipalName",
    "email": "mail",
    "azure_id": "id",
    "job_title": "jobTitle",
    "display_name": "displayName",
    "first_name": "givenName",
    "last_name": "surname",
}

ADMIN_EMAILS = [i[1] for i in settings.ADMINS]


def default_group(**kwargs):
    is_new = kwargs.get("is_new", False)
    user = kwargs.get("user")
    if is_new:
        if user.email in ADMIN_EMAILS:
            user.is_staff = True
            user.is_superuser = True
            user.save()
        elif group_name := constance.DEFAULT_GROUP:
            group = Group.objects.filter(name=group_name).first()
            if group:
                user.groups.add(group)


def get_unicef_user(backend, details, response, *args, **kwargs):
    User = get_user_model()  # noqa
    if details.get("email"):
        filters = {"email": details["email"]}
    elif details.get("unique_name"):
        filters = {"username": details["unique_name"]}
    elif details.get("username"):
        filters = {"username": details["username"]}

    try:
        user = User.objects.get(**filters)
        social = user.social_auth.get()
        user.social_user = social
        created = False
    except (User.DoesNotExist, UserSocialAuth.DoesNotExist):
        for k, v in response.items():
            if k in ["email", "family_name", "unique_name"]:
                details[k] = v
        try:
            sync = Synchronizer()
            data = sync.get_user(details["email"])

            for k, v in data.items():
                details[k] = v

        except (ValueError, KeyError) as e:  # pragma: no cover
            logger.error(e)

        user, created = User.objects.get_or_create(
            username=details["unique_name"],
            defaults={
                "first_name": details.get("givenName", ""),
                "last_name": details.get("surname", ""),
                "job_title": details.get("jobTitle", ""),
                "display_name": details.get("displayName", details["unique_name"]),
                "email": details.get("email", ""),
                "azure_id": details.get("id"),
            },
        )
        social, _ = UserSocialAuth.objects.get_or_create(user=user, provider=backend.name, uid=user.username)
        user.social_user = social
    return {"user": user, "social": social, "uid": details.get("id"), "is_new": created}


class SyncResult:
    def __init__(self, keep_records=False):
        """Class to synchronize against external providers.

        :param keep_records: if True keep track of record instances
        """
        self.created = []
        self.updated = []
        self.skipped = []
        self.keep_records = keep_records

    def log(self, *result):
        if len(result) == 2:
            obj = {True: result[0], False: result[0].pk}[self.keep_records]
            if result[1]:
                self.created.append(obj)
            else:
                self.updated.append(obj)
        else:
            self.skipped.append(result)

    def __add__(self, other):
        if isinstance(other, SyncResult):
            ret = SyncResult()
            ret.created = self.created + other.created
            ret.updated = self.updated + other.updated
            ret.skipped = self.skipped + other.skipped
            return ret
        raise ValueError("Cannot add %s to SyncResult object" % type(other))

    def __repr__(self):
        return f"<SyncResult: {len(self.created)} {len(self.updated)} {len(self.skipped)}>"

    def __eq__(self, other):
        if isinstance(other, SyncResult):
            return self.created == other.created and self.updated == other.updated and self.skipped == other.skipped
        return False


NotSet = object()


class Synchronizer:
    def __init__(self, user_model=None, mapping=None, echo=None, identifier=None, secret=None):
        self.id = identifier or GRAPH_CLIENT_ID
        self.secret = secret or GRAPH_CLIENT_SECRET

        self.user_model = user_model or get_user_model()
        self.field_map = dict(mapping or DJANGOUSERMAP)
        self.user_pk_fields = self.field_map.pop("_pk")
        self._baseurl = f"{config.AZURE_GRAPH_API_BASE_URL}/{config.AZURE_GRAPH_API_VERSION}/users"
        self.startUrl = "%s/delta" % self._baseurl
        self.access_token = self.get_token()
        self.next_link = None
        self._delta_link = ""
        self.echo = echo or (lambda lmn: True)

    def get_token(self):
        if not self.id and self.secret:  # pragma: no cover
            raise ValueError("Configure AZURE_CLIENT_ID and/or AZURE_CLIENT_SECRET")
        post_dict = {
            "grant_type": "client_credentials",
            "client_id": self.id,
            "client_secret": self.secret,
            "resource": config.AZURE_GRAPH_API_BASE_URL,
        }
        response = requests.post(f"{config.AZURE_URL}/unicef.org/oauth2/token", post_dict, timeout=60)
        if response.status_code != 200:  # pragma: no cover
            logger.error(f"Unable to fetch token from Azure. {response.status_code} {response.content}")
            raise BaseException(f"Error during token retrieval: {response.status_code} {response.content}")
        jresponse = response.json()
        return jresponse["access_token"]

    @property
    def delta_link(self):
        return self._delta_link

    @delta_link.setter
    def delta_link(self, value):
        self._delta_link = value

    def get_page(self, url, single=False):
        while True:
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            try:
                response = requests.get(url, headers=headers, timeout=60)
                if response.status_code == 401:  # pragma: no cover
                    data = response.json()
                    if data["error"]["message"] == "Access token has expired.":
                        continue
                    raise ConnectionError(f"400: Error processing the response {response.content}")

                if response.status_code != 200:  # pragma: no cover
                    raise ConnectionError(
                        f"Code {response.status_code}. Error processing the response {response.content}"
                    )
                break
            except ConnectionError as e:  # pragma: no cover
                logger.exception(e)
                raise

        jresponse = response.json()
        self.next_link = jresponse.get("@odata.nextLink", None)
        self.delta_link = jresponse.get("@odata.deltaLink", None)
        if single:
            return jresponse
        return jresponse.get("value", [])

    def __iter__(self):
        values = self.get_page(self.startUrl)
        pages = 1
        while True:
            try:
                yield values.pop()
            except IndexError:
                if not self.next_link:
                    logger.debug(f"All pages  fetched. deltaLink: {self.delta_link}")
                    break
                values = self.get_page(self.next_link)
                logger.debug(f"fetched page {pages}")
                pages += 1
            except GeneratorExit as e:
                logger.exception(e)
                break

    def get_record(self, user_info: dict) -> (dict, dict):
        data = {fieldname: user_info.get(mapped_name, "") for fieldname, mapped_name in self.field_map.items()}
        pk = {fieldname: data.pop(fieldname) for fieldname in self.user_pk_fields}
        return pk, data

    def fetch_users(self, filter_params, max_records=None, callback=None):
        self.startUrl = "%s?$filter=%s" % (self._baseurl, filter_params)
        return self.synchronize(max_records=max_records, callback=callback)

    def search_users(self, record):
        url = "%s?$filter=" % self._baseurl
        filters = []
        field_map = {
            "email": "mail eq '{value}'",
            "last_name": "surname eq '{value}'",
            "first_name": "givenName eq '{value}'",
        }

        for field, filter_template in field_map.items():
            value = getattr(record, field, None)
            if value:
                filters.append(filter_template.format(value=value))

        page = self.get_page(url + " or ".join(filters), single=True)
        return page["value"]

    def filter_users_by_email(self, email):
        """Filter users by email.

        https://graph.microsoft.com/v1.0/users?$filter=mail eq 'sapostolico@unicef.org'
        """
        url = "%s?$filter=mail eq '%s'" % (self._baseurl, email)
        page = self.get_page(url, single=True)
        return page["value"]

    def get_user(self, username):
        url = "%s/%s" % (self._baseurl, username)
        return self.get_page(url, single=True)

    def sync_user(self, user, azure_id=None):
        if not (azure_id or user.azure_id):
            raise ValueError("Cannot sync user without azure_id")
        url = "%s/%s" % (self._baseurl, azure_id or user.azure_id)
        user_info = self.get_page(url, single=True)
        pk, values = self.get_record(user_info)
        user, __ = self.user_model.objects.update_or_create(**pk, defaults=values)
        return user

    def resume(self, *, delta_link=None, max_records=None):
        if delta_link:
            self.startUrl = delta_link
        return self.synchronize(max_records)

    def is_valid(self, user_info):
        return user_info.get("email")

    def synchronize(self, max_records=None, callback=None):
        logger.debug("Start Azure user synchronization")
        results = SyncResult()
        try:
            for i, user_info in enumerate(iter(self)):
                pk, values = self.get_record(user_info)
                if self.is_valid(values):
                    user, created = self.user_model.objects.update_or_create(**pk, defaults=values)
                    if callback:
                        callback(user=user, is_new=created)
                    self.echo([user, created])
                    results.log(user, created)
                else:
                    results.log(user_info)
                if max_records and i > max_records:
                    break
        except BaseException as e:  # pragma: no cover
            logger.exception(e)
            raise
        logger.debug(f"End Azure user synchronization: {results}")
        return results
