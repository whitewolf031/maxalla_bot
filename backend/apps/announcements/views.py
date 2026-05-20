from rest_framework import serializers, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as drf_status
from .models import Announcement
from django.urls import path


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'text', 'sent_by', 'sent_at', 'recipients_count']
        read_only_fields = ['id', 'sent_at']


class AnnouncementListCreateView(generics.ListCreateAPIView):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer


# URLs
urlpatterns = [
    path('', AnnouncementListCreateView.as_view(), name='announcement-list'),
]
