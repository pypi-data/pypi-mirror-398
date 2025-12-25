# Pulumi Django Deployment

This project aims to make a simple Django deployment on Azure easier.

To have a proper and secure environment, we need these components:
* Storage account for media and static files
* CDN endpoint in front with a domain name of our choosing
* PostgreSQL server
* Azure Communication Services to send e-mails
* Webapp with multiple custom host names and managed SSL for the website itself
* Azure Key Vault per application
* Webapp running pgAdmin

## Project requirements

## Installation
This package is published on PyPi, so you can just add pulumi-django-azure to your requirements file.

To use a specific branch in your project, add to pyproject.toml dependencies:
```
pulumi-django-azure = { git = "git@gitlab.com:MaartenUreel/pulumi-django-azure.git", branch = "dev" }
```

A simple project could look like this:
```python
import pulumi
import pulumi_azure_native as azure
from pulumi_django_azure import DjangoDeployment

stack = pulumi.get_stack()
config = pulumi.Config()


# Create resource group
rg = azure.resources.ResourceGroup(f"rg-{stack}")

# Create VNet
vnet = azure.network.VirtualNetwork(
    f"vnet-{stack}",
    resource_group_name=rg.name,
    address_space=azure.network.AddressSpaceArgs(
        address_prefixes=["10.0.0.0/16"],
    ),
)

# Deploy the website and all its components
django = DjangoDeployment(
    stack,
    tenant_id="abc123...",
    resource_group_name=rg.name,
    vnet=vnet,
    pgsql_ip_prefix="10.0.10.0/24",
    appservice_ip_prefix="10.0.20.0/24",
    app_service_sku=azure.web.SkuDescriptionArgs(
        name="B2",
        tier="Basic",
    ),
    storage_account_name="mystorageaccount",
    cdn_host="cdn.example.com",
)

django.add_django_website(
    name="web",
    db_name="mywebsite",
    repository_url="git@gitlab.com:project/website.git",
    repository_branch="main",
    website_hosts=["example.com", "www.example.com"],
    django_settings_module="mywebsite.settings.production",
    comms_data_location="europe",
    comms_domains=["mydomain.com"],
)

django.add_database_administrator(
    object_id="a1b2c3....",
    user_name="user@example.com",
    tenant_id="a1b2c3....",
)
```

## Changes to your Django project
1. Add `pulumi_django_azure` to your `INSTALLED_APPS`
2. Add to your settings file:
   ```python
   from pulumi_django_azure.settings import *  # noqa: F403

   # This will provide the management command to purge the CDN and cache
   INSTALLED_APPS += ["pulumi_django_azure"]

   # This will provide the health check middleware that will also take care of credential rotation.
   MIDDLEWARE += ["pulumi_django_azure.middleware.HealthCheckMiddleware"]
   ```
   This will pre-configure most settings to make your app work on Azure. You can check the source for details,
   and ofcourse override any value after importing them.


## Deployment steps
1. Deploy without custom hosts (for CDN and websites)
2. Configure the PostgreSQL server (create and grant permissions to role for your websites)
3. Retrieve the deployment SSH key and configure your remote GIT repository with it
4. Configure your CDN host (add the CNAME record)
5. Configure your custom website domains (add CNAME/A record and TXT validation records)
6. Re-deploy with custom hosts
7. Re-deploy once more to enable HTTPS on website domains
8. Manually activate HTTPS on the CDN host
9. Go to the e-mail communications service on Azure and configure DKIM, SPF,... for your custom domains.

## Custom domain name for CDN
When deploying the first time, you will get a `cdn_cname` output. You need to create a CNAME to this domain before the deployment of the custom domain will succeed.

You can safely deploy with the failing CustomDomain to get the CNAME, create the record and then deploy again.

To enable HTTPS, you need to do this manually in the console. This is because of a limitation in the Azure API:
https://github.com/Azure/azure-rest-api-specs/issues/17498

