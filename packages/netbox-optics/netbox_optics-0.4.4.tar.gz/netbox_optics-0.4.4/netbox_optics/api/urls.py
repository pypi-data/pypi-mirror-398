from rest_framework import routers

from . import views

NetBoxRouter = routers.DefaultRouter


app_name = "netbox_optical"

router = NetBoxRouter()
router.register("optical-grid-types", views.OpticalGridTypeViewSet)
router.register("optical-grid-type-wavelengths", views.OpticalGridTypeWavelengthViewSet)
router.register("optical-grids", views.OpticalGridViewSet)
router.register("optical-grid-wavelengths", views.OpticalGridWavelengthViewSet)
router.register("optical-spans", views.OpticalSpanViewSet)
router.register("optical-connections", views.OpticalConnectionViewSet)
router.register("mux-wavelength-maps", views.MuxWavelengthMapViewSet)
urlpatterns = router.urls
