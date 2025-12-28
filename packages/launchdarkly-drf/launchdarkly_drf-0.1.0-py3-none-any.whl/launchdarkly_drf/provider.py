import logging
import warnings
from typing import Optional, Union, overload

from ldclient import Context, LDClient
from ldclient.config import Config
from rest_framework.request import Request

logger = logging.getLogger(__name__)

__all__ = [
    "FlagValue",
    "get_all_flag_values",
    "get_flag_value",
    "init_launch_darkly",
    "has_feature",
]

FlagValue = Union[bool, str, int, float, list, dict, None]

_ld_client: Optional[LDClient] = None
"""https://launchdarkly.com/docs/sdk/concepts/getting-started#implement-sdks-in-a-singleton-pattern"""


def init_launch_darkly(*, sdk_key: str, offline: bool = False) -> LDClient:
    """
    Initialize the LaunchDarkly client.

    This should typically be called in your Django app's AppConfig.ready() method.

    Args:
        sdk_key: Your LaunchDarkly SDK key
        offline: If True, the client will not connect to LaunchDarkly (useful for testing)

    Example:
        ```python
        from django.apps import AppConfig
        from django.conf import settings
        from launchdarkly_drf import init_launch_darkly

        class MyAppConfig(AppConfig):
            name = "myapp"

            def ready(self):
                init_launch_darkly(
                    sdk_key=settings.LAUNCHDARKLY_SDK_KEY,
                    offline=settings.IN_TESTING,
                )
        ```

    Note:
        DEV-4213: previously wasn't thread-safe and was crashing app
        DEV-4312: initializes LD in AppConfig.ready(), don't need threading lock anymore, keeping for safety
    """
    global _ld_client

    if _ld_client:
        return _ld_client

    try:
        _ld_client = LDClient(config=Config(sdk_key=sdk_key, offline=offline))
        return _ld_client
    except Exception:
        logger.exception("Failed to initialize LaunchDarkly client")


def get_all_flag_values(request: Request) -> dict[str, FlagValue]:
    """
    Get all feature flag values for a given request context.

    Args:
        request: Django REST framework request object. User info is extracted
                to create a LaunchDarkly context.

    Returns:
        Dictionary mapping flag keys to their values.

    Example:
        ```python
        from launchdarkly_drf import get_all_flag_values

        def my_view(request):
            flags = get_all_flag_values(request)
            # flags = {"feature-1": True, "feature-2": "variant-a", ...}
        ```
    """
    return (
        _get_ld_client()
        .all_flags_state(_build_ld_context(request=request))
        .to_json_dict()
    )


@overload
def has_feature(key: str, *, request: Request, context: None = None) -> bool: ...


@overload
def has_feature(key: str, *, request: None = None, context: dict) -> bool: ...


@overload
def has_feature(key: str) -> bool: ...


def has_feature(
    key: str,
    *,
    request: Optional[Request] = None,
    context: Optional[dict] = None,
) -> bool:
    """
    Check if a boolean feature flag is enabled.

    For non-boolean flags, use `get_flag_value()` instead.

    Args:
        key: Flag key in LaunchDarkly.
        request: Django REST framework request object. User info is extracted
                to create a LaunchDarkly context. Cannot be used together with context.
        context: Custom LaunchDarkly context dictionary for user targeting.
                Cannot be used together with request.
                https://launchdarkly.com/docs/home/flags/contexts

    Returns:
        Boolean value of the flag, or False if the flag doesn't exist or is None.

    Warns:
        UserWarning: If the flag returns a non-boolean value.

    Examples:
        ```python
        from launchdarkly_drf import has_feature

        # With request
        if has_feature("new-ui", request=request):
            return render_new_ui()

        # With custom context
        if has_feature("beta-feature", context={"key": "user@example.com"}):
            enable_beta_features()

        # Anonymous context (no request or context)
        if has_feature("public-feature"):
            show_public_feature()
        ```
    """
    value = _get_ld_client().variation(
        key, _build_ld_context(request=request, context=context), None
    )

    # allow None as default bool flag value
    if not isinstance(value, bool) and value is not None:
        warnings.warn(
            f"Feature flag '{key}' returned non-boolean value. Use get_flag_value() for non-boolean flags.",
            stacklevel=2,
        )
    return bool(value)


@overload
def get_flag_value(
    key: str, *, request: Request, context: None = None
) -> FlagValue: ...


@overload
def get_flag_value(key: str, *, request: None = None, context: dict) -> FlagValue: ...


@overload
def get_flag_value(key: str) -> FlagValue: ...


def get_flag_value(
    key: str,
    *,
    request: Optional[Request] = None,
    context: Optional[dict] = None,
) -> FlagValue:
    """
    Get the value of any feature flag (boolean, string, number, JSON, etc.).

    Args:
        key: Flag key in LaunchDarkly.
        request: Django REST framework request object. User info is extracted
                to create a LaunchDarkly context. Cannot be used together with context.
        context: Custom LaunchDarkly context dictionary for user targeting.
                Cannot be used together with request.

    Returns:
        The flag value, which can be bool, str, int, float, list, dict, or None.

    Examples:
        ```python
        from launchdarkly_drf import get_flag_value

        # String flag
        variant = get_flag_value("ui-variant", request=request)
        # variant = "blue" or "green" etc.

        # Number flag
        max_items = get_flag_value("max-items", request=request)
        # max_items = 10

        # JSON flag
        config = get_flag_value("feature-config", request=request)
        # config = {"timeout": 30, "retries": 3}
        ```
    """
    return _get_ld_client().variation(
        key, _build_ld_context(request=request, context=context), None
    )


def _get_ld_client() -> LDClient:
    """
    Returns:
        The initialized LaunchDarkly client.

    Raises:
        RuntimeError: If the LaunchDarkly client hasn't been initialized.

    Note:
        For type hints: guarantees it returns LDClient and not None.
    """
    if _ld_client is None:
        raise RuntimeError(
            "LaunchDarkly client not initialized. Call init_launch_darkly() "
            "in your AppConfig.ready() method before using feature flags."
        )
    return _ld_client


def _build_ld_context(
    *,
    request: Optional[Request] = None,
    context: Optional[dict] = None,
) -> Context:
    """
    Build a LaunchDarkly context from a request or custom context dictionary.

    If both request and context are provided, request takes precedence.
    If both request and context are None, creates an anonymous context.

    Args:
        request: To extract user info from.
        context: Used to target users.
    """
    if request is not None and context is not None:
        warnings.warn(
            "Both request and context provided to _build_ld_context; request will take precedence.",
            stacklevel=2,
        )
    if request is not None:
        context = _extract_user_info(request)
    return _build_with_defaults(context)


def _build_with_defaults(context: Optional[dict] = None) -> Context:
    """Build a LaunchDarkly context with required defaults."""
    ld_context = {
        "kind": "user",  # required in LD SDK 9+
        **(context or {}),
    }
    if not context or not context.get("key"):
        if context:
            warnings.warn(
                "Provided context is missing 'key': using 'anonymous' as key.",
                stacklevel=2,
            )
        ld_context["key"] = "anonymous"
        ld_context["anonymous"] = True
    return Context.from_dict(ld_context)


def _extract_user_info(request: Request) -> dict:
    """
    Extract user information from a Django request.

    Args:
        request: The request object to extract user info from.

    Returns:
        Dictionary containing user context information (email as key if available).
    """
    context = {}
    user = getattr(request, "user", None)
    if user and getattr(user, "email", None):
        context["key"] = user.email
    return context
