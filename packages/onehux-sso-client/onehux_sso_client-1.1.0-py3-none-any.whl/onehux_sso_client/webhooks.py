# sso_client/webhooks.py (Service Provider - COMPLETE FIX)

"""
Webhook Handler for Onehux SSO Events - FIXED VERSION
Handles user profile updates, role changes, and Single Logout events from Onehux.

CRITICAL FIX: Properly handles full user data in role_updated webhooks.

Events:
- user.updated: User profile changed at Onehux
- user.role_updated: User role changed in THIS organization
- user.logout: User logged out at Onehux (trigger SLO)
- user.deleted: User deleted their account
"""

import hmac
import hashlib
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.cache import SessionStore
from django.utils import timezone
import logging
from .models import SSOSession

User = get_user_model()
logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(['POST'])
def onehux_webhook_handler(request):
    """
    Handle webhooks from Onehux Accounts.
    
    Security:
    - Verifies HMAC signature
    - Validates webhook secret
    - Logs all webhook events
    """
    
    # Verify webhook signature
    signature = request.META.get('HTTP_X_ONEHUX_SIGNATURE')
    if not signature:
        logger.warning("Webhook received without signature")
        return HttpResponse("Missing signature", status=401)
    
    # Compute expected signature
    webhook_secret = settings.ONEHUX_SSO['WEBHOOK_SECRET']
    payload = request.body
    
    expected_signature = hmac.new(
        webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        logger.warning("Webhook signature mismatch")
        return HttpResponse("Invalid signature", status=401)
    
    # Parse webhook payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return HttpResponse("Invalid JSON", status=400)
    
    event_type = data.get('event')
    
    logger.info(f"Received webhook: {event_type}")
    logger.debug(f"Webhook data: {data}")
    
    # Route to appropriate handler
    if event_type == 'user.updated':
        _handle_user_updated(data)
    elif event_type == 'user.role_updated':
        _handle_user_role_updated(data)
    elif event_type == 'user.logout':
        _handle_user_logout(data)
    elif event_type == 'user.deleted':
        _handle_user_deleted(data)
    elif event_type == 'user.created':
        _handle_user_created(data)
    else:
        logger.warning(f"Unknown webhook event type: {event_type}")
    
    return HttpResponse("OK", status=200)


# ============================================================================
# SINGLE LOGOUT HANDLER
# ============================================================================

def _handle_user_logout(data):
    """
    Handle Single Logout event from Onehux.
    Terminate user's session in this application.
    """
    idp_session_id = data.get('data', {}).get('session_id')

    mapping = SSOSession.objects.filter(
        idp_session_id=idp_session_id
    ).first()

    if not mapping:
        logger.info("Duplicate SLO ignored: %s", idp_session_id)
        return

    django_session_key = mapping.django_session_key

    # Delete Django session
    deleted, _ = Session.objects.filter(
        session_key=django_session_key
    ).delete()

    # Delete Cache session
    store = SessionStore(session_key=django_session_key)
    store.delete()
    
    logger.info(
        "✓ SLO OK: idp_session_id=%s django_session=%s deleted=%s",
        idp_session_id,
        django_session_key,
        deleted
    )
    logger.info("✓ Django cache session deleted")

    mapping.delete()


# ============================================================================
# USER PROFILE UPDATE HANDLER
# ============================================================================

def _handle_user_updated(data):
    """
    Handle user profile update from Onehux.
    Syncs user data including role for THIS organization only.
    """
    try:
        user_data = data.get('data', {})
        email = user_data.get('email')
        user_id = user_data.get('user_id')
        
        if not email and not user_id:
            logger.warning("Missing user identifiers in webhook")
            return
        
        # Find local user (prefer onehux_user_id, fallback to email)
        user = None
        if user_id:
            try:
                user = User.objects.get(onehux_user_id=user_id)
            except User.DoesNotExist:
                pass
        
        if not user and email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
        
        if not user:
            logger.warning(f"User not found for sync: email={email}, user_id={user_id}")
            return

        # Update user with synced data
        user.update_from_idp(user_data)
        
        logger.info(f"✓ Synced user profile from Onehux: {user.email}")
        
    except Exception as e:
        logger.error(f"Error handling user.updated webhook: {str(e)}", exc_info=True)


# ============================================================================
# USER ROLE UPDATE HANDLER - FIXED VERSION
# ============================================================================

def _handle_user_role_updated(data):
    """
    Handle user role changes from Onehux.
    
    ✅ FIXED: Now properly syncs all user data from the webhook payload.
    
    The IDP sends complete user profile data in role_updated webhooks,
    so we use update_from_idp() to sync everything, not just the role.
    
    CRITICAL MULTI-TENANT LOGIC:
    - Each SP application belongs to ONE organization
    - Only update user's role if this webhook is for OUR organization
    - Ignore webhooks for other organizations (user has different roles there)
    
    Payload format:
    {
        "event": "user.role_updated",
        "timestamp": "2024-01-01T00:00:00Z",
        "data": {
            "user_id": "uuid",
            "email": "user@example.com",
            "username": "alice",
            "first_name": "Alice",
            "last_name": "Smith",
            "full_name": "Alice Smith",
            "bio": "My bio",
            "picture": "https://...",
            "phone_number": "+1234567890",
            "organization_id": "uuid",
            "organization_name": "Acme Corp",
            "organization_slug": "acme-corp",
            "role": "admin",
            "role_name": "Administrator",
            "updated_at": "2024-01-01T00:00:00Z",
            ... (all other profile fields)
        }
    }
    """
    try:
        user_data = data.get('data', {})
        email = user_data.get('email')
        user_id = user_data.get('user_id')
        new_role = user_data.get('role')
        webhook_org_id = user_data.get('organization_id')
        webhook_org_name = user_data.get('organization_name')
        
        # ================================================================
        # VALIDATION: Ensure required fields are present
        # ================================================================
        if not (email or user_id):
            logger.warning("Missing user identifiers in role update webhook")
            return
        
        if not new_role:
            logger.warning("Missing new_role in role update webhook")
            return
        
        if not webhook_org_id:
            logger.error("Missing organization_id in role update webhook - CRITICAL!")
            return
        
        # ================================================================
        # FIND USER: Try onehux_user_id first, fallback to email
        # ================================================================
        user = None
        
        if user_id:
            try:
                user = User.objects.get(onehux_user_id=user_id)
            except User.DoesNotExist:
                logger.debug(f"User not found by onehux_user_id: {user_id}")
        
        if not user and email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warning(
                    f"User not found in this SP: email={email}, user_id={user_id}. "
                    f"User may not have logged into this application yet."
                )
                return
        
        if not user:
            logger.warning(
                f"User not found for role update: email={email}, user_id={user_id}"
            )
            return
        
        # ================================================================
        # CRITICAL CHECK: Is this webhook for OUR organization?
        # ================================================================
        
        # Case 1: User doesn't have an organization yet (first login pending)
        if not user.organization_id:
            logger.info(
                f"User {user.email} has no organization set. "
                f"Initializing with {webhook_org_name} and role {new_role}"
            )
            
            # ✅ FIX: Use update_from_idp to sync ALL fields from webhook
            # The IDP sends complete user data in the role_updated webhook
            user.update_from_idp(user_data)
            
            logger.info(
                f"✓ Initialized organization and role for {user.email}: "
                f"{webhook_org_name} → {new_role}"
            )
            return
        
        # Case 2: Webhook is for a DIFFERENT organization - IGNORE IT
        if str(webhook_org_id) != str(user.organization_id):
            logger.info(
                f"Ignoring role update for {user.email}: "
                f"Webhook is for org {webhook_org_name} ({webhook_org_id}), "
                f"but this SP belongs to org {user.organization_name} ({user.organization_id})"
            )
            return
        
        # ================================================================
        # Case 3: Webhook is for OUR organization
        # ✅ FIX: Sync ALL user data, not just role
        # The IDP provides complete user profile in role_updated webhooks
        # ================================================================
        old_role = user.role
        
        # ✅ Use update_from_idp to sync all fields properly
        # This ensures profile fields (bio, picture, phone, etc.) are also updated
        # and avoids the issue where other fields get blanked out
        user.update_from_idp(user_data)
        
        logger.info(
            f"✓ Updated user profile and role for {user.email} in {user.organization_name}: "
            f"{old_role or 'no-role'} → {new_role}"
        )
        
        # ================================================================
        # OPTIONAL: Invalidate user's sessions if role changed to lower permission
        # ================================================================
        if _is_permission_downgrade(old_role, new_role):
            logger.info(
                f"Permission downgrade detected for {user.email}. "
                f"Consider invalidating active sessions."
            )
            # Uncomment to force re-login on permission downgrade:
            # _invalidate_user_sessions(user)
        
    except Exception as e:
        logger.error(
            f"Error handling user.role_updated webhook: {str(e)}", 
            exc_info=True
        )


def _is_permission_downgrade(old_role, new_role):
    """
    Check if the role change represents a permission downgrade.
    
    Role hierarchy (higher = more permissions):
    owner (100) > admin (80) > staff (50) > member (30) > viewer (10)
    """
    role_levels = {
        'owner': 100,
        'admin': 80,
        'staff': 50,
        'member': 30,
        'viewer': 10,
        '': 0,
        None: 0,
    }
    
    old_level = role_levels.get(old_role, 0)
    new_level = role_levels.get(new_role, 0)
    
    return new_level < old_level


def _invalidate_user_sessions(user):
    """
    Invalidate all active sessions for a user.
    Useful when permissions are downgraded.
    """
    from django.contrib.sessions.models import Session
    from .models import SSOSession
    
    # Get all SSO sessions for this user
    sso_sessions = SSOSession.objects.filter(user=user)
    
    for sso_session in sso_sessions:
        # Delete Django session
        Session.objects.filter(
            session_key=sso_session.django_session_key
        ).delete()
        
        # Delete cache-based session
        from django.contrib.sessions.backends.cache import SessionStore
        store = SessionStore(session_key=sso_session.django_session_key)
        store.delete()
    
    # Delete SSO session mappings
    sso_sessions.delete()
    
    logger.info(f"Invalidated all sessions for user {user.email}")


# ============================================================================
# USER CREATED HANDLER
# ============================================================================

def _handle_user_created(data):
    """
    Handle new user creation from Onehux.
    
    This is useful when users are created at IdP and need to be
    pre-provisioned at the SP before they login.
    """
    try:
        user_data = data.get('data', {})
        email = user_data.get('email')
        user_id = user_data.get('user_id')
        
        if not email or not user_id:
            logger.warning("Missing user identifiers in user.created webhook")
            return
        
        # Check if user already exists
        if User.objects.filter(onehux_user_id=user_id).exists():
            logger.info(f"User already exists: {email}")
            return
        
        if User.objects.filter(email=email).exists():
            logger.info(f"User with email already exists: {email}")
            return
        
        # Create new user
        username = user_data.get('username') or email.split('@')[0]
        
        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create(
            username=username,
            email=email,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            is_active=True,
            onehux_user_id=user_id,
        )
        
        # Update with full profile data
        user.update_from_idp(user_data)
        
        logger.info(f"✓ Created new user from webhook: {email}")
        
    except Exception as e:
        logger.error(f"Error handling user.created webhook: {str(e)}", exc_info=True)


# ============================================================================
# USER DELETION HANDLER
# ============================================================================

def _handle_user_deleted(data):
    """
    Handle user account deletion from Onehux.
    
    Options:
    1. Delete user completely (GDPR compliance)
    2. Anonymize user (preserve data relationships)
    
    Current implementation: Anonymize (safer for data integrity)
    """
    try:
        user_data = data.get('data', {})
        email = user_data.get('email')
        user_id = user_data.get('user_id')
        
        if not email and not user_id:
            logger.warning("Missing user identifiers in deletion webhook")
            return
        
        # Find user
        user = None
        if user_id:
            try:
                user = User.objects.get(onehux_user_id=user_id)
            except User.DoesNotExist:
                pass
        
        if not user and email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
        
        if not user:
            logger.warning(f"User not found for deletion: email={email}, user_id={user_id}")
            return
        
        # Option 1: Complete deletion (uncomment if preferred)
        # user.delete()
        # logger.info(f"✓ Deleted user account: {email}")
        
        # Option 2: Anonymize user (default - safer for data integrity)
        user.email = f"deleted_{user.id}@onehux.local"
        user.username = f"deleted_{user.id}"
        user.first_name = "Deleted"
        user.last_name = "User"
        user.is_active = False
        user.profile_picture_url = ""
        user.bio = ""
        user.phone_number = ""
        user.role = ""
        user.organization_id = None
        user.organization_name = ""
        user.onehux_user_id = None
        user.save()
        
        logger.info(f"✓ Anonymized user account: {email}")
        
    except Exception as e:
        logger.error(f"Error handling user.deleted webhook: {str(e)}", exc_info=True)




