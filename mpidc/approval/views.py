import os
from io import BytesIO
from django.db import DatabaseError
from django.http import FileResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_RIGHT
import requests
from .models import *
from .serializers import *
from sws.models import IndustrialAreaList, DepartmentList
from userprofile.utils import getOtherMessage, getSuccessfulMessage
from django.db.models import Q
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE
from reportlab.lib.styles import ParagraphStyle

class KnowYourApprovalView(APIView):
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "sector": openapi.Schema(type=openapi.TYPE_INTEGER, description="Sector"),
                "sub_sector": openapi.Schema(type=openapi.TYPE_INTEGER, description="Sub Sector")
            }
        )
    )

    def post(self, request):
        pass

    def get(self, request):
        pass

class GetIndustrialAreaView(APIView):
    def get(self,request):
        authority = request.query_params.get("authority")
        incentive_authority = request.query_params.get("incentive_authority")
        district = request.query_params.get("district")
        if authority or district:
            if authority and district:
                areas = IndustrialAreaList.objects.filter(authority=authority, district_id = int(district)).values("id", "name")
            elif authority:
                areas = IndustrialAreaList.objects.filter(authority=authority).values("id", "name")
            else:
                areas = IndustrialAreaList.objects.filter(district_id = int(district)).values("id", "name")
        elif incentive_authority:
            if incentive_authority and district:
                areas = IndustrialAreaList.objects.filter(incentive_authority=incentive_authority, district_id = int(district)).values("id", "name")
            else:
                areas = IndustrialAreaList.objects.filter(incentive_authority=incentive_authority).values("id", "name")
        else:
            areas = IndustrialAreaList.objects.values("id", "name")
        if areas.exists():
            message = "All data fetched"
            data = list(areas)
        else:
            message = "No data found"
            data = []
        return Response(
            {
                "status": True, 
                "message": message,
                "data": data
            },
            status=status.HTTP_200_OK,
        )


class SectorApprovalView(APIView):

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "sector": openapi.Schema(type=openapi.TYPE_INTEGER, description="Sector")
            }
        )
    )

    def get(self, request):
        sector_id = request.GET.get('sector_id',0)
        if not sector_id:
            sector_id = 0
        sector_question_options = SectorQuestionOption.objects.filter(
             Q(sector_question__sector_id=sector_id) | Q(sector_question__sector_id__isnull=True)
        ).order_by("display_order")
        all_options = self.get_options_data(
            sector_question_options
        )
        sector_question_method = SectorQuestionMethod.objects.filter(
            Q(sector_question__sector_id=sector_id) | Q(sector_question__sector_id__isnull=True)
        )
        all_dynamic = self.get_dynamic_data(
            sector_question_method
        )
        service_data = self.get_service_approvals(
            operation_type = 'sector_service',
            sector_id=sector_id,
            all_options=all_options,
            all_dynamic=all_dynamic
        )

        clearance_data = self.get_service_approvals(
            operation_type = 'sector_clearance',
            sector_id=sector_id,
            all_options=all_options,
            all_dynamic=all_dynamic
        )

        data = [service_data, clearance_data]
        return Response(
            {
                "status": True,
                "message": "Data Retrived Successfully",
                "data": data
            },
            status=status.HTTP_200_OK,
        )

    def get_service_approvals(self, *args, **kwargs):
        sector_id = kwargs['sector_id']
        operation_type = kwargs['operation_type']
        all_options = kwargs['all_options']
        all_dynamic = kwargs['all_dynamic']
        
        if operation_type == 'sector_service':
            services = {
                "id": "services",
                "label": "Services",
                "fields": []
            }    
        elif operation_type == 'sector_clearance':
            services = {
                "id": "clearance",
                "label": "Clearance",
                "fields": []
            }
        
        try:
            if operation_type == 'sector_service':
                sector_question_mapping = SectorQuestionMapping.objects.filter(
                    Q(sector_id=sector_id) | Q(sector_id__isnull=True),
                    approval_type__in=['service', 'service_question'],
                    status='active'
                ).order_by("-mode","display_order")
            elif operation_type == 'sector_clearance':
                sector_question_mapping = SectorQuestionMapping.objects.filter(
                    Q(sector_id=sector_id) | Q(sector_id__isnull=True),
                    approval_type__in=['optional', 'mandatory_question'],
                    status='active'
                ).order_by("-mode","display_order")

            if sector_question_mapping.exists():
                fields = []
                for item in sector_question_mapping:
                    options = []
                    if all_options and item.id in all_options:
                        options = all_options[item.id]
                    dynamic = {}
                    if all_dynamic and item.id in all_dynamic:
                        dynamic = all_dynamic[item.id]

                    response_data = {
                        'id': item.question.question_tag,
                        'label': item.question.question_text,
                        'type': item.question.question_type,
                        'mode': item.mode,
                        'options': options,
                        'dynamic': dynamic,
                        'next_question_tag': item.next_question_tag
                    }
                    fields.append(response_data)
                services['fields'] = fields
                services['total'] = get_max_questions(services)
            return services
        except Exception as e:
            return services

    def get_options_data(self, data):
        all_options = {}
        try:
            if data.exists():
                for itm in data:
                    option_data = {
                        'value': itm.question_options.option_value,
                        'label': itm.question_options.option_display_name,
                        'next_question_tag': itm.next_question_tag
                    }
                    if itm.sector_question_id not in all_options:
                        all_options[itm.sector_question_id] = []
                    all_options[itm.sector_question_id].append(option_data)
            return all_options  
        except Exception as e:
            return all_options

    def get_dynamic_data(self, data):
        all_dynamic = {}
        try:
            if data.exists():
                for itm in data:
                    option_data = {
                        'target': itm.target,
                        'method': itm.method,
                    }
                    all_dynamic[itm.sector_question_id] = option_data
            return all_dynamic
        except Exception as e:
            return all_dynamic

    def post(self, request):
        pass

