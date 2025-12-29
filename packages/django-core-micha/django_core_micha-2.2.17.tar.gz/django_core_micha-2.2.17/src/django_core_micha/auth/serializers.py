# django_core_micha/auth/serializers.py
from rest_framework import serializers
from .recovery import RecoveryRequest
from django.contrib.auth import get_user_model
from django.conf import settings

from .security import get_user_security_state
from .roles import RolePolicy, get_role_level_for_user, ROLE_LEVEL_3, ROLE_LEVEL_0
from .permissions import (
    has_invite_admin_rights,
    has_access_code_admin_rights,
    can_manage_support_agents,
)

User = get_user_model()

class RecoveryRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = RecoveryRequest
        fields = (
            "id",
            "user",
            "user_email",
            "message",
            "support_note",
            "status",
            "created_at",
            "resolved_at",
        )
        read_only_fields = (
            "user",
            "status",
            "created_at",
            "resolved_at",
        )



class BaseUserSerializer(serializers.ModelSerializer):
    """
    Standard Serializer für User + Profile.
    Flattened Profil-Felder (role, language, etc.) in die Top-Level-Ansicht.
    """
    # --- Profile Fields (Read/Write) ---
    role = serializers.CharField(source="profile.role", required=False)
    language = serializers.CharField(source="profile.language", required=False)
    is_new = serializers.BooleanField(source="profile.is_new", required=False)
    is_invited = serializers.BooleanField(source="profile.is_invited", required=False)
    
    accepted_privacy_statement = serializers.BooleanField(
        source="profile.accepted_privacy_statement", required=False
    )
    accepted_convenience_cookies = serializers.BooleanField(
        source="profile.accepted_convenience_cookies", required=False
    )
    is_support_agent = serializers.BooleanField(
        source="profile.is_support_agent",
        required=False,
    )
    # Support Contact (Optional)
    support_contact_id = serializers.PrimaryKeyRelatedField(
        source="profile.support_contact",
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )

    # --- Computed Fields (Read Only) ---
    security_state = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    can_manage_support_agents = serializers.SerializerMethodField()

    ui_permissions = serializers.SerializerMethodField()
    available_roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name", 
            "is_superuser", "is_active", "last_login", "date_joined",
            # Profil-Felder
            "role", "language", "is_new", "is_invited",
            "accepted_privacy_statement", "accepted_convenience_cookies",
            "support_contact_id", "is_support_agent",
            # Computed
            "security_state", "can_manage", "can_manage_support_agents",
            "ui_permissions", "available_roles",
        ]
        read_only_fields = ["email", "username", "last_login", "date_joined", "is_superuser"]

    # --- Method Fields ---

    def get_security_state(self, obj):
        request = self.context.get("request")
        return get_user_security_state(obj, request=request)

    def get_can_manage(self, obj) -> bool:
        """
        Darf der Request-User den Ziel-User (obj) bearbeiten?
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        
        # Superuser darf alles
        if request.user.is_superuser:
            return True

        policy = RolePolicy()
        # Darf ich die Rolle des Ziels ändern? Wenn ja, darf ich ihn generell managen.
        # Wir nutzen hier 'role' des Ziels, oder default fallback.
        target_role = getattr(obj.profile, 'role', 'none')
        
        # Check: Habe ich höhere Rechte als das Ziel?
        return policy.can_change_role(request.user, obj, target_role)

    def get_can_manage_support_agents(self, obj) -> bool:
        """
        Darf der aktuelle User Support-Agents verwalten?
        Delegiert komplett an den zentralen Helper.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return can_manage_support_agents(user)

    # --- Update Logic (Critical for Nested Fields) ---

    def update(self, instance, validated_data):
        """
        Überschreibt Standard-Update, um Profil-Felder (source='profile.xyz')
        korrekt im Profil-Modell zu speichern.
        """
        # 1. Profil-Daten extrahieren (DRF packt source='profile.x' in ein verschachteltes Dict)
        profile_data = validated_data.pop("profile", {})

        # 2. User-Felder updaten
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 3. Profil-Felder updaten
        if hasattr(instance, 'profile'):
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance
    
    def get_ui_permissions(self, obj) -> dict:
        """
        Liefert die UI-Permissions des *aktuellen* Request-Users.
        Diese Flags steuern Tabs wie Users / Invite / Access Codes / Support.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return {
                "can_view_users": False,
                "can_invite": False,
                "can_manage_access_codes": False,
                "can_view_support": False,
            }

        # Superuser darf alles
        if user.is_superuser:
            return {
                "can_view_users": True,
                "can_invite": True,
                "can_manage_access_codes": True,
                "can_view_support": True,
            }

        policy = RolePolicy()
        profile = getattr(user, "profile", None)
        is_support_agent = bool(getattr(profile, "is_support_agent", False))

        return {
            "can_view_users": policy.is_admin_like(user),
            "can_invite": has_invite_admin_rights(user),
            "can_manage_access_codes": has_access_code_admin_rights(user),
            # Support-UI: Support-Agent ODER jemand, der Support-Agent-Rollen verwalten darf
            "can_view_support": is_support_agent or can_manage_support_agents(user),
        }
    
    def get_available_roles(self, obj) -> list[str]:
        """
        Liefert eine Liste von Rollencodes, die der aktuelle Request-User
        prinzipiell vergeben darf (für UI-Dropdowns).
        """
        request = self.context.get("request")
        acting = getattr(request, "user", None)

        if not acting or not acting.is_authenticated:
            return []

        policy = RolePolicy()
        role_defs = policy.role_definitions()

        # Superuser: alle Rollen
        if acting.is_superuser:
            return list(role_defs.keys())

        acting_level = policy.get_user_level(acting)
        available = []

        for code, info in role_defs.items():
            level = int(info.get("level", ROLE_LEVEL_0))
            if level <= acting_level:
                available.append(code)

        return available