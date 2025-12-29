# onehux_sso_client/decorators.py

"""
Client-Side View Protection Decorators for Onehux SSO Integration
Works with single-organization role model for proper multi-tenant isolation.

FIXED: Now properly handles prompt parameter for authentication flows.

Usage Examples:
--------------
from onehux_sso_client.decorators import (
    sso_login_required, 
    require_sso_role,
    require_any_role,
)

@sso_login_required
def my_protected_view(request):
    # User is authenticated via SSO
    return render(request, 'dashboard.html')

@require_sso_role('admin')
def admin_panel(request):
    # User has 'admin' role in THIS organization
    return render(request, 'admin.html')

@require_any_role('admin', 'moderator')
def moderation_panel(request):
    # User has either 'admin' or 'moderator' role
    return render(request, 'moderation.html')
"""

from functools import wraps
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.cache import cache
import logging

from .utils import SSOSessionManager, OnehuxSSOClient

logger = logging.getLogger(__name__)


# ============================================================================
# SSO LOGIN REQUIRED DECORATOR (FIXED)
# ============================================================================

def sso_login_required(view_func):
    """
    Decorator to ensure user is authenticated via SSO.
    
    FIXED: Now initiates proper SSO flow with prompt='login' parameter.
    
    Checks:
    1. User is logged in (Django auth)
    2. Valid SSO access token exists in session
    3. Token is not expired (auto-refresh if needed)
    
    If any check fails, redirects to IdP for authentication.
    
    Usage:
        @sso_login_required
        def my_view(request):
            # User is authenticated
            user = request.user
            return render(request, 'dashboard.html')
    """
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # =====================================================================
        # CHECK 1: Is user authenticated via Django?
        # =====================================================================
        if not request.user.is_authenticated:
            logger.info(f"User not authenticated, initiating SSO flow for: {request.path}")
            
            # Store the next URL for redirect after login
            request.session['login_next_url'] = request.path
            
            # Initialize SSO client
            client = OnehuxSSOClient()
            
            # Generate authorization URL with prompt='login'
            # This forces the IdP to show login screen even if user has active session
            auth_url, state, code_verifier = client.get_authorization_url(
                request, 
                prompt='login'
            )
            
            logger.info(f"Redirecting to IdP for authentication (prompt=login)")
            return redirect(auth_url)
        
        # =====================================================================
        # CHECK 2: Does user have valid SSO token?
        # =====================================================================
        access_token = SSOSessionManager.get_access_token(request)
        
        if not access_token:
            logger.warning(f"No SSO token for user {request.user.email}, re-authenticating")
            
            # Store next URL for redirect after login
            request.session['login_next_url'] = request.path
            
            # Initialize SSO client
            client = OnehuxSSOClient()
            
            # Generate authorization URL with prompt='login'
            auth_url, state, code_verifier = client.get_authorization_url(
                request, 
                prompt='login'
            )
            
            logger.info(f"Redirecting to IdP for re-authentication")
            return redirect(auth_url)
        
        # =====================================================================
        # CHECK 3: Is token still valid? (Auto-refresh if needed)
        # =====================================================================
        if not SSOSessionManager.refresh_token_if_needed(request):
            logger.warning(f"Token refresh failed for user {request.user.email}, forcing re-login")
            
            # Token refresh failed - force complete re-authentication
            request.session['login_next_url'] = request.path
            
            # Initialize SSO client
            client = OnehuxSSOClient()
            
            # Generate authorization URL with prompt='login'
            auth_url, state, code_verifier = client.get_authorization_url(
                request, 
                prompt='login'
            )
            
            logger.info(f"Redirecting to IdP due to token refresh failure")
            return redirect(auth_url)
        
        # =====================================================================
        # All checks passed - execute protected view
        # =====================================================================
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ============================================================================
# ROLE-BASED DECORATORS (MULTI-TENANT ISOLATED)
# ============================================================================

