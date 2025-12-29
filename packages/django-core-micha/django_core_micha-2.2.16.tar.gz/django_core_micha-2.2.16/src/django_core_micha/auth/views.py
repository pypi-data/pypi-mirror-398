# src/django_core_micha/auth/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed

from allauth.mfa.models import Authenticator

from django_core_micha.invitations.mixins import InviteActionsMixin
from django_core_micha.auth.roles import RolePolicy
from django_core_micha.auth import services  # <--- Central Logic Import
from .recovery import RecoveryRequest
from .serializers import RecoveryRequestSerializer
from .permissions import IsSupportAgent, IsAssignedSupportOrAdmin

User = get_user_model()

# --- Standard Views ---

def recovery_complete_view(request, token: str):
    """
    Entry point from the email link. Redirects to frontend.
    """
    target_base = f"{settings.PUBLIC_ORIGIN}/login"
    try:
        rr = RecoveryRequest.objects.select_related("user").get(token=token)
    except RecoveryRequest.DoesNotExist:
        return redirect(f"{target_base}?recovery=invalid")

    if not rr.is_active():
        return redirect(f"{target_base}?recovery=expired")

    email = rr.user.email or ""
    return redirect(f"{target_base}?recovery={rr.token}&email={email}")


@ensure_csrf_cookie
def csrf_token_view(request):
    """
    Hilfs-View für SPAs. Erzwingt das Setzen des CSRF-Cookies,
    damit das Frontend den Token auslesen und im Header mitsenden kann.
    """
    return JsonResponse({"detail": "CSRF cookie set"})

# --- API ViewSets ---

class BaseUserViewSet(InviteActionsMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = None 
    permission_classes = [IsAuthenticated]
    role_policy_class = RolePolicy

    def get_role_policy(self):
        return self.role_policy_class()

    @action(detail=False, methods=["get", "patch"], url_path="current")
    def current(self, request):
        user = request.user
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="update-role")
    def update_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get("role")
        policy = self.get_role_policy()

        if not policy.is_valid_code(new_role):
            return Response({"detail": "Invalid role."}, status=400)

        if not policy.can_change_role(request.user, user, new_role):
            return Response({"detail": "Permission denied."}, status=403)

        user.profile.role = new_role
        user.profile.save()
        return Response({"detail": "Role updated successfully."})
    
    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="mfa/support-help")
    def mfa_support_help(self, request):
        identifier = request.data.get("email") or request.data.get("identifier")
        message = request.data.get("message", "")

        if not identifier:
            return Response({"code": "Auth.MFA_IDENTIFIER_REQUIRED"}, status=400)

        # Logic moved to service? Or keep simple DB create here if trivial.
        # Keeping it here is acceptable as it's just a "create", but strictly:
        try:
            user = User.objects.get(email__iexact=identifier)
            RecoveryRequest.objects.create(user=user, message=message)
        except User.DoesNotExist:
            pass # Silent fail

        return Response({"code": "Auth.MFA_HELP_REQUESTED"}, status=200)


class PasskeyViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        qs = Authenticator.objects.filter(user=request.user, type=Authenticator.Type.WEBAUTHN)
        data = []
        for a in qs:
            wrapped = a.wrap()
            data.append({
                "id": a.pk,
                "name": getattr(wrapped, "name", None),
                "created_at": a.created_at,
                "last_used_at": a.last_used_at,
                "is_device_passkey": getattr(wrapped, "is_device_passkey", None),
            })
        return Response(data)

    def destroy(self, request, pk=None):
        obj = get_object_or_404(Authenticator, pk=pk, user=request.user, type=Authenticator.Type.WEBAUTHN)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecoveryRequestViewSet(viewsets.ModelViewSet):
    queryset = RecoveryRequest.objects.all().select_related("user", "resolved_by")
    serializer_class = RecoveryRequestSerializer

    def get_permissions(self):
        if self.action == "recovery_login":
            return [AllowAny()]
        if self.action == "create_from_mfa":
            return [IsAuthenticated()]
        if self.action in ("list", "retrieve"):
            return [IsSupportAgent()]
        if self.action in ("approve", "reject"):
            return [IsAssignedSupportOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(methods=["post"], detail=True)
    def approve(self, request, pk=None):
        rr = self.get_object()
        # Permission check via get_permissions handles the class check, 
        # but specific object permission is checked by DRF automatically in many cases.
        # However, since we use custom logic in permissions.py, calling it explicitly is safer if not using standard DRF flow.
        self.check_object_permissions(request, rr)

        support_note = request.data.get("support_note", "")
        
        # Call Service
        recovery_url = services.approve_recovery_request(request, rr, support_note)

        serializer = self.get_serializer(rr)
        data = serializer.data
        data["recovery_link"] = recovery_url
        return Response(data)

    @action(methods=["post"], detail=True)
    def reject(self, request, pk=None):
        rr = self.get_object()
        self.check_object_permissions(request, rr)

        support_note = request.data.get("support_note", "")
        
        # Call Service
        services.reject_recovery_request(request, rr, support_note)
        
        serializer = self.get_serializer(rr)
        return Response(serializer.data)

    @action(methods=["post"], detail=False, permission_classes=[AllowAny], url_path=r"recovery-login/(?P<token>[^/.]+)")
    def recovery_login(self, request, token=None):
        identifier = request.data.get("email") or request.data.get("identifier")
        password = request.data.get("password")

        if not identifier or not password:
            return Response({"code": "Auth.CREDENTIALS_REQUIRED"}, status=400)

        try:
            # Call Service
            services.perform_recovery_login(request, identifier, password, token)
        except AuthenticationFailed as e:
            # Use the code from the service exception
            return Response({"code": e.detail.code}, status=400)

        return Response({"status": 200, "code": "Auth.RECOVERY_LOGIN_OK"}, status=200)