# src/django_core_micha/auth/security.py
import logging
from django.conf import settings
from allauth.mfa.models import Authenticator
from functools import wraps
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from django_core_micha.auth.roles import get_role_level_for_user, ROLE_LEVEL_3
from django_core_micha.auth.recovery import RecoveryRequest
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)


def get_security_level(request) -> str:
    """
    Returns the current security level for this request.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return "anon"
    return request.session.get("auth_level", settings.SECURITY_DEFAULT_LEVEL)


def set_security_level(request, level: str) -> None:
    """
    Stores the security level in the session if the user is authenticated.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return
    if level not in settings.SECURITY_LEVELS:
        logger.warning("Attempt to set invalid security level: %s", level)
        return
    request.session["auth_level"] = level


def is_level_sufficient(current: str, required: str) -> bool:
    """
    Compares two levels based on SECURITY_LEVELS order.
    """
    levels = list(settings.SECURITY_LEVELS)
    try:
        return levels.index(current) >= levels.index(required)
    except ValueError:
        return False


def require_security_level(required: str):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(*args, **kwargs):
            # DRF-Methoden: self, request, ...
            if len(args) >= 2 and hasattr(args[0], "request"):
                self = args[0]
                request = args[1]
                remaining = args[2:]
            else:
                self = None
                request = args[0]
                remaining = args[1:]

            current = get_security_level(request)
            sufficient = is_level_sufficient(current, required)
            enforce = getattr(settings, "SECURITY_ENFORCE_STRONG_AUTH", False)

            if not sufficient and enforce:
                if not request.user or not request.user.is_authenticated:
                    raise NotAuthenticated("Authentication required")
                raise PermissionDenied("Strong authentication required")

            if not sufficient and not enforce:
                logger.info(
                    "Security level too low for view %s: current=%s required=%s",
                    getattr(view_func, "__name__", str(view_func)),
                    current,
                    required,
                )

            if self is None:
                return view_func(request, *remaining, **kwargs)
            return view_func(self, request, *remaining, **kwargs)

        return _wrapped
    return decorator

def get_user_security_state(user, request=None) -> dict:
    """
    Beschreibt, wie 'sicher' die aktuelle Session im Vergleich zur Projektpolicy ist.
    """
    if not user or not user.is_authenticated:
        return {
            "required_level": "anon",
            "current_level": "anon",
            "has_totp": False,
            "has_webauthn": False,
            "has_recovery_codes": False,
            "requires_additional_security": False,
        }

    # 1. Policy-seitige Anforderung
    required_level = getattr(settings, "SECURITY_DEFAULT_LEVEL", "basic")

    # 2. Aktuelles Session-Level
    if request is not None:
        current_level = get_security_level(request)
    else:
        # Fallback, falls kein Request im Kontext
        current_level = "basic"

    # 3. Vorhandene MFA-Authenticators (nur Info)
    authenticators = Authenticator.objects.filter(user=user)
    has_totp = authenticators.filter(type=Authenticator.Type.TOTP).exists()
    has_webauthn = authenticators.filter(type=Authenticator.Type.WEBAUTHN).exists()
    has_recovery = authenticators.filter(type=Authenticator.Type.RECOVERY_CODES).exists()

    # 4. Mismatch zwischen Policy und Session?
    #    Wenn Policy 'strong' verlangt, Session aber noch nicht strong ist,
    #    dann soll das Frontend einen Hinweis zeigen / auf Security-Tab umleiten.
    requires_additional = (
        required_level == "strong"
        and not is_level_sufficient(current_level, "strong")
    )

    return {
        "required_level": required_level,
        "current_level": current_level,
        "has_totp": has_totp,
        "has_webauthn": has_webauthn,
        "has_recovery_codes": has_recovery,
        "requires_additional_security": requires_additional,
    }

def create_recovery_request_for_user(request, message: str = "") -> RecoveryRequest:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        raise ValueError("User must be authenticated to create a recovery request.")

    rr = RecoveryRequest.objects.create(
        user=user,
        message=message or "",
    )

    # Session auf 'recovery' setzen
    set_security_level(request, "recovery")

    return rr