def require_sso_role(role_name):
    """
    Decorator to ensure user has a specific role in CURRENT organization.
    
    IMPORTANT: Multi-tenant isolated - only checks roles for the current org.
    
    Args:
        role_name (str): Name of required role (e.g., 'admin', 'editor', 'viewer')
    
    Usage:
        @require_sso_role('admin')
        def admin_only_view(request):
            # User has 'admin' role
            return render(request, 'admin.html')
    
    Returns:
        403 Forbidden if user doesn't have the role
    """
    
    def decorator(view_func):
        @wraps(view_func)
        @sso_login_required  # Ensure user is authenticated first
        def wrapper(request, *args, **kwargs):
            # Get user's roles from session
            user_info = request.session.get('sso_user_info', {})
            user_roles = user_info.get('roles', [])
            
            # Check if user has the required role
            if role_name not in user_roles:
                logger.warning(
                    f"User {request.user.email} attempted to access {view_func.__name__} "
                    f"without required role: {role_name}"
                )
                
                # Return 403 Forbidden
                return render(
                    request, 
                    'onehux_sso_client/403.html',
                    {
                        'required_role': role_name,
                        'user_roles': user_roles,
                    },
                    status=403
                )
            
            # User has required role - execute view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_any_role(*role_names):
    """
    Decorator to ensure user has AT LEAST ONE of the specified roles.
    
    IMPORTANT: Multi-tenant isolated - only checks roles for current org.
    
    Args:
        *role_names: Variable number of role names
    
    Usage:
        @require_any_role('admin', 'moderator', 'editor')
        def content_management_view(request):
            # User has at least one of the specified roles
            return render(request, 'content.html')
    
    Returns:
        403 Forbidden if user doesn't have any of the roles
    """
    
    def decorator(view_func):
        @wraps(view_func)
        @sso_login_required  # Ensure user is authenticated first
        def wrapper(request, *args, **kwargs):
            # Get user's roles from session
            user_info = request.session.get('sso_user_info', {})
            user_roles = user_info.get('roles', [])
            
            # Check if user has any of the required roles
            has_required_role = any(role in user_roles for role in role_names)
            
            if not has_required_role:
                logger.warning(
                    f"User {request.user.email} attempted to access {view_func.__name__} "
                    f"without any required roles: {role_names}"
                )
                
                # Return 403 Forbidden
                return render(
                    request, 
                    'onehux_sso_client/403.html',
                    {
                        'required_roles': role_names,
                        'user_roles': user_roles,
                    },
                    status=403
                )
            
            # User has at least one required role - execute view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_all_roles(*role_names):
    """
    Decorator to ensure user has ALL of the specified roles.
    
    IMPORTANT: Multi-tenant isolated - only checks roles for current org.
    
    Args:
        *role_names: Variable number of role names
    
    Usage:
        @require_all_roles('admin', 'developer')
        def admin_developer_view(request):
            # User has both 'admin' AND 'developer' roles
            return render(request, 'admin_dev.html')
    
    Returns:
        403 Forbidden if user doesn't have all roles
    """
    
    def decorator(view_func):
        @wraps(view_func)
        @sso_login_required  # Ensure user is authenticated first
        def wrapper(request, *args, **kwargs):
            # Get user's roles from session
            user_info = request.session.get('sso_user_info', {})
            user_roles = user_info.get('roles', [])
            
            # Check if user has all required roles
            has_all_roles = all(role in user_roles for role in role_names)
            
            if not has_all_roles:
                missing_roles = [role for role in role_names if role not in user_roles]
                logger.warning(
                    f"User {request.user.email} attempted to access {view_func.__name__} "
                    f"but missing roles: {missing_roles}"
                )
                
                # Return 403 Forbidden
                return render(
                    request, 
                    'onehux_sso_client/403.html',
                    {
                        'required_roles': role_names,
                        'missing_roles': missing_roles,
                        'user_roles': user_roles,
                    },
                    status=403
                )
            
            # User has all required roles - execute view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# PERMISSION-BASED DECORATORS (MULTI-TENANT ISOLATED)
# ============================================================================

def require_sso_permission(permission_name):
    """
    Decorator to ensure user has a specific permission in CURRENT organization.
    
    IMPORTANT: Multi-tenant isolated - only checks permissions for current org.
    
    Args:
        permission_name (str): Name of required permission (e.g., 'can_delete_posts')
    
    Usage:
        @require_sso_permission('can_delete_posts')
        def delete_post_view(request, post_id):
            # User has 'can_delete_posts' permission
            post.delete()
            return redirect('posts:list')
    
    Returns:
        403 Forbidden if user doesn't have the permission
    """
    
    def decorator(view_func):
        @wraps(view_func)
        @sso_login_required  # Ensure user is authenticated first
        def wrapper(request, *args, **kwargs):
            # Get user's permissions from session
            user_info = request.session.get('sso_user_info', {})
            user_permissions = user_info.get('permissions', [])
            
            # Check if user has the required permission
            if permission_name not in user_permissions:
                logger.warning(
                    f"User {request.user.email} attempted to access {view_func.__name__} "
                    f"without required permission: {permission_name}"
                )
                
                # Return 403 Forbidden
                return render(
                    request, 
                    'onehux_sso_client/403.html',
                    {
                        'required_permission': permission_name,
                        'user_permissions': user_permissions,
                    },
                    status=403
                )
            
            # User has required permission - execute view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# AJAX-FRIENDLY DECORATORS
