from django.urls import path
from . import views

urlpatterns = [
    path('', views.BotUserListView.as_view(), name='user-list'),
    path('register/', views.BotUserCreateOrUpdateView.as_view(), name='user-register'),
    path('chat-ids/', views.AllChatIdsView.as_view(), name='chat-ids'),
]
