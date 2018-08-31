import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url, include

router = DefaultRouter()
router.register(r'diseases', views.DiseaseViewSet, base_name='disease')
router.register(r'targets', views.TargetViewSet, base_name='target')

urlpatterns = [
  url(r'^targets/(?P<pk>[0-9])/diseases/$',
      views.TargetDiseasesView.as_view(),
      name='target-diseases')
  ] + router.urls
