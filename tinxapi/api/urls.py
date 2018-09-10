import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url, include

router = DefaultRouter()
router.register(r'diseases', views.DiseaseViewSet, base_name='disease')
router.register(r'targets', views.TargetViewSet, base_name='target')

urlpatterns = \
  [
    url(r'^targets/(?P<pk>[0-9]+)/diseases/$',
        views.TargetDiseasesView.as_view(),
        name='target-diseases'),
    url(r'^diseases/(?P<pk>[0-9]+)/targets/$',
        views.DiseaseTargetsView.as_view(),
        name='disease-targets'),
      url(r'^diseases/(?P<parent_id>[0-9]+)/children/$',
          views.DiseaseViewSet.as_view({'get' : 'list'}),
          name='disease-children')
  ] + router.urls
