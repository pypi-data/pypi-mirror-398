import os
from typing import Any

from django.http import HttpRequest


def current_state(request: HttpRequest) -> dict[str, Any]:
    return {
        "app": {
            "version": os.environ.get("VERSION", ""),
            "build_date": os.environ.get("BUILD_DATE", ""),
            "commit": os.environ.get("GIT_SHA", "-"),
        },
    }
