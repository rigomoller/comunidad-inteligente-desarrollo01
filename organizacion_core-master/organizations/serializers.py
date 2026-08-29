from rest_framework import serializers

from .models import BoardMember, BoardRole, Commune, NeighborhoodOrganization, Province, Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = "__all__"


class ProvinceSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source="region.name", read_only=True)

    class Meta:
        model = Province
        fields = "__all__"


class CommuneSerializer(serializers.ModelSerializer):
    province_name = serializers.CharField(source="province.name", read_only=True)
    region_name = serializers.CharField(source="province.region.name", read_only=True)

    class Meta:
        model = Commune
        fields = "__all__"


class BoardRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardRole
        fields = "__all__"


class BoardMemberSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = BoardMember
        fields = "__all__"


class OrganizationSerializer(serializers.ModelSerializer):
    commune_name = serializers.CharField(source="commune.name", read_only=True)
    province_name = serializers.CharField(read_only=True)
    region_name = serializers.CharField(read_only=True)
    board_members = BoardMemberSerializer(many=True, read_only=True)

    class Meta:
        model = NeighborhoodOrganization
        fields = "__all__"
