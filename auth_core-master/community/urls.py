from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, CommunityRequestViewSet, DocumentViewSet, MessageViewSet, PostViewSet, ProfileViewSet, assistant, contacts, dashboard, me, register_neighbor

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")
router.register("activities", ActivityViewSet, basename="activity")
router.register("documents", DocumentViewSet, basename="document")
router.register("profiles", ProfileViewSet, basename="profile")
router.register("messages", MessageViewSet, basename="message")
router.register("requests", CommunityRequestViewSet, basename="request")
urlpatterns = [path("", include(router.urls)), path("me/", me), path("contacts/", contacts), path("dashboard/", dashboard), path("assistant/", assistant), path("neighbors/register/", register_neighbor)]
