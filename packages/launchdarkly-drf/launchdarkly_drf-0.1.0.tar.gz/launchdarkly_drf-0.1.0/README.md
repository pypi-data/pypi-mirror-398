# Django LaunchDarkly Flags

A Django + DRF integration for [LaunchDarkly](https://launchdarkly.com/) feature flags with built-in REST API support.

## Installation

```bash
pip install launchdarkly-drf
```

## Quick Start

### 1. Add to `INSTALLED_APPS`

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'launchdarkly_drf',
]

# Configure your LaunchDarkly SDK key
LAUNCHDARKLY_SDK_KEY = 'your-sdk-key-here'

# Optional: disable LaunchDarkly in tests
LAUNCHDARKLY_OFFLINE = False  # Set to True in test settings
```

### 2. Use Feature Flags in Your Code

```python
from launchdarkly_drf import has_feature, get_flag_value

def my_view(request):
    # Boolean flags
    if has_feature('new-ui-enabled', request=request):
        return render_new_ui(request)

    # String/number/JSON flags
    theme = get_flag_value('ui-theme', request=request)
    max_items = get_flag_value('max-items-per-page', request=request)
    config = get_flag_value('feature-config', request=request)
```

### 3. (Optional) Add REST API Endpoint

Expose flags to your frontend:

```python
# urls.py
from rest_framework.routers import DefaultRouter
from launchdarkly_drf import FeatureFlagViewSet

router = DefaultRouter()
router.register(r'feature-flags', FeatureFlagViewSet, basename='feature-flags')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

Now you can GET `/api/feature-flags/` to retrieve all flags as JSON.

## Usage Guide

### Boolean Feature Flags

Use `has_feature()` for simple on/off toggles:

```python
from launchdarkly_drf import has_feature

# With request (automatically extracts user context)
if has_feature('beta-features', request=request):
    enable_beta_features()

# With custom context
if has_feature('beta-features', context={'key': 'user@example.com', 'custom': 'value'}):
    enable_beta_features()

# Anonymous context (no targeting)
if has_feature('public-feature'):
    show_public_feature()
```

### Multi-Variant Flags

Use `get_flag_value()` for string, number, or JSON flags:

```python
from launchdarkly_drf import get_flag_value

# String flags (e.g., A/B test variants)
variant = get_flag_value('ui-variant', request=request)
if variant == 'blue':
    render_blue_theme()
elif variant == 'green':
    render_green_theme()

# Number flags
max_retries = get_flag_value('max-retries', request=request)

# JSON flags
config = get_flag_value('feature-config', request=request)
timeout = config.get('timeout', 30)
```

### Get All Flags

Retrieve all flags at once (useful for frontend):

```python
from launchdarkly_drf import get_all_flag_values

flags = get_all_flag_values(request)
# Returns: {'flag-1': True, 'flag-2': 'variant-a', 'flag-3': 42, ...}
```

## Testing

Use the `patch_feature_flag` decorator to mock flags in tests:

```python
from launchdarkly_drf.testing import patch_feature_flag
from launchdarkly_drf import has_feature, get_flag_value

@patch_feature_flag('new-ui-enabled', True)
@patch_feature_flag('ui-theme', 'dark')
def test_my_feature():
    assert has_feature('new-ui-enabled') is True
    assert get_flag_value('ui-theme') == 'dark'
```

You can stack multiple decorators to patch multiple flags.

## Advanced Configuration

### Custom User Context

By default, the package extracts the user's email from `request.user.email`. You can provide custom context:

```python
from launchdarkly_drf import has_feature

# Custom targeting
context = {
    'key': 'user-123',
    'email': 'user@example.com',
    'custom': {
        'plan': 'enterprise',
        'region': 'us-west',
    }
}

if has_feature('enterprise-feature', context=context):
    show_enterprise_features()
```

## How It Works

1. **Initialization**: The LaunchDarkly client is initialized when Django starts (in `AppConfig.ready()`)
2. **Singleton Pattern**: A singleton LaunchDarkly client instance is shared across your app
3. **User Context**: User information is automatically extracted from drf requests for flag targeting
4. **Offline Mode**: Set `LAUNCHDARKLY_OFFLINE=True` in test settings to disable LaunchDarkly connections

## Support

- [LaunchDarkly Documentation](https://docs.launchdarkly.com/)
- [GitHub Issues](https://github.com/Fullchee/launchdarkly-drf/issues)
