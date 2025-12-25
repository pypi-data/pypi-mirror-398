from django.core.cache import cache
from django.core.management.base import BaseCommand
from django_redis import get_redis_connection


class Command(BaseCommand):
    help = "Purges the entire cache."

    def handle(self, *args, **options):
        self.stdout.write("Purging cache...")

        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Successfully purged cache using cache.clear()."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to purge cache using cache.clear(): {e}"))

        try:
            redis_conn = get_redis_connection("default")
            redis_conn.flushall()
            self.stdout.write(self.style.SUCCESS("Successfully purged cache using redis flushall()."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to purge cache using redis flushall(): {e}"))
