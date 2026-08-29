from django.contrib import admin

from .models import BoardMember, BoardRole, Commune, NeighborhoodOrganization, Province, Region

admin.site.register([Region, Province, Commune, NeighborhoodOrganization, BoardRole, BoardMember])