# ============================================================================

def api_sso_login_required(view_func):
    """
    API-friendly version of sso_login_required.
    Returns JSON error instead of redirect for AJAX requests.
    
    Usage:
        @api_sso_login_required
        def api_endpoint(request):
            # User is authenticated
            return JsonResponse({'status': 'success'})
    """
    
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'authentication_required',
                'message': 'You must be logged in to access this endpoint'
            }, status=401)
        
        # Check if SSO token exists
        access_token = SSOSessionManager.get_access_token(request)
        
        if not access_token:
            return JsonResponse({
                'error': 'sso_token_missing',
                'message': 'Valid SSO token required'
            }, status=401)
        
        # Check if token needs refresh
        if not SSOSessionManager.refresh_token_if_needed(request):
            return JsonResponse({
                'error': 'token_refresh_failed',
                'message': 'Unable to refresh authentication token'
            }, status=401)
        
        # All checks passed - execute view
        return view_func(request, *args, **kwargs)
    
    return wrapper




# ============================================================================
# SSO USER INFO DECORATOR (Inject user info into view)
# ============================================================================

def with_sso_user_info(view_func):
    """
    Decorator to inject fresh SSO user info into the view.
    Fetches latest user data from Onehux before executing view.
    
    Usage:
        @with_sso_user_info
        def profile_view(request):
            # Access fresh user info
            user_info = request.sso_user_info
            return render(request, 'profile.html', {'user_info': user_info})
    """
    
    @wraps(view_func)
    @sso_login_required
    def wrapper(request, *args, **kwargs):
        # Check cache first
        cache_key = f'sso_user_info:{request.user.id}'
        
        user_info = cache.get(cache_key)
        
        if not user_info:
            # Fetch from Onehux
            access_token = SSOSessionManager.get_access_token(request)
            client = OnehuxSSOClient()
            user_info = client.get_user_info(access_token)
            
            if user_info:
                # Cache for 5 minutes
                cache.set(cache_key, user_info, 300)
                
                # Also update local user model with latest data
                try:
                    request.user.update_from_idp(user_info)
                except Exception as e:
                    logger.error(f"Failed to update user from IdP: {e}")
        
        # Attach to request
        request.sso_user_info = user_info or {}
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# ============================================================================
# COMBINED DECORATORS
# ============================================================================

def require_role_and_scope(role, scopes):
    """
    Decorator that combines role and scope checking.
    
    Args:
        role: Required role name
        scopes: List of required scopes
    
    Usage:
        @require_role_and_scope('admin', ['profile', 'email'])
        def admin_user_management(request):
            # User has admin role AND granted profile/email scopes
            return render(request, 'admin_users.html')
    """
    
    def decorator(view_func):
        @wraps(view_func)
        @require_sso_role(role)
        @require_sso_scopes(scopes)
        def wrapper(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator





# ============================================================================
# SSO SCOPE REQUIRED DECORATOR
# ============================================================================

def require_sso_scopes(required_scopes):
    """
    Decorator to ensure user has granted specific OAuth scopes.
    
    Args:
        required_scopes: List of required scopes (e.g., ['profile', 'email'])
    
    Usage:
        @require_sso_scopes(['profile', 'email'])
        def profile_view(request):
            # User has profile and email scopes
            return render(request, 'profile.html')
    """
    
    def decorator(view_func):
        @wraps(view_func)
        @sso_login_required  # Must be SSO authenticated first
        def wrapper(request, *args, **kwargs):
            # Get user's granted scopes from session
            user_scopes = request.session.get('sso_scope', '').split()
            
            # Check if all required scopes are present
            missing_scopes = [s for s in required_scopes if s not in user_scopes]
            
            if missing_scopes:
                logger.warning(
                    f"User {request.user.email} missing scopes: {missing_scopes}"
                )
                return HttpResponseForbidden(
                    f"This action requires additional permissions: {', '.join(missing_scopes)}. "
                    "Please re-authenticate to grant these permissions."
                )
            
            # User has all required scopes
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


