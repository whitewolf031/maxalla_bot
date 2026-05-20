from rest_framework import serializers
from .models import Driver, DailyStatus


class DriverSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Driver
        fields = [
            'id', 'full_name', 'phone_number', 'car_name', 'car_number',
            'telegram_id', 'telegram_username', 'status', 'status_display',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DriverCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            'full_name', 'phone_number', 'car_name', 'car_number',
            'telegram_id', 'telegram_username'
        ]


class DailyStatusSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    driver_phone = serializers.CharField(source='driver.phone_number', read_only=True)
    car_name = serializers.CharField(source='driver.car_name', read_only=True)
    car_number = serializers.CharField(source='driver.car_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DailyStatus
        fields = [
            'id', 'driver', 'driver_name', 'driver_phone', 'car_name', 'car_number',
            'date', 'status', 'status_display', 'location', 'moving_direction', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']
