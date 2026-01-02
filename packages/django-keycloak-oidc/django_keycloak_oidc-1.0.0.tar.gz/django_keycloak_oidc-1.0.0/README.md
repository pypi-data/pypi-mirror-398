# django-keyclock-oidc

This project is fork of [mozilla-django-oidc](https://github.com/mozilla/mozilla-django-oidc/) and modified to map keycloak roles / groups to django user permissions / groups. You can read more about the original project documentation [here](https://mozilla-django-oidc.readthedocs.io/en/latest/).

## Features
- Automatic mapping of Keycloak roles and groups to Django user permissions and groups
- Django admin login integration with Keycloak
- OIDC authentication with Keycloak

## Installation

1. You can install the package via your python package manager, example:

```bash
pip install django-keyclock-oidc
# or
poetry add django-keyclock-oidc
# or
uv add django-keyclock-oidc
```

2. Add `django_keyclock_oidc` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    'django_keyclock_oidc', # (here) at the top of the admin app
    "django.contrib.admin",
    ...
]
```

3. Add the authentication backend to your `AUTHENTICATION_BACKENDS` in `settings.py`:

```python
AUTHENTICATION_BACKENDS = [
    'django_keycloak_oidc.auth.KeyCloakAuthenticationBackend', # here
    'django.contrib.auth.backends.ModelBackend', # django default (need it too)
    ..., # and other
]
```

4. Add urls to your `urls.py`:

```python
urlpatterns = [
    ...,
    path("oidc/", include("django_keycloak_oidc.urls")),
    ...,
]
```
**Important Note:** If you changed your admin root path, Make sure that the `oidc/` and `admin/` paths are in same root.

for example:

```python
urlpatterns = [
    ...,
    path(
        "root/",  # your root (if you did it)
        include(
            [
                ...,
                path("admin/", admin.site.urls),
                path("oidc/", include("django_keycloak_oidc.urls")),
                ...,
            ]
        )
    ),
    ...,
]
```

5. (Optional) Add the settings_context to your context_processors in `settings.py` if you want to customize the authentication button in django admin login page:

```python
TEMPLATES = [
    {
        ...,
        "OPTIONS": {
            "context_processors": [
                ...,
                "django_keycloak_oidc.context_processor.settings_context", # here
            ],
        },
    },
]
```

6. Run migrations (Done):

```bash
python manage.py migrate
```

## Configuration
You can see configuration of the original project [here](https://mozilla-django-oidc.readthedocs.io/en/latest/).

My sample configuration(`settings.py`) is as below:

```python
OIDC_RP_CLIENT_ID = "<client-id>"
OIDC_RP_CLIENT_SECRET = "<client-secret>"
OIDC_RP_SIGN_ALGO = "RS256"

OIDC_VERIFY_SSL = False

OIDC_OP_AUTHORIZATION_ENDPOINT = "http://<keycloak-host>/realms/<realm>/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = "http://<keycloak-host>/realms/<realm>/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = "http://<keycloak-host>/realms/<realm>/protocol/openid-connect/userinfo"
OIDC_OP_JWKS_ENDPOINT = "http://<keycloak-host>/realms/<realm>/protocol/openid-connect/certs"

LOGIN_URL = "/oidc/authenticate/"
LOGIN_REDIRECT_URL = "/leasing/admin/"
LOGIN_REDIRECT_URL_FAILURE = "/leasing/admin/"
LOGOUT_REDIRECT_URL = "/leasing/admin/login/"

# Optional settings for customizing the login button in django admin login page if you added the context processor (step 5 in Installation)
KEYCLOAK_DJANGO_ADMIN_LOGIN_DIRECTION = "ltr"
KEYCLOAK_DJANGO_ADMIN_LOGIN_TEXT = "Login with"
KEYCLOAK_DJANGO_ADMIN_LOGIN_LOGO = "https://karnameh.com/assets/logos/karnameh-logo.svg"
```
