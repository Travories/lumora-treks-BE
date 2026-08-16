import logging
import sys

from django.apps import AppConfig

logger = logging.getLogger("lumora.startup")

# Management commands that don't touch the DB/cache — skip the connectivity
# banner for these so `collectstatic` etc. doesn't print noise or fail early.
_SKIP_COMMANDS = {"collectstatic", "makemigrations", "shell", "check"}


class CoreConfig(AppConfig):
    name = "apps.core"
    label = "core"
    verbose_name = "Core (media & shared blocks)"

    def ready(self):
        if len(sys.argv) > 1 and sys.argv[1] in _SKIP_COMMANDS:
            return
        _log_connectivity()


def _log_connectivity():
    from django.conf import settings
    from django.db import connection

    try:
        connection.ensure_connection()
        db_name = connection.settings_dict.get("NAME")
        logger.info("Database connected (%s)", db_name)
    except Exception as exc:
        logger.warning("Database connection FAILED: %s", exc)

    if getattr(settings, "ENABLE_REDIS", False) and getattr(settings, "REDIS_URL", ""):
        try:
            import redis

            redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2).ping()
            logger.info("Redis connected")
        except Exception as exc:
            logger.warning("Redis connection FAILED: %s", exc)
    else:
        logger.info("Redis disabled (ENABLE_REDIS not set)")
