import logging
import os
import signal

from django.conf import settings
from django.db import connection
from django.http import HttpResponse

from .azure_helper import get_db_password

logger = logging.getLogger("pulumi_django_azure.health_check")


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def _self_heal(self):
        logger.warning("Self-healing by gracefully restarting Gunicorn.")

        master_pid = os.getppid()

        logger.debug("Master PID: %d", master_pid)

        # https://docs.gunicorn.org/en/latest/signals.html

        # Reload a new master with new workers,
        # since the application is preloaded this is the only safe way for now.
        os.kill(master_pid, signal.SIGUSR2)

        # Gracefully shutdown the current workers
        os.kill(master_pid, signal.SIGTERM)

    def __call__(self, request):
        if request.path == settings.HEALTH_CHECK_PATH:
            # Update the database credentials if needed
            if settings.AZURE_DB_PASSWORD:
                try:
                    current_db_password = settings.DATABASES["default"]["PASSWORD"]
                    new_db_password = get_db_password()

                    if new_db_password != current_db_password:
                        logger.debug("Database password has changed, updating credentials")
                        settings.DATABASES["default"]["PASSWORD"] = new_db_password

                        # Close existing connections to force reconnect with new password
                        connection.close()
                    else:
                        logger.debug("Database password unchanged, keeping existing credentials")
                except Exception as e:
                    logger.error("Failed to update database credentials: %s", str(e))
                    self._self_heal()
                    return HttpResponse(status=503)

            try:
                # Test the database connection
                connection.ensure_connection()
                logger.debug("Database connection check passed")

                return HttpResponse("OK")

            except Exception as e:
                logger.error("Health check failed with unexpected error: %s", str(e))
                self._self_heal()
                return HttpResponse(status=503)

        return self.get_response(request)
