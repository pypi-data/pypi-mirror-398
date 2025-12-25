import os

from azure.mgmt.cdn import CdnManagementClient
from azure.mgmt.cdn.models import AfdPurgeParameters
from django.conf import settings
from django.core.management.base import BaseCommand

from pulumi_django_azure.azure_helper import AZURE_CREDENTIAL


class Command(BaseCommand):
    help = "Purges the CDN endpoint"

    def add_arguments(self, parser):
        parser.add_argument(
            "--wait",
            action="store_true",
            help="Wait for the purge operation to complete",
        )

    def handle(self, *args, **options):
        # Read environment variables
        resource_group = os.getenv("WEBSITE_RESOURCE_GROUP")
        profile_name = os.getenv("CDN_PROFILE")
        endpoint_name = os.getenv("CDN_ENDPOINT")
        cdn_host = os.getenv("CDN_HOST")
        media_container = os.getenv("AZURE_STORAGE_CONTAINER_MEDIA")
        static_container = os.getenv("AZURE_STORAGE_CONTAINER_STATICFILES")
        content_paths = [f"/{media_container}/*", f"/{static_container}/*"]

        # Ensure all required environment variables are set
        if not all([resource_group, profile_name, endpoint_name]):
            self.stderr.write(self.style.ERROR("Missing required environment variables."))
            return

        # Authenticate with Azure
        cdn_client = CdnManagementClient(AZURE_CREDENTIAL, settings.AZURE_SUBSCRIPTION_ID)

        try:
            # Purge the CDN endpoint
            purge_operation = cdn_client.afd_endpoints.begin_purge_content(
                resource_group_name=resource_group,
                profile_name=profile_name,
                endpoint_name=endpoint_name,
                contents=AfdPurgeParameters(
                    domains=[cdn_host],
                    content_paths=content_paths,
                ),
            )

            # Check if the --wait argument was provided
            if options["wait"]:
                purge_operation.result()  # Wait for the operation to complete
                self.stdout.write(self.style.SUCCESS("CDN endpoint purge operation completed successfully."))
            else:
                self.stdout.write(self.style.SUCCESS("CDN endpoint purge operation started successfully."))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error executing CDN endpoint purge command: {e}"))
