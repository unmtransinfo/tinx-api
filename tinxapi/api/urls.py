import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url, include

router = DefaultRouter()
router.register(r'diseases', views.DiseaseViewSet, base_name='disease')
router.register(r'targets', views.TargetViewSet, base_name='target')
router.register(r'articles', views.ArticleViewSet, base_name='article')

# TODO: Can we use ViewSet actions to clean up these urlpatterns?
urlpatterns = \
  [
    # GET /targets/:target_id/diseases
    url(r'^targets/(?P<target_id>[0-9]+)/diseases/$',
        views.TargetDiseasesViewSet.as_view({'get' : 'list'}),
        name='target-diseases'),

    # GET /targets/:target_id/diseases/:disease_id
    url(r'^targets/(?P<target_id>[0-9]+)/diseases/(?P<pk>[0-9]+)/$',
        views.TargetDiseasesViewSet.as_view({'get' : 'retrieve'}),
        name='target-diseases'),

    # GET /diseases/:disease_id/targets
    url(r'^diseases/(?P<disease_id>[0-9]+)/targets/$',
        views.DiseaseTargetsViewSet.as_view({'get' : 'list'}),
        name='disease-targets'),

    # GET /diseases/:disease_id/targets/:target_id
    url(r'^diseases/(?P<disease_id>[0-9]+)/targets/(?P<pk>[0-9]+)$',
        views.DiseaseTargetsViewSet.as_view({'get' : 'retrieve'}),
        name='disease-targets'),

    url(r'^diseases/(?P<disease_id>[0-9]+)/targets/(?P<target_id>[0-9]+)/articles$',
        views.ArticleViewSet.as_view({'get' : 'list'}),
        name='disease-target-articles'),

    url(r'^targets/(?P<target_id>[0-9]+)/diseases/(?P<disease_id>[0-9]+)/articles$',
        views.ArticleViewSet.as_view({'get' : 'list'}),
        name='target-disease-articles'),

  ] + router.urls
