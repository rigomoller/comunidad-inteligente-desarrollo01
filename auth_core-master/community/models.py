from django.contrib.auth.models import User
from django.db import models

class Neighborhood(models.Model):
    name = models.CharField(max_length=160)
    commune = models.CharField(max_length=120)
    address = models.CharField(max_length=200, blank=True)
    def __str__(self): return self.name

class Profile(models.Model):
    ROLES = [("neighbor", "Vecino"), ("board", "Directiva"), ("admin", "Administrador")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.SET_NULL, null=True, related_name="profiles")
    role = models.CharField(max_length=20, choices=ROLES, default="neighbor")
    birth_year = models.PositiveIntegerField(null=True, blank=True)
    household_size = models.PositiveIntegerField(default=1)

class Post(models.Model):
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    title = models.CharField(max_length=180)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)

class Activity(models.Model):
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.CASCADE, related_name="activities")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    location = models.CharField(max_length=180)

class CommunityDocument(models.Model):
    neighborhood = models.ForeignKey(Neighborhood, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=180)
    category = models.CharField(max_length=80, default="General")
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class PrivateMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class CommunityRequest(models.Model):
    CATEGORIES = [
        ("certificate", "Certificado"),
        ("security", "Seguridad"),
        ("social", "Apoyo social"),
        ("infrastructure", "Infraestructura"),
        ("other", "Otro"),
    ]
    STATUSES = [
        ("received", "Recibida"),
        ("in_progress", "En gestión"),
        ("resolved", "Resuelta"),
    ]
    neighborhood = models.ForeignKey(
        Neighborhood, on_delete=models.CASCADE, related_name="requests"
    )
    requester = models.ForeignKey(User, on_delete=models.PROTECT, related_name="community_requests")
    category = models.CharField(max_length=30, choices=CATEGORIES, default="other")
    subject = models.CharField(max_length=180)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUSES, default="received")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
