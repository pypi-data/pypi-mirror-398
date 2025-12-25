from collections.abc import Sequence

import pulumi
import pulumi_azure as azure_classic
import pulumi_azure_native as azure
import pulumi_random

REDIS_IMAGE = "mcr.microsoft.com/mirror/docker/library/redis:7.2"


class HostDefinition:
    """
    A definition for a custom host name, optionally with a DNS zone.

    :param host: The host name. If a zone is given, this is the relative host name.
    :param zone: The DNS zone (optional).
    :param identifier: An identifier for this host definition (optional).
    """

    def __init__(self, host: str, zone: azure.dns.Zone | None = None, identifier: str | None = None):
        self.host = host
        self.zone = zone
        self._identifier = identifier

    def __eq__(self, other):
        return self.host == other.host and self.zone.name == other.zone.name

    @property
    def identifier(self) -> str:
        """
        The identifier for this host definition.

        :return: The identifier
        """
        if not self._identifier:
            if self.zone:
                raise ValueError(f"An identifier is required for the HostDefinition with host '{self.host}' ensure uniqueness.")
            else:
                # Use the host name as the identifier
                return self.host.replace(".", "-")
        else:
            return self._identifier

    @property
    def full_host(self) -> pulumi.Output[str]:
        """
        The full host name, including the zone.

        :return: The full host name
        """
        if not self.zone:
            return pulumi.Output.concat(self.host)
        elif self.host == "@":
            return self.zone.name
        else:
            return pulumi.Output.concat(self.host, ".", self.zone.name)


