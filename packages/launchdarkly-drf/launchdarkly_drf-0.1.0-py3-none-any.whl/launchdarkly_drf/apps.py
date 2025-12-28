from django.apps import AppConfig


class DjangoLaunchDarklyFlagsConfig(AppConfig):
    """
    Django app configuration for launchdarkly-drf.

    To use this package, add it to your INSTALLED_APPS and configure the SDK key.

    Example settings.py:
        ```python
        INSTALLED_APPS = [
            ...
            'launchdarkly_drf',
        ]

        LAUNCHDARKLY_SDK_KEY = 'your-sdk-key-here'
        # Optional: set to True to disable LaunchDarkly in tests
        LAUNCHDARKLY_OFFLINE = False
        ```

    The app will automatically initialize the LaunchDarkly client when Django starts,
    or you can manually initialize it in your own AppConfig.ready() method using:

        ```python
        from launchdarkly_drf import init_launch_darkly

        init_launch_darkly(
            sdk_key=settings.LAUNCHDARKLY_SDK_KEY,
            offline=settings.LAUNCHDARKLY_OFFLINE,
        )
        ```
    """

    name = "launchdarkly_drf"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Initialize LaunchDarkly client when Django starts."""
        from django.conf import settings

        from launchdarkly_drf.provider import init_launch_darkly

        sdk_key = getattr(settings, "LAUNCHDARKLY_SDK_KEY", None)
        offline = getattr(settings, "LAUNCHDARKLY_OFFLINE", False)

        if sdk_key:
            init_launch_darkly(sdk_key=sdk_key, offline=offline)
        elif not offline:
            import warnings

            warnings.warn(
                "LAUNCHDARKLY_SDK_KEY not found in settings. "
                "LaunchDarkly client will not be initialized. "
                "Set settings.LAUNCHDARKLY_SDK_KEY or call init_launch_darkly() manually.",
                stacklevel=2,
            )