class SubSectorApprovalView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        subsector_id = request.GET.get('subsector_id', 0)        
        subsector_question_options = SubSectorQuestionOption.objects.filter(
            Q(subsector_question__subsector_id=subsector_id) | Q(subsector_question__subsector_id=True)
        ).order_by("display_order")
        all_options = self.get_options_data(
            subsector_question_options
        )
        subsector_question_method = SubSectorQuestionMethod.objects.filter(
            Q(subsector_question__subsector_id=subsector_id) | Q(subsector_question__subsector_id=True)
        )
        all_dynamic = self.get_dynamic_data(
            subsector_question_method
        )

        data = self.get_service_approvals(
            operation_type = 'subsector_clearance',
            subsector_id=subsector_id,
            all_options=all_options,
            all_dynamic=all_dynamic
        )

        return Response(
            {
                "status": True,
                "message": "Data Retrived Successfully",
                "data": data
            },
            status=status.HTTP_200_OK,
        )


    def get_service_approvals(self, *args, **kwargs):
        subsector_id = kwargs['subsector_id']
        operation_type = kwargs['operation_type']
        all_options = kwargs['all_options']
        all_dynamic = kwargs['all_dynamic']
        
        if operation_type == 'subsector_clearance':
            services = {
                "id": "subsector_clearance",
                "label": "Subsector Clearance",
                "fields": []
            }
        
        try:
            if operation_type == 'subsector_clearance':
                subsector_question_mapping = SubSectorQuestionMapping.objects.filter(
                    Q(subsector_id=subsector_id) | Q(subsector_id=True),
                    approval_type__in=['optional', 'mandatory_question'],
                    status='active'
                ).order_by("-mode","display_order")

            if subsector_question_mapping.exists():
                fields = []
                for item in subsector_question_mapping:
                    options = []
                    if all_options and item.id in all_options:
                        options = all_options[item.id]
                    dynamic = {}
                    if all_dynamic and item.id in all_dynamic:
                        dynamic = all_dynamic[item.id]
                    response_data = {
                        'id': item.question.question_tag,
                        'label': item.question.question_text,
                        'type': item.question.question_type,
                        'mode': item.mode,
                        'options': options,
                        'dynamic': dynamic,
                        'next_question_tag': item.next_question_tag
                    }
                    fields.append(response_data)
                services['fields'] = fields
                services['total'] = get_max_questions(services)
                
            return services
        except Exception as e:
            return services

    def get_options_data(self, data):
        all_options = {}
        try:
            if data.exists():
                for itm in data:
                    option_data = {
                        'value': itm.question_options.option_value,
                        'label': itm.question_options.option_display_name,
                        'next_question_tag': itm.next_question_tag
                    }
                    if itm.subsector_question_id not in all_options:
                        all_options[itm.subsector_question_id] = []
                    all_options[itm.subsector_question_id].append(option_data)
                
            return all_options  
        except Exception as e:
            return all_options

    def get_dynamic_data(self, data):
        all_dynamic = {}
        try:
            if data.exists():
                for itm in data:
                    option_data = {
                        'target': itm.target,
                        'method': itm.method,
                    }
                    all_dynamic[itm.subsector_question] = option_data
            return all_dynamic
        except Exception as e:
            return all_dynamic


    def post(self, request):
        pass

