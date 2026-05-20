from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import BotUser
from .serializers import BotUserSerializer


class BotUserListView(generics.ListAPIView):
    queryset = BotUser.objects.filter(is_active=True)
    serializer_class = BotUserSerializer


class BotUserCreateOrUpdateView(APIView):
    """Bot foydalanuvchisini yaratish yoki yangilash"""
    def post(self, request):
        telegram_id = request.data.get('telegram_id')
        user, created = BotUser.objects.update_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': request.data.get('username'),
                'first_name': request.data.get('first_name'),
                'last_name': request.data.get('last_name'),
                'is_group': request.data.get('is_group', False),
                'is_active': True,
            }
        )
        return Response(BotUserSerializer(user).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class AllChatIdsView(APIView):
    """Barcha foydalanuvchi va guruh chat ID larini olish (elon uchun)"""
    def get(self, request):
        users = BotUser.objects.filter(is_active=True).values_list('telegram_id', flat=True)
        return Response({'chat_ids': list(users)})
