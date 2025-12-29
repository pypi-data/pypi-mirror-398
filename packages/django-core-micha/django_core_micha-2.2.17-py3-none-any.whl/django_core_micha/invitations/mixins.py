# django_core_micha/invitations/mixins.py

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django_core_micha.auth.permissions import (
    has_invite_admin_rights,
    IsInviteAdminOrSuperuser,
)
from .serializers import InviteUserSerializer
from .emails import send_invite_or_reset_email
from .access_codes import validate_access_code_or_error

User = get_user_model()


class InviteActionsMixin:
    """
    Bietet:
      - POST /invite/         (Self-Signup + Admin-Invite)
      - POST /reset-request/  (Passwort vergessen)
      - GET  /<pk>/invite-link/ (Admin-Link)
    """

    invite_serializer_class = InviteUserSerializer
    

    def _get_invite_serializer(self, *args, **kwargs):
        return self.invite_serializer_class(*args, **kwargs)
    
    def get_throttles(self):
        # Set throttle_scope based on action & user before throttling is evaluated.
        if getattr(self, "action", None) == "reset_request":
            self.throttle_scope = "password_reset"
        elif getattr(self, "action", None) == "invite":
            user = getattr(self.request, "user", None)
            if user and user.is_authenticated:
                self.throttle_scope = "invite_admin"
            else:
                self.throttle_scope = "invite_anon"
        else:
            self.throttle_scope = None

        return super().get_throttles()

    def _mark_invited_profile(self, user, *, created: bool) -> None:
        profile = getattr(user, "profile", None)
        if not profile:
            return

        if created and hasattr(profile, "is_new"):
            profile.is_new = True

        if hasattr(profile, "is_invited"):
            profile.is_invited = True

        profile.save()

    def _build_frontend_url(self, request, user, *, is_new_user: bool) -> str:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        base = request.build_absolute_uri("/").rstrip("/")
        if is_new_user:
            path = f"/invite/{uid}/{token}/"
        else:
            path = f"/reset/{uid}/{token}/"

        return f"{base}{path}"

    # ------------------------------------------------------------------ #
    # 1) Kombinierter Invite-Endpoint                                   #
    # ------------------------------------------------------------------ #
    @action(
        detail=False,
        methods=["post"],
        url_path="invite",
        permission_classes=[AllowAny],  # anonym + eingeloggt
    )
    def invite(self, request):
        """
        1) Self-Signup (anonym):
           - ACCESS_CODE_REGISTRATION_ENABLED = True
           - access_code Pflicht & Validierung
        2) Admin-Invite (eingeloggt):
           - nur Rollen in INVITE_ADMIN_ROLES oder Superuser
           - kein access_code nötig
        """
        serializer = self._get_invite_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = getattr(request, "user", None)
        is_authenticated = bool(user and user.is_authenticated)

        if is_authenticated:
            # --- Admin-Invite ---
            if not has_invite_admin_rights(user):
                return Response(
                    {"code": "Auth.INVITE_PERMISSION_DENIED"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            # --- Self-Signup ---
            if not getattr(settings, "ACCESS_CODE_REGISTRATION_ENABLED", False):
                return Response(
                    {"code": "Auth.SELF_SIGNUP_DISABLED"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            code = request.data.get("access_code")
            validate_access_code_or_error(
                code,
                consume=getattr(settings, "ACCESS_CODE_SINGLE_USE", False),
            )

        # ab hier: User erstellen / holen + Mail senden
        user_obj, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email},
        )

        self._mark_invited_profile(user_obj, created=created)
        url = self._build_frontend_url(request, user_obj, is_new_user=True)

        send_invite_or_reset_email(
            user=user_obj,
            url=url,
            is_new_user=True,
        )

        return Response(
        {
            "code": "Auth.INVITE_SENT",
            "email": email,
        },
        status=status.HTTP_201_CREATED,
    )

    # ------------------------------------------------------------------ #
    # 2) Passwort-vergessen-Flow                                        #
    # ------------------------------------------------------------------ #
    @action(
        detail=False,
        methods=["post"],
        url_path="reset-request",
        permission_classes=[AllowAny],
        authentication_classes=[],
    )
    def reset_request(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"code": "Auth.EMAIL_REQUIRED"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # kein User-Leak, immer dieselbe Antwort
            return Response(
                {"code": "Auth.RESET_REQUEST_ACCEPTED"},
                status=status.HTTP_200_OK,
            )

        url = self._build_frontend_url(request, user, is_new_user=False)
        send_invite_or_reset_email(user=user, url=url, is_new_user=False)

        return Response(
            {"code": "Auth.RESET_REQUEST_ACCEPTED"},
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------ #
    # 3) Invite-Link für Admins                                         #
    # ------------------------------------------------------------------ #
    @action(
        detail=True,
        methods=["get"],
        url_path="invite-link",
        permission_classes=[IsAuthenticated, IsInviteAdminOrSuperuser],
    )
    def invite_link(self, request, pk=None):
        """
        Nur für Invite-Admins / Superuser.
        """
        user = self.get_object()
        url = self._build_frontend_url(request, user, is_new_user=True)
        return Response({"invite_link": url}, status=status.HTTP_200_OK)
