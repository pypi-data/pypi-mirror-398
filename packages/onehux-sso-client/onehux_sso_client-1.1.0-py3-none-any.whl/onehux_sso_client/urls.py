# onehux_sso_client/urls.py

from django.urls import path
from . import views, webhooks

app_name = 'sso'


urlpatterns = [

    # =========================================================================
    # AUTHENTICATION ENDPOINTS (SP-Native)
    # =========================================================================
    # Native login and signup views (redirect to IdP with context)
    path('login/', views.sp_login_view, name='sp_login'),
    path('signup/', views.sp_signup_view, name='sp_signup'),
    

    # # =========================================================================
    # # SSO ENDPOINTS (OAuth2/OIDC)
    # # =========================================================================

    # SSO Login - initiates OAuth flow
    path('login/', views.sso_login_view, name='sso_login'),
    
    # OAuth Callback - receives authorization code
    path('callback/', views.sso_callback_view, name='sso_callback'),
    
    # SSO Logout - initiates Single Logout
    path('logout/', views.sso_logout_view, name='sso_logout'),
    
    # =========================================================================
    # LOGOUT CALLBACK (NEW - REQUIRED FOR SLO)
    # =========================================================================
    # This is where IdP redirects after completing logout
    # MUST be registered in IdP's Application.post_logout_redirect_uris
    path('logout-callback/', views.sso_logout_callback_view, name='logout_callback'),
    
    # Webhook endpoint for user sync and SLO
    path('webhooks/onehux/', webhooks.onehux_webhook_handler, name='webhook'),


]

