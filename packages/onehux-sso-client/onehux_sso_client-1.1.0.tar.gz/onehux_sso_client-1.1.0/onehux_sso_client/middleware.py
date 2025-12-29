# onehux_sso_client/middleware.py (Service Provider - FIXED PUBLIC PAGES)

"""
FIXED Middleware for Onehux SSO
Now properly handles public pages that don't require authentication.

Key Changes:
1. PUBLIC_PATHS setting - pages that don't require auth
2. Only runs silent SSO on PROTECTED pages
3. Configurable via settings
"""

from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from django.core.cache import cache
from .utils import SSOSessionManager, OnehuxSSOClient
import logging

logger = logging.getLogger(__name__)


class SSOTokenRefreshMiddleware(MiddlewareMixin):
    """
    Automatically refresh SSO access token if expired/near expiry.
    Only runs for authenticated users.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        
        # Get admin path
        admin_path = getattr(settings, 'ADMIN_LOGIN_PATH', '/admin/')
        if not admin_path.startswith('/'):
            admin_path = '/' + admin_path
        if not admin_path.endswith('/'):
            admin_path = admin_path + '/'
        self.ADMIN_PATH = admin_path
        
        # Get additional excluded paths
        self.CUSTOM_EXCLUDED_PATHS = getattr(
            settings, 
            'SSO_TOKEN_REFRESH_EXCLUDED_PATHS', 
            []
        )
        
        logger.info(f"SSOTokenRefreshMiddleware initialized")
    
    def process_request(self, request):
        """Check if access token needs refresh"""
        
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return None
        
        # Skip for excluded paths
        if self._should_skip_path(request.path):
            return None
        
        # Check if we have an SSO token
        access_token = SSOSessionManager.get_access_token(request)
        
        if not access_token:
            # No SSO token - might be non-SSO user (e.g., superuser)
            if hasattr(request.user, 'onehux_user_id') and request.user.onehux_user_id:
                logger.warning(f"SSO user {request.user.email} has no token")
                return self._force_relogin(request)
            return None
        
        # Use cache to avoid checking every request
        cache_key = f'token_checked:{request.user.id}'
        if cache.get(cache_key):
            return None
        
        cache.set(cache_key, True, 30)  # Check every 30 seconds
        
        # Refresh token if needed
        if not SSOSessionManager.refresh_token_if_needed(request):
            logger.warning(f"Token refresh failed for {request.user.email}")
            return self._force_relogin(request)
        
        return None
    
    def _should_skip_path(self, request_path):
        """Check if path should be skipped"""
        excluded_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            self.ADMIN_PATH,
        ] + self.CUSTOM_EXCLUDED_PATHS
        
        try:
            excluded_paths.extend([
                reverse('sso:sso_logout'),
                reverse('sso:sso_callback'),
            ])
        except NoReverseMatch:
            pass
        
        return any(request_path.startswith(p) for p in excluded_paths)
    
    def _force_relogin(self, request):
        """Force user to re-login"""
        from django.contrib.auth import logout
        
        logout(request)
        request.session['login_next_url'] = request.path
        
        try:
            return redirect('sso:sso_login')
        except NoReverseMatch:
            return redirect('/sso/login/')


class SilentSSOMiddleware(MiddlewareMixin):
    """
    FIXED: Silent SSO middleware that respects public pages.
    
    Only attempts silent authentication on PROTECTED pages.
    Public pages (home, about, etc.) are accessible without auth.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.sso_client = OnehuxSSOClient()
        
        # Get admin path
        admin_path = getattr(settings, 'ADMIN_LOGIN_PATH', '/admin/')
        if not admin_path.startswith('/'):
            admin_path = '/' + admin_path
        if not admin_path.endswith('/'):
            admin_path = admin_path + '/'
        self.ADMIN_PATH = admin_path
        
        # Check if silent SSO is enabled
        self.ENABLED = getattr(settings, 'SSO_SILENT_AUTH_ENABLED', True)
        
        # =====================================================================
        # PUBLIC PATHS - CRITICAL FOR SAAS
        # =====================================================================
        # These paths are accessible WITHOUT authentication
        # Silent SSO will NOT run on these paths
        self.PUBLIC_PATHS = getattr(settings, 'SSO_PUBLIC_PATHS', [
            '/',              # Home page
            '/about/',
            '/pricing/',
            '/features/',
            '/contact/',
            '/docs/',
            '/blog/',
            '/legal/',
            '/privacy/',
            '/terms/',
            '/signup/',       # Allow signup page
            '/login/',        # Allow login page (native)
        ])
        # Get additional ignored paths (for SSO operations)
        self.CUSTOM_IGNORED_PATHS = getattr(
            settings,
            'SSO_SILENT_AUTH_IGNORED_PATHS',
            []
        )
        
        logger.info(
            f"SilentSSOMiddleware initialized (enabled: {self.ENABLED}, "
            f"public_paths: {len(self.PUBLIC_PATHS)})"
        )
    
    def process_request(self, request):
        """Check if anonymous user can be auto-logged in via IdP"""

        # Skip if disabled
        if not self.ENABLED:
            return None
        
        # Skip if user is already authenticated
        if request.user.is_authenticated:
            return None
        
        # Skip for HTMX requests
        if request.headers.get('HX-Request'):
            return None
        
        # =====================================================================
        # CRITICAL: Skip for public paths
        # =====================================================================
        if self._is_public_path(request.path):
            return None
        
        # Skip for ignored paths (SSO operations)
        if self._should_skip_path(request.path):
            return None
        
        # Loop protection - only try once per session
        if request.session.get('sso_auto_check_done'):
            return None
        
        # Skip if this is an error from previous silent attempt
        if request.GET.get('error') in ['login_required', 'consent_required']:
            request.session['sso_auto_check_done'] = True
            return None
        
        # =====================================================================
        # PERFORM SILENT AUTH - Only on protected pages
        # =====================================================================
        
        logger.info(f"Attempting silent SSO for protected path: {request.path}")
        
        # Mark session to prevent loop
        request.session['sso_auto_check_done'] = True
        
        # Store original path for redirect after login
        if request.path != '/':
            request.session['login_next_url'] = request.path
        
        # Generate URL with prompt=none (silent authentication)
        auth_url, _, _ = self.sso_client.get_authorization_url(request, prompt='none')
        
        return redirect(auth_url)
    
    def _is_public_path(self, request_path):
        """
        Check if path is public (doesn't require authentication).
        
        Returns True for paths in SSO_PUBLIC_PATHS setting.
        """
        for public_path in self.PUBLIC_PATHS:
            if request_path == public_path or request_path.startswith(public_path):
                return True
        return False
    
    def _should_skip_path(self, request_path):
        """Check if path should be skipped for silent SSO (SSO operations)"""
        
        ignored_paths = [
            '/static/',
            '/media/',
            '/favicon.ico',
            self.ADMIN_PATH,
        ] + self.CUSTOM_IGNORED_PATHS
        
        # Add SSO URLs
        try:
            ignored_paths.extend([
                reverse('sso:sso_callback'),
                reverse('sso:sso_login'),
                reverse('sso:sso_logout'),
                reverse('sso:logout_callback'),
            ])
        except NoReverseMatch:
            ignored_paths.extend(['/sso/', '/login/', '/logout/'])
        
        return any(request_path.startswith(p) for p in ignored_paths)

