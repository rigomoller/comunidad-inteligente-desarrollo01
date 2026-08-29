from django.contrib import admin
from .models import Activity, CommunityDocument, CommunityRequest, Neighborhood, Post, PrivateMessage, Profile

admin.site.register([Neighborhood, Profile, Post, Activity, CommunityDocument, PrivateMessage, CommunityRequest])
