from rest_framework import serializers
from .models import *
from sws.serializers import DepartmentListSerializer
    
class ApprovalListSerializer(serializers.Serializer):
    class Meta:
        model = ApprovalList
        fields = ['id', 'name', 'phase']

class SectorApprovalMappingSerializer(serializers.Serializer):
    class Meta:
        model = SectorApprovalMapping
        fields = '__all__'

class SubSectorApprovalMappingSerializer(serializers.Serializer):
    class Meta:
        model = SubSectorApprovalMapping
        fields = '__all__'

class IAExemptionMappingSerializer(serializers.Serializer):
    approval = ApprovalListSerializer()

    class Meta:
        model = IAExemptionMapping
        fields = [ 'approval']

    

class KYAQuestionBankSerializer(serializers.Serializer):
    class Meta:
        model = KYAQuestionBank
        fields = '__all__'

class KYAQuestionBankOptionSerializer(serializers.Serializer):
    class Meta:
        model = KYAQuestionBankOption
        fields = '__all__'

class SectorQuestionMappingSerializer(serializers.Serializer):
    class Meta:
        model = SectorQuestionMapping
        fields = '__all__'

class SectorQuestionMethodSerializer(serializers.Serializer):
    class Meta:
        model = SectorQuestionMethod
        fields = '__all__'

class SectorQuestionOptionSerializer(serializers.Serializer):
    class Meta:
        model = SectorQuestionOption
        fields = '__all__'

class SectorQuestionApprovalSerializer(serializers.Serializer):
    class Meta:
        model = SectorQuestionApproval
        fields = '__all__'

class SubSectorQuestionMappingSerializer(serializers.Serializer):
    class Meta:
        model = SubSectorQuestionMapping
        fields = '__all__'

class SubSectorQuestionMethodSerializer(serializers.Serializer):
    class Meta:
        model = SubSectorQuestionMethod
        fields = '__all__'

class SubSectorQuestionOptionSerializer(serializers.Serializer):
    class Meta:
        model = SubSectorQuestionOption
        fields = '__all__'

class SubSectorQuestionApprovalSerializer(serializers.Serializer):
    class Meta:
        model = SubSectorQuestionApproval
        fields = '__all__'

class ApprovalDepartmentListSerializer(serializers.Serializer):
    department = DepartmentListSerializer()

    class Meta:
        model = ApprovalDepartmentList
        fields = [ 'department']

class UserCAFServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCAFService
        fields = "__all__"

