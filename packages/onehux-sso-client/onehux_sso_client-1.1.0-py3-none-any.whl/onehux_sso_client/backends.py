# onehux_sso_client/backends.py

"""
Custom Authentication Backend for Onehux SSO Integration
Handles SSO-specific authentication, token validation, and user syncing.

This backend integrates with Django's authentication system to provide
seamless SSO authentication for Service Providers.

Usage in settings.py:
    AUTHENTICATION_BACKENDS = [
        'onehux_sso_client.backends.OnehuxSSOBackend',
        'django.contrib.auth.backends.ModelBackend',  # Fallback for superusers
    ]
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .utils import OnehuxSSOClient, SSOSessionManager

User = get_user_model()
logger = logging.getLogger(__name__)


class OnehuxSSOBackend(BaseBackend):
    """
    Custom authentication backend for Onehux SSO.
    
    This backend:
    - Validates SSO tokens from Onehux IdP
    - Creates/updates local user accounts automatically
    - Syncs user data including roles and organizations
    - Handles token refresh
    - Provides role-based permissions
    
    Authentication Flow:
    1. User logs in via SSO (redirected to IdP)
    2. IdP redirects back with authorization code
    3. SP exchanges code for tokens
    4. Backend validates token and fetches user info
    5. Backend creates/updates local user account
    6. User is logged in with Django session
    """
    
    def authenticate(self, request, access_token=None, user_info=None, **kwargs):
        """
        Authenticate user with SSO access token.
        
        Args:
            request: HttpRequest object
            access_token: OAuth2 access token from IdP (optional if user_info provided)
            user_info: User claims from IdP (optional if access_token provided)
        
        Returns:
            User instance if authentication succeeds, None otherwise
        """
        
        # ====================================================================
        # STEP 1: Validate Input
        # ====================================================================
        
        if not access_token and not user_info:
            logger.warning("OnehuxSSOBackend called without access_token or user_info")
            return None
        
        # ====================================================================
        # STEP 2: Fetch User Info from IdP (if not provided)
        # ====================================================================
        
        if not user_info and access_token:
            client = OnehuxSSOClient()
            user_info = client.get_user_info(access_token)
            
            if not user_info:
                logger.error("Failed to fetch user info from IdP with access token")
                return None
        
        # ====================================================================
        # STEP 3: Validate User Info
        # ====================================================================
        
        email = user_info.get('email')
        sub = user_info.get('sub')  # Onehux user ID
        
        if not email or not sub:
            logger.error("Missing required user info (email or sub)")
            return None
        
        # ====================================================================
        # STEP 4: Get or Create User
        # ====================================================================
        
        user = self._get_or_create_user(user_info)
        
        if not user:
            logger.error(f"Failed to get/create user for email: {email}")
            return None
        
        # ====================================================================
        # STEP 5: Verify User is Active
        # ====================================================================
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {email}")
            return None
        
        # ====================================================================
        # STEP 6: Update Last Login
        # ====================================================================
        
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # ====================================================================
        # STEP 7: Cache User Info for Quick Access
        # ====================================================================
        
        cache_key = f'sso_user_info:{user.id}'
        cache.set(cache_key, user_info, 300)  # 5 minutes
        
        logger.info(f"✓ User authenticated via SSO: {email} (role: {user.role})")
        
        return user
    
    def get_user(self, user_id):
        """
        Get user by ID (required by Django auth backend).
        
        Args:
            user_id: User's primary key
        
        Returns:
            User instance or None
        """
        try:
            user = User.objects.get(pk=user_id)
            
            # Check if user is still active
            if not user.is_active:
                return None
            
            return user
            
        except User.DoesNotExist:
            return None
    
    # ========================================================================
    # PERMISSION METHODS (Required for Django Admin and Permissions System)
    # ========================================================================
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has a specific permission.
        
        For SSO users, permissions are based on their role from IdP.
        Admins and Owners have all permissions.
        
        Args:
            user_obj: User instance
            perm: Permission string (e.g., 'app.view_model')
            obj: Optional object for object-level permissions
        
        Returns:
            bool: True if user has permission
        """
        if not user_obj.is_active:
            return False
        
        # Superusers have all permissions
        if user_obj.is_superuser:
            return True
        
        # Owners and Admins have all permissions
        if hasattr(user_obj, 'is_admin') and user_obj.is_admin():
            return True
        
        # Check Django permissions (fallback)
        return user_obj.has_perm(perm)
    
    def has_module_perms(self, user_obj, app_label):
        """
        Check if user has permissions to access a Django app.
        
        Args:
            user_obj: User instance
            app_label: Django app label (e.g., 'auth', 'core')
        
        Returns:
            bool: True if user has access to the app
        """
        if not user_obj.is_active:
            return False
        
        # Superusers have all module permissions
        if user_obj.is_superuser:
            return True
        
        # Owners and Admins have access to all modules
        if hasattr(user_obj, 'is_admin') and user_obj.is_admin():
            return True
        
        return False
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_or_create_user(self, user_info):
        """
        Get existing user or create new one from IdP user info.
        
        This method:
        - Tries to find user by onehux_user_id (primary key from IdP)
        - Falls back to email if not found
        - Creates new user if doesn't exist
        - Updates existing user with latest data from IdP
        
        Args:
            user_info: User claims from IdP
        
        Returns:
            User instance or None
        """
        try:
            email = user_info.get('email')
            sub = user_info.get('sub')
            
            user = None
            is_new_user = False
            
            # Try to find by Onehux user ID (most reliable)
            if sub:
                try:
                    user = User.objects.get(onehux_user_id=sub)
                except User.DoesNotExist:
                    pass
            
            # Fallback to email
            if not user and email:
                try:
                    user = User.objects.get(email=email)
                    # Update onehux_user_id if found by email
                    if sub:
                        user.onehux_user_id = sub
                except User.DoesNotExist:
                    pass
            
            # Create new user if not found
            if not user:
                user = self._create_user(user_info)
                is_new_user = True
            
            # Update user with latest data from IdP
            if user:
                user.update_from_idp(user_info)
                
                if is_new_user:
                    logger.info(f"✓ Created new user via SSO: {email}")
                else:
                    logger.info(f"✓ Updated existing user via SSO: {email}")
            
            return user
            
        except Exception as e:
            logger.error(f"Error in _get_or_create_user: {str(e)}", exc_info=True)
            return None
    
    def _create_user(self, user_info):
        """
        Create new user from IdP user info.
        
        Args:
            user_info: User claims from IdP
        
        Returns:
            User instance
        """
        email = user_info.get('email')
        sub = user_info.get('sub')
        username = user_info.get('preferred_username') or email.split('@')[0]
        
        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create(
            username=username,
            email=email,
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            is_active=True,
            onehux_user_id=sub,
        )
        
        return user
    
    def _sync_user_data(self, user, user_info):
        """
        Sync user data with IdP (DEPRECATED - use user.update_from_idp instead).
        
        This method is kept for backward compatibility.
        """
        user.update_from_idp(user_info)


