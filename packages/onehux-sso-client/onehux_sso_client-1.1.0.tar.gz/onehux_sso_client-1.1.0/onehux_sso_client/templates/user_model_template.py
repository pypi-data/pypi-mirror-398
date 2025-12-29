"""
Onehux SSO User Model Template
===============================

Copy this file to your Django project and customize as needed.

Installation Steps:
1. Copy this file to your app's models.py (e.g., accounts/models.py)
2. Customize the User model with your additional fields
3. Set AUTH_USER_MODEL in settings.py:
   AUTH_USER_MODEL = 'accounts.User'
4. Run: python manage.py makemigrations
5. Run: python manage.py migrate

⚠️  IMPORTANT: Do this BEFORE creating any users or running migrations!
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


# ==============================================================================
# OPTION 1: FULL FEATURED USER MODEL (Recommended)
# ==============================================================================

class User(AbstractUser):
    """
    Custom User model with Onehux SSO integration.
    
    Includes all Onehux SSO fields + space for your custom fields.
    """
    
    # Use UUID as primary key (optional, but recommended)
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    # =========================================================================
    # ONEHUX SSO FIELDS (Required for SSO integration)
    # =========================================================================
    
    # Identity Provider Sync
    onehux_user_id = models.UUIDField(
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        help_text="User ID from Onehux Accounts Identity Provider"
    )
    
    # Make email unique and required
    email = models.EmailField(unique=True, db_index=True)
    
    # Profile fields synced from IdP
    profile_picture_url = models.URLField(
        blank=True,
        help_text="Profile picture URL from Onehux Accounts"
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="User's date of birth"
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text="User's country"
    )
    
    region = models.CharField(
        max_length=100,
        blank=True,
        help_text="User's state/region"
    )
    
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="User's bio (max 500 characters)"
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="User's phone number"
    )
    
    # Organization & Role (single organization model)
    organization_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="UUID of the organization this user belongs to"
    )
    
    organization_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the organization (for display)"
    )
    
    role = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="User's role in their organization (e.g., 'admin', 'member')"
    )
    
    # Sync metadata
    profile_version = models.IntegerField(
        default=1,
        help_text="Profile version from IdP for sync tracking"
    )
    
    last_synced_at = models.DateTimeField(
        auto_now=True,
        help_text="When user data was last synced from IdP"
    )
    
    idp_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp from IdP of last profile update"
    )
    
    # Verification status
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Whether email is verified at IdP"
    )
    
    is_phone_verified = models.BooleanField(
        default=False,
        help_text="Whether phone is verified at IdP"
    )
    
    # Additional metadata from IdP
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata from IdP"
    )
    
    # =========================================================================
    # YOUR CUSTOM FIELDS - Add your application-specific fields here
    # =========================================================================
    
    # Example custom fields (uncomment and modify as needed):
    
    # department = models.CharField(
    #     max_length=100,
    #     blank=True,
    #     help_text="User's department"
    # )
    
    # employee_id = models.CharField(
    #     max_length=20,
    #     blank=True,
    #     unique=True,
    #     help_text="Internal employee ID"
    # )
    
    # job_title = models.CharField(
    #     max_length=100,
    #     blank=True,
    #     help_text="User's job title"
    # )
    
    # manager = models.ForeignKey(
    #     'self',
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='team_members',
    #     help_text="User's manager"
    # )
    
    # preferences = models.JSONField(
    #     default=dict,
    #     blank=True,
    #     help_text="User preferences for your application"
    # )
    
    # =========================================================================
    # METADATA
    # =========================================================================
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'  # Change this to your preferred table name
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['onehux_user_id']),
            models.Index(fields=['email']),
            models.Index(fields=['organization_id', 'role']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    # =========================================================================
    # ONEHUX SSO METHODS (Required - Do not modify)
    # =========================================================================
    
    def update_from_idp(self, user_data):
        """
        Update local user data from IdP user_data.
        Called by SSO callback and webhook handlers.
        
        Args:
            user_data: Dictionary of user data from IdP
        """
        # Basic profile
        self.username = user_data.get('username', self.username)
        self.first_name = user_data.get('given_name', '')
        self.last_name = user_data.get('family_name', '')
        self.email = user_data.get('email', self.email)
        
        # Extended profile
        self.profile_picture_url = user_data.get('picture', '')
        self.bio = user_data.get('bio', '')
        self.country = user_data.get('country', '')
        self.region = user_data.get('region', '')
        self.phone_number = user_data.get('phone_number', '')
        
        # Date of birth
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
        
        # Organization & Role
        self.role = user_data.get('role', '')
        self.organization_id = user_data.get('organization_id')
        self.organization_name = user_data.get('organization_name', '')
        
        # Sync metadata
        self.profile_version = user_data.get('profile_version', self.profile_version)
        
        # Handle updated_at timestamp
        if user_data.get('updated_at'):
            try:
                updated_at = user_data['updated_at']
                if isinstance(updated_at, (int, float)):
                    self.idp_updated_at = datetime.fromtimestamp(
                        updated_at, 
                        tz=timezone.get_current_timezone()
                    )
                elif isinstance(updated_at, str):
                    self.idp_updated_at = datetime.fromisoformat(
                        updated_at.replace('Z', '+00:00')
                    )
            except (ValueError, TypeError, OSError) as e:
                logger.warning(f"Could not parse updated_at: {e}")
        
        # Mark as active
        self.is_active = True
        
        self.save()
    
    def has_role(self, role_slug):
        """Check if user has a specific role"""
        return self.role == role_slug
    
    def has_any_role(self, *role_slugs):
        """Check if user has any of the specified roles"""
        return self.role in role_slugs
    
    def is_admin(self):
        """Check if user is admin or owner"""
        return self.role in ['admin', 'owner']
    
    def is_owner(self):
        """Check if user is owner"""
        return self.role == 'owner'
    
    def belongs_to_organization(self, org_id):
        """Check if user belongs to specified organization"""
        if not self.organization_id:
            return False
        return str(self.organization_id) == str(org_id)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username
    
    def get_profile_picture_url(self):
        """Get profile picture URL with fallback"""
        if self.profile_picture_url:
            return self.profile_picture_url
        return f"{settings.STATIC_URL}images/default-avatar.png"
    
    def get_role_display(self):
        """Get human-readable role name"""
        role_names = {
            'owner': 'Owner',
            'admin': 'Administrator',
            'member': 'Member',
            'viewer': 'Viewer',
            'developer': 'Developer',
            'manager': 'Manager',
        }
        return role_names.get(self.role, self.role.title() if self.role else 'No Role')


# ==============================================================================
# OPTION 2: MINIMAL USER MODEL (For simple projects)
# ==============================================================================

class MinimalUser(AbstractUser):
    """
    Minimal user model with only essential Onehux SSO fields.
    Use this if you want a lighter model.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Only essential SSO fields
    onehux_user_id = models.UUIDField(unique=True, null=True, blank=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    
    # Organization
    organization_id = models.UUIDField(null=True, blank=True, db_index=True)
    role = models.CharField(max_length=50, blank=True, db_index=True)
    
    # Sync tracking
    last_synced_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True  # Mark as abstract so you can copy just the fields
    
    def update_from_idp(self, user_data):
        """Minimal sync from IdP"""
        self.email = user_data.get('email', self.email)
        self.first_name = user_data.get('given_name', '')
        self.last_name = user_data.get('family_name', '')
        self.role = user_data.get('role', '')
        self.organization_id = user_data.get('organization_id')
        self.is_active = True
        self.save()
    
    def has_role(self, role_slug):
        return self.role == role_slug


# ==============================================================================
# OPTION 3: USING THE MIXIN (Most flexible)
# ==============================================================================

# If you want maximum flexibility, use the mixin from sso_client:
#
# from sso_client.models import OnehuxSSOUserMixin
#
# class User(OnehuxSSOUserMixin, AbstractUser):
#     """Your custom user with SSO support"""
#     
#     # Add only YOUR custom fields here
#     department = models.CharField(max_length=100, blank=True)
#     employee_id = models.CharField(max_length=20, blank=True)
#     
#     class Meta:
#         db_table = 'users'


# ==============================================================================
# ADMIN CONFIGURATION (Optional but recommended)
# ==============================================================================

# Add this to your admin.py:
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'role', 'organization_name', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff', 'organization_name']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Onehux SSO', {
            'fields': (
                'onehux_user_id',
                'profile_picture_url',
                'organization_id',
                'organization_name',
                'role',
            )
        }),
        ('Extended Profile', {
            'fields': (
                'date_of_birth',
                'country',
                'region',
                'bio',
                'phone_number',
            )
        }),
        ('Sync Info', {
            'fields': (
                'last_synced_at',
                'idp_updated_at',
                'profile_version',
                'is_email_verified',
                'is_phone_verified',
            )
        }),
    )
"""


