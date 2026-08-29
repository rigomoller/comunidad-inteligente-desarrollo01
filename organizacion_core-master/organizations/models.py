from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Province(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="provinces")
    name = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["region", "name"], name="unique_province_region")
        ]

    def __str__(self):
        return self.name


class Commune(models.Model):
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name="communes")
    name = models.CharField(max_length=120)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["province", "name"], name="unique_commune_province")
        ]

    @property
    def region(self):
        return self.province.region

    def __str__(self):
        return self.name


class NeighborhoodOrganization(models.Model):
    name = models.CharField(max_length=180)
    rut = models.CharField(max_length=20, unique=True)
    purpose = models.TextField()
    relation_funds = models.CharField(max_length=160, blank=True)
    constitution_date = models.DateField()
    legal_representative = models.CharField(max_length=160)
    institution_type = models.CharField(max_length=100, default="Junta de vecinos")
    thematic_area = models.CharField(max_length=120, default="Desarrollo comunitario")
    legal_personality = models.CharField(max_length=80, blank=True)
    assets = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    address = models.CharField(max_length=220)
    commune = models.ForeignKey(Commune, on_delete=models.PROTECT, related_name="organizations")

    @property
    def province_name(self):
        return self.commune.province.name

    @property
    def region_name(self):
        return self.commune.province.region.name

    def __str__(self):
        return self.name


class BoardRole(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


class BoardMember(models.Model):
    organization = models.ForeignKey(
        NeighborhoodOrganization, on_delete=models.CASCADE, related_name="board_members"
    )
    user_id = models.PositiveIntegerField()
    full_name = models.CharField(max_length=160)
    role = models.ForeignKey(BoardRole, on_delete=models.PROTECT)
    assigned_at = models.DateField()
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "role"], name="unique_active_board_role"
            )
        ]

    def __str__(self):
        return f"{self.full_name} - {self.role}"
