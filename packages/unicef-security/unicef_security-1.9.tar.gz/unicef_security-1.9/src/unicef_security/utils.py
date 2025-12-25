from django.conf import settings


def get_setting(settings_list, default=None):
    for setting_name in settings_list:
        if value := getattr(settings, setting_name, None):
            return value
    return default