class ExemptionApprovalView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            industrial_area_id = request.GET.get('industrial_area_id', '')
            if industrial_area_id:
                exemptiondata = IAExemptionMapping.objects.filter(industrial_area_id=industrial_area_id)
                data = []
                msg = "No exemption available"

                if exemptiondata.exists():
                    department_data = DepartmentList.objects.all()
                    department_dict = {}
                    if department_data:
                        department_dict = { department.id: department.name for department in department_data}
                   
                    msg = "There are some exemptions available"
                    for exemption in exemptiondata:
                        approval = exemption.approval
                        departments = ApprovalDepartmentList.objects.filter(approval=approval, status=True)
                        department_names = []
                        if departments and department_dict:
                            department_names = [{'name': department_dict[department.department_id]} for department in departments]

                        # Append the approval and department data to the result
                        data.append({
                            'approval_id': approval.id,
                            'approval_name': approval.name,
                            'department': department_names
                        })

                return Response(
                    getSuccessfulMessage(data, msg),
                    status=status.HTTP_200_OK,
                )   
            
            return Response(
                getOtherMessage({}, "Parameter Missing"),
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                getOtherMessage({}, global_err_message),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        pass


class GetApprovalByQuestionView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        pass

    def get(self, request):
        sector_id = request.GET.get('sector_id', '')
        subsector_id = request.GET.get('subsector_id', '')
        industrial_area_id = request.GET.get('industrial_area_id', '')
        question_id = request.GET.get('question_id', '')
        answer = request.GET.get('answer', '')
        if question_id and answer and (sector_id or subsector_id):
            if sector_id:
                mappings = SectorQuestionMapping.objects.filter(
                    Q(sector_id=sector_id) | Q(sector_id__isnull=True),
                    question__question_tag=question_id,
                    status = 'active'
                ).values('id').first()
            else:
                mappings = SubSectorQuestionMapping.objects.filter(
                    Q(subsector_id=subsector_id) | Q(subsector_id__isnull=True),
                    question__question_tag=question_id,
                    status = 'active'
                ).values('id').first()

            approvals_data = data = []
            msg = "Data is not available"
            if mappings and sector_id:
                approvals_data = SectorQuestionApproval.objects.filter(
                    question_tag=question_id,
                    sector_question_id=mappings['id'],
                    question_output=answer
                ).values('approval_id')
            elif mappings and subsector_id:
                approvals_data = SubSectorQuestionApproval.objects.filter(
                    question_tag=question_id,
                    subsector_question_id=mappings['id'],
                    question_output=answer
                ).values('approval_id')
            
            if approvals_data.exists():
                for apr in approvals_data:
                    clearance_data = ApprovalDepartmentList.objects.filter(
                        approval_id=apr['approval_id'],
                        criteria=answer,
                        status=True
                    ).first()
                    approvals = ApprovalList.objects.filter(
                        id=apr['approval_id']
                    ).first()
                    if clearance_data and approvals:
                        is_exempt = False
                        if industrial_area_id:
                            checkApprovalExemption = IAExemptionMapping.objects.filter(
                                industrial_area_id=industrial_area_id,
                                approval_id=apr['approval_id']
                            ).first()
                            if checkApprovalExemption:
                                is_exempt = True

                        clearance = ApprovalDepartmentListSerializer(clearance_data).data
                        data.append({
                            "approval_id": approvals.id,
                            "approval_tag": question_id,
                            "name": approvals.name,
                            "phase": approvals.phase,
                            "department": clearance['department']['name'],
                            "is_exempt": is_exempt
                        })
                        msg = "Data is retrived successfully"
                    
            return Response(
                getSuccessfulMessage(data, msg),
                status=status.HTTP_200_OK,
            )
                
        return Response(
            getOtherMessage({}, "Parameter Missing"),
            status=status.HTTP_400_BAD_REQUEST,
        )

class UserApprovalView(APIView):
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        try:
            user = request.user
            sector_id = request.data.get("sector_id")
            subsector_id = request.data.get("subsector_id")
            line_of_business = request.data.get("line_of_business")
            scale_of_industry = request.data.get("scale_of_industry")
            approvals = request.data.get("approvals", [])

            sector = Sector.objects.filter(id=sector_id).first()
            subsector = SubSector.objects.filter(id=subsector_id).first()
            if not sector or not subsector:
                return Response(
                    {"success": False, "message": "Invalid Sector or Subsector"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            existing_approval = UserApprovals.objects.filter(user=user, sector=sector, subsector=subsector).first()

            if existing_approval:
                existing_approval.line_of_business = line_of_business
                existing_approval.scale_of_industry = scale_of_industry
                existing_approval.save()

                UserApprovalItems.objects.filter(user_approval=existing_approval).delete()
            else:
                existing_approval = UserApprovals.objects.create(
                    user=user,
                    sector=sector,
                    subsector=subsector,
                    line_of_business=line_of_business,
                    scale_of_industry=scale_of_industry
                )

            approval_items = [
                UserApprovalItems(user_approval=existing_approval, approval_id=approval["id"])
                for approval in approvals
            ]
            UserApprovalItems.objects.bulk_create(approval_items)

            return Response(
                {"success": True, "message": "User approval updated successfully"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"success": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserCAFServiceView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
            caf_id = request.GET.get("caf_id")
            message= "CAF ID is required"
            if caf_id:
                services = UserCAFService.objects.filter(caf_id=caf_id)
                message= "No service data found."
                if services.exists():
                    serializer = UserCAFServiceSerializer(services, many=True)

                    return Response(
                        {"status": True, "data": serializer.data, "message": "Service data retrieved successfully"},
                        status=status.HTTP_200_OK,
                    )
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )                

class ApprovalPDFView(APIView):
    def get(self, request):
        try:
            sector_id = request.query_params.get('sector_id')
            subsector_id = request.query_params.get('subsector_id')
            request_type = request.query_params.get('request_type',"")
            # Fetch sector-based approvals
            if sector_id and subsector_id:
                sector_approvals = SectorApprovalMapping.objects.filter(
                Q(sector_id=sector_id) | Q(sector_id__isnull=True)).select_related('approval','sector').order_by('approval_type')
                subsector_approvals = SubSectorApprovalMapping.objects.filter(
                Q(subsector_id=subsector_id) | Q(subsector_id__isnull=True)).select_related('approval','subsector').order_by('approval_type')
                sector_name = ""
                if sector_approvals:
                    sector_data = Sector.objects.filter(id=sector_id).first()
                    sector_name = " for " + sector_data.name
                if subsector_approvals:
                    subsector_data = SubSector.objects.filter(id=subsector_id).first()
                    sector_name = sector_name + "<br />" + subsector_data.name 
                data = {
                    "sector": [
                        {
                            "approval_name": s.approval.name,
                            "approval_type": s.approval_type,
                            "duration": s.approval.timelines,
                            "approval_id": s.approval.id
                        }
                        for s in sector_approvals
                    ],
                    "subsector": [
                        {
                            "approval_name": ss.approval.name,
                            "approval_type": ss.approval_type,
                            "duration": ss.approval.timelines,
                            "approval_id": ss.approval.id
                        }
                        for ss in subsector_approvals
                    ]
                }
                if not data:
                    return Response({"status": False, "message": "No approval data found"}, status=status.HTTP_400_BAD_REQUEST)

                # Merge sector + subsector approvals
                all_approvals = data.get("sector", []) + data.get("subsector", [])
                
                all_approval_id = [item['approval_id'] for item in all_approvals]
                all_approval_depatments_list = ApprovalDepartmentList.objects.filter(approval_id__in=all_approval_id)
                all_depatment_data = {}
                if all_approval_depatments_list.exists():
                    departmentList = []
                    for appr in all_approval_depatments_list:
                        if appr.approval_id in all_depatment_data:
                            if appr.department.name not in departmentList:
                                all_depatment_data[appr.approval_id] = all_depatment_data[appr.approval_id] + "/" + appr.department.name
                        else:
                            all_depatment_data[appr.approval_id] = appr.department.name
                            departmentList.append(appr.department.name)
                if request_type == 'data':
                    output = []
                    for item in all_approvals:
                        item_data = {
                            "approval_name" : item["approval_name"],
                            "approval_type" : item["approval_type"],
                            "department" : all_depatment_data[item['approval_id']] if item.get('approval_id') in all_depatment_data else "NA",
                            "duration" : item["duration"]
                        }
                        output.append(item_data)
                    return Response({
                        "status": True,
                        "message": "Approval Data",
                        "data": output
                    }, status=status.HTTP_200_OK)
                        
                styles = getSampleStyleSheet()
                header_style = ParagraphStyle(
                    name="HeaderWrapped",
                    parent=styles["Heading4"],
                    fontSize=9,
                    alignment=1,  # center
                    wordWrap='CJK',
                    textColor=colors.white,
                    fontName='Helvetica-Bold'
                )

                sno_style = ParagraphStyle(
                    name="SNoStyle",
                    parent=styles["Heading4"],
                    fontSize=9,
                    alignment=TA_RIGHT,  # Align to right
                    textColor=colors.black,
                    fontName='Helvetica-Bold',
                    wordWrap='CJK'
                )

                # Build table data (header + rows)
                table_data = [[
                    Paragraph("S.No.", header_style),
                    Paragraph("Name of the Services/Clearance", header_style),
                    Paragraph("Mandatory/Optional", header_style),
                    Paragraph("Name of the Department/<br/>Authority", header_style),
                    Paragraph("Timeline<br/>(as per PSG Act)", header_style)
                ]]

                i=1
                for item in all_approvals:
                    approval_name = item.get("approval_name", "")
                    approval_type = item.get("approval_type", "")
                    department = all_depatment_data[item['approval_id']] if item['approval_id'] in all_depatment_data else "NA"
                    timeline = item.get("duration", "N/A")
                    # table_data.append([Paragraph(str(i) + ". "+approval_name), Paragraph(approval_type.capitalize()), Paragraph(department), Paragraph(timeline)])
                    table_data.append([
                        Paragraph(str(i), sno_style), 
                        Paragraph(approval_name), 
                        Paragraph(approval_type.capitalize()), 
                        Paragraph(department), 
                        Paragraph(timeline)
                    ])

                    i=i+1
                # Create PDF
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                elements = []
                # --- Add logo and title section ---

                logo_path = os.path.join(settings.MEDIA_ROOT, 'MPIDC_Logo.jpg')
                if os.path.exists(logo_path):
                    logo_image = Image(logo_path, width=2.3*inch, height=1*inch)
                else:
                    logo_image = Paragraph("MPIDC Logo Not Found", getSampleStyleSheet()["Normal"])


                title_style = ParagraphStyle(
                    name="CenteredTitle",
                    parent=styles["Title"],
                    alignment=1,  # Center
                    fontSize=14
                )
                title = "List of Approvals" + sector_name
                mpidc_title = Paragraph(title, title_style)

                # Logo + title in a header row
                elements.append(Spacer(1, -50)) 
                header_table = Table([[logo_image, mpidc_title]], colWidths=[2.2*inch, 5*inch])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                # Add header
                elements.append(header_table)
                # Table
                table = Table(table_data, colWidths=[40, 180, 100, 150, 90])

                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0070C0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))

                elements.append(table)
                doc.build(elements, onFirstPage=set_metadata, onLaterPages=set_metadata)
                buffer.seek(0)

                return FileResponse(buffer, as_attachment=True, filename="List_of_All_Approvals.pdf")
            return Response(
                {
                    "status": False,
                    "message": "Bad Request"
                },
                status=status.HTTP_400_BAD_REQUEST ,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class CommonApprovalView(APIView):
    def get(self, request):
        sector_id = request.query_params.get('sector_id')
        subsector_id = request.query_params.get('subsector_id')
        # Fetch sector-based approvals
        if sector_id and subsector_id:
            sector_approvals = SectorApprovalMapping.objects.filter(
            Q(sector_id=sector_id) | Q(sector_id__isnull=True), approval_type='mandatory').select_related('approval','sector').order_by('approval_type')
            subsector_approvals = SubSectorApprovalMapping.objects.filter(
            Q(subsector_id=subsector_id) | Q(subsector_id__isnull=True), approval_type='mandatory').select_related('approval','subsector').order_by('approval_type')
            data = {
                "sector": [
                    {
                        "approval_name": s.approval.name,
                        "approval_type": s.approval_type,
                        "duration": s.approval.timelines,
                        "approval_id": s.approval.id,
                        "phase": s.approval.phase
                    }
                    for s in sector_approvals
                ],
                "subsector": [
                    {
                        "approval_name": ss.approval.name,
                        "approval_type": ss.approval_type,
                        "duration": ss.approval.timelines,
                        "approval_id": ss.approval.id,
                        "phase": ss.approval.phase
                    }
                    for ss in subsector_approvals
                ]
            }
            if not data:
                return Response(
                    {
                        "status": True,
                        "message": "No approval data found",
                        "data":[]
                    }, status=status.HTTP_200_OK
                )

            # Merge sector + subsector approvals
            all_approvals = data.get("sector", []) + data.get("subsector", [])
            all_approval_id = [item['approval_id'] for item in all_approvals]
            all_approval_depatments_list = ApprovalDepartmentList.objects.filter(approval_id__in=all_approval_id)
            all_depatment_data = {}
            if all_approval_depatments_list.exists():
                departmentList = []
                for appr in all_approval_depatments_list:
                    if appr.approval_id in all_depatment_data:
                        if appr.department.name not in departmentList:
                            all_depatment_data[appr.approval_id] = all_depatment_data[appr.approval_id] + "/" + appr.department.name
                    else:
                        all_depatment_data[appr.approval_id] = appr.department.name
                        departmentList.append(appr.department.name)
            output = []
            for item in all_approvals:
                item_data = {
                    "approval_id": item["approval_id"],
                    "approval_tag": "approval_"+str(item["approval_id"]),
                    "name": item["approval_name"],
                    "phase": item['phase'],
                    "department":  all_depatment_data[item['approval_id']] if item.get('approval_id') in all_depatment_data else "NA",
                    "is_exempt": False
                }
                output.append(item_data)
            return Response({
                "status": True,
                "message": "Approval Data",
                "data": output
            }, status=status.HTTP_200_OK)
        return Response(
            {
                "status": False,
                "message": "Bad Request"
            },
            status=status.HTTP_400_BAD_REQUEST ,
        )

class DownloadApprovalView(APIView):
    def post(self, request):
        try:
            user = request.user
            sector_id = request.data.get("sector_id")
            subsector_id = request.data.get("subsector_id")
            approvals = request.data.get("approvals", [])
            
            if sector_id and subsector_id and approvals:
                sector_name = "List of Approvals"
                sector_data = Sector.objects.filter(id=sector_id).first()
                subsector_data = SubSector.objects.filter(id=subsector_id).first()
                if sector_data:
                    sector_name = " for " + sector_data.name
                
                if subsector_data:    
                    sector_name = sector_name + "<br />" + subsector_data.name 

                ids = sorted(set(item["id"] for item in approvals))
                user_approvals = ApprovalList.objects.filter(id__in=ids)
                data=[
                        {
                            "approval_name": s.name,
                            "duration": s.timelines,
                            "approval_id": s.id
                        }
                        for s in user_approvals
                    ]
                
                all_approval_depatments_list = ApprovalDepartmentList.objects.filter(approval_id__in=ids)
                all_depatment_data = {}
                if all_approval_depatments_list.exists():
                    departmentList = []
                    for appr in all_approval_depatments_list:
                        if appr.approval_id in all_depatment_data:
                            if appr.department.name not in departmentList:
                                all_depatment_data[appr.approval_id] = all_depatment_data[appr.approval_id] + "/" + appr.department.name
                        else:
                            all_depatment_data[appr.approval_id] = appr.department.name
                            departmentList.append(appr.department.name)
                styles = getSampleStyleSheet()
                header_style = ParagraphStyle(
                    name="HeaderWrapped",
                    parent=styles["Heading4"],
                    fontSize=9,
                    alignment=1,  # Center align
                    wordWrap='CJK',  # Wrap for Asian/long text
                    textColor=colors.white,
                    fontName='Helvetica-Bold',
                    leading=10,  # Line height
                    spaceAfter=4
                )
                table_data = [[
                    Paragraph("S.No.", header_style),
                    Paragraph("Name of the Services/Clearance", header_style),
                    Paragraph("Name of the Department/<br/>Authority", header_style),
                    Paragraph("Timeline<br/>(as per PSG Act)", header_style)
                ]]

                sno_style = ParagraphStyle(
                    name="SNoStyle",
                    parent=styles["Heading4"],
                    fontSize=9,
                    alignment=TA_RIGHT,  # Align to right
                    textColor=colors.black,
                    fontName='Helvetica-Bold',
                    wordWrap='CJK'
                )

                i=1
                for item in data:
                    approval_name = item.get("approval_name", "")
                    department = all_depatment_data[item['approval_id']] if item['approval_id'] in all_depatment_data else "NA"
                    timeline = item.get("duration", "N/A")
                    # table_data.append([Paragraph(str(i) + ". "+approval_name), Paragraph(department), Paragraph(timeline)])
                    table_data.append([
                        Paragraph(str(i), sno_style), 
                        Paragraph(approval_name), 
                        Paragraph(department), 
                        Paragraph(timeline)
                    ])
                    i=i+1
                # Create PDF
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                elements = []
                # --- Add logo and title section ---
                # logo_url = "https://geoportal.mp.gov.in/mpidc/images/MPIDC_Logo.jpg"
                # response = requests.get(logo_url)
                # logo_image = Image(BytesIO(response.content), width=1.4*inch, height=1.2*inch)

                logo_path = os.path.join(settings.MEDIA_ROOT, 'MPIDC_Logo.jpg')
                if os.path.exists(logo_path):
                    logo_image = Image(logo_path, width=1.4*inch, height=1.2*inch)
                else:
                    logo_image = Paragraph("MPIDC Logo Not Found", getSampleStyleSheet()["Normal"])


                title_style = ParagraphStyle(
                    name="CenteredTitle",
                    parent=styles["Title"],
                    alignment=1,  # Center
                    fontSize=14
                )
                title = "List of Approvals" + sector_name
                mpidc_title = Paragraph(title, title_style)

                # Logo + title in a header row
                elements.append(Spacer(1, -50)) 
                header_table = Table([[logo_image, mpidc_title]], colWidths=[1.5*inch, 4.4*inch])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
                # Add header
                elements.append(header_table)
                # Table
                table = Table(table_data, colWidths=[40, 230, 200, 90])
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0070C0")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))

                elements.append(table)
                doc.build(elements, onFirstPage=set_metadata, onLaterPages=set_metadata)
                buffer.seek(0)

                return FileResponse(buffer, as_attachment=True, filename="List_of_My_Approval.pdf")
            return Response(
                {
                    "success": False,
                    "message": "Parameter missing"
                },status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
def set_metadata(pdf_canvas, doc):
    pdf_canvas.setAuthor("MPIDC")
    pdf_canvas.setTitle("List of All Approvals")
    pdf_canvas.setSubject("List of All Approvals")
    pdf_canvas.setCreator("MPIDC")


def get_max_questions(section):
    fields = section["fields"]
    field_map = build_field_map(fields)
    
    max_questions = 0
    for field in fields:
        path_length = dfs(field_map, field["id"], set())
        max_questions = max(max_questions, path_length)
    return max_questions
    
def build_field_map(fields):
    return {field["id"]: field for field in fields}

def dfs(field_map, current_id, visited):
    if current_id in visited:
        return 0  # Avoid cycles

    visited.add(current_id)
    field = field_map.get(current_id)
    if not field:
        return 0

    max_depth = 0
    for option in field.get("options", []):
        next_tag = option.get("next_question_tag")
        if next_tag:
            depth = dfs(field_map, next_tag, visited.copy())
            max_depth = max(max_depth, depth)
    return 1 + max_depth 