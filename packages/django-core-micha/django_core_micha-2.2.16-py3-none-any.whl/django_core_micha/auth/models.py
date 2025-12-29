# src/django_core_micha/auth/models.py
from django.db import models
from django.conf import settings
from .roles import get_role_choices, get_default_role_code # <--- Import aus roles.py
import uuid

class AbstractUserProfile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="profile"
    )
    
    # Hier nutzen wir die zentralen Funktionen
    role = models.CharField(
        max_length=64,
        choices=get_role_choices(),      # <--- Neu
        default=get_default_role_code    # <--- Existierend
    )

    language = models.CharField(max_length=10, default="en")
    is_new = models.BooleanField(default=True)
    is_invited = models.BooleanField(default=False)
    accepted_privacy_statement = models.BooleanField(default=False)
    accepted_convenience_cookies = models.BooleanField(default=False)

    is_support_agent = models.BooleanField(default=False)
    
    support_contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="supported_users",
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.user.email} ({self.role})"