# onehux_sso_client/views.py (OPTIMIZED VERSION)

"""
Optimized Django Views for Onehux SSO Integration (Service Provider Side)
Uses custom authentication backend for better integration and maintainability.

NEW FEATURES:
- Uses OnehuxSSOBackend for authentication
- Better error handling and logging
- DRY code structure
- Optimized token management
- Silent SSO support
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import resolve_url
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from urllib.parse import urlencode
import logging

from .utils import OnehuxSSOClient, SSOSessionManager
from .decorators import sso_login_required, require_sso_role
from .models import SSOSession

# logger = logging.getLogger(__name__)
logger = logging.getLogger('onehux_sso_client') 

# ============================================================================
# SP-NATIVE LOGIN VIEW (Redirects to IdP)
# ============================================================================

@require_http_methods(['GET'])
@csrf_protect
def sp_login_view(request):
    """
    Service Provider's login page.
    Redirects to Onehux IdP for authentication with proper context.
    """
    
    # Check if user is already logged in
    if request.user.is_authenticated:
        next_url = request.GET.get('next', settings.LOGIN_REDIRECT_URL)
        return redirect(next_url)
    
    # Store next URL for post-login redirect
    next_url = request.GET.get('next')
    if next_url:
        request.session['login_next_url'] = next_url
    
    # Get login_hint if provided (pre-fill email)
    login_hint = request.GET.get('email', '')
    
    # Initialize SSO client
    client = OnehuxSSOClient()
    
    # Generate authorization URL with PKCE and prompt=login
    auth_url, state, code_verifier = client.get_authorization_url(request, prompt='login')
    
    # Add login_hint if provided
    if login_hint:
        separator = '&' if '?' in auth_url else '?'
        auth_url += f"{separator}login_hint={login_hint}"
    
    logger.info(f"Redirecting to Onehux for login (next: {next_url})")
    
    return redirect(auth_url)



# ============================================================================
# SSO LOGIN VIEW (Original - kept for backward compatibility)
# ============================================================================

@require_http_methods(['GET'])
@csrf_protect
def sso_login_view(request):
    """
    Direct SSO login flow.
    Kept for backward compatibility and direct SSO flows.
    """
    
    # Check if user is already logged in
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    
    # Initialize SSO client
    client = OnehuxSSOClient()
    
    # Generate authorization URL with PKCE
    auth_url, state, code_verifier = client.get_authorization_url(request)
    
    logger.info("Redirecting user to Onehux for SSO login")
    
    return redirect(auth_url)


# ============================================================================
# SSO CALLBACK VIEW (OPTIMIZED - Uses Custom Backend)
# ============================================================================

@require_http_methods(['GET'])
@csrf_protect
def sso_callback_view(request):
    """
    OAuth2 callback endpoint (OPTIMIZED).
    
    Uses OnehuxSSOBackend for authentication.
    
    Flow:
    1. Verify state parameter (CSRF protection)
    2. Exchange authorization code for tokens
    3. Authenticate user via OnehuxSSOBackend (auto-creates/updates user)
    4. Store tokens in session
    5. Redirect to app
    """
    
    # ========================================================================
    # STEP 1: Extract and Validate Parameters
    # ========================================================================
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    error = request.GET.get('error')
    error_description = request.GET.get('error_description')
    
    # Check for authorization errors
    if error:
        logger.error(f"OAuth error: {error} - {error_description}")
        messages.error(request, f"Authentication failed: {error_description}")
        return _handle_callback_error(request, error, error_description)
    
    # Validate required parameters
    if not code:
        logger.error("No authorization code received")
        messages.error(request, "Authentication failed: No authorization code received")
        return redirect('/')
    
    # Verify state parameter (CSRF protection)
    stored_state = request.session.get('oauth_state')
    if not stored_state or stored_state != state:
        logger.error("State mismatch - possible CSRF attack")
        messages.error(request, "Authentication failed: Invalid state parameter")
        return redirect('/')
    
    # ========================================================================
    # STEP 2: Handle Silent SSO Errors (prompt=none)
    # ========================================================================
    
    # If this is a silent SSO attempt that failed, just clear the flag and continue
    if request.session.get('sso_auto_check_done'):
        if error == 'login_required' or error == 'consent_required':
            # User needs to login explicitly - clear flag and continue as anonymous
            request.session.pop('sso_auto_check_done', None)
            logger.info("Silent SSO check failed - user not logged in at IdP")
            return redirect('/')
    
    # ========================================================================
    # STEP 3: Exchange Code for Tokens
    # ========================================================================
    
    code_verifier = request.session.get('oauth_code_verifier')
    if not code_verifier:
        logger.error("No code verifier found in session")
        messages.error(request, "Authentication failed: Session expired")
        return redirect('/')
    
    client = OnehuxSSOClient()
    token_response = client.exchange_code_for_tokens(code, code_verifier)
    
    if not token_response:
        logger.error("Failed to exchange code for tokens")
        messages.error(request, "Authentication failed: Could not obtain access token")
        return redirect('/')
    
    # ========================================================================
    # STEP 4: Fetch User Info from IdP
    # ========================================================================
    
    access_token = token_response['access_token']
    user_info = client.get_user_info(access_token)
    
    if not user_info:
        logger.error("Failed to fetch user info")
        messages.error(request, "Authentication failed: Could not retrieve user information")
        return redirect('/')
    
    # ========================================================================
    # STEP 5: Authenticate User via Custom Backend
    # ========================================================================
    
    # ✅ IMPROVED: Use custom authentication backend
    # This automatically creates/updates the user
    user = authenticate(
        request=request,
        access_token=access_token,
        user_info=user_info
    )
    
    if not user:
        logger.error("Authentication backend returned None")
        messages.error(request, "Authentication failed: Could not create user account")
        return redirect('/')
    
    # ========================================================================
    # STEP 6: Store Tokens in Session
    # ========================================================================
    
    SSOSessionManager.store_tokens(request, token_response)
    request.session['sso_user_info'] = user_info
    
    # ========================================================================
    # STEP 7: Login User
    # ========================================================================
    
    # ✅ IMPROVED: Specify backend explicitly
    login(request, user, backend='onehux_sso_client.backends.OnehuxSSOBackend')
    

    # ========================================================================
    # STEP 7.5: CREATE SSO SESSION MAPPING (CRITICAL FOR SLO)
    # ========================================================================
    # OIDC session id (standard claim)
    idp_session_id = user_info.get('sid')
    if not idp_session_id:
        logger.warning("No 'sid' claim found in ID token / userinfo")
    else:
        SSOSession.objects.update_or_create(
            idp_session_id=idp_session_id,
            defaults={
                'user': user,
                'django_session_key': request.session.session_key,
            }
        )

        logger.info(
            f"SSO session mapped: idp_session_id={idp_session_id} "
            f"→ django_session_key={request.session.session_key}"
        )



    # Clear silent SSO flag if it was set
    request.session.pop('sso_auto_check_done', None)
    
    # ========================================================================
    # STEP 8: Show Welcome Message
    # ========================================================================
    
    # Check if this is a new user (first login)
    is_new_user = user.last_login is None or (
        user.last_login and 
        (timezone.now() - user.last_login).total_seconds() < 60
    )
    
    if is_new_user:
        logger.info(f"New user registered via SSO: {user.email}")
        messages.success(
            request,
            f"Welcome to {settings.ONEHUX_SSO.get('APP_NAME', 'our platform')}, "
            f"{user.get_full_name() or user.username}! Your account has been created successfully."
        )
    else:
        logger.info(f"User logged in via SSO: {user.email}")
        messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
    
    # ========================================================================
    # STEP 9: Redirect to Next URL
    # ========================================================================
    
    next_url = request.session.pop('login_next_url', None)
    if not next_url:
        next_url = resolve_url(settings.LOGIN_REDIRECT_URL)
    
    return redirect(next_url)



# ============================================================================
# SSO LOGOUT VIEW (FIXED)
# ============================================================================

@login_required
@require_http_methods(['GET', 'POST'])
@csrf_protect
def sso_logout_view(request):
    """
    Logout user from local app and trigger Single Logout at Onehux IdP.
    
    FIXED: Now uses /sso/logout-callback/ as post_logout_redirect_uri
    which must be registered in the IdP application settings.
    """
    
    if request.method == 'POST':
        # Get tokens before clearing session
        access_token = SSOSessionManager.get_access_token(request)
        id_token = request.session.get('sso_id_token')
        
        # Revoke access token at IdP
        if access_token:
            client = OnehuxSSOClient()
            client.revoke_token(access_token, 'access_token')
            logger.info("Access token revoked at IdP")
        







        # ====================================================================
        # REMOVE SSO SESSION MAPPING (SP-initiated logout)
        # ====================================================================

        SSOSession.objects.filter(
            django_session_key=request.session.session_key
        ).delete()



        # Clear SSO session data
        SSOSessionManager.clear_session(request)
        
        # Django logout (clears session)
        logout(request)
        
        # ====================================================================
        # FIXED: Use registered post_logout_redirect_uri
        # ====================================================================
        
        # Build the FULL URL for post-logout redirect
        # This MUST match one of the URIs registered in IdP
        post_logout_redirect_uri = request.build_absolute_uri(
            reverse('sso:logout_callback')  # e.g., /sso/logout-callback/
        )
        
        # Build Onehux logout URL for SLO
        logout_params = {
            'post_logout_redirect_uri': post_logout_redirect_uri,
            'client_id': settings.ONEHUX_SSO['CLIENT_ID'],
        }
        
        # Add id_token_hint if available (recommended for OIDC)
        if id_token:
            logout_params['id_token_hint'] = id_token
        
        # Build full logout URL
        logout_url = f"{settings.ONEHUX_SSO['LOGOUT_URL']}?{urlencode(logout_params)}"
        
        logger.info(f"Redirecting to IdP logout: {logout_url}")
        
        return redirect(logout_url)
    
    # GET - show logout confirmation page
    return render(request, 'onehux_sso_client/logout_confirm.html')



# ============================================================================
# LOGOUT CALLBACK (NEW - REQUIRED)
# ============================================================================

@require_http_methods(['GET'])
def sso_logout_callback_view(request):
    """
    Callback endpoint after IdP completes logout.
    
    This is where the IdP redirects after successful logout.
    User is already logged out, just show a confirmation message.
    
    This URL MUST be registered in IdP's post_logout_redirect_uris:
    - http://dev.client.onehux.com:8002/sso/logout-callback/
    """
    
    # Get state parameter if provided (for CSRF validation)
    state = request.GET.get('state')
    
    logger.info("User returned from IdP after logout")
    
    # Show logout success page
    return render(request, 'onehux_sso_client/logout_success.html', {
        'message': 'You have been logged out successfully from all applications.',
        'show_login_button': True,
    })
















# ============================================================================
# SP-NATIVE SIGNUP VIEW (Redirects to IdP)
# ============================================================================

@require_http_methods(['GET'])
@csrf_protect
def sp_signup_view(request):
    """
    Service Provider's signup page.
    Redirects to Onehux IdP signup page with proper context.
    """
    
    # Check if user is already logged in
    if request.user.is_authenticated:
        next_url = request.GET.get('next', settings.LOGIN_REDIRECT_URL)
        return redirect(next_url)
    
    # Store next URL for post-signup redirect
    next_url = request.GET.get('next')
    if next_url:
        request.session['login_next_url'] = next_url
    
    # Get pre-fill data
    email = request.GET.get('email', '')
    
    # Initialize SSO client
    client = OnehuxSSOClient()
    
    # Generate authorization URL with PKCE and prompt=create
    auth_url, state, code_verifier = client.get_authorization_url(request, prompt='create')
    
    # Add login_hint if provided
    if email:
        separator = '&' if '?' in auth_url else '?'
        auth_url += f"{separator}login_hint={email}"
    
    logger.info(f"Redirecting to Onehux for signup (email: {email})")
    
    return redirect(auth_url)



# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _handle_callback_error(request, error, error_description):
    """
    Handle OAuth callback errors gracefully.
    
    Args:
        request: HttpRequest object
        error: Error code
        error_description: Error description
    
    Returns:
        HttpResponse: Rendered error page or redirect
    """
    
    # Map error codes to user-friendly messages
    error_messages = {
        'access_denied': 'You denied authorization to the application.',
        'invalid_request': 'Invalid authentication request.',
        'unauthorized_client': 'Application is not authorized.',
        'server_error': 'Authentication server error. Please try again.',
        'temporarily_unavailable': 'Authentication service is temporarily unavailable.',
        'login_required': 'You need to login first.',
        'consent_required': 'You need to authorize this application.',
    }
    
    user_message = error_messages.get(error, error_description)
    
    # Log the error
    logger.error(f"OAuth callback error: {error} - {error_description}")
    
    # Show error to user
    messages.error(request, f"Authentication failed: {user_message}")
    
    # Redirect to home
    return redirect('/')


# ============================================================================
# DASHBOARD VIEWS (EXAMPLES)
# ============================================================================

@sso_login_required
def member_dashboard(request):
    """
    Member dashboard - accessible to all authenticated users.
    """
    context = {
        'page_title': 'Dashboard',
        'user': request.user,
    }
    return render(request, "sso_client/member_dashboard.html", context)


@require_sso_role('admin')
def admin_dashboard(request):
    """
    Admin dashboard - requires admin role from IdP.
    """
    context = {
        'page_title': 'Admin Dashboard',
        'user': request.user,
    }
    return render(request, 'sso_client/admin_dashboard.html', context)


@require_sso_role('owner')
def owner_dashboard(request):
    """
    Owner dashboard - requires owner role from IdP.
    """
    context = {
        'page_title': 'Owner Dashboard',
        'user': request.user,
    }
    return render(request, 'sso_client/owner_dashboard.html', context)


# ============================================================================
# PROFILE VIEW (Example of using with_sso_user_info decorator)
# ============================================================================

from .decorators import with_sso_user_info

@with_sso_user_info
def user_profile_view(request):
    """
    User profile view with fresh data from IdP.
    """
    # Access fresh user info from decorator
    user_info = request.sso_user_info
    
    context = {
        'page_title': 'My Profile',
        'user': request.user,
        'user_info': user_info,
        'organization': {
            'id': request.user.organization_id,
            'name': request.user.organization_name,
        },
        'role': request.user.get_role_display(),
    }
    
    return render(request, 'sso_client/profile.html', context)