## Custom domain names for web application
Because of a circular dependency in custom domain name bindings and certificates that is out of our control, you need to deploy the stack twice.

The first time will create the bindings without a certificate.
The second deployment will then create the certificate for the domain (which is only possible if the binding exists), but also set the fingerprint of that certificate on the binding.

To make the certificate work, you need to create a TXT record named `asuid` point to the output of `{your_app}_site_domain_verification_id`. For example:

```
asuid.mywebsite.com.      TXT  "A1B2C3D4E5..."
asuid.www.mywebsite.com.  TXT  "A1B2C3D4E5..."
```

## Database authentication
The PostgreSQL uses Entra ID authentication only, no passwords.

### Administrator login
If you want to log in to the database yourself, you can add yourself as an administrator with the `add_database_administrator` function.
Your username is your e-mailaddress, a temporary password can be obtained using `az account get-access-token`.

You can use this method to log in to pgAdmin.

### Application
Refer to this documentation:
https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/how-to-manage-azure-ad-users#create-a-role-using-microsoft-entra-object-identifier

In short, run something like this in the `postgres` database:
```
SELECT * FROM pgaadauth_create_principal_with_oid('web_managed_identity', 'c8b25b85-d060-4cfc-bad4-b8581cfdf946', 'service', false, false);
```
Replace the GUID of course with the managed identity our web app gets.

The name of the role is outputted by `{your_app}_site_db_user`

Be sure to grant this role the correct permissions too.

## pgAdmin specifics
pgAdmin will be created with a default login:
* Login: dbadmin@dbadmin.net
* Password: dbadmin

Best practice is to log in right away, create a user for yourself and delete this default user.

## Azure OAuth2 / Django Social Auth
If you want to set up login with Azure, which would make sense since you are in the ecosystem, you need to create an App Registration in Entra ID, create a secret and then register these settings in your stack:
```
pulumi config set --secret --path 'mywebsite_social_auth_azure.key' secret_ID
pulumi config set --secret --path 'mywebsite_social_auth_azure.secret' secret_value
pulumi config set --secret --path 'mywebsite_social_auth_azure.tenant_id' directory_tenant_id
pulumi config set --secret --path 'mywebsite_social_auth_azure.client_id' application_id
```

Then in your Django deployment, pass to the `add_django_website` command:
```
secrets={
    "mywebsite_social_auth_azure": "AZURE_OAUTH",
},
```

The value will be automatically stored in the vault where the application has access to.
The environment variable will be suffixed with `_SECRET_NAME`.

Then, in your application, retrieve this data from the vault, e.g.:
```python
# Social Auth settings
oauth_secret = AZURE_KEY_VAULT_CLIENT.get_secret(env("AZURE_OAUTH_SECRET_NAME"))
oauth_secret = json.loads(oauth_secret.value)
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = oauth_secret["client_id"]
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = oauth_secret["secret"]
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = oauth_secret["tenant_id"]
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ["username", "first_name", "last_name", "email"]
SOCIAL_AUTH_POSTGRES_JSONFIELD = True

AUTHENTICATION_BACKENDS = (
    "social_core.backends.azuread_tenant.AzureADTenantOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)
```

And of course add the login button somewhere, following Django Social Auth instructions.

## Automate deployments
When using a service like GitLab, you can configure a Webhook to fire upon a push to your branch.

You need to download the deployment profile to obtain the deployment username and password, and then you can construct a URL like this:

```
https://{user}:{pass}@{appname}.scm.azurewebsites.net/deploy

```

```
https://{appname}.scm.azurewebsites.net/api/sshkey?ensurePublicKey=1
```

Be sure to configure the SSH key that Azure will use on GitLab side. You can obtain it using:

This would then trigger a redeploy everytime you make a commit to your live branch.


## Change requests
I created this for internal use but since it took me a while to puzzle all the things together I decided to share it.
Therefore this project is not super generic, but tailored to my needs. I am however open to pull or change requests to improve this project or to make it more usable for others.
