from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
import hashlib

from community.models import Activity, CommunityDocument, CommunityRequest, Neighborhood, Post, PrivateMessage, Profile, ResidenceCertificateRequest


class Command(BaseCommand):
    help = "Crear información ficticia para demostrar la plataforma"

    def handle(self, *args, **kwargs):
        neighborhood, _ = Neighborhood.objects.get_or_create(
            name="Junta de Vecinos Nueva Esperanza",
            commune="Santiago",
            defaults={"address": "Avenida Los Aromos 1450"},
        )

        demo_users = [
            ("administrador", "Admin1234!", "admin", "Marcela", "Rojas", 1978, 2, True),
            ("directiva", "Demo1234!", "board", "Carolina", "Muñoz", 1985, 4, False),
            ("vecino", "Demo1234!", "neighbor", "Diego", "Pérez", 1962, 2, False),
            ("ana.soto", "Vecino1234!", "neighbor", "Ana", "Soto", 1991, 3, False),
            ("luis.torres", "Vecino1234!", "neighbor", "Luis", "Torres", 1955, 2, False),
            ("camila.reyes", "Vecino1234!", "neighbor", "Camila", "Reyes", 2001, 1, False),
            ("jorge.silva", "Vecino1234!", "neighbor", "Jorge", "Silva", 1970, 5, False),
            ("marta.diaz", "Vecino1234!", "neighbor", "Marta", "Díaz", 1948, 1, False),
            ("felipe.vera", "Vecino1234!", "neighbor", "Felipe", "Vera", 1988, 4, False),
            ("sofia.leiva", "Vecino1234!", "neighbor", "Sofía", "Leiva", 2010, 4, False),
            ("ricardo.nunez", "Vecino1234!", "neighbor", "Ricardo", "Núñez", 1965, 3, False),
            ("paula.mora", "Vecino1234!", "neighbor", "Paula", "Mora", 1997, 2, False),
            ("andres.fuentes", "Vecino1234!", "neighbor", "Andrés", "Fuentes", 1980, 5, False),
            ("elena.castro", "Vecino1234!", "neighbor", "Elena", "Castro", 1952, 1, False),
            ("tomas.rivera", "Vecino1234!", "neighbor", "Tomás", "Rivera", 2007, 4, False),
        ]

        for username, password, role, first, last, birth_year, household, superuser in demo_users:
            user, _ = User.objects.get_or_create(username=username)
            user.first_name = first
            user.last_name = last
            user.email = f"{username}@ejemplo.cl"
            user.is_staff = superuser
            user.is_superuser = superuser
            user.set_password(password)
            user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "neighborhood": neighborhood,
                    "role": role,
                    "birth_year": birth_year,
                    "household_size": household,
                },
            )

        author = User.objects.get(username="directiva")
        posts = [
            ("Bienvenida a Comunidad Inteligente", "Centralizar información y fortalecer la participación de todas las familias del sector."),
            ("Reunión mensual de la directiva", "Invitar a la comunidad a revisar avances, necesidades y próximos proyectos barriales."),
            ("Campaña de reciclaje", "Depositar papel, cartón, vidrio y latas limpias en la sede vecinal durante la jornada comunitaria."),
            ("Actualización del registro vecinal", "Solicitar a cada hogar revisar sus datos para mantener nuestros indicadores actualizados."),
            ("Alerta preventiva de seguridad", "Recordar mantener iluminados los accesos y comunicar situaciones sospechosas por los canales oficiales."),
            ("Fondo para iniciativas comunitarias", "Presentar propuestas de mejoramiento del barrio hasta el último viernes del mes."),
        ]
        for title, content in posts:
            Post.objects.update_or_create(
                neighborhood=neighborhood,
                title=title,
                defaults={"author": author, "content": content, "is_published": True},
            )

        now = timezone.now()
        activities = [
            ("Operativo de salud preventiva", "Control de presión, glicemia y orientación para personas mayores.", 4, "Sede vecinal"),
            ("Taller de alfabetización digital", "Aprender a utilizar ClaveÚnica, correo electrónico y trámites en línea.", 8, "Biblioteca comunitaria"),
            ("Jornada de reciclaje", "Recibir residuos limpios y entregar orientación sobre separación domiciliaria.", 12, "Plaza Nueva Esperanza"),
            ("Asamblea general de vecinos", "Revisar el presupuesto, proyectos vigentes y prioridades del próximo trimestre.", 16, "Sede vecinal"),
            ("Tarde deportiva familiar", "Realizar actividades recreativas para niñas, niños, jóvenes y personas adultas.", 23, "Multicancha del sector"),
            ("Plantación de árboles", "Recuperar áreas verdes con especies de bajo consumo hídrico.", 30, "Parque Los Aromos"),
        ]
        for title, description, days, location in activities:
            Activity.objects.update_or_create(
                neighborhood=neighborhood,
                title=title,
                defaults={"description": description, "starts_at": now + timedelta(days=days), "location": location},
            )

        documents = [
            ("Estatutos de la junta de vecinos", "Institucional", "https://example.com/estatutos"),
            ("Acta de la última asamblea", "Actas", "https://example.com/acta-asamblea"),
            ("Reglamento de uso de la sede", "Reglamentos", "https://example.com/reglamento-sede"),
            ("Calendario comunitario anual", "Planificación", "https://example.com/calendario"),
            ("Protocolo de emergencias", "Seguridad", "https://example.com/emergencias"),
            ("Formulario de inscripción de actividades", "Formularios", "https://example.com/inscripcion"),
        ]
        for title, category, url in documents:
            CommunityDocument.objects.update_or_create(
                neighborhood=neighborhood,
                title=title,
                defaults={"category": category, "url": url},
            )

        neighbor = User.objects.get(username="vecino")
        PrivateMessage.objects.get_or_create(
            sender=neighbor,
            recipient=author,
            body="Hola, quisiera confirmar el horario de la próxima asamblea.",
        )
        PrivateMessage.objects.get_or_create(
            sender=author,
            recipient=neighbor,
            body="Hola Diego. La asamblea será a las 19:00 en la sede vecinal.",
        )
        CommunityRequest.objects.update_or_create(
            neighborhood=neighborhood,
            requester=neighbor,
            subject="Certificado de residencia",
            defaults={
                "category": "certificate",
                "description": "Necesitar certificado para presentar en trámite municipal.",
                "status": "in_progress",
            },
        )
        CommunityRequest.objects.update_or_create(
            neighborhood=neighborhood,
            requester=User.objects.get(username="ana.soto"),
            subject="Reparación de luminaria",
            defaults={
                "category": "security",
                "description": "Informar luminaria apagada en el pasaje Los Maitenes.",
                "status": "received",
            },
        )

        demo_proof = b"%PDF-1.4\n% Comprobante ficticio para demostracion del Capstone\n"
        certificate = ResidenceCertificateRequest.objects.filter(
            neighborhood=neighborhood,
            requester=neighbor,
            purpose="Postulación a beneficio municipal",
        ).first()
        if certificate is None:
            certificate = ResidenceCertificateRequest(
                neighborhood=neighborhood,
                requester=neighbor,
                applicant_name=neighbor.get_full_name(),
                rut="12345678-5",
                address="Pasaje Los Maitenes 245",
                commune=neighborhood.commune,
                purpose="Postulación a beneficio municipal",
                proof_type="utility_bill",
                document_date=timezone.localdate() - timedelta(days=12),
                proof_sha256=hashlib.sha256(demo_proof).hexdigest(),
                sworn_declaration=True,
                automatic_status="passed",
                automatic_notes=(
                    "Formato, tamaño e integridad básica del archivo: correctos. "
                    "La autenticidad legal fue confirmada por una persona de la directiva."
                ),
                status="issued",
                reviewer_notes="Antecedentes ficticios revisados para la demostración.",
                reviewed_by=author,
                reviewed_at=now,
                issued_at=now,
            )
            certificate.proof_document.save(
                "comprobante-demo.pdf", ContentFile(demo_proof), save=False
            )
            certificate.save()
            certificate.certificate_number = f"CI-{timezone.localdate():%Y}-{certificate.pk:06d}"
            certificate.save(update_fields=["certificate_number"])

        pending_neighbor = User.objects.get(username="ana.soto")
        pending_proof = b"%PDF-1.4\n% Cuenta de electricidad ficticia para revision\n"
        pending_certificate = ResidenceCertificateRequest.objects.filter(
            neighborhood=neighborhood,
            requester=pending_neighbor,
            purpose="Acreditar domicilio ante una institución bancaria",
        ).first()
        if pending_certificate is None:
            pending_certificate = ResidenceCertificateRequest(
                neighborhood=neighborhood,
                requester=pending_neighbor,
                applicant_name=pending_neighbor.get_full_name(),
                rut="11111111-1",
                address="Calle Los Álamos 782",
                commune=neighborhood.commune,
                purpose="Acreditar domicilio ante una institución bancaria",
                proof_type="utility_bill",
                document_date=timezone.localdate() - timedelta(days=7),
                proof_sha256=hashlib.sha256(pending_proof).hexdigest(),
                sworn_declaration=True,
                automatic_status="passed",
                automatic_notes=(
                    "Formato, tamaño, fecha y coincidencia de comuna: correctos. "
                    "Pendiente de confirmar autenticidad por la directiva."
                ),
                status="pending",
            )
            pending_certificate.proof_document.save(
                "cuenta-electricidad-demo.pdf", ContentFile(pending_proof), save=False
            )
            pending_certificate.save()

        self.stdout.write(
            self.style.SUCCESS(
                "Información ficticia creada: "
                f"{neighborhood.profiles.count()} usuarios, "
                f"{neighborhood.posts.count()} publicaciones, "
                f"{neighborhood.activities.count()} actividades y "
                f"{neighborhood.documents.count()} documentos y "
                f"{neighborhood.residence_certificate_requests.count()} certificados."
            )
        )
