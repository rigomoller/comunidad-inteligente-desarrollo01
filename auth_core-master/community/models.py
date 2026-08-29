from django.contrib.auth.models import User
from django.db import models
from pathlib import Path
from uuid import uuid4


def residence_proof_upload(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"residence_proofs/{instance.neighborhood_id or 'pending'}/{uuid4().hex}{extension}"

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


class ResidenceCertificateRequest(models.Model):
    PROOF_TYPES = [
        ("utility_bill", "Cuenta de servicio básico"),
        ("lease", "Contrato de arriendo"),
        ("bank_statement", "Documento bancario o institucional"),
        ("other", "Otro comprobante"),
    ]
    STATUSES = [
        ("pending", "Pendiente de revisión"),
        ("needs_changes", "Requiere corrección"),
        ("rejected", "Rechazada"),
        ("issued", "Certificado emitido"),
    ]
    AUTOMATIC_STATUSES = [
        ("passed", "Prevalidación aprobada"),
        ("review", "Revisión manual necesaria"),
    ]

    neighborhood = models.ForeignKey(
        Neighborhood,
        on_delete=models.CASCADE,
        related_name="residence_certificate_requests",
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="residence_certificate_requests",
    )
    applicant_name = models.CharField(max_length=180)
    rut = models.CharField(max_length=12)
    address = models.CharField(max_length=250)
    commune = models.CharField(max_length=120)
    purpose = models.CharField(max_length=250)
    proof_type = models.CharField(max_length=30, choices=PROOF_TYPES)
    proof_document = models.FileField(upload_to=residence_proof_upload)
    document_date = models.DateField()
    proof_sha256 = models.CharField(max_length=64, editable=False)
    sworn_declaration = models.BooleanField(default=False)
    automatic_status = models.CharField(
        max_length=20,
        choices=AUTOMATIC_STATUSES,
        default="review",
    )
    automatic_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    reviewer_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_residence_certificates",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    certificate_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    verification_code = models.UUIDField(default=uuid4, unique=True, editable=False)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.certificate_number or f"Solicitud #{self.pk} - {self.applicant_name}"