# ============================================================================
# TOKEN VALIDATION BACKEND (For API Endpoints)
# ============================================================================

class OnehuxTokenBackend(BaseBackend):
    """
    Token-based authentication backend for API endpoints.
    
    Validates Bearer tokens from Authorization header.
    Does NOT create Django sessions - used for stateless API auth.
    
    Usage:
        from django.contrib.auth import authenticate
        
        user = authenticate(request, bearer_token='token-here')
        if user:
            # User is authenticated
            pass
    """
    
    def authenticate(self, request, bearer_token=None, **kwargs):
        """
        Authenticate user with Bearer token.
        
        Args:
            request: HttpRequest object
            bearer_token: Bearer token from Authorization header
        
        Returns:
            User instance if token is valid, None otherwise
        """
        if not bearer_token:
            return None
        
        # Validate token with IdP
        client = OnehuxSSOClient()
        user_info = client.get_user_info(bearer_token)
        
        if not user_info:
            return None
        
        # Find user
        email = user_info.get('email')
        sub = user_info.get('sub')
        
        if not email or not sub:
            return None
        
        try:
            user = User.objects.get(onehux_user_id=sub)
            
            if not user.is_active:
                return None
            
            # Update user data if needed
            if user.needs_sync():
                user.update_from_idp(user_info)
            
            return user
            
        except User.DoesNotExist:
            # Could auto-create user here if desired
            logger.warning(f"Token valid but user not found: {email}")
            return None
    
    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# ============================================================================
# USAGE IN SETTINGS.PY
# ============================================================================

"""
# website/settings.py

AUTHENTICATION_BACKENDS = [
    # Primary: Onehux SSO Backend (for SSO users)
    'onehux_sso_client.backends.OnehuxSSOBackend',
    
    # Secondary: Token Backend (for API endpoints)
    'onehux_sso_client.backends.OnehuxTokenBackend',
    
    # Fallback: Django's default backend (for superusers and local accounts)
    'django.contrib.auth.backends.ModelBackend',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Onehux SSO Middlewares (in this order)
    'onehux_sso_client.middleware.SilentSSOMiddleware',
    'onehux_sso_client.middleware.SSOTokenRefreshMiddleware',
]
"""