class DjangoDeployment(pulumi.ComponentResource):
    HEALTH_CHECK_PATH = "/health-check"

    def __init__(
        self,
        name,
        tenant_id: str,
        resource_group_name: pulumi.Input[str],
        vnet: azure.network.VirtualNetwork,
        pgsql_sku: azure.dbforpostgresql.SkuArgs,
        pgsql_ip_prefix: str,
        app_service_ip_prefix: str,
        app_service_sku: azure.web.SkuDescriptionArgs,
        storage_account_name: str,
        storage_allowed_origins: Sequence[str] | None = None,
        pgsql_version: str = "17",
        pgsql_parameters: dict[str, str] | None = None,
        pgadmin_access_ip: Sequence[str] | None = None,
        pgadmin_dns_zone: azure.dns.Zone | None = None,
        cdn_host: HostDefinition | None = None,
        opts=None,
    ):
        """
        Create a Django deployment.

        :param name: The name of the deployment, will be used to name subresources.
        :param tenant_id: The Entra tenant ID for the database authentication.
        :param resource_group_name: The resource group name to create the resources in.
        :param vnet: The virtual network to create the subnets in.
        :param pgsql_sku: The SKU for the PostgreSQL server.
        :param pgsql_ip_prefix: The IP prefix for the PostgreSQL subnet.
        :param app_service_ip_prefix: The IP prefix for the app service subnet.
        :param app_service_sku: The SKU for the app service plan.
        :param storage_account_name: The name of the storage account. Should be unique across Azure.
        :param storage_allowed_origins: The origins (hosts) to allow access through CORS policy. You can specify '*' to allow all.
        :param pgsql_parameters: The parameters to set on the PostgreSQL server. (optional)
        :param pgadmin_access_ip: The IP addresses to allow access to pgAdmin. If empty, all IP addresses are allowed.
        :param pgadmin_dns_zone: The Azure DNS zone to a pgadmin DNS record in. (optional)
        :param cdn_host: A custom CDN host name. (optional)
        :param opts: The resource options
        """

        super().__init__("pkg:index:DjangoDeployment", name, None, opts)

        # child_opts = pulumi.ResourceOptions(parent=self)
        self._config = pulumi.Config()

        self._name = name
        self._tenant_id = tenant_id
        self._rg = resource_group_name
        self._vnet = vnet

        # Storage resources
        self._create_storage(account_name=storage_account_name, allowed_origins=storage_allowed_origins)
        self._cdn_host = self._create_cdn(custom_host=cdn_host)

        # PostgreSQL resources
        self._create_database(sku=pgsql_sku, version=pgsql_version, ip_prefix=pgsql_ip_prefix, parameters=pgsql_parameters)

        # Subnet for the apps
        self._app_subnet = self._create_subnet(
            name="app-service",
            prefix=app_service_ip_prefix,
            delegation_service="Microsoft.Web/serverFarms",
            service_endpoints=["Microsoft.Storage"],
        )

        # Create App Service plan that will host all websites
        self._app_service_plan = self._create_app_service_plan(sku=app_service_sku)

        # Create a pgAdmin app
        self._create_pgadmin_app(access_ip=pgadmin_access_ip, dns_zone=pgadmin_dns_zone)

    def _create_storage(self, account_name: str, allowed_origins: Sequence[str] | None = None):
        # Create blob storage
        self._storage_account = azure.storage.StorageAccount(
            f"sa-{self._name}",
            resource_group_name=self._rg,
            account_name=account_name,
            sku=azure.storage.SkuArgs(
                name=azure.storage.SkuName.STANDARD_LRS,
            ),
            kind=azure.storage.Kind.STORAGE_V2,
            access_tier=azure.storage.AccessTier.HOT,
            allow_blob_public_access=True,
            public_network_access=azure.storage.PublicNetworkAccess.ENABLED,
            enable_https_traffic_only=True,
        )

        if allowed_origins:
            azure.storage.BlobServiceProperties(
                f"sa-{self._name}-blob-properties",
                resource_group_name=self._rg,
                account_name=self._storage_account.name,
                blob_services_name="default",
                cors=azure.storage.CorsRulesArgs(
                    cors_rules=[
                        azure.storage.CorsRuleArgs(
                            allowed_headers=["*"],
                            allowed_methods=["GET", "OPTIONS", "HEAD"],
                            allowed_origins=allowed_origins,
                            exposed_headers=["Access-Control-Allow-Origin"],
                            max_age_in_seconds=86400,
                        )
                    ]
                ),
            )

    def _create_cdn(self, custom_host: HostDefinition | None) -> pulumi.Output[str]:
        """
        Create a CDN endpoint. If a host name is given, it will be used as the custom domain.
        Otherwise, the default CDN host name will be returned.

        :param custom_host: The custom domain (optional)
        :return: The CDN host name
        """

        # Put CDN in front
        self._cdn_profile = azure.cdn.Profile(
            f"cdn-{self._name}",
            resource_group_name=self._rg,
            location="global",
            sku=azure.cdn.SkuArgs(
                name=azure.cdn.SkuName.STANDARD_AZURE_FRONT_DOOR,
            ),
        )

        endpoint_origin = self._storage_account.primary_endpoints.apply(
            lambda primary_endpoints: primary_endpoints.blob.replace("https://", "").replace("/", "")
        )

        self._cdn_endpoint = azure.cdn.AFDEndpoint(
            f"cdn-endpoint-{self._name}",
            resource_group_name=self._rg,
            location="global",
            profile_name=self._cdn_profile.name,
        )

        origin_group = azure.cdn.AFDOriginGroup(
            f"cdn-origin-group-{self._name}",
            resource_group_name=self._rg,
            profile_name=self._cdn_profile.name,
            load_balancing_settings=azure.cdn.LoadBalancingSettingsParametersArgs(
                sample_size=4, successful_samples_required=3, additional_latency_in_milliseconds=50
            ),
        )

        azure.cdn.AFDOrigin(
            f"cdn-origin-{self._name}",
            resource_group_name=self._rg,
            profile_name=self._cdn_profile.name,
            origin_group_name=origin_group.name,
            host_name=endpoint_origin,
            origin_host_header=endpoint_origin,
        )

        if custom_host:
            # Add custom hostname
            custom_domain = azure.cdn.AFDCustomDomain(
                f"cdn-custom-domain-{self._name}",
                resource_group_name=self._rg,
                profile_name=self._cdn_profile.name,
                host_name=custom_host.host,
            )
            custom_domains = [azure.cdn.ResourceReferenceArgs(id=custom_domain.id)]

            # Export the TXT validation records needed
            pulumi.export("cdn_validation_record_txt_name", f"_dnsauth.{custom_host.host}")
            pulumi.export(
                "cdn_validation_record_txt_value", custom_domain.validation_properties.apply(lambda properties: properties.validation_token)
            )
        else:
            custom_domains = None

        azure.cdn.Route(
            f"cdn-route-{self._name}",
            resource_group_name=self._rg,
            profile_name=self._cdn_profile.name,
            endpoint_name=self._cdn_endpoint.name,
            origin_group=azure.cdn.ResourceReferenceArgs(id=origin_group.id),
            link_to_default_domain=azure.cdn.LinkToDefaultDomain.ENABLED,
            custom_domains=custom_domains,
            cache_configuration=azure.cdn.AfdRouteCacheConfigurationArgs(
                compression_settings=azure.cdn.CompressionSettingsArgs(
                    content_types_to_compress=[
                        "application/javascript",
                        "application/json",
                        "application/x-javascript",
                        "application/xml",
                        "text/css",
                        "text/html",
                        "text/javascript",
                        "text/plain",
                    ],
                    is_compression_enabled=True,
                ),
                query_string_caching_behavior=azure.cdn.AfdQueryStringCachingBehavior.USE_QUERY_STRING,
            ),
            supported_protocols=[azure.cdn.AFDEndpointProtocols.HTTP, azure.cdn.AFDEndpointProtocols.HTTPS],
            https_redirect=azure.cdn.HttpsRedirect.ENABLED,
            opts=pulumi.ResourceOptions(depends_on=[origin_group]),
        )

        pulumi.export("cdn_cname", self._cdn_endpoint.host_name)

        if custom_host:
            return custom_domain.host_name
        else:
            return self._cdn_endpoint.host_name

    def _create_database(self, sku: azure.dbforpostgresql.SkuArgs, version: str, ip_prefix: str, parameters: dict[str, str]):
        # Create subnet for PostgreSQL
        subnet = self._create_subnet(
            name="pgsql",
            prefix=ip_prefix,
            delegation_service="Microsoft.DBforPostgreSQL/flexibleServers",
        )

        # Create private DNS zone
        dns = azure.privatedns.PrivateZone(
            f"dns-pgsql-{self._name}",
            resource_group_name=self._rg,
            location="global",
            # The zone name must end with this to work with Azure DB
            private_zone_name=f"{self._name}.postgres.database.azure.com",
        )

        # Link the private DNS zone to the VNet in order to make resolving work
        azure.privatedns.VirtualNetworkLink(
            f"vnet-link-pgsql-{self._name}",
            resource_group_name=self._rg,
            location="global",
            private_zone_name=dns.name,
            virtual_network=azure.network.SubResourceArgs(id=self._vnet.id),
            registration_enabled=False,
        )

        # Create PostgreSQL server
        self._pgsql = azure.dbforpostgresql.Server(
            f"pgsql-{self._name}",
            resource_group_name=self._rg,
            sku=sku,
            version=version,
            auth_config=azure.dbforpostgresql.AuthConfigArgs(
                password_auth=azure.dbforpostgresql.PasswordAuthEnum.DISABLED,
                active_directory_auth=azure.dbforpostgresql.ActiveDirectoryAuthEnum.ENABLED,
                tenant_id=self._tenant_id,
            ),
            storage=azure.dbforpostgresql.StorageArgs(
                storage_size_gb=32,
                auto_grow=azure.dbforpostgresql.StorageAutoGrow.ENABLED,
            ),
            network=azure.dbforpostgresql.NetworkArgs(
                delegated_subnet_resource_id=subnet.id,
                private_dns_zone_arm_resource_id=dns.id,
            ),
            backup=azure.dbforpostgresql.BackupArgs(
                backup_retention_days=7,
                geo_redundant_backup=azure.dbforpostgresql.GeoRedundantBackupEnum.DISABLED,
            ),
        )

        # Add parameters
        if parameters:
            for name, value in parameters.items():
                azure.dbforpostgresql.Configuration(
                    f"pgsql-config-{self._name}-{name}",
                    resource_group_name=self._rg,
                    server_name=self._pgsql.name,
                    source="user-override",
                    configuration_name=name,
                    value=value,
                )

        pulumi.export("pgsql_host", self._pgsql.fully_qualified_domain_name)

    def _create_subnet(
        self,
        name,
        prefix,
        delegation_service: str | None = None,
        service_endpoints: Sequence[str] = [],
    ) -> azure.network.Subnet:
        """
        Generic method to create a subnet with a delegation.

        :param name: The name of the subnet
        :param prefix: The IP prefix
        :param delegation_service: The service to delegate to
        :param service_endpoints: The service endpoints to enable
        :return: The subnet
        """

        if delegation_service:
            delegation_service = azure.network.DelegationArgs(
                name=f"delegation-{name}-{self._name}",
                service_name=delegation_service,
            )

        service_endpoints = [azure.network.ServiceEndpointPropertiesFormatArgs(service=s) for s in service_endpoints]

        return azure.network.Subnet(
            f"subnet-{name}-{self._name}",
            resource_group_name=self._rg,
            virtual_network_name=self._vnet.name,
            address_prefix=prefix,
            # We cannot pass an empty list to the delegations parameter, so either list or None
            delegations=[delegation_service] if delegation_service else None,
            service_endpoints=service_endpoints,
        )

    def _create_app_service_plan(self, sku: azure.web.SkuDescriptionArgs) -> azure.web.AppServicePlan:
        # Create App Service plan
        return azure.web.AppServicePlan(
            f"asp-{self._name}",
            resource_group_name=self._rg,
            kind="Linux",
            reserved=True,
            sku=sku,
        )

    def _create_pgadmin_app(self, access_ip: Sequence[str] | None = None, dns_zone: azure.dns.Zone | None = None):
        # Determine the IP restrictions
        ip_restrictions = []
        default_restriction = azure.web.DefaultAction.ALLOW
        if access_ip:
            default_restriction = azure.web.DefaultAction.DENY

            for ip in access_ip:
                ip_restrictions.append(
                    azure.web.IpSecurityRestrictionArgs(
                        action="Allow",
                        ip_address=ip,
                        priority=300,
                    )
                )

        # The app itself
        app = azure.web.WebApp(
            f"app-pgadmin-{self._name}",
            resource_group_name=self._rg,
            server_farm_id=self._app_service_plan.id,
            virtual_network_subnet_id=self._app_subnet.id,
            identity=azure.web.ManagedServiceIdentityArgs(
                type=azure.web.ManagedServiceIdentityType.SYSTEM_ASSIGNED,
            ),
            https_only=True,
            site_config=azure.web.SiteConfigArgs(
                ftps_state=azure.web.FtpsState.DISABLED,
                linux_fx_version="DOCKER|dpage/pgadmin4",
                health_check_path="/misc/ping",
                app_settings=[
                    azure.web.NameValuePairArgs(
                        name="DOCKER_REGISTRY_SERVER_URL",
                        value="https://index.docker.io/v1",
                    ),
                    azure.web.NameValuePairArgs(name="DOCKER_ENABLE_CI", value="true"),
                    # azure.web.NameValuePairArgs(name="WEBSITE_HTTPLOGGING_RETENTION_DAYS", value="7"),
                    # pgAdmin settings
                    azure.web.NameValuePairArgs(name="PGADMIN_DISABLE_POSTFIX", value="true"),
                    azure.web.NameValuePairArgs(name="PGADMIN_DEFAULT_EMAIL", value="dbadmin@dbadmin.net"),
                    azure.web.NameValuePairArgs(name="PGADMIN_DEFAULT_PASSWORD", value="dbadmin"),
                ],
                # IP restrictions
                ip_security_restrictions_default_action=default_restriction,
                ip_security_restrictions=ip_restrictions,
            ),
        )

        # Create a storage container for persistent data (SMB share)
        share = azure.storage.FileShare(
            f"share-pgadmin-{self._name}",
            resource_group_name=self._rg,
            account_name=self._storage_account.name,
            share_name="pgadmin",
        )

        if dns_zone:
            # Create a DNS record for the pgAdmin app
            cname = azure.dns.RecordSet(
                f"dns-cname-pgadmin-{self._name}",
                resource_group_name=self._rg,
                zone_name=dns_zone.name,
                relative_record_set_name="pgadmin",
                record_type="CNAME",
                ttl=3600,
                cname_record=azure.dns.CnameRecordArgs(
                    cname=app.default_host_name,
                ),
            )

            # For the certificate validation to work
            txt_validation = azure.dns.RecordSet(
                f"dns-txt-pgadmin-{self._name}",
                resource_group_name=self._rg,
                zone_name=dns_zone.name,
                relative_record_set_name="asuid.pgadmin",
                record_type="TXT",
                ttl=3600,
                txt_records=[
                    azure.dns.TxtRecordArgs(
                        value=[app.custom_domain_verification_id],
                    )
                ],
            )

            # Add custom hostname
            self._add_webapp_host(
                app=app,
                host=dns_zone.name.apply(lambda name: f"pgadmin.{name}"),
                suffix=self._name,
                depends_on=[cname, txt_validation],
                identifier="pgadmin",
            )

            # Export the custom hostname
            pulumi.export("pgadmin_url", dns_zone.name.apply(lambda name: f"https://pgadmin.{name}"))
        else:
            # Export the default hostname
            pulumi.export("pgadmin_url", app.default_host_name.apply(lambda host: f"https://{host}"))

        # Mount the storage container
        azure.web.WebAppAzureStorageAccounts(
            f"app-pgadmin-mount-{self._name}",
            resource_group_name=self._rg,
            name=app.name,
            properties={
                "pgadmin-data": azure.web.AzureStorageInfoValueArgs(
                    account_name=self._storage_account.name,
                    access_key=self._get_storage_account_access_keys(self._storage_account)[0].value,
                    mount_path="/var/lib/pgadmin",
                    share_name=share.name,
                    type=azure.web.AzureStorageType.AZURE_FILES,
                )
            },
        )

    def _add_webapp_host(
        self,
        app: azure.web.WebApp,
        host: str | pulumi.Input[str],
        suffix: str,
        identifier: str,
        depends_on: Sequence[pulumi.Resource] | None = None,
    ) -> azure.web.WebAppHostNameBinding:
        """
        We need to use a few steps and CertificateBinding from Azure Classic to make this work.

        See also: https://github.com/pulumi/pulumi-azure-native/issues/578

        :param app: The web app
        :param host: The host name
        :param suffix: A suffix to make the resource name unique
        :param depend_on: The resource to depend on (optional)
        """

        if not depends_on:
            depends_on = []

        # Create a binding without a certificate
        binding = azure.web.WebAppHostNameBinding(
            f"host-binding-{suffix}-{identifier}",
            resource_group_name=self._rg,
            name=app.name,
            host_name=host,
            ssl_state=azure.web.SslState.DISABLED,
            # Ignore changes in SSL state and thumbprint
            opts=pulumi.ResourceOptions(depends_on=depends_on, ignore_changes=["ssl_state", "thumbprint"]),
        )

        # Create a certificate that depends on the binding
        certificate = azure.web.Certificate(
            f"cert-{suffix}-{identifier}",
            resource_group_name=self._rg,
            server_farm_id=app.server_farm_id,
            canonical_name=host,
            opts=pulumi.ResourceOptions(depends_on=[binding] + depends_on),
        )

        # Create CertificateBinding from Azure Classic to link it together
        # Inspired by https://github.com/pulumi/pulumi-azure-native/issues/578#issuecomment-2705952672
        azure_classic.appservice.CertificateBinding(
            f"cert-binding-{suffix}-{identifier}",
            hostname_binding_id=binding.id,
            certificate_id=certificate.id,
            ssl_state="SniEnabled",
            opts=pulumi.ResourceOptions(depends_on=depends_on, ignore_changes=["hostname_binding_id"]),
        )

        return binding

    def _create_comms_dns_records(self, suffix, host: HostDefinition, records: dict) -> list[azure.dns.RecordSet]:
        created_records = []

        # Domain validation and SPF record (one TXT record with multiple values)
        r = azure.dns.RecordSet(
            f"dns-comms-{suffix}-{host.identifier}-domain",
            resource_group_name=self._rg,
            zone_name=host.zone.name,
            relative_record_set_name=host.host,
            record_type="TXT",
            ttl=3600,
            txt_records=[
                azure.dns.TxtRecordArgs(value=[records["domain"]["value"]]),
                azure.dns.TxtRecordArgs(value=[records["s_pf"]["value"]]),
            ],
        )
        created_records.append(r)

        # DKIM records (two CNAME records)
        for record in ("d_kim", "d_kim2"):
            if host.host == "@":  # noqa: SIM108
                relative_record_set_name = records[record]["name"]
            else:
                relative_record_set_name = f"{records[record]['name']}.{host.host}"

            r = azure.dns.RecordSet(
                f"dns-comms-{suffix}-{host.identifier}-{record}",
                resource_group_name=self._rg,
                zone_name=host.zone.name,
                relative_record_set_name=relative_record_set_name,
                record_type="CNAME",
                ttl=records[record]["ttl"],
                cname_record=azure.dns.CnameRecordArgs(cname=records[record]["value"]),
            )
            created_records.append(r)

        return created_records

    def _add_webapp_comms(self, data_location: str, domains: list[HostDefinition], suffix: str) -> azure.communication.CommunicationService:
        email_service = azure.communication.EmailService(
            f"comms-email-{suffix}",
            resource_group_name=self._rg,
            location="global",
            data_location=data_location,
        )

        domain_resources = []
        comm_dependencies = []

        # Add our own custom domains
        for domain in domains:
            d = azure.communication.Domain(
                f"comms-email-domain-{suffix}-{domain.identifier}",
                resource_group_name=self._rg,
                location="global",
                domain_management=azure.communication.DomainManagement.CUSTOMER_MANAGED,
                domain_name=domain.full_host,
                email_service_name=email_service.name,
            )

            if domain.zone:
                # Create DNS records in the managed zone
                comm_dependencies = pulumi.Output.all(suffix, domain, d.verification_records).apply(
                    lambda args: self._create_comms_dns_records(suffix=args[0], host=args[1], records=args[2])
                )

            domain_resources.append(d.id)

        # Add an Azure managed domain
        d = azure.communication.Domain(
            f"comms-email-domain-{suffix}-azure",
            resource_group_name=self._rg,
            location="global",
            domain_management=azure.communication.DomainManagement.AZURE_MANAGED,
            domain_name="AzureManagedDomain",
            email_service_name=email_service.name,
        )
        domain_resources.append(d.id)

        # Create Communication Services and link the domains
        comm_service = azure.communication.CommunicationService(
            f"comms-{suffix}",
            resource_group_name=self._rg,
            location="global",
            data_location=data_location,
            linked_domains=domain_resources,
            opts=pulumi.ResourceOptions(depends_on=comm_dependencies),
        )

        return comm_service

    def _add_webapp_vault(self, administrators: list[str], suffix: str) -> azure.keyvault.Vault:
        # Create a keyvault with a random suffix to make the name unique
        random_suffix = pulumi_random.RandomString(
            f"vault-suffix-{suffix}",
            # Total length is 24, so deduct the length of the suffix
            length=(24 - 7 - len(suffix)),
            special=False,
            upper=False,
        )

        vault = azure.keyvault.Vault(
            f"vault-{suffix}",
            resource_group_name=self._rg,
            vault_name=random_suffix.result.apply(lambda r: f"vault-{suffix}-{r}"),
            properties=azure.keyvault.VaultPropertiesArgs(
                tenant_id=self._tenant_id,
                sku=azure.keyvault.SkuArgs(
                    name=azure.keyvault.SkuName.STANDARD,
                    family=azure.keyvault.SkuFamily.A,
                ),
                enable_rbac_authorization=True,
            ),
        )

        # Add vault administrators
        if administrators:
            # Find the Key Vault Administrator role
            administrator_role = vault.id.apply(
                lambda scope: azure.authorization.get_role_definition(
                    role_definition_id="00482a5a-887f-4fb3-b363-3b7fe8e74483",
                    scope=scope,
                )
            )

            # Actual administrator roles
            for a in administrators:
                azure.authorization.RoleAssignment(
                    f"ra-{suffix}-vault-admin-{a}",
                    principal_id=a,
                    principal_type=azure.authorization.PrincipalType.USER,
                    role_definition_id=administrator_role.id,
                    scope=vault.id,
                )

        return vault

    def _add_webapp_secret(
        self,
        vault: azure.keyvault.Vault,
        secret_name: str,
        config_secret_name: str,
        suffix: str,
    ):
        secret = self._config.require_secret(config_secret_name)

        # Normalize the secret name
        secret_name = secret_name.replace("_", "-").lower()

        # Create a secret in the vault
        return azure.keyvault.Secret(
            f"secret-{suffix}-{secret_name}",
            resource_group_name=self._rg,
            vault_name=vault.name,
            secret_name=secret_name,
            properties=azure.keyvault.SecretPropertiesArgs(
                value=secret,
            ),
        )

    def _get_storage_account_access_keys(
        self, storage_account: azure.storage.StorageAccount
    ) -> Sequence[azure.storage.outputs.StorageAccountKeyResponse]:
        """
        Helper function to get the access keys for a storage account.

        :param storage_account: The storage account
        :return: The access keys
        """
        keys = pulumi.Output.all(self._rg, storage_account.name).apply(
            lambda args: azure.storage.list_storage_account_keys(
                resource_group_name=args[0],
                account_name=args[1],
            )
        )

        return keys.keys

    def add_database_administrator(self, object_id: str, user_name: str):
        """
        Add an Entra ID as database administrator.

        :param object_id: The object ID of the user
        :param user_name: The user name (user@example.com)
        """

        azure.dbforpostgresql.Administrator(
            # Must be random but a GUID
            f"pgsql-admin-{user_name.replace('@', '_')}-{self._name}",
            resource_group_name=self._rg,
            server_name=self._pgsql.name,
            object_id=object_id,
            principal_name=user_name,
            principal_type=azure.dbforpostgresql.PrincipalType.USER,
            tenant_id=self._tenant_id,
        )

    def add_django_website(
        self,
        name: str,
        db_name: str,
        repository_url: str,
        repository_branch: str,
        website_hosts: list[HostDefinition],
        django_settings_module: str,
        python_version: str = "3.14",
        environment_variables: dict[str, str] | None = None,
        secrets: dict[str, str] | None = None,
        comms_data_location: str | None = None,
        comms_domains: list[HostDefinition] | None = None,
        dedicated_app_service_sku: azure.web.SkuDescriptionArgs | None = None,
        vault_administrators: list[str] | None = None,
        redis_sidecar: bool = True,
        django_tasks: bool = True,
        startup_timeout: int = 600,
        log_retention_days: int = 7,
    ) -> azure.web.WebApp:
        """
        Create a Django website with it's own database and storage containers.

        :param name: The reference for the website, will be used to name subresources.
        :param db_name: The name of the database to create.
        :param repository_url: The URL of the Git repository.
        :param repository_branch: The Git branch to deploy.
        :param website_hosts: The list of custom host names for the website.
        :param django_settings_module: The Django settings module to load.
        :param python_version: The Python version to use.
        :param environment_variables: A dictionary of environment variables to set.
        :param secrets: A dictionary of secrets to store in the Key Vault and assign as environment variables.
            The key is the name of the Pulumi secret, the value is the name of the environment variable
            and the name of the secret in the Key Vault.
        :param comms_data_location: The data location for the Communication Services (optional if you don't need it).
        :param comms_domains: The list of custom domains for the E-mail Communication Services (optional).
        :param dedicated_app_service_sku: The SKU for the dedicated App Service Plan (optional).
        :param vault_administrators: The principal IDs of the vault administrators (optional).
        :param redis_sidecar: Whether to create a Redis sidecar container.
        :param startup_timeout: The startup timeout for the App Service (default is 300 seconds).
        """

        # Create a database
        db = azure.dbforpostgresql.Database(
            f"db-{name}",
            database_name=db_name,
            resource_group_name=self._rg,
            server_name=self._pgsql.name,
        )

        # Container for media files
        media_container = azure.storage.BlobContainer(
            f"storage-container-{name}-media-{self._name}",
            resource_group_name=self._rg,
            account_name=self._storage_account.name,
            public_access=azure.storage.PublicAccess.BLOB,
            container_name=f"{name}-media",
        )

        # Container for static files
        static_container = azure.storage.BlobContainer(
            f"storage-container-{name}-static-{self._name}",
            resource_group_name=self._rg,
            account_name=self._storage_account.name,
            public_access=azure.storage.PublicAccess.BLOB,
            container_name=f"{name}-static",
        )

        # Redis cache environment variable
        if redis_sidecar:
            environment_variables["REDIS_SIDECAR"] = "true"

        if django_tasks:
            if not redis_sidecar:
                raise ValueError("django-tasks requires redis-sidecar to be enabled.")

            environment_variables["DJANGO_TASKS"] = "true"

        # Communication Services (optional)
        if comms_data_location:
            if not comms_domains:
                comms_domains = []

            comms = self._add_webapp_comms(comms_data_location, comms_domains, f"{name}-{self._name}")

            # Add the service endpoint as environment variable
            environment_variables["AZURE_COMMUNICATION_SERVICE_ENDPOINT"] = comms.host_name.apply(lambda host: f"https://{host}")
        else:
            comms = None

        # Key Vault
        vault = self._add_webapp_vault(vault_administrators, f"{name}-{self._name}")

        # Add secrets
        for config_name, env_name in secrets.items():
            s = self._add_webapp_secret(vault, env_name, config_name, f"{name}-{self._name}")
            environment_variables[f"{env_name}_SECRET_NAME"] = s.name

        # Create a Django Secret Key (random)
        secret_key = pulumi_random.RandomString(f"django-secret-{name}-{self._name}", length=50)

        if log_retention_days > 0:
            environment_variables["WEBSITE_HTTPLOGGING_RETENTION_DAYS"] = str(log_retention_days)

        # Convert environment variables to NameValuePairArgs
        environment_variables = [
            azure.web.NameValuePairArgs(
                name=key,
                value=value,
            )
            for key, value in environment_variables.items()
        ]

        allowed_hosts = pulumi.Output.concat(*[pulumi.Output.concat(host.full_host, ",") for host in website_hosts])

        # Create a dedicated App Service Plan if requested
        if dedicated_app_service_sku:
            app_service_plan = azure.web.AppServicePlan(
                f"asp-{self._name}-{name}",
                resource_group_name=self._rg,
                kind="Linux",
                reserved=True,
                sku=dedicated_app_service_sku,
            )
        else:
            app_service_plan = self._app_service_plan

        app = azure.web.WebApp(
            f"app-{name}-{self._name}",
            resource_group_name=self._rg,
            server_farm_id=app_service_plan.id,
            virtual_network_subnet_id=self._app_subnet.id,
            identity=azure.web.ManagedServiceIdentityArgs(
                type=azure.web.ManagedServiceIdentityType.SYSTEM_ASSIGNED,
            ),
            https_only=True,
            site_config=azure.web.SiteConfigArgs(
                app_command_line="cicd/startup.sh",
                always_on=True,
                health_check_path=self.HEALTH_CHECK_PATH,
                ftps_state=azure.web.FtpsState.DISABLED,
                python_version=python_version,
                # scm_type=azure.web.ScmType.EXTERNAL_GIT,
                linux_fx_version=f"PYTHON|{python_version}",
                http20_enabled=True,
                app_settings=[
                    # Startup settings
                    azure.web.NameValuePairArgs(name="WEBSITES_CONTAINER_START_TIME_LIMIT", value=str(startup_timeout)),
                    # To support our settings helper
                    azure.web.NameValuePairArgs(name="IS_AZURE_ENVIRONMENT", value="true"),
                    # Build settings
                    azure.web.NameValuePairArgs(name="SCM_DO_BUILD_DURING_DEPLOYMENT", value="true"),
                    azure.web.NameValuePairArgs(name="PRE_BUILD_COMMAND", value="curl -sSL https://bootstrap.django-azu.re | bash"),
                    # azure.web.NameValuePairArgs(name="PRE_BUILD_COMMAND", value="cicd/pre_build.sh"),
                    # This script will be created by the bootstrap script
                    azure.web.NameValuePairArgs(name="POST_BUILD_COMMAND", value="cicd/post_build.sh"),
                    azure.web.NameValuePairArgs(name="DISABLE_COLLECTSTATIC", value="true"),
                    azure.web.NameValuePairArgs(name="HEALTH_CHECK_PATH", value=self.HEALTH_CHECK_PATH),
                    # Django settings
                    # azure.web.NameValuePairArgs(name="DEBUG", value="true"),
                    azure.web.NameValuePairArgs(name="DJANGO_SETTINGS_MODULE", value=django_settings_module),
                    azure.web.NameValuePairArgs(name="DJANGO_SECRET_KEY", value=secret_key.result),
                    azure.web.NameValuePairArgs(name="DJANGO_ALLOWED_HOSTS", value=allowed_hosts),
                    # Vault settings
                    azure.web.NameValuePairArgs(name="AZURE_KEY_VAULT", value=vault.name),
                    # Storage settings
                    azure.web.NameValuePairArgs(name="AZURE_STORAGE_ACCOUNT_NAME", value=self._storage_account.name),
                    azure.web.NameValuePairArgs(name="AZURE_STORAGE_CONTAINER_STATICFILES", value=static_container.name),
                    azure.web.NameValuePairArgs(name="AZURE_STORAGE_CONTAINER_MEDIA", value=media_container.name),
                    # CDN
                    azure.web.NameValuePairArgs(name="CDN_HOST", value=self._cdn_host),
                    azure.web.NameValuePairArgs(name="CDN_PROFILE", value=self._cdn_profile.name),
                    azure.web.NameValuePairArgs(name="CDN_ENDPOINT", value=self._cdn_endpoint.name),
                    # Database settings
                    azure.web.NameValuePairArgs(name="DB_HOST", value=self._pgsql.fully_qualified_domain_name),
                    azure.web.NameValuePairArgs(name="DB_NAME", value=db.name),
                    azure.web.NameValuePairArgs(name="DB_USER", value=f"{name}_managed_identity"),
                    *environment_variables,
                ],
            ),
        )

        # Redis cache
        if redis_sidecar:
            azure.web.WebAppSiteContainer(
                f"redis-sidecar-{name}-{self._name}",
                resource_group_name=self._rg,
                name=app.name,
                is_main=False,
                container_name="redis-sidecar",
                image=REDIS_IMAGE,
                # target_port="6379",
            )

        # We need this to create the database role and grant permissions
        principal_id = app.identity.apply(lambda identity: identity.principal_id)
        pulumi.export(f"{name}_site_principal_id", principal_id)
        pulumi.export(f"{name}_site_db_user", f"{name}_managed_identity")

        # We need this to verify custom domains
        pulumi.export(f"{name}_site_domain_verification_id", app.custom_domain_verification_id)
        pulumi.export(f"{name}_site_domain_cname", app.default_host_name)
        virtual_ip = app.outbound_ip_addresses.apply(lambda addresses: addresses.split(",")[-1])
        pulumi.export(f"{name}_site_virtual_ip", virtual_ip)

        # Get the URL of the publish profile.
        # Use app.identity here too to ensure the app is actually created before getting credentials.
        credentials = pulumi.Output.all(self._rg, app.name, app.identity).apply(
            lambda args: azure.web.list_web_app_publishing_credentials(
                resource_group_name=args[0],
                name=args[1],
            )
        )

        pulumi.export(f"{name}_deploy_url", pulumi.Output.concat(credentials.scm_uri, "/deploy"))

        bindings = []
        for host in website_hosts:
            # Only one binding can be created at a time, so we need to depend on the previous one.
            dependencies = bindings or []

            if host.zone:
                # Create a DNS record in the zone.
                # We always use an A record instead of CNAME to avoid collisions with TXT records.
                a = azure.dns.RecordSet(
                    f"dns-a-{name}-{self._name}-{host.identifier}",
                    resource_group_name=self._rg,
                    zone_name=host.zone.name,
                    relative_record_set_name=host.host,
                    record_type="A",
                    ttl=3600,
                    a_records=[
                        azure.dns.ARecordArgs(
                            ipv4_address=virtual_ip,
                        )
                    ],
                )

                dependencies.append(a)

                # For the certificate validation to work
                relative_record_set_name = "asuid" if host.host == "@" else pulumi.Output.concat("asuid.", host.host)

                txt_validation = azure.dns.RecordSet(
                    f"dns-txt-{name}-{self._name}-{host.identifier}",
                    resource_group_name=self._rg,
                    zone_name=host.zone.name,
                    relative_record_set_name=relative_record_set_name,
                    record_type="TXT",
                    ttl=3600,
                    txt_records=[
                        azure.dns.TxtRecordArgs(
                            value=[app.custom_domain_verification_id],
                        )
                    ],
                )

                dependencies.append(txt_validation)

            # Add the host with optional dependencies
            binding = self._add_webapp_host(
                app=app,
                host=host.full_host,
                suffix=f"{name}-{self._name}",
                identifier=host.identifier,
                depends_on=dependencies,
            )

            bindings.append(binding)

        # To enable deployment from GitLab
        azure.web.WebAppSourceControl(
            f"app-{name}-sourcecontrol-{self._name}",
            resource_group_name=self._rg,
            name=app.name,
            repo_url=repository_url,
            branch=repository_branch,
            is_git_hub_action=False,
            is_manual_integration=True,
            is_mercurial=False,
        )

        # Where we can retrieve the SSH key
        pulumi.export(
            f"{name}_deploy_ssh_key_url",
            app.name.apply(lambda name: f"https://{name}.scm.azurewebsites.net/api/sshkey?ensurePublicKey=1"),
        )

        # Find the role for Key Vault Secrets User
        vault_access_role = vault.id.apply(
            lambda scope: azure.authorization.get_role_definition(
                role_definition_id="4633458b-17de-408a-b874-0445c86b69e6",
                scope=scope,
            )
        )

        # Grant the app access to the vault
        azure.authorization.RoleAssignment(
            f"ra-{name}-vault-user",
            principal_id=principal_id,
            principal_type=azure.authorization.PrincipalType.SERVICE_PRINCIPAL,
            # Key Vault Secrets User
            role_definition_id=vault_access_role.id,
            scope=vault.id,
        )

        # Find the role for Storage Blob Data Contributor
        storage_role = self._storage_account.id.apply(
            lambda scope: azure.authorization.get_role_definition(
                role_definition_id="ba92f5b4-2d11-453d-a403-e96b0029c9fe",
                scope=scope,
            )
        )

        # Grant the app access to the storage account
        azure.authorization.RoleAssignment(
            f"ra-{name}-storage",
            principal_id=principal_id,
            principal_type=azure.authorization.PrincipalType.SERVICE_PRINCIPAL,
            role_definition_id=storage_role.id,
            scope=self._storage_account.id,
        )

        # Grant the app to send e-mails
        if comms:
            comms_role = comms.id.apply(
                lambda scope: azure.authorization.get_role_definition(
                    # Contributor
                    role_definition_id="b24988ac-6180-42a0-ab88-20f7382dd24c",
                    scope=scope,
                )
            )

            azure.authorization.RoleAssignment(
                f"ra-{name}-comms",
                principal_id=principal_id,
                principal_type=azure.authorization.PrincipalType.SERVICE_PRINCIPAL,
                role_definition_id=comms_role.id,
                scope=comms.id,
            )

        # Grant the app to manage the CDN endpoint (CDN Profile Contributor)
        cdn_profile_role = self._cdn_profile.id.apply(
            lambda scope: azure.authorization.get_role_definition(
                role_definition_id="ec156ff8-a8d1-4d15-830c-5b80698ca432",
                scope=scope,
            )
        )

        azure.authorization.RoleAssignment(
            f"ra-{name}-cdn-profile",
            principal_id=principal_id,
            principal_type=azure.authorization.PrincipalType.SERVICE_PRINCIPAL,
            role_definition_id=cdn_profile_role.id,
            scope=self._cdn_profile.id,
        )

        return app
