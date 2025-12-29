# onehux_sso_client/utils.py

"""
Utility functions and classes for Onehux SSO Client integration.

Includes:
- OnehuxSSOClient: Main SSO client for OAuth2/OIDC flows
- SSOSessionManager: Session management for tokens and user info
"""

import secrets
import hashlib
import base64
import requests
import jwt
import logging
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import pkg_resources
from datetime import timedelta
from urllib.parse import urlencode, parse_qs, urlparse

logger = logging.getLogger(__name__)


# ============================================================================
# SSO SESSION MANAGER
# ============================================================================

class SSOSessionManager:
    """
    Manages SSO tokens and user info in Django session.
    
    Handles:
    - Storing access/refresh tokens
    - Token expiration tracking
    - Automatic token refresh
    - Session cleanup
    """
    
    @staticmethod
    def store_tokens(request, token_response):
        """
        Store OAuth tokens in session.
        
        Args:
            request: Django request object
            token_response (dict): Token response from IdP containing:
                - access_token
                - refresh_token (optional)
                - id_token (optional)
                - expires_in (seconds)
                - token_type
        """
        # Store tokens
        request.session['sso_access_token'] = token_response.get('access_token')
        request.session['sso_refresh_token'] = token_response.get('refresh_token')
        request.session['sso_id_token'] = token_response.get('id_token')
        request.session['sso_token_type'] = token_response.get('token_type', 'Bearer')
        
        # Calculate expiration time (with 5 minute buffer)
        expires_in = token_response.get('expires_in', 3600)  # Default 1 hour
        expiration_time = timezone.now() + timedelta(seconds=expires_in - 300)
        request.session['sso_token_expires_at'] = expiration_time.isoformat()
        
        # Mark session as modified
        request.session.modified = True
        
        logger.info("SSO tokens stored in session")
    
    @staticmethod
    def get_access_token(request):
        """
        Get access token from session.
        
        Returns:
            str: Access token or None if not found
        """
        return request.session.get('sso_access_token')
    
    @staticmethod
    def get_refresh_token(request):
        """
        Get refresh token from session.
        
        Returns:
            str: Refresh token or None if not found
        """
        return request.session.get('sso_refresh_token')
    
    @staticmethod
    def is_token_expired(request):
        """
        Check if access token is expired.
        
        Returns:
            bool: True if expired or expiration unknown
        """
        expiration_str = request.session.get('sso_token_expires_at')
        
        if not expiration_str:
            return True  # No expiration info = assume expired
        
        try:
            expiration_time = timezone.datetime.fromisoformat(expiration_str)
            return timezone.now() >= expiration_time
        except (ValueError, TypeError):
            return True  # Invalid format = assume expired
    
    @staticmethod
    def refresh_token_if_needed(request):
        """
        Refresh access token if expired or about to expire.
        
        Args:
            request: Django request object
        
        Returns:
            bool: True if token is valid or successfully refreshed, False otherwise
        """
        # Check if token is expired
        if not SSOSessionManager.is_token_expired(request):
            return True  # Token still valid
        
        # Get refresh token
        refresh_token = SSOSessionManager.get_refresh_token(request)
        
        if not refresh_token:
            logger.warning("No refresh token available for token refresh")
            return False
        
        # Initialize SSO client
        client = OnehuxSSOClient()
        
        # Attempt to refresh token
        token_response = client.refresh_access_token(refresh_token)
        
        if not token_response:
            logger.error("Token refresh failed")
            return False
        
        # Store new tokens
        SSOSessionManager.store_tokens(request, token_response)
        
        logger.info("Access token successfully refreshed")
        return True
    
    @staticmethod
    def clear_session(request):
        """
        Clear all SSO-related session data.
        
        Args:
            request: Django request object
        """
        # List of SSO session keys to remove
        sso_keys = [
            'sso_access_token',
            'sso_refresh_token',
            'sso_id_token',
            'sso_token_type',
            'sso_token_expires_at',
            'sso_user_info',
            'oauth_state',
            'oauth_nonce',
            'oauth_code_verifier',
            'login_next_url',
            'sso_auto_check_done',
        ]
        
        # Remove each key
        for key in sso_keys:
            request.session.pop(key, None)
        
        # Mark session as modified
        request.session.modified = True
        
        logger.info("SSO session data cleared")


