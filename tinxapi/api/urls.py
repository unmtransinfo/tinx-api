from api import views
from django.urls import path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers


class ApiRootView(routers.APIRootView):
    """
    This is the root of the TIN-X REST API. Explore the API by following the
    links below.

    <p>
    For more detailed information, please consult the
    <b><a href="/docs">API Documentation</a></b>
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = ApiRootView


router = DocumentedRouter()

router.register(r"diseases", views.DiseaseViewSet, basename="disease")
router.register(r"targets", views.TargetViewSet, basename="target")
router.register(r"articles", views.ArticleViewSet, basename="article")
router.register(r"dto", views.DTOViewSet, basename="dto")

# TODO: Can we use ViewSet actions to clean up these urlpatterns?
urlpatterns = [
    path("docs/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="docs",
    ),
    # GET /targets/:target_id/diseases
    path(
        "targets/<int:target_id>/diseases/",
        views.TargetDiseasesViewSet.as_view({"get": "list"}),
        name="target-diseases",
    ),
    # GET /targets/:target_id/diseases/:doid
    path(
        "targets/<int:target_id>/diseases/<str:doid>/",
        views.TargetDiseasesViewSet.as_view({"get": "retrieve"}),
        name="target-diseases",
    ),
    # GET /diseases/:doid/targets
    path(
        "diseases/<str:doid>/targets/",
        views.DiseaseTargetsViewSet.as_view({"get": "list"}),
        name="disease-targets",
    ),
    # GET /diseases/:doid/targets/:target_id
    path(
        "diseases/<str:doid>/targets/<int:target_id>",
        views.DiseaseTargetsViewSet.as_view({"get": "retrieve"}),
        name="disease-targets",
    ),
    path(
        "diseases/<path:doid>/targets/<int:target_id>/articles",
        views.ArticleViewSet.as_view({"get": "list"}),
        name="disease-target-articles",
    ),
    path(
        "targets/<int:target_id>/diseases/<path:doid>/articles",
        views.ArticleViewSet.as_view({"get": "list"}),
        name="target-disease-articles",
    ),
    re_path(r"^search/", views.Search.as_view(), name="search-api"),
] + router.urls
