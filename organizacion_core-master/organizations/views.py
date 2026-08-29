from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import BoardMember, BoardRole, Commune, NeighborhoodOrganization, Province, Region
from .permissions import IsBoardOrReadOnly
from .serializers import (
    BoardMemberSerializer,
    BoardRoleSerializer,
    CommuneSerializer,
    OrganizationSerializer,
    ProvinceSerializer,
    RegionSerializer,
)


class ReadMostlyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsBoardOrReadOnly]


class RegionViewSet(ReadMostlyViewSet):
    queryset = Region.objects.all().order_by("name")
    serializer_class = RegionSerializer


class ProvinceViewSet(ReadMostlyViewSet):
    queryset = Province.objects.select_related("region").all().order_by("name")
    serializer_class = ProvinceSerializer


class CommuneViewSet(ReadMostlyViewSet):
    queryset = Commune.objects.select_related("province__region").all().order_by("name")
    serializer_class = CommuneSerializer


class OrganizationViewSet(ReadMostlyViewSet):
    queryset = NeighborhoodOrganization.objects.select_related(
        "commune__province__region"
    ).prefetch_related("board_members__role")
    serializer_class = OrganizationSerializer


class BoardRoleViewSet(ReadMostlyViewSet):
    queryset = BoardRole.objects.all().order_by("name")
    serializer_class = BoardRoleSerializer


class BoardMemberViewSet(ReadMostlyViewSet):
    queryset = BoardMember.objects.select_related("organization", "role").all()
    serializer_class = BoardMemberSerializer


@api_view(["GET"])
def my_organization(request):
    organization = (
        NeighborhoodOrganization.objects.select_related("commune__province__region")
        .prefetch_related("board_members__role")
        .first()
    )
    if not organization:
        return Response({"detail": "No existe una organización registrada."}, status=404)
    return Response(OrganizationSerializer(organization).data)
