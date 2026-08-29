from django.contrib.auth.models import User
from rest_framework import serializers
from datetime import date, timedelta
from pathlib import Path
import hashlib
import re

from .models import Activity, CommunityDocument, CommunityRequest, Neighborhood, Post, PrivateMessage, Profile, ResidenceCertificateRequest

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


class ResidenceCertificateSerializer(serializers.ModelSerializer):
    requester_name = serializers.CharField(source="requester.get_full_name", read_only=True)
    proof_type_label = serializers.CharField(source="get_proof_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    automatic_status_label = serializers.CharField(source="get_automatic_status_display", read_only=True)
    reviewer_name = serializers.CharField(source="reviewed_by.get_full_name", read_only=True)
    proof_document = serializers.FileField(write_only=True)
    proof_extension = serializers.SerializerMethodField()
    verification_url = serializers.SerializerMethodField()

    class Meta:
        model = ResidenceCertificateRequest
        fields = [
            "id", "requester", "requester_name", "applicant_name", "rut", "address",
            "commune", "purpose", "proof_type", "proof_type_label", "proof_document",
            "proof_extension", "document_date", "sworn_declaration", "automatic_status",
            "automatic_status_label", "automatic_notes", "status", "status_label",
            "reviewer_notes", "reviewed_by", "reviewer_name", "reviewed_at",
            "certificate_number", "verification_code", "verification_url", "issued_at",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "requester", "applicant_name", "automatic_status", "automatic_notes", "status",
            "reviewer_notes", "reviewed_by", "reviewed_at", "certificate_number",
            "verification_code", "issued_at", "created_at", "updated_at",
        ]

    def get_proof_extension(self, obj):
        return Path(obj.proof_document.name).suffix.lower().lstrip(".")

    def get_verification_url(self, obj):
        if obj.status != "issued":
            return ""
        request = self.context.get("request")
        path = f"/api/certificates/verify/{obj.verification_code}/"
        return request.build_absolute_uri(path) if request else path

    def validate_rut(self, value):
        compact = re.sub(r"[^0-9kK]", "", value)
        if len(compact) < 8:
            raise serializers.ValidationError("Ingresar un RUT chileno válido.")
        body, verifier = compact[:-1], compact[-1].upper()
        total = sum(int(digit) * (2 + index % 6) for index, digit in enumerate(reversed(body)))
        result = 11 - total % 11
        expected = "0" if result == 11 else "K" if result == 10 else str(result)
        if verifier != expected:
            raise serializers.ValidationError("El dígito verificador del RUT no es válido.")
        return f"{body}-{verifier}"

    def validate_document_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("La fecha del comprobante no puede ser futura.")
        return value

    def validate_proof_document(self, uploaded):
        if uploaded.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("El comprobante no puede superar 5 MB.")
        extension = Path(uploaded.name).suffix.lower()
        if extension not in {".pdf", ".jpg", ".jpeg", ".png"}:
            raise serializers.ValidationError("Adjuntar un archivo PDF, JPG o PNG.")
        header = uploaded.read(8)
        uploaded.seek(0)
        signatures = {
            ".pdf": header.startswith(b"%PDF"),
            ".jpg": header.startswith(b"\xff\xd8\xff"),
            ".jpeg": header.startswith(b"\xff\xd8\xff"),
            ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        }
        if not signatures[extension]:
            raise serializers.ValidationError("El contenido del archivo no coincide con su extensión.")
        return uploaded

    def validate(self, attrs):
        sworn = attrs.get("sworn_declaration", getattr(self.instance, "sworn_declaration", False))
        if not sworn:
            raise serializers.ValidationError({
                "sworn_declaration": "Debes declarar que los datos entregados son verdaderos."
            })
        return attrs

    def _prevalidate(self, attrs, requester, instance=None):
        uploaded = attrs.get("proof_document")
        if uploaded is None and instance is not None:
            return instance.proof_sha256, instance.automatic_status, instance.automatic_notes

        digest = hashlib.sha256()
        for chunk in uploaded.chunks():
            digest.update(chunk)
        uploaded.seek(0)
        proof_sha256 = digest.hexdigest()
        notes = ["Formato, tamaño e integridad básica del archivo: correctos."]
        automatic_status = "passed"
        document_date = attrs.get("document_date", getattr(instance, "document_date", None))
        commune = attrs.get("commune", getattr(instance, "commune", ""))
        neighborhood = requester.profile.neighborhood

        if document_date < date.today() - timedelta(days=90):
            automatic_status = "review"
            notes.append("El comprobante tiene más de 90 días y requiere revisión especial.")
        if commune.strip().casefold() != neighborhood.commune.strip().casefold():
            automatic_status = "review"
            notes.append("La comuna informada no coincide con la registrada para la junta de vecinos.")
        duplicates = ResidenceCertificateRequest.objects.filter(proof_sha256=proof_sha256).exclude(requester=requester)
        if instance is not None:
            duplicates = duplicates.exclude(pk=instance.pk)
        if duplicates.exists():
            automatic_status = "review"
            notes.append("El mismo archivo fue utilizado por otra cuenta; verificar manualmente.")
        notes.append("La autenticidad legal debe ser confirmada por una persona de la directiva.")
        return proof_sha256, automatic_status, " ".join(notes)

    def create(self, validated_data):
        requester = self.context["request"].user
        proof_sha256, automatic_status, automatic_notes = self._prevalidate(validated_data, requester)
        return ResidenceCertificateRequest.objects.create(
            requester=requester,
            neighborhood=requester.profile.neighborhood,
            applicant_name=requester.get_full_name() or requester.username,
            proof_sha256=proof_sha256,
            automatic_status=automatic_status,
            automatic_notes=automatic_notes,
            status="pending",
            **validated_data,
        )

    def update(self, instance, validated_data):
        requester = self.context["request"].user
        proof_sha256, automatic_status, automatic_notes = self._prevalidate(
            validated_data, requester, instance
        )
        validated_data.update(
            proof_sha256=proof_sha256,
            automatic_status=automatic_status,
            automatic_notes=automatic_notes,
        )
        return super().update(instance, validated_data)
