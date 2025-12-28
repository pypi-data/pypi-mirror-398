from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from launchdarkly_drf.provider import get_all_flag_values


class FeatureFlagViewSet(viewsets.ViewSet):
    """
    REST API ViewSet for retrieving feature flags.

    Returns the current status of all feature flags for the requesting user.

    Example:
        Add to your urls.py:
        ```python
        from rest_framework.routers import DefaultRouter
        from launchdarkly_drf import FeatureFlagViewSet

        router = DefaultRouter()
        router.register(r'feature-flags', FeatureFlagViewSet, basename='feature-flags')

        urlpatterns = [
            path('api/', include(router.urls)),
        ]
        ```

        Then you can GET /api/feature-flags/ to retrieve all flags.

    Note:
        By default, this endpoint allows any user (AllowAny). You may want to
        customize the permission_classes for your use case.
    """

    permission_classes = (AllowAny,)

    def list(self, request: Request):
        """
        List all feature flags and their values for the current user/context.

        Returns:
            JsonResponse with flag key-value pairs and 200 status on success,
            or 404 if flags cannot be retrieved.
        """
        data = get_all_flag_values(request)
        if data or data == {}:
            return JsonResponse(data=data, status=status.HTTP_200_OK)
        else:
            return JsonResponse(data=None, status=status.HTTP_404_NOT_FOUND)
