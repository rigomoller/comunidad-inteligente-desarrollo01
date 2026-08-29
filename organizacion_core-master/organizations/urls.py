from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BoardMemberViewSet,
    BoardRoleViewSet,
    CommuneViewSet,
    OrganizationViewSet,
    ProvinceViewSet,
    RegionViewSet,
    my_organization,
)

router = DefaultRouter()
router.register("geography/regions", RegionViewSet)
router.register("geography/provinces", ProvinceViewSet)
router.register("geography/communes", CommuneViewSet)
router.register("institution/organizations", OrganizationViewSet)
router.register("institution/board-roles", BoardRoleViewSet)
router.register("institution/board-members", BoardMemberViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("institucion/mi-jdv-info/", my_organization),
]
