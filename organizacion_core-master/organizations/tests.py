from django.test import TestCase

from .models import Commune, NeighborhoodOrganization, Province, Region


class OrganizationModelTests(TestCase):
    def test_commune_exposes_its_region(self):
        region = Region.objects.create(name="Metropolitana")
        province = Province.objects.create(name="Santiago", region=region)
        commune = Commune.objects.create(name="Santiago", province=province)
        organization = NeighborhoodOrganization.objects.create(
            name="Junta Demo",
            rut="65.000.000-0",
            purpose="Participación",
            constitution_date="2020-01-01",
            legal_representative="Persona Demo",
            address="Dirección demo",
            commune=commune,
        )
        self.assertEqual(organization.region_name, "Metropolitana")
        self.assertEqual(organization.province_name, "Santiago")
