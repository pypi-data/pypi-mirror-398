# Syneto API

Syneto Client API library: authentication, storage, virtualization and protection

# Installation

```
$ pip install syneto-api
```

# Basic Usage

```
from syneto_api import Authentication, Virtualization, Storage, Protection

auth_api = Authentication(url_base="https://syneto-instance-ip-address/api/auth", insecure_ssl=True)
response = auth_api.login(username="admin", password="admin")
jwt = response['jwt']

virt_api = Virtualization(url_base="https://syneto-instance-ip-address/api/virtualization", insecure_ssl=True)
virt_api.set_auth_jwt(jwt)
print(virt_api.get_vms())

storage_api = Storage(url_base="https://syneto-instance-ip-address/api/storage", insecure_ssl=True)
storage_api.set_auth_jwt(jwt)
print(storage_api.get_pools())
```

# Environment Variables

For conveninence, the base urls for the api endpoints are also accepted as environment variables, please see below.

```
AUTHORIZATION_USER=admin
AUTHORIZATION_PASS=admin
AUTHORIZATION_SERVICE=https://syneto-instance-ip-address/api/auth
VIRTUALIZATION_SERVICE=https://syneto-instance-ip-address/api/virtualization
STORAGE_SERVICE=https://syneto-instance-ip-address/api/storage
PROTECTION_SERVICE=https://syneto-instance-ip-address/api/protection
```

If you are using self-signed SSL certificates, set the following env. so that the http request library does not perform ssl verification. 

```
ALLOW_INSECURE_SSL=True
```

# Publishing

See `RELEASE.md`
