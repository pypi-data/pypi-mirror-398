import hashlib
import json
import os
from datetime import datetime

from django.conf import settings

_build_info_cache = None


def add_build_info(request):
    if settings.DEBUG:
        # Generate SHA-1 hash from current timestamp
        timestamp = str(datetime.now().timestamp()).encode("utf-8")
        dev_hash = hashlib.sha1(timestamp).hexdigest()
        return {
            "build_info": {
                "commit": dev_hash,
                "date": datetime.now(),
            }
        }

    global _build_info_cache

    if _build_info_cache is None:
        path = settings.BASE_DIR / "build-info.json"

        if os.path.exists(path):
            with open(path) as f:
                build_info = json.load(f)

                _build_info_cache = {
                    "build_info": {
                        "commit": build_info["commit"],
                        "date": datetime.fromisoformat(build_info["date"]),
                    }
                }
        else:
            # No build info available
            _build_info_cache = {}

    return _build_info_cache
