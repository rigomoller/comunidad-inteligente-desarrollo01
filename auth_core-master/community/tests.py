from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from .models import Activity, Neighborhood, Profile

class CommunityApiTests(APITestCase):
    def setUp(self):
        self.neighborhood = Neighborhood.objects.create(name="Barrio Demo", commune="Santiago")
        self.board = User.objects.create_user("directiva_test", password="Test1234!")
        self.neighbor = User.objects.create_user("vecino_test", password="Test1234!")
        Profile.objects.create(user=self.board, neighborhood=self.neighborhood, role="board", birth_year=1980)
        Profile.objects.create(user=self.neighbor, neighborhood=self.neighborhood, role="neighbor", birth_year=1960)

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
