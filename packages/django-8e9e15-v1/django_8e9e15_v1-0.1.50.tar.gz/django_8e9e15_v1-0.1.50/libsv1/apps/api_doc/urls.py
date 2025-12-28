from django.urls import path
from .views import erd_view, graph_models_view, ApiSchemaGenerator, DashboardApiSchemaGenerator
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.contrib.auth.decorators import login_required
from django.conf import settings

base_scheme_name = getattr(settings, 'SECURITY_SCHEME_NAME', 'Bearer')
dashboard_scheme_name = f"{base_scheme_name}_dashboard"
DASHBOARD_SPECTACULAR_SETTINGS = {
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            dashboard_scheme_name: {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'Token',
            }
        }
    },
    'SECURITY': [
        {dashboard_scheme_name: []}
    ],
}

urlpatterns = [
    path('doc/api/schema', login_required(SpectacularAPIView.as_view(
        generator_class=ApiSchemaGenerator,
    )), name='api_schema'),
    path('doc/api/redoc', login_required(SpectacularRedocView.as_view(
        url_name='api_schema',
        title=f"{settings.PROJECT_NAME} API"
    )), name='doc/api/redoc'),
    path('doc/api/swagger', login_required(SpectacularSwaggerView.as_view(
        url_name='api_schema',
        title=f"{settings.PROJECT_NAME} API"
    )), name='doc/api/swagger'),

    path('doc/dashboard/api/schema', login_required(SpectacularAPIView.as_view(
        generator_class=DashboardApiSchemaGenerator,
        custom_settings=DASHBOARD_SPECTACULAR_SETTINGS,
    )), name='dashboard_api_schema'),
    path('doc/dashboard/api/redoc', login_required(SpectacularRedocView.as_view(
        url_name='dashboard_api_schema',
        title=f"{settings.PROJECT_NAME} Dashboard API"
    )), name='doc/dashboard/api/redoc'),
    path('doc/dashboard/api/swagger', login_required(SpectacularSwaggerView.as_view(
        url_name='dashboard_api_schema',
        title=f"{settings.PROJECT_NAME} Dashboard API"
    )), name='doc/dashboard/api/swagger'),

    path('doc/erd.<ext>', erd_view, name='doc/erd'),
    path('doc/models.<ext>', graph_models_view, name='doc/models'),
]


