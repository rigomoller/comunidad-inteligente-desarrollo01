from datetime import date

from django.core.management.base import BaseCommand

from organizations.models import BoardMember, BoardRole, Commune, NeighborhoodOrganization, Province, Region


class Command(BaseCommand):
    help = "Crear datos ficticios de organización y geografía"

    def handle(self, *args, **kwargs):
        region, _ = Region.objects.get_or_create(name="Región Metropolitana de Santiago")
        province, _ = Province.objects.get_or_create(region=region, name="Santiago")
        commune, _ = Commune.objects.get_or_create(province=province, name="Santiago")
        organization, _ = NeighborhoodOrganization.objects.update_or_create(
            rut="65.123.456-7",
            defaults={
                "name": "Junta de Vecinos Nueva Esperanza",
                "purpose": "Fortalecer la participación, la seguridad y el bienestar comunitario.",
                "relation_funds": "Fondo de Desarrollo Vecinal y aportes comunitarios",
                "constitution_date": date(2012, 4, 14),
                "legal_representative": "Carolina Muñoz",
                "institution_type": "Junta de vecinos",
                "thematic_area": "Desarrollo comunitario",
                "legal_personality": "Vigente",
                "assets": 2850000,
                "address": "Avenida Los Aromos 1450",
                "commune": commune,
            },
        )
        members = [
            ("Presidenta", 2, "Carolina Muñoz"),
            ("Secretario", 4, "Jorge Silva"),
            ("Tesorera", 5, "Ana Soto"),
        ]
        for role_name, user_id, full_name in members:
            role, _ = BoardRole.objects.get_or_create(name=role_name)
            BoardMember.objects.update_or_create(
                organization=organization,
                role=role,
                defaults={
                    "user_id": user_id,
                    "full_name": full_name,
                    "assigned_at": date(2026, 3, 1),
                    "active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Organización y directiva ficticia creadas."))