# ============================================================================
# ONEHUX SSO CLIENT
# ============================================================================

class OnehuxSSOClient:
    """
    Onehux SSO Client for Service Providers.
    Handles OAuth2/OIDC flows with PKCE.
    """
    
    def __init__(self):
        self.config = settings.ONEHUX_SSO
        self.client_id = self.config['CLIENT_ID']
        self.client_secret = self.config['CLIENT_SECRET']
        self.redirect_uri = self.config['REDIRECT_URI']
    
    # ========================================================================
    # PKCE UTILITIES
    # ========================================================================
    
    @staticmethod
    def generate_code_verifier():
        """
        Generate PKCE code verifier (random string).
        
        Returns:
            str: 64-character random URL-safe string
        """
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def generate_code_challenge(code_verifier):
        """
        Generate PKCE code challenge from verifier using SHA256.
        
        Args:
            code_verifier (str): Code verifier string
        
        Returns:
            str: Base64 URL-encoded SHA256 hash of verifier
        """
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode().rstrip('=')
        return challenge
    
    @staticmethod
    def generate_state():
        """
        Generate random state for CSRF protection.
        
        Returns:
            str: 32-character random URL-safe string
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_nonce():
        """
        Generate random nonce for OIDC replay protection.
        
        Returns:
            str: 32-character random URL-safe string
        """
        return secrets.token_urlsafe(32)
    
    # ========================================================================
    # AUTHORIZATION FLOW
    # ========================================================================
    
    def get_authorization_url(self, request, prompt=None):
        """
        Generate authorization URL to redirect user to Onehux for login.
        
        Args:
            request: Django request object
            prompt (str): OIDC prompt parameter. Valid values:
                - 'login': Force user to re-authenticate even if session exists
                - 'create': Show signup page instead of login
                - 'none': Silent authentication (no user interaction)
                - 'consent': Force consent screen
                - None: Default behavior (show login if no session)
        
        Returns:
            tuple: (authorization_url, state, code_verifier)
        """
        logger.info(f"Generating authorization URL with prompt={prompt}")
        
        # Generate security parameters
        state = self.generate_state()
        nonce = self.generate_nonce()
        code_verifier = self.generate_code_verifier()
        code_challenge = self.generate_code_challenge(code_verifier)
        
        # Store in session for verification during callback
        request.session['oauth_state'] = state
        request.session['oauth_nonce'] = nonce
        request.session['oauth_code_verifier'] = code_verifier
        
        # Build parameters for authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.config['SCOPES'],
            'state': state,
            'nonce': nonce,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        
        # Add prompt parameter if provided
        if prompt:
            params['prompt'] = prompt
            logger.info(f"Added prompt parameter: {prompt}")
        
        # Build full authorization URL
        auth_url = f"{self.config['AUTHORIZATION_URL']}?{urlencode(params)}"
        
        logger.info(f"Authorization URL generated successfully (prompt={prompt})")
        
        return auth_url, state, code_verifier
    
    # ========================================================================
    # TOKEN EXCHANGE
    # ========================================================================
    
    def exchange_code_for_tokens(self, code, code_verifier):
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code (str): Authorization code from callback
            code_verifier (str): PKCE code verifier from session
        
        Returns:
            dict: Token response containing:
                - access_token
                - refresh_token
                - id_token
                - expires_in
                - token_type
            Or None if exchange fails
        """
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code_verifier': code_verifier,
        }
        
        try:
            response = requests.post(
                self.config['TOKEN_URL'],
                data=data,
                verify=self.config.get('VERIFY_SSL', True),
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Successfully exchanged code for tokens")
                return response.json()
            else:
                logger.error(
                    f"Token exchange failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}", exc_info=True)
            return None
    
    # ========================================================================
    # TOKEN REFRESH
    # ========================================================================
    
    def refresh_access_token(self, refresh_token):
        """
        Refresh expired access token using refresh token.
        
        Args:
            refresh_token (str): Valid refresh token
        
        Returns:
            dict: New token response or None if refresh fails
        """
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        try:
            response = requests.post(
                self.config['TOKEN_URL'],
                data=data,
                verify=self.config.get('VERIFY_SSL', True),
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Successfully refreshed access token")
                return response.json()
            else:
                logger.error(
                    f"Token refresh failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
            return None
    
    # ========================================================================
    # USERINFO
    # ========================================================================
    
    def get_user_info(self, access_token):
        """
        Fetch user information from Onehux using access token.
        
        Args:
            access_token (str): Valid access token
        
        Returns:
            dict: User claims (sub, email, name, roles, permissions, etc.)
            Or None if request fails
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(
                self.config['USERINFO_URL'],
                headers=headers,
                verify=self.config.get('VERIFY_SSL', True),
                timeout=10
            )
            print("RESPONSE FROM get_user_info method in onehux_sso_client/utils.py =============== >>>>>>>>>>> ", response)
            # print("RESPONSE FROM get_user_info method in onehux_sso_client/utils.py =============== >>>>>>>>>>> ", response)
            # print("RESPONSE FROM get_user_info method in onehux_sso_client/utils.py =============== >>>>>>>>>>> ", response)
            # print("RESPONSE FROM get_user_info method in onehux_sso_client/utils.py =============== >>>>>>>>>>> ", response)
            # print("RESPONSE FROM get_user_info method in onehux_sso_client/utils.py =============== >>>>>>>>>>> ", response)
            
            if response.status_code == 200:
                logger.info("Successfully fetched user info")
                return response.json()
            else:
                logger.error(
                    f"UserInfo request failed: {response.status_code} - {response.text}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user info: {str(e)}", exc_info=True)
            return None
    
    # ========================================================================
    # TOKEN REVOCATION
    # ========================================================================
    
    def revoke_token(self, token, token_type_hint='access_token'):
        """
        Revoke an access or refresh token at the IdP.
        
        Args:
            token (str): Token to revoke
            token_type_hint (str): 'access_token' or 'refresh_token'
        
        Returns:
            bool: True if revocation request was successful
        """
        data = {
            'token': token,
            'token_type_hint': token_type_hint,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        # Build revocation URL (typically /token/revoke or /revoke)
        revoke_url = self.config.get(
            'REVOKE_URL',
            self.config['TOKEN_URL'].replace('/token/', '/revoke/')
        )
        
        try:
            response = requests.post(
                revoke_url,
                data=data,
                verify=self.config.get('VERIFY_SSL', True),
                timeout=10
            )
            
            # RFC 7009: Token revocation endpoint always returns 200
            logger.info(f"Token revocation request sent: {token_type_hint}")
            return True
                
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}", exc_info=True)
            return False
        


def get_user_model_template():
    """
    Get the user model template content as a string.
    
    Returns:
        str: Content of user_model_template.py
    
    Example:
        from onehux_sso_client.utils import get_user_model_template
        
        template = get_user_model_template()
        with open('accounts/models.py', 'w') as f:
            f.write(template)
    """
    try:
        return pkg_resources.resource_string(
            'onehux_sso_client',
            'templates/user_model_template.py'
        ).decode('utf-8')
    except Exception as e:
        raise FileNotFoundError(
            f"Could not load user model template: {e}"
        )

def get_template_path():
    """Get the file path to the user model template."""
    return pkg_resources.resource_filename(
        'onehux_sso_client',
        'templates/user_model_template.py'
    )






