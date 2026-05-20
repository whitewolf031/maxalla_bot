from django.urls import path
from .views import AnnouncementListCreateView

urlpatterns = [
    path('', AnnouncementListCreateView.as_view(), name='announcement-list'),
]
