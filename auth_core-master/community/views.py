from datetime import date
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.html import escape
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .certificate_pdf import build_residence_certificate_pdf
from .models import Activity, CommunityDocument, CommunityRequest, Neighborhood, Post, PrivateMessage, Profile, ResidenceCertificateRequest
from .permissions import IsBoardMember
from .serializers import ActivitySerializer, CommunityRequestSerializer, ContactSerializer, DocumentSerializer, MessageSerializer, NeighborhoodSerializer, PostSerializer, ProfileSerializer, ResidenceCertificateSerializer, UserSerializer
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


class ResidenceCertificateViewSet(viewsets.ModelViewSet):
    serializer_class = ResidenceCertificateSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        neighborhood = self.request.user.profile.neighborhood
        queryset = ResidenceCertificateRequest.objects.filter(
            neighborhood=neighborhood
        ).select_related("requester", "reviewed_by", "neighborhood")
        if self.request.user.profile.role == "neighbor":
            queryset = queryset.filter(requester=self.request.user)
        return queryset

    def get_permissions(self):
        if self.action in {"approve", "request_changes", "reject", "proof"}:
            return [IsBoardMember()]
        return [IsAuthenticated()]

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Utilizar las acciones de revisión o corrección del certificado."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Las solicitudes se conservan para mantener la trazabilidad."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        certificate = self.get_object()
        if certificate.status != "pending":
            return Response(
                {"detail": "Solo se puede aprobar una solicitud pendiente."},
                status=status.HTTP_409_CONFLICT,
            )
        now = timezone.now()
        certificate.status = "issued"
        certificate.reviewed_by = request.user
        certificate.reviewed_at = now
        certificate.issued_at = now
        certificate.reviewer_notes = request.data.get("reviewer_notes", "Antecedentes revisados.").strip()
        certificate.certificate_number = f"CI-{timezone.localdate():%Y}-{certificate.pk:06d}"
        certificate.save()
        return Response(self.get_serializer(certificate).data)

    @action(detail=True, methods=["post"], url_path="request-changes")
    def request_changes(self, request, pk=None):
        certificate = self.get_object()
        reviewer_notes = request.data.get("reviewer_notes", "").strip()
        if not reviewer_notes:
            return Response(
                {"detail": "Indicar qué antecedente debe corregir el vecino."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        certificate.status = "needs_changes"
        certificate.reviewer_notes = reviewer_notes
        certificate.reviewed_by = request.user
        certificate.reviewed_at = timezone.now()
        certificate.save(update_fields=["status", "reviewer_notes", "reviewed_by", "reviewed_at", "updated_at"])
        return Response(self.get_serializer(certificate).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        certificate = self.get_object()
        reviewer_notes = request.data.get("reviewer_notes", "").strip()
        if not reviewer_notes:
            return Response(
                {"detail": "Indicar el motivo del rechazo."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        certificate.status = "rejected"
        certificate.reviewer_notes = reviewer_notes
        certificate.reviewed_by = request.user
        certificate.reviewed_at = timezone.now()
        certificate.save(update_fields=["status", "reviewer_notes", "reviewed_by", "reviewed_at", "updated_at"])
        return Response(self.get_serializer(certificate).data)

    @action(detail=True, methods=["post"])
    def resubmit(self, request, pk=None):
        certificate = self.get_object()
        if certificate.requester_id != request.user.id:
            return Response({"detail": "Solo el solicitante puede corregir el expediente."}, status=403)
        if certificate.status != "needs_changes":
            return Response({"detail": "La solicitud no está esperando una corrección."}, status=409)
        serializer = self.get_serializer(certificate, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            status="pending",
            reviewer_notes="",
            reviewed_by=None,
            reviewed_at=None,
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def proof(self, request, pk=None):
        certificate = self.get_object()
        extension = certificate.proof_document.name.rsplit(".", 1)[-1]
        return FileResponse(
            certificate.proof_document.open("rb"),
            as_attachment=True,
            filename=f"respaldo-solicitud-{certificate.pk}.{extension}",
        )

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        certificate = self.get_object()
        if certificate.status != "issued":
            return Response({"detail": "El certificado todavía no ha sido emitido."}, status=409)
        verification_url = request.build_absolute_uri(
            f"/api/certificates/verify/{certificate.verification_code}/"
        )
        pdf = build_residence_certificate_pdf(certificate, verification_url)
        return FileResponse(
            pdf,
            as_attachment=True,
            filename=f"{certificate.certificate_number}.pdf",
            content_type="application/pdf",
        )

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
        "certificate_requests": n.residence_certificate_requests.count(),
        "pending_certificates": n.residence_certificate_requests.filter(status="pending").count(),
        "older_adults": sum(1 for age in ages if age >= 60),
        "age_groups": {"children": sum(1 for age in ages if age < 18), "adults": sum(1 for age in ages if 18 <= age < 60), "older": sum(1 for age in ages if age >= 60)},
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_residence_certificate(request, code):
    certificate = get_object_or_404(
        ResidenceCertificateRequest.objects.select_related("neighborhood"),
        verification_code=code,
        status="issued",
    )
    compact_rut = certificate.rut.replace(".", "")
    masked_rut = f"***.***.{compact_rut[-5:]}"
    issued = timezone.localtime(certificate.issued_at).strftime("%d-%m-%Y")
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verificación {escape(certificate.certificate_number)}</title>
<style>body{{margin:0;background:#f4f6f8;font-family:Arial,sans-serif;color:#172438}}main{{max-width:680px;margin:8vh auto;background:white;border-radius:18px;padding:38px;box-shadow:0 18px 45px #102b4922}}.ok{{display:inline-block;background:#dff5e8;color:#176b3a;padding:8px 13px;border-radius:999px;font-weight:bold}}h1{{color:#102b49}}dl{{display:grid;grid-template-columns:180px 1fr;gap:14px;margin-top:28px}}dt{{color:#64748b}}dd{{margin:0;font-weight:bold}}footer{{border-top:4px solid #f2af21;margin-top:32px;padding-top:16px;color:#64748b;font-size:13px}}@media(max-width:700px){{main{{margin:0;border-radius:0;min-height:100vh;padding:28px}}dl{{grid-template-columns:1fr;gap:5px}}dd{{margin-bottom:12px}}}}</style></head>
<body><main><span class="ok">CERTIFICADO VÁLIDO</span><h1>Certificado de residencia</h1>
<p>Este documento fue emitido y permanece registrado en Comunidad Inteligente.</p><dl>
<dt>Folio</dt><dd>{escape(certificate.certificate_number)}</dd>
<dt>Persona</dt><dd>{escape(certificate.applicant_name)}</dd>
<dt>RUT protegido</dt><dd>{escape(masked_rut)}</dd>
<dt>Junta de vecinos</dt><dd>{escape(certificate.neighborhood.name)}</dd>
<dt>Comuna</dt><dd>{escape(certificate.commune)}</dd>
<dt>Fecha de emisión</dt><dd>{issued}</dd></dl>
<footer>La verificación pública no muestra el comprobante de domicilio ni la dirección completa.</footer></main></body></html>"""
    return HttpResponse(html)

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
