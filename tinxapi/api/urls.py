from views import DiseaseViewSet, TargetViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'diseases', DiseaseViewSet, base_name='disease')
router.register(r'targets', TargetViewSet, base_name='target')
urlpatterns = router.urls
