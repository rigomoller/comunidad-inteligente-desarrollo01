from datetime import timedelta
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
import shutil
import tempfile

from .models import Activity, Neighborhood, Profile, ResidenceCertificateRequest

class CommunityApiTests(APITestCase):
    def setUp(self):
        self.media_directory = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory)
        self.media_override.enable()
        self.neighborhood = Neighborhood.objects.create(name="Barrio Demo", commune="Santiago")
        self.board = User.objects.create_user("directiva_test", password="Test1234!")
        self.neighbor = User.objects.create_user("vecino_test", password="Test1234!")
        Profile.objects.create(user=self.board, neighborhood=self.neighborhood, role="board", birth_year=1980)
        Profile.objects.create(user=self.neighbor, neighborhood=self.neighborhood, role="neighbor", birth_year=1960)

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_directory, ignore_errors=True)

    def proof_file(self, name="cuenta-servicio.pdf"):
        return SimpleUploadedFile(
            name,
            b"%PDF-1.4\n% respaldo de prueba\n",
            content_type="application/pdf",
        )

    def certificate_payload(self):
        return {
            "rut": "12.345.678-5",
            "address": "Pasaje Los Aromos 123",
            "commune": "Santiago",
            "purpose": "Postulación a beneficio municipal",
            "proof_type": "utility_bill",
            "document_date": timezone.localdate().isoformat(),
            "sworn_declaration": "true",
            "proof_document": self.proof_file(),
        }

    def authenticate(self, user):
        response = self.client.post("/api/auth/login/", {"username": user.username, "password": "Test1234!"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_board_can_create_and_delete_post(self):
        self.authenticate(self.board)
        created = self.client.post("/api/posts/", {"title": "Aviso", "content": "Reunión", "is_published": True})
        self.assertEqual(created.status_code, 201)
        deleted = self.client.delete(f"/api/posts/{created.data['id']}/")
        self.assertEqual(deleted.status_code, 204)

    def test_neighbor_cannot_create_post(self):
        self.authenticate(self.neighbor)
        response = self.client.post("/api/posts/", {"title": "No autorizado", "content": "Contenido"})
        self.assertEqual(response.status_code, 403)

    def test_dashboard_returns_aggregated_data(self):
        self.authenticate(self.board)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["neighbors"], 2)
        self.assertEqual(response.data["older_adults"], 1)

    def test_assistant_uses_authorized_activity(self):
        Activity.objects.create(neighborhood=self.neighborhood, title="Operativo de salud", starts_at=timezone.now()+timedelta(days=2), location="Sede")
        self.authenticate(self.neighbor)
        response = self.client.post("/api/assistant/", {"question": "¿Cuál es la próxima actividad?"})
        self.assertContains(response, "Operativo de salud")

    def test_board_can_register_neighbor(self):
        self.authenticate(self.board)
        response = self.client.post("/api/neighbors/register/", {"username":"nuevo","password":"Nuevo1234!","first_name":"Ana","birth_year":1995,"household_size":3})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Profile.objects.filter(user__username="nuevo", role="neighbor").exists())

    def test_neighbor_can_send_message_inside_neighborhood(self):
        self.authenticate(self.neighbor)
        response = self.client.post(
            "/api/messages/",
            {"recipient": self.board.id, "body": "Hola directiva"},
        )
        self.assertEqual(response.status_code, 201)

    def test_neighbor_can_create_request(self):
        self.authenticate(self.neighbor)
        response = self.client.post(
            "/api/requests/",
            {"category": "security", "subject": "Luminaria", "description": "Está apagada"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "received")

    def test_neighbor_can_submit_residence_certificate_request(self):
        self.authenticate(self.neighbor)
        response = self.client.post(
            "/api/residence-certificates/",
            self.certificate_payload(),
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["automatic_status"], "passed")
        self.assertNotIn("proof_document", response.data)

    def test_board_can_review_issue_download_and_verify_certificate(self):
        self.authenticate(self.neighbor)
        created = self.client.post(
            "/api/residence-certificates/",
            self.certificate_payload(),
            format="multipart",
        )
        certificate_id = created.data["id"]
        self.authenticate(self.board)
        approved = self.client.post(
            f"/api/residence-certificates/{certificate_id}/approve/",
            {"reviewer_notes": "Documento revisado y domicilio confirmado."},
            format="json",
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.data["status"], "issued")
        self.assertTrue(approved.data["certificate_number"].startswith("CI-"))

        downloaded = self.client.get(
            f"/api/residence-certificates/{certificate_id}/download/"
        )
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded["Content-Type"], "application/pdf")
        self.assertTrue(b"".join(downloaded.streaming_content).startswith(b"%PDF"))

        verification_code = approved.data["verification_code"]
        self.client.credentials()
        verified = self.client.get(f"/api/certificates/verify/{verification_code}/")
        self.assertEqual(verified.status_code, 200)
        self.assertContains(verified, "CERTIFICADO VÁLIDO")

    def test_neighbor_cannot_approve_certificate(self):
        self.authenticate(self.neighbor)
        created = self.client.post(
            "/api/residence-certificates/",
            self.certificate_payload(),
            format="multipart",
        )
        response = self.client.post(
            f"/api/residence-certificates/{created.data['id']}/approve/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ResidenceCertificateRequest.objects.get().status, "pending")

    def test_invalid_rut_is_rejected(self):
        self.authenticate(self.neighbor)
        payload = self.certificate_payload()
        payload["rut"] = "12.345.678-9"
        response = self.client.post(
            "/api/residence-certificates/", payload, format="multipart"
        )
        self.assertEqual(response.status_code, 400)
