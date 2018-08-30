from views import DiseaseViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'diseases', DiseaseViewSet, base_name='disease')
urlpatterns = router.urls
