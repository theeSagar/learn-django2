from rest_framework import serializers
from .models import *
from sws.models import (
    State,
    District,
    RegionalOffice,
    KnowYourPolicy,
    IndustrialAreaList,
    RegionalOfficeDistrictMapping,
)

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']

class DistrictSerializer(serializers.ModelSerializer):
    state_name = serializers.ReadOnlyField(source="state.name")

    class Meta:
        model = District
        fields = ["id", "state", "state_name", "name"]

class DistrictCreateSerializer(serializers.Serializer):
    state_id = serializers.IntegerField()
    district_names = serializers.ListField(
        child=serializers.CharField(max_length=255)
    )

    def validate_state_id(self, value):
        if not State.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid state ID.")
        return value

class RegionalCreatOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionalOffice
        fields = ['id', 'name']
    
class KnowYourPolicyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowYourPolicy
        fields = "__all__"

class IndustrialAreaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustrialAreaList
        fields = "__all__"

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name"]

class IndustrialAreaListSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustrialAreaList
        fields = "__all__"

class RegionalOfficeDistrictMapSerializer(serializers.ModelSerializer):
    regional_office = serializers.PrimaryKeyRelatedField(
        queryset=RegionalOffice.objects.all()
    )
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all()
    )

    class Meta:
        model = RegionalOfficeDistrictMapping
        fields = '__all__'
