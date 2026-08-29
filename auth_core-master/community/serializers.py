from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Activity, CommunityDocument, CommunityRequest, Neighborhood, Post, PrivateMessage, Profile

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)
    neighborhood_id = serializers.IntegerField(source="profile.neighborhood_id", read_only=True)
    class Meta: model = User; fields = ["id", "username", "first_name", "last_name", "email", "role", "neighborhood_id"]

class NeighborhoodSerializer(serializers.ModelSerializer):
    class Meta: model = Neighborhood; fields = "__all__"

class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    class Meta: model = Post; fields = "__all__"; read_only_fields = ["author", "neighborhood"]

class ActivitySerializer(serializers.ModelSerializer):
    class Meta: model = Activity; fields = "__all__"; read_only_fields = ["neighborhood"]

class DocumentSerializer(serializers.ModelSerializer):
    class Meta: model = CommunityDocument; fields = "__all__"; read_only_fields = ["neighborhood"]

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    class Meta: model = Profile; fields = ["id", "user", "username", "first_name", "last_name", "email", "neighborhood", "role", "birth_year", "household_size"]


class ContactSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source="user_id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "user", "username", "first_name", "last_name", "role"]


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.get_full_name", read_only=True)
    recipient_name = serializers.CharField(source="recipient.get_full_name", read_only=True)

    class Meta:
        model = PrivateMessage
        fields = ["id", "sender", "sender_name", "recipient", "recipient_name", "body", "created_at", "read_at"]
        read_only_fields = ["sender", "created_at", "read_at"]


class CommunityRequestSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source="requester.get_full_name", read_only=True)
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CommunityRequest
        fields = "__all__"
        read_only_fields = ["neighborhood", "requester", "created_at"]
