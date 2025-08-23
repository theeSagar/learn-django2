from rest_framework import serializers
from .models import *
from sws.serializers import *

class CalculateIncentiveSerializer(serializers.Serializer):
    yop = serializers.IntegerField()
    investment = serializers.FloatField()
    sector_name = serializers.CharField()
    yuc = serializers.IntegerField()
    cyp = serializers.IntegerField() 
    total_employer = serializers.IntegerField()
    is_company_exports = serializers.BooleanField()
    export_per = serializers.FloatField()
    is_back_area_company = serializers.BooleanField()
    is_cement_company = serializers.BooleanField()
    is_company_fdi = serializers.BooleanField()
    fdi_per = serializers.FloatField()



class CustomerIntentionProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerIntentionProject
        fields=["id","intention_id","product_name","land_industrial_area"]

class InCAFProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model=InCAFProject
        fields="__all__"

class IncentiveCAFSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=IncentiveCAF
        fields="__all__"

class InCAFProductSerializer(serializers.ModelSerializer):

    class Meta:
        model=InCAFProduct
        fields="__all__"

class DocumentListSerializer(serializers.ModelSerializer):

    class Meta:
        model=DocumentList
        fields="__all__"

class InCAFDocumentsSerializer(serializers.ModelSerializer):
    entity_doc_type = serializers.SerializerMethodField()
    digi_doc_type = serializers.SerializerMethodField()

    class Meta:
        model=InCAFDocuments
        fields= ["document_id","document_path","document_name","entity_doc_type","digi_doc_type"]

    def get_entity_doc_type(self, obj):
        return obj.document.entity_doc_type if obj.document else None

    def get_digi_doc_type(self, obj):
        return obj.document.digi_doc_type if obj.document else None  

class IncentiveAgendaProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncentiveAgendaProduct
        fields = "__all__"

class IncentiveAgendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncentiveAgenda  
        fields = '__all__'  

class IncentiveAgendaSlecSerializer(serializers.ModelSerializer):
    class Meta:
        model= IncentiveAgenda
        fields=["unit_name","constitution_type_name","activity_name","sector_name","unit_type","sub_sector_name","category_of_block","eligible_investment_plant_machinery","bipa","yearly_bipa","status"]


class IncentiveCAFListSerializer(serializers.ModelSerializer):
    intention_id = serializers.CharField(source='intention.intention_id', read_only=True)
    
    class Meta:
        model = IncentiveCAF
        fields = [
            'id', 'status', 'user', 'caf_pdf_url', 'incentive_caf_number', 
            'acknowledgement', 'acknowledgement_date','intention_id', 'created_at', 'updated_at'
        ]

class SectorDocumentSerializer(serializers.ModelSerializer):
    document_id = serializers.SerializerMethodField()
    document_name = serializers.SerializerMethodField()
    entity_doc_type = serializers.SerializerMethodField()
    digi_doc_type = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    template_file_path = serializers.SerializerMethodField()

    class Meta:
        model = SectorDocumentList
        fields = ['document_id', 'title' ,'document_name', 'entity_doc_type', 'digi_doc_type', 'file_type','template_file_path']

    def get_document_id(self, obj):
        return obj.document.id if obj.document and obj.document.id else ""

    def get_document_name(self, obj):
        return obj.document.name if obj.document and obj.document.name else ""

    def get_entity_doc_type(self, obj):
        return obj.document.entity_doc_type if obj.document and obj.document.entity_doc_type else ""

    def get_digi_doc_type(self, obj):
        return obj.document.digi_doc_type if obj.document and obj.document.digi_doc_type else ""

    def get_title(self, obj):
        return obj.document.title if obj.document and obj.document.title else ""

    def get_file_type(self, obj):
        return obj.document.file_type if obj.document and obj.document.file_type else ""
    
    def get_template_file_path(self, obj):
        return obj.document.template_file_path if obj.document and obj.document.template_file_path else ""       


class IncentiveSlecOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model=IncentiveSlecOrder
        exclude=("created_at" ,"updated_at")

class IncentiveSlecYealySerializer(serializers.ModelSerializer):

    class Meta:
        model=IncentiveSlecYealy
        fields="__all__"

class IncentiveSlecProductSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=IncentiveSlecProduct
        fields="__all__"


class IncentiveApprovalHistorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model=IncentiveApprovalHistory
        fields="__all__"

class CustomerIntentionProjectListSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerIntentionProject
        fields="__all__"

class CAFCreationPDFSerializer(serializers.ModelSerializer):
    class Meta:
        model=CAFCreationPDF
        fields=["pdf_url"]

class IncentiveCAFPdfSerializer(serializers.ModelSerializer):

    class Meta:
        model=IncentiveCAF
        fields=["caf_pdf_url"]

class InCAFDocumentsPdfSerializer(serializers.ModelSerializer):

    class Meta:
        model=InCAFDocuments
        fields= ["document_path","document_name"]

class IncentiveAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=IncentiveAuditLog
        fields="__all__"

class IncentiveActivityHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model=IncentiveActivityHistory
        fields="__all__"

class InCAFExpansionSerializer(serializers.ModelSerializer):

    class Meta:
        model=InCAFExpansion
        exclude=("created_at","updated_at")


class InCAFInvestmentPreviousSerializer(serializers.ModelSerializer):
    class Meta:
        model=InCAFInvestment
        fields= ["id","comm_production_date","caf","turnover", "is_fdi","fdi_percentage","csr","is_export_unit","promoters_equity_amount","term_loan_amount","fdi_amount", "total_finance_amount","is_csr"]

class InCAFInvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model=InCAFInvestment
        exclude= ("created_at","updated_at","comm_production_date","caf","turnover", "is_fdi","fdi_percentage","csr","is_export_unit","promoters_equity_amount","term_loan_amount","fdi_amount", "total_finance_amount","is_csr")

class IPAUnitDataMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model=IPAUnitDataMaster
        fields= ["intention_id","intention_date","unit_name","date_of_production", "unit_type","sector","block_priority","slec_meeting_date","eligible_investment","bipa","ybipa", "eligibility_start_date","eligibility_end_date","slec_meeting_no"]

class IPAIntentionSerializer(serializers.ModelSerializer):
    class Meta:
        model=IPAUnitDataMaster
        fields= ["intention_id","unit_name"]

class IncentiveDepartmentQuerySerializer(serializers.ModelSerializer):
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    class Meta:
        model=IncentiveDepartmentQueryModel
        fields= ["id",'department_remark',"department_user_name", "updated_at"]


class IncentiveQueryDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncentiveQueryDocumentModel
        fields = ["document_name", "document_path"]

class IncentiveDepartmentQueryListSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S") 

    class Meta:
        model = IncentiveDepartmentQueryModel
        fields = ["department_remark", "user_remark", "user_name", "documents", "updated_at"]

    def get_documents(self, obj):
        documents = obj.queries.all() 
        return IncentiveQueryDocumentSerializer(documents, many=True).data

class IncentiveTypeSectorModelSerializer(serializers.ModelSerializer):
    input_tag = serializers.CharField(source='incentive_type.incentive_type')
    title = serializers.CharField(source='incentive_type.title')
    # sector = serializers.IntegerField(source='sector.id', allow_null=True)

    class Meta:
        model = IncentiveTypeSectorModel
        fields = ['input_tag', 'title']

class AgendaInvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgendaInvestmentModel 
        exclude=("id","created_at" ,"updated_at")

class AgendaIncentiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgendaIncentiveModel 
        fields = '__all__'  