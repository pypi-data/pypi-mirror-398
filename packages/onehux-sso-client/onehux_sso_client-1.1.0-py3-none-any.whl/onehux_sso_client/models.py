# onehux_sso_client/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import datetime
import logging
from uuid6 import uuid7

logger = logging.getLogger(__name__)


class OnehuxSSOUserMixin(models.Model):
    """
    Mixin to add Onehux SSO fields to any User model.
    
    Usage in your project:
        from django.contrib.auth.models import AbstractUser
        from sso_client.models import OnehuxSSOUserMixin
        
        class User(OnehuxSSOUserMixin, AbstractUser):
            # Add your custom fields here
            department = models.CharField(max_length=100)
            pass
    """
    
    # Identity Provider Sync
    onehux_user_id = models.UUIDField(
        unique=True,
        default=uuid7,  # Use uuid7 as default
        blank=True,
        editable=False,
        null=True,
        db_index=True,
        help_text="User ID from Onehux Accounts Identity Provider"
    )
    
    # Profile fields synced from IdP
    full_name = models.CharField(max_length=50,blank=True)
    profile_picture_url = models.URLField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Organization & Role (single organization)
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    organization_name = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=50, blank=True, db_index=True)
    
    # Sync metadata
    profile_version = models.IntegerField(default=1)
    last_synced_at = models.DateTimeField(auto_now=True)
    idp_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Verification status
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        abstract = True  # ← CRITICAL: Makes this a mixin, not a concrete model
    


    # ========================================================================
    # ROLE CHECK METHODS
    # ========================================================================
    
    def has_role(self, role_slug):
        """
        Check if user has a specific role in THIS organization.
        
        Args:
            role_slug: Role slug (e.g., 'admin', 'developer')
        
        Returns:
            bool: True if user has this role
        """
        return self.role == role_slug
    
    def has_any_role(self, *role_slugs):
        """
        Check if user has any of the specified roles.
        
        Args:
            role_slugs: Variable number of role slugs
        
        Returns:
            bool: True if user has at least one of the roles
        """
        return self.role in role_slugs
    
    def is_admin(self):
        """Check if user is admin or owner"""
        return self.role in ['admin', 'owner']
    
    def is_owner(self):
        """Check if user is owner"""
        return self.role == 'owner'
    
    def is_member(self):
        """Check if user is at least a member"""
        return bool(self.role)
    
    # ========================================================================
    # ORGANIZATION METHODS
    # ========================================================================
    
    def belongs_to_organization(self, org_id):
        """
        Check if user belongs to the specified organization.
        
        Args:
            org_id: Organization UUID (string or UUID object)
        
        Returns:
            bool: True if this is the user's organization
        """
        if not self.organization_id:
            return False
        return str(self.organization_id) == str(org_id)
    
    # ========================================================================
    # PROFILE METHODS
    # ========================================================================
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def get_profile_picture_url(self):
        """Get profile picture URL with fallback"""
        if self.profile_picture_url:
            return self.profile_picture_url
        return f"{settings.STATIC_URL}images/default-avatar.png"
    
    def needs_sync(self):
        """
        Check if user data might be stale and needs syncing.
        
        Returns:
            bool: True if last sync was more than 1 hour ago
        """
        from datetime import timedelta
        if not self.last_synced_at:
            return True
        
        threshold = timezone.now() - timedelta(hours=1)
        return self.last_synced_at < threshold
    
    # ========================================================================
    # SYNC HELPER METHOD - UPDATED FOR SINGLE ORGANIZATION
    # ========================================================================

    def update_from_idp(self, user_data):
        """
        Update local user data from IdP user_data.
        ONLY accepts role for a SINGLE organization.
        
        Args:
            user_data: Dictionary of user data from IdP
                Expected format:
                {
                    'sub': 'user-uuid',
                    'email': 'user@example.com',
                    'username': 'johndoe',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'full_name': 'John Doe',
                    ... other profile fields
                }
        
        This method is called by:
        - SSO callback after login
        - Webhook handlers when user is updated
        """
        from datetime import datetime
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Basic profile
        self.username = user_data.get('username', self.username)
        self.first_name = user_data.get('first_name', '')
        self.last_name = user_data.get('last_name', '')
        self.email = user_data.get('email', self.email)
        self.is_email_verified = user_data.get('is_verified', False)

        # Extended profile
        self.profile_picture_url = user_data.get('profile_picture', '')
        self.bio = user_data.get('bio', '')
        self.country = user_data.get('country', '')
        self.region = user_data.get('region', '')
        self.phone_number = user_data.get('phone_number', '')
        
        # Date of birth (handle ISO format)
        if user_data.get('birthdate'):
            try:
                self.date_of_birth = datetime.fromisoformat(
                    user_data['birthdate']
                ).date()
            except (ValueError, TypeError):
                pass
        
        # Verification status
        self.is_email_verified = user_data.get('email_verified', False)
        self.is_phone_verified = user_data.get('phone_number_verified', False)
        
        # ===================================================================
        # CRITICAL: ONLY STORE ROLE FOR THIS APPLICATION'S ORGANIZATION
        # ===================================================================
        
        self.role = user_data.get('role', '')  # Single role string
        self.organization_id = user_data.get('organization_id')
        self.organization_name = user_data.get('organization_name', '')
        
        # Sync metadata
        self.profile_version = user_data.get('profile_version', self.profile_version)
        
        # ✅ FIXED: Handle both Unix timestamp (int) and ISO string formats
        if user_data.get('updated_at'):
            try:
                updated_at = user_data['updated_at']
                
                # Check if it's a Unix timestamp (int or float)
                if isinstance(updated_at, (int, float)):
                    # ✅ Use Django's timezone.now() to get timezone-aware datetime
                    from django.utils import timezone as django_tz
                    self.idp_updated_at = datetime.fromtimestamp(updated_at, tz=django_tz.get_current_timezone())
                # Check if it's an ISO string
                elif isinstance(updated_at, str):
                    # Handle both formats: '2024-11-10T14:37:55Z' and '2024-11-10T14:37:55+00:00'
                    self.idp_updated_at = datetime.fromisoformat(
                        updated_at.replace('Z', '+00:00')
                    )
            except (ValueError, TypeError, OSError) as e:
                # Log the error but don't fail the entire sync
                logger.warning(f"Could not parse updated_at timestamp: {updated_at} - {e}")
        
        # # Mark as active(We can't always mark as active)
        # self.is_active = True
        
        self.save()




    # ========================================================================
    # DISPLAY METHODS
    # ========================================================================
    
    def get_role_display(self):
        """Get human-readable role name"""
        role_names = {
            'owner': 'Owner',
            'admin': 'Administrator',
            'member': 'Member',
            'viewer': 'Viewer',
            'developer': 'Developer',
            'manager': 'Manager',
            'support': 'Support',
        }
        return role_names.get(self.role, self.role.title() if self.role else 'No Role')
    
    def get_organization_display(self):
        """Get organization display string"""
        if self.organization_name:
            return self.organization_name
        elif self.organization_id:
            return f"Organization {str(self.organization_id)[:8]}"
        return "No Organization"
    








class OnehuxSSOUserBase(OnehuxSSOUserMixin, AbstractUser):
    """
    Optional: Complete user model for quick start.
    
    Users can either:
    1. Use this directly (simple projects)
    2. Copy and customize (most projects)
    3. Use OnehuxSSOUserMixin with their own base (complex projects)
    
    NOT RECOMMENDED for production - use as reference only.
    """
    
    class Meta:
        abstract = True  # Still abstract - users must subclass it

    



class SSOSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    idp_session_id = models.CharField(max_length=64, unique=True)
    django_session_key = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


