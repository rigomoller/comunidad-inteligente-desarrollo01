from django.contrib import admin
from .models import Activity, CommunityDocument, CommunityRequest, Neighborhood, Post, PrivateMessage, Profile, ResidenceCertificateRequest

admin.site.register([Neighborhood, Profile, Post, Activity, CommunityDocument, PrivateMessage, CommunityRequest])


@admin.register(ResidenceCertificateRequest)
class ResidenceCertificateRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id", "applicant_name", "rut", "neighborhood", "automatic_status",
        "status", "certificate_number", "created_at",
    )
    list_filter = ("status", "automatic_status", "proof_type", "neighborhood")
    search_fields = ("applicant_name", "rut", "address", "certificate_number")
    readonly_fields = (
        "proof_sha256", "verification_code", "created_at", "updated_at",
        "reviewed_at", "issued_at",
    )
