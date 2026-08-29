from datetime import date
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Activity, CommunityDocument, CommunityRequest, Neighborhood, Post, PrivateMessage, Profile
from .permissions import IsBoardMember
from .serializers import ActivitySerializer, CommunityRequestSerializer, ContactSerializer, DocumentSerializer, MessageSerializer, NeighborhoodSerializer, PostSerializer, ProfileSerializer, UserSerializer
from .services import answer_community_question


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        if hasattr(user, "profile"):
            token["role"] = user.profile.role
            token["neighborhood_id"] = user.profile.neighborhood_id
        return token


class RoleTokenObtainPairView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer

class ScopedViewSet(viewsets.ModelViewSet):
    def get_neighborhood(self): return self.request.user.profile.neighborhood
    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsBoardMember()]
        return [IsAuthenticated()]

class PostViewSet(ScopedViewSet):
    serializer_class = PostSerializer
    def get_queryset(self): return Post.objects.filter(neighborhood=self.get_neighborhood()).order_by("-created_at")
    def perform_create(self, serializer): serializer.save(author=self.request.user, neighborhood=self.get_neighborhood())

class ActivityViewSet(ScopedViewSet):
    serializer_class = ActivitySerializer
    def get_queryset(self): return Activity.objects.filter(neighborhood=self.get_neighborhood()).order_by("starts_at")
    def perform_create(self, serializer): serializer.save(neighborhood=self.get_neighborhood())

class DocumentViewSet(ScopedViewSet):
    serializer_class = DocumentSerializer
    def get_queryset(self): return CommunityDocument.objects.filter(neighborhood=self.get_neighborhood()).order_by("-created_at")
    def perform_create(self, serializer): serializer.save(neighborhood=self.get_neighborhood())

class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsBoardMember]
    def get_queryset(self): return Profile.objects.filter(neighborhood=self.request.user.profile.neighborhood).select_related("user").order_by("user__first_name")


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        neighborhood = self.request.user.profile.neighborhood
        return PrivateMessage.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user),
            sender__profile__neighborhood=neighborhood,
            recipient__profile__neighborhood=neighborhood,
        ).select_related("sender", "recipient")

    def perform_create(self, serializer):
        recipient = serializer.validated_data["recipient"]
        if recipient.profile.neighborhood_id != self.request.user.profile.neighborhood_id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Solo puedes escribir a personas de tu junta de vecinos.")
        serializer.save(sender=self.request.user)

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Los mensajes enviados no pueden modificarse."}, status=405)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Los mensajes enviados no pueden eliminarse."}, status=405)


class CommunityRequestViewSet(viewsets.ModelViewSet):
    serializer_class = CommunityRequestSerializer

    def get_queryset(self):
        neighborhood = self.request.user.profile.neighborhood
        queryset = CommunityRequest.objects.filter(neighborhood=neighborhood).select_related("requester")
        if self.request.user.profile.role == "neighbor":
            queryset = queryset.filter(requester=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            requester=self.request.user,
            neighborhood=self.request.user.profile.neighborhood,
            status="received",
        )

    def get_permissions(self):
        if self.action in {"update", "partial_update", "destroy"}:
            return [IsBoardMember()]
        return [IsAuthenticated()]

@api_view(["GET"])
def me(request): return Response(UserSerializer(request.user).data)


@api_view(["GET"])
def contacts(request):
    profiles = Profile.objects.filter(
        neighborhood=request.user.profile.neighborhood
    ).select_related("user").order_by("user__first_name")
    return Response(ContactSerializer(profiles, many=True).data)

@api_view(["GET"])
def dashboard(request):
    n = request.user.profile.neighborhood
    profiles = n.profiles.exclude(birth_year__isnull=True)
    year = date.today().year
    ages = [year - p.birth_year for p in profiles]
    return Response({
        "neighbors": n.profiles.count(), "posts": n.posts.count(), "activities": n.activities.count(),
        "documents": n.documents.count(), "average_age": round(sum(ages) / len(ages), 1) if ages else 0,
        "older_adults": sum(1 for age in ages if age >= 60),
        "age_groups": {"children": sum(1 for age in ages if age < 18), "adults": sum(1 for age in ages if 18 <= age < 60), "older": sum(1 for age in ages if age >= 60)},
    })

@api_view(["POST"])
def assistant(request):
    n = request.user.profile.neighborhood
    return Response({"answer": answer_community_question(request.data.get("question", ""), n)})

@api_view(["POST"])
@permission_classes([IsBoardMember])
def register_neighbor(request):
    required = ["username", "password", "first_name"]
    if any(not request.data.get(field) for field in required):
        return Response({"detail": "Usuario, contraseña y nombre son obligatorios."}, status=400)
    if User.objects.filter(username=request.data["username"]).exists():
        return Response({"detail": "El nombre de usuario ya existe."}, status=400)
    with transaction.atomic():
        user = User.objects.create_user(
            username=request.data["username"], password=request.data["password"],
            first_name=request.data["first_name"], last_name=request.data.get("last_name", ""), email=request.data.get("email", ""),
        )
        Profile.objects.create(user=user, neighborhood=request.user.profile.neighborhood, role="neighbor", birth_year=request.data.get("birth_year") or None, household_size=request.data.get("household_size") or 1)
    return Response(UserSerializer(user).data, status=201)
