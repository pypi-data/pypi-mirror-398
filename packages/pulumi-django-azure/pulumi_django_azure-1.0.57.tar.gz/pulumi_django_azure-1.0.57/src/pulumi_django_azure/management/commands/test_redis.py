"""
Management command to test Redis connectivity and functionality.
"""

import time

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Test Redis connectivity and basic functionality"

    def add_arguments(self, parser):
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed Redis information and run comprehensive tests",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Only show errors and final status",
        )

    def handle(self, *args, **options):
        verbosity = 0 if options["quiet"] else (2 if options["detailed"] else 1)

        if verbosity >= 1:
            self.stdout.write("Testing Redis connectivity...")
            self.stdout.write("-" * 50)

        try:
            # Test basic connectivity
            self._test_basic_connectivity(verbosity)

            # Test basic cache operations
            self._test_cache_operations(verbosity)

            # If detailed mode, run additional tests
            if options["detailed"]:
                self._test_detailed_operations(verbosity)
                self._show_cache_info(verbosity)

            if verbosity >= 1:
                self.stdout.write(self.style.SUCCESS("✓ All Redis tests passed successfully!"))

        except Exception as e:
            if verbosity >= 1:
                self.stdout.write(self.style.ERROR(f"✗ Redis test failed: {str(e)}"))
            raise CommandError(f"Redis connectivity test failed: {str(e)}") from e

    def _test_basic_connectivity(self, verbosity):
        """Test basic Redis connectivity."""
        if verbosity >= 2:
            self.stdout.write("Testing basic connectivity...")

        try:
            # Try to set and get a simple value
            cache.set("redis_test_key", "test_value", 30)
            value = cache.get("redis_test_key")

            if value != "test_value":
                raise Exception("Failed to retrieve test value from cache")

            # Clean up
            cache.delete("redis_test_key")

            if verbosity >= 2:
                self.stdout.write(self.style.SUCCESS("  ✓ Basic connectivity test passed"))

        except Exception as e:
            raise Exception(f"Basic connectivity test failed: {str(e)}") from e

    def _test_cache_operations(self, verbosity):
        """Test various cache operations."""
        if verbosity >= 2:
            self.stdout.write("Testing cache operations...")

        test_data = {
            "string_test": "Hello Redis!",
            "number_test": 42,
            "dict_test": {"key": "value", "nested": {"data": True}},
            "list_test": [1, 2, 3, "four", 5.0],
        }

        try:
            # Test different data types
            for key, value in test_data.items():
                cache.set(f"test_{key}", value, 60)
                retrieved_value = cache.get(f"test_{key}")

                if retrieved_value != value:
                    raise Exception(f"Data mismatch for {key}: expected {value}, got {retrieved_value}")

                if verbosity >= 2:
                    self.stdout.write(f"  ✓ {key}: {type(value).__name__} data test passed")

            # Test cache.get_or_set
            default_value = "default_from_function"
            result = cache.get_or_set("test_get_or_set", default_value, 60)
            if result != default_value:
                raise Exception("get_or_set test failed")

            if verbosity >= 2:
                self.stdout.write("  ✓ get_or_set operation test passed")

            # Test cache.add (should fail on existing key)
            if cache.add("test_string_test", "should_not_override"):
                raise Exception("add() should have failed on existing key")

            if verbosity >= 2:
                self.stdout.write("  ✓ add operation test passed")

            # Test cache expiration
            cache.set("test_expiration", "will_expire", 1)
            time.sleep(1.1)  # Wait for expiration
            expired_value = cache.get("test_expiration")
            if expired_value is not None:
                raise Exception("Cache expiration test failed - value should have expired")

            if verbosity >= 2:
                self.stdout.write("  ✓ Cache expiration test passed")

            # Clean up test keys
            for key in test_data:
                cache.delete(f"test_{key}")
            cache.delete("test_get_or_set")

            if verbosity >= 2:
                self.stdout.write(self.style.SUCCESS("  ✓ All cache operations tests passed"))

        except Exception as e:
            raise Exception(f"Cache operations test failed: {str(e)}") from e

    def _test_detailed_operations(self, verbosity):
        """Run detailed Redis operations tests."""
        if verbosity >= 2:
            self.stdout.write("Running detailed operations...")

        try:
            # Test cache.get_many and set_many
            test_data = {
                "bulk_key_1": "value_1",
                "bulk_key_2": "value_2",
                "bulk_key_3": "value_3",
            }

            cache.set_many(test_data, 60)
            retrieved_data = cache.get_many(test_data.keys())

            for key, expected_value in test_data.items():
                if retrieved_data.get(key) != expected_value:
                    raise Exception(f"Bulk operation failed for key {key}")

            if verbosity >= 2:
                self.stdout.write("  ✓ Bulk operations (set_many/get_many) test passed")

            # Test cache.delete_many
            cache.delete_many(test_data.keys())
            remaining_data = cache.get_many(test_data.keys())
            if any(remaining_data.values()):
                raise Exception("delete_many operation failed")

            if verbosity >= 2:
                self.stdout.write("  ✓ Bulk delete (delete_many) test passed")

            # Test cache versioning if supported
            try:
                cache.set("version_test", "version_1", 60, version=1)
                cache.set("version_test", "version_2", 60, version=2)

                v1_value = cache.get("version_test", version=1)
                v2_value = cache.get("version_test", version=2)

                if v1_value == "version_1" and v2_value == "version_2":
                    if verbosity >= 2:
                        self.stdout.write("  ✓ Cache versioning test passed")
                else:
                    if verbosity >= 2:
                        self.stdout.write("  ! Cache versioning not supported or failed")

                cache.delete("version_test", version=1)
                cache.delete("version_test", version=2)

            except Exception:
                if verbosity >= 2:
                    self.stdout.write("  ! Cache versioning not supported")

        except Exception as e:
            raise Exception(f"Detailed operations test failed: {str(e)}") from e

    def _show_cache_info(self, verbosity):
        """Show information about the cache configuration."""
        if verbosity >= 2:
            self.stdout.write("\nCache Configuration Information:")
            self.stdout.write("-" * 35)

            # Show cache backend information
            cache_config = getattr(settings, "CACHES", {}).get("default", {})
            backend = cache_config.get("BACKEND", "Unknown")
            location = cache_config.get("LOCATION", "Not specified")

            self.stdout.write(f"Backend: {backend}")
            self.stdout.write(f"Location: {location}")

            # Show cache options if any
            options = cache_config.get("OPTIONS", {})
            if options:
                self.stdout.write("Options:")
                for key, value in options.items():
                    # Don't show sensitive information like passwords
                    if "password" in key.lower() or "secret" in key.lower():
                        value = "***hidden***"
                    self.stdout.write(f"  {key}: {value}")

            # Try to get cache stats if available
            try:
                if hasattr(cache, "_cache") and hasattr(cache._cache, "get_stats"):
                    stats = cache._cache.get_stats()
                    if stats:
                        self.stdout.write("\nCache Statistics:")
                        for stat_key, stat_value in stats.items():
                            self.stdout.write(f"  {stat_key}: {stat_value}")
            except Exception:
                pass  # Stats not available

            # Test if we can determine Redis info
            try:
                # Try to access Redis client directly if using django-redis
                if hasattr(cache, "_cache") and hasattr(cache._cache, "_client"):
                    client = cache._cache._client
                    if hasattr(client, "connection_pool"):
                        pool = client.connection_pool
                        self.stdout.write("\nConnection Pool Info:")
                        self.stdout.write(f"  Max connections: {getattr(pool, 'max_connections', 'Unknown')}")
                        self.stdout.write(f"  Connection class: {getattr(pool, 'connection_class', 'Unknown')}")

                        connection_kwargs = getattr(pool, "connection_kwargs", {})
                        if connection_kwargs:
                            self.stdout.write("  Connection parameters:")
                            for key, value in connection_kwargs.items():
                                if "password" in key.lower():
                                    value = "***hidden***"
                                self.stdout.write(f"    {key}: {value}")
            except Exception:
                pass  # Redis-specific info not available
