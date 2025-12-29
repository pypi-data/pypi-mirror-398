# Onehux SSO Client for Django

Official Django client library for integrating with [Onehux Accounts](https://accounts.onehux.com) - A production-ready OAuth2/OIDC Identity Provider with SSO/SLO support.

## Features

- ✅ **OAuth2/OIDC Authentication** - Complete authorization code flow with PKCE
- ✅ **Single Sign-On (SSO)** - Seamless login across multiple applications
- ✅ **Single Logout (SLO)** - Logout from all connected applications
- ✅ **Token Management** - Automatic token refresh and validation
- ✅ **User Synchronization** - Real-time user profile updates via webhooks
- ✅ **Django Integration** - Middleware, authentication backend, and decorators
- ✅ **Type Hints** - Full type annotations for better IDE support
- ✅ **Production Ready** - Battle-tested and secure








## Quick Start

### 1. Install the package
```bash
pip install onehux-sso-client
```


### 2. Configure settings.py
```python
INSTALLED_APPS = [
    'onehux_sso_client',
    'accounts',  # Your app with User model
    ...
]

AUTH_USER_MODEL = 'accounts.User'
```


### 3. Create your User model
You have four ways you can create your user models to work with this package

**Option 1: Mixin (Recommended)**

```bash
# myproject/models.py
from django.contrib.auth.models import AbstractUser
from sso_client.models import OnehuxSSOUserMixin

class User(OnehuxSSOUserMixin, AbstractUser):
    """Custom user with SSO support + your own fields"""
    department = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20)
    
    class Meta:
        db_table = 'users'
```


**Option 2: Minimal Integration**
For users who just want SSO without profile sync:

```bash
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    onehux_user_id = models.UUIDField(unique=True, null=True)
    # You handle profile sync yourself
```


**Option 3: Use management command (easiest)**

```bash
python manage.py onehux_init --app=accounts
```

**Option 4: Copy template manually**

Download the [user_model_template.py](https://github.com/onehuxco/onehux-sso-client/blob/main/sso_client/templates/user_model_template.py) 
and save it as `accounts/models.py`.

**Option 5: Copy from installed package**

```bash
cp $(python -c "import onehux_sso_client; print(onehux_sso_client.__path__[0])")/templates/user_model_template.py accounts/models.py
```


### 4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```


### 5. Add onehux configuration to your settings.py


```python
# Onehux SSO Configuration
ONEHUX_SSO = {
    'CLIENT_ID': env('CLIENT_ID'),
    'CLIENT_SECRET': env('CLIENT_SECRET'),
    'REDIRECT_URI': env('REDIRECT_URI'),  # http://client.onehux.com/sso/callback/
    
    # IdP Endpoints
    'AUTHORIZATION_URL': env('AUTHORIZATION_URL'),  # http://accounts.onehux.com/sso/authorize/
    'TOKEN_URL': env('TOKEN_URL'),  # http://accounts.onehux.com/sso/token/
    'USERINFO_URL': env('USERINFO_URL'),  # http://accounts.onehux.com/sso/userinfo/
    'LOGOUT_URL': env('LOGOUT_URL'),  # http://accounts.onehux.com/sso/logout/
    'JWKS_URL': env('JWKS_URL'),  # http://accounts.onehux.com/sso/.well-known/jwks.json
    
    # Security
    'USE_PKCE': True,  # Highly recommended
    'VERIFY_SSL': False,  # Set to True in production
    
    # Scopes
    'SCOPES': 'openid profile email',
    
    # Token Management
    'TOKEN_REFRESH_THRESHOLD': 300,  # Refresh 5 minutes before expiry
    
    # Webhook
    'WEBHOOK_SECRET': env('WEBHOOK_SECRET'),
    'WEBHOOK_ENDPOINT': '/sso/api/webhooks/onehux/',
}

# ============================================================================
# PUBLIC PATHS CONFIGURATION (CRITICAL FOR SAAS)
# ============================================================================
# Define which paths are accessible WITHOUT authentication
# The SilentSSOMiddleware will NOT run on these paths

SSO_PUBLIC_PATHS = [
    # Core Public Pages
    '/',                    # Homepage
    '/about/',
    '/pricing/',
    '/features/',
    '/contact/',
    '/faq/',
    
    # Content Pages
    '/blog/',
    '/docs/',
    '/help/',
    '/support/',
    
    # Legal Pages
    '/legal/',
    '/privacy/',
    '/terms/',
    '/cookies/',
    
    # Authentication Pages (if you have native login)
    '/signup/',
    '/login/',
    '/forgot-password/',
    '/reset-password/',
    
    # Public API Endpoints
    '/api/public/',
    '/api/docs/',
    
    # Health Checks
    '/health/',
    '/status/',
]

# ============================================================================
# SILENT SSO CONFIGURATION
# ============================================================================

# Enable/disable silent SSO (auto-login if IdP session exists)
SSO_SILENT_AUTH_ENABLED = True

# Additional paths to ignore for silent SSO (beyond public paths)
# Use this for monitoring endpoints, admin pages, etc.


# Optional : Additional paths to ignore for silent SSO (beyond public paths)
SSO_SILENT_AUTH_IGNORED_PATHS = [
    '/health/',
    '/metrics/',
    '/monitoring/',
    '/health/'
]

# Optional : Paths to exclude from token refresh checks
SSO_TOKEN_REFRESH_EXCLUDED_PATHS = [
    '/health/',
    '/metrics/',
]


# ============================================================================
# TOKEN REFRESH CONFIGURATION
# ============================================================================

# Paths to exclude from token refresh checks
SSO_TOKEN_REFRESH_EXCLUDED_PATHS = [
    '/health/',
    '/metrics/',
    '/monitoring/',
]

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # =========================================================================
    # ONEHUX SSO MIDDLEWARES (Order matters!)
    # =========================================================================
    # 1. Silent SSO - tries to auto-login anonymous users on protected pages
    'onehux_sso_client.middleware.SilentSSOMiddleware',
    
    # 2. Token Refresh - auto-refreshes expired tokens for authenticated users
    'onehux_sso_client.middleware.SSOTokenRefreshMiddleware',
]

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================

# Custom authentication backend for SSO
AUTHENTICATION_BACKENDS = [
    'onehux_sso_client.backends.OnehuxSSOBackend',  # SSO authentication
    'django.contrib.auth.backends.ModelBackend',     # Fallback (superuser)
]

# Custom user model (if using OnehuxSSOUserMixin)
AUTH_USER_MODEL = 'accounts.User'

# Login/Logout URLs

# Where `login_required` / `@login_required` should redirect
# when an anonymous user hits a protected page
LOGIN_URL = 'sso:sso_login'  # Redirect to SSO login

# Where to send the user after they click “log out”
LOGOUT_REDIRECT_URL = '/'


# Where to send the user after a *successful* login
LOGIN_REDIRECT_URL = 'accounts:dashboard'          # or '/dashboard/'






# Session Configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_SECURE = False  # Set to True in production (HTTPS only)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================================================
# ADMIN CONFIGURATION
# ============================================================================

# Custom admin URL (for security)
ADMIN_URL = env('ADMIN_URL', default='a6b9c3d0e2f5g8h1i4j7k0')
ADMIN_LOGIN_PATH = f'/{ADMIN_URL}/'




MIDDLEWARE = [
    # ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # ...

    ## ================================================ ###
    # --- ONEHUX SSO MIDDLEWARES (in this order) ---
    
    # 1. First, check if anonymous user can be auto-logged in
    'onehux_sso_client.middleware.SilentSSOMiddleware', 
    
    # 2. Second, if they ARE logged in, ensure token is fresh
    'onehux_sso_client.middleware.SSOTokenRefreshMiddleware',

    # 3. Thirdly(Optional), 
    # 'onehux_sso_client.middleware.SSORateLimitMiddleware',  # Optional

]

```


### 6. Add url pattern to your project main urls.py

```bash
from django.urls import path, include

urlpatterns = [

    ....
    # # =========================================================================
    # # SSO ENDPOINTS / URLS
    # # =========================================================================
    path('sso/', include('onehux_sso_client.urls', namespace='sso')),
    ....
    
]
```




### 7 Protecting views in SP's

```bash
from onehux_sso_client.decorators import (
    sso_login_required,      # Basic SSO auth
    require_sso_role,        # Specific role
    require_any_role,        # Multiple roles
    require_admin,           # Admin or owner
)
```




### 3. Protect your views

```bash
# views.py

# Basic SSO protection
@sso_login_required
def dashboard(request):
    pass



# Only owners can access
@require_sso_role('owner')
def owner_panel(request):
    pass

# Owners OR admins can access
@require_any_role('owner', 'admin')
def management(request):
    pass


```



## Advanced Usage

### Manual OAuth2 Flow

```python
from onehux_sso_client import OnehuxClient

# Initialize client
client = OnehuxClient(
    client_id='your-client-id',
    client_secret='your-client-secret',
    redirect_uri='http://yourapp.com/oauth/callback',
    onehux_base_url='https://accounts.onehux.com'
)

# 1. Generate authorization URL
auth_url, state, code_verifier = client.get_authorization_url(
    scopes=['openid', 'profile', 'email']
)

# Store state and code_verifier in session, then redirect user to auth_url

# 2. Exchange authorization code for tokens (in callback view)
tokens = client.exchange_code_for_tokens(
    code='authorization-code',
    code_verifier=code_verifier
)

# 3. Get user information
user_info = client.get_user_info(tokens['access_token'])

# 4. Verify ID token (optional)
id_token_payload = client.verify_id_token(tokens['id_token'])
```

### Token Refresh

```python
# Refresh an expired access token
new_tokens = client.refresh_access_token(refresh_token)
```

### Webhook Handling

Onehux sends webhooks for user events (login, logout, profile updates). The client automatically handles these via the `onehux_webhook` view.

**Webhook Events:**
- `user.login` - User logged into your application
- `user.logout` - User logged out (global SLO)
- `user.updated` - User profile was updated

**Webhook Payload Example:**
```json
{
  "event": "user.updated",
  "timestamp": "2024-01-15T12:00:00Z",
  "user": {
    "sub": "user-uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "given_name": "John",
    "family_name": "Doe",
    "profile_version": 5
  }
}
```

## Configuration Options

| Setting | Required | Description |
|---------|----------|-------------|
| `ONEHUX_CLIENT_ID` | Yes | Your application's client ID from Onehux |
| `ONEHUX_CLIENT_SECRET` | Yes | Your application's client secret |
| `ONEHUX_REDIRECT_URI` | Yes | OAuth2 callback URL |
| `ONEHUX_BASE_URL` | No | Onehux platform URL (default: https://accounts.onehux.com) |
| `ONEHUX_WEBHOOK_SECRET` | No | Secret for webhook signature verification |
| `ONEHUX_LOGIN_URL` | No | Custom login URL (default: /oauth/login/) |

## Security Features

- **PKCE (Proof Key for Code Exchange)** - Protects against authorization code interception
- **State Parameter** - CSRF protection for OAuth2 flow
- **Webhook Signature Verification** - HMAC-SHA256 validation
- **Token Validation** - JWT signature verification with RSA keys
- **Secure Token Storage** - Session-based token management

## Development

```bash
# Clone the repository
git clone https://github.com/programmerisaac/onehux-sso-client.git
cd onehux-sso-client

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black onehux_sso_client/

# Lint code
flake8 onehux_sso_client/
```

## Example Application

See the [example-service-provider](./examples/service_provider/) directory for a complete Django application demonstrating SSO/SLO integration.

## Support

- **Documentation**: https://docs.onehux.com
- **Issues**: https://github.com/programmerisaac/onehux-sso-client/issues
- **Email**: support@onehux.com

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

## Changelog

### 1.0.0 (2025-12-18)
- Bug fixes
- Improved token validation
- Better error handling
- Single Logout bug fix
- Properly synchronize user data accross service providers

### 0.1.0 (2025-12-15)
- Initial release
- OAuth2/OIDC authentication with PKCE









