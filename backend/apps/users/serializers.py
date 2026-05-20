from rest_framework import serializers
from .models import BotUser


class BotUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotUser
        fields = ['id', 'telegram_id', 'username', 'first_name', 'last_name', 'is_group', 'joined_at', 'is_active']
        read_only_fields = ['id', 'joined_at']
