from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, CommunityRequestViewSet, DocumentViewSet, MessageViewSet, PostViewSet, ProfileViewSet, ResidenceCertificateViewSet, assistant, contacts, dashboard, me, register_neighbor, verify_residence_certificate

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("activities", ActivityViewSet, basename="activity")
router.register("documents", DocumentViewSet, basename="document")
router.register("profiles", ProfileViewSet, basename="profile")
router.register("messages", MessageViewSet, basename="message")
router.register("requests", CommunityRequestViewSet, basename="request")
router.register("residence-certificates", ResidenceCertificateViewSet, basename="residence-certificate")
urlpatterns = [
    path("", include(router.urls)),
    path("certificates/verify/<uuid:code>/", verify_residence_certificate),
    path("me/", me),
    path("contacts/", contacts),
    path("dashboard/", dashboard),
    path("assistant/", assistant),
    path("neighbors/register/", register_neighbor),
]
