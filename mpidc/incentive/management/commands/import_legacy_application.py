import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from incentive.models import *
from datetime import datetime, date
from django.db import transaction
from sws.models import CustomerIntentionProject, Activity, Sector
from django.utils import timezone

class Command(BaseCommand):
    help = 'import_legacy_application'

    def handle(self, *args, **kwargs):
        get_incentive_data = IPAUnitDataMaster.objects.all().order_by("intention_date","slec_meeting_no","sanctioned_date")
        if get_incentive_data.exists():
            try:
                with transaction.atomic():
                    for itm in get_incentive_data:
                        intention_id = itm.intention_id.strip()
                        intention_date = parse_and_format_date(itm.intention_date)
                        production_date = parse_and_format_date(itm.date_of_production)
                        period_from = parse_and_format_date(itm.eligibility_start_date)
                        period_to = parse_and_format_date(itm.eligibility_end_date)
                        slec_meeting_date = parse_and_format_date(itm.slec_meeting_date)
                        self.stdout.write(self.style.SUCCESS(slec_meeting_date))
                        slec_meeting_number = itm.slec_meeting_no
                        unit_name = itm.unit_name
                        unit_type = itm.unit_type
                        block_priority = itm.block_priority
                        bipa = itm.bipa
                        ybipa = itm.ybipa
                        products = itm.product_name
                        eligible_investment = itm.eligible_investment
                        activity = Activity.objects.filter(name="Manufacturing").first()
                        if activity:
                            sector =Sector.objects.filter(incentive_name=itm.sector, activity=activity).first()
                            if not sector:
                                sector = None
                        else:
                            activity = None
                            sector = None
                        intention_data = CustomerIntentionProject.objects.filter(intention_id = intention_id).first()
                        if not intention_data:
                            intention_data = CustomerIntentionProject.objects.create(
                                intention_id=intention_id,
                                created_at= intention_date if intention_date else timezone.now() ,
                                product_name= unit_name,
                                company_name = unit_name,
                                investment_type= unit_type,
                                address=unit_name,
                                product_proposed_date= production_date,
                                sectors= sector,
                                activities=activity,
                                activity = activity.name if activity else "",
                                sector = sector.incentive_name if sector else "",
                                intention_type= "incentive",
                                status="new"
                            )
                        slec_caf_data = True
                        all_caf_data = IncentiveCAF.objects.filter(intention_id=intention_data.id).order_by("id")
                        if all_caf_data.exists():
                            for caf in all_caf_data:
                                caf_slec_data = IncentiveSlecOrder.objects.filter(caf=caf, 
                                    date_of_slec_meeting=slec_meeting_date,
                                    slec_meeting_number=slec_meeting_number).first()
                                if caf_slec_data:
                                    slec_caf_data = False
                                    message = "slec exist with same date and meeting number"
                                    break
                                else:
                                    caf.status = "Approve Sanction Order"
                                    caf.save()
                        if slec_caf_data:
                            caf_data = IncentiveCAF.objects.create(
                                intention_id=intention_data.id,
                                status="Pending For Request Claim",
                                acknowledgement=True,
                                is_offline=True
                            )

                            caf_project_data = InCAFProject.objects.create(
                                unit_name=unit_name,
                                intention_id=intention_id,
                                date_of_intention= intention_date if intention_date else timezone.now(),
                                address_of_unit=unit_name,
                                sector= sector,
                                activity=activity,
                                activity_name = activity.name if activity else "",
                                sector_name = sector.name if sector else "",
                                unit_type=unit_type,
                                caf=caf_data
                            )

                            caf_investment_data = InCAFInvestment.objects.create(
                                comm_production_date=production_date,
                                period_from=period_from,
                                period_to=period_to,
                                caf=caf_data
                            )

                            caf_agenda_data = IncentiveAgenda.objects.create(
                                comm_production_date=production_date,
                                unit_name=unit_name,
                                address_of_unit=unit_name,
                                category_of_block=block_priority,
                                sector= sector,
                                activity=activity,
                                activity_name = activity.name if activity else "",
                                sector_name = sector.name if sector else "",
                                application_filling_date=intention_date if intention_date else timezone.now(),
                                first_production_year = get_year_from_date(period_from),
                                unit_type = unit_type,
                                eligible_investment_plant_machinery=eligible_investment,
                                bipa=bipa,
                                yearly_bipa=ybipa,
                                ipp="IPA-2014",
                                caf=caf_data,
                                status="Approved"
                            )

                            caf_slec_data = IncentiveSlecOrder.objects.create(
                                commencement_date=production_date,
                                unit_name=unit_name,
                                unit_type=unit_type,
                                sector= sector,
                                activity=activity,
                                activity_name = activity.name if activity else "",
                                sector_name = sector.name if sector else "",
                                category_of_block=block_priority,
                                date_of_slec_meeting=slec_meeting_date,
                                slec_meeting_number=slec_meeting_number,
                                eligible_investment_plant_machinery=eligible_investment,
                                bipa=bipa,
                                yearly_bipa=ybipa,
                                eligibility_from=period_from,
                                eligibility_to=period_to,
                                caf=caf_data,
                                status="Approved"
                            )
                        
                            if products:
                                caf_product_data = InCAFProduct.objects.create(
                                    product_name=products,
                                    caf=caf_data
                                )

                                caf_agenda_product_data = IncentiveAgendaProduct.objects.create(
                                    product_name=products,
                                    agenda=caf_agenda_data,
                                    comm_production_date=production_date
                                )

                                caf_slec_product_data = IncentiveSlecProduct.objects.create(
                                    product_name=products,
                                    slec_order=caf_slec_data,
                                    comm_production_date=production_date
                                )

                            years = generate_financial_years(period_from)
                            if years:
                                for claim_yrs in years:
                                    caf_slec_year_data = IncentiveSlecYealy.objects.filter(
                                        slec_order=caf_slec_data,
                                        incentive_year=claim_yrs
                                    ).first()
                                    if not caf_slec_year_data:
                                        caf_slec_year_data = IncentiveSlecYealy.objects.create(
                                            slec_order=caf_slec_data,
                                            incentive_year=claim_yrs,
                                        )

                        else:
                            caf_data = IncentiveCAF.objects.filter(id=caf_slec_data.caf_id).first()

                        if caf_slec_data:
                            claim_year = itm.claim_fy
                            current_financial_year = get_current_financial_year()
                            if current_financial_year == claim_year:
                                caf_data.status ="Pending For Request Claim"
                                caf_data.save()
                            if claim_year:
                                caf_slec_year_data = IncentiveSlecYealy.objects.filter(
                                    slec_order=caf_slec_data,
                                    incentive_year=claim_year
                                ).first()
                                if not caf_slec_year_data:
                                    caf_slec_year_data = IncentiveSlecYealy.objects.create(
                                        slec_order=caf_slec_data,
                                        incentive_year=claim_year,
                                    )
                                
                                claim_basic_data = IncentiveClaimBasic.objects.filter(
                                    incentive_slec_year_id=caf_slec_year_data.id,
                                    year_of_claimed_assistance=claim_year
                                ).first()
                                if not claim_basic_data:
                                    claim_basic_data = IncentiveClaimBasic.objects.create(
                                        year_of_claimed_assistance=claim_year,
                                        acknowledgement=True,
                                        status='Submitted',
                                        incentive_slec_year_id=caf_slec_year_data.id,
                                        action_date=timezone.now(),
                                        action_by_name = "script",
                                        action_by_id = 1,
                                        apply_date = timezone.now()
                                    )
                                
                                if products:
                                    slec_product_data = IncentiveSlecProduct.objects.filter(
                                        product_name=products,
                                        slec_order=caf_slec_data
                                    ).first()
                                    if slec_product_data:
                                        claim_product_data = IncentiveClaimProductDetail.objects.filter(
                                            incentive_slec_product= slec_product_data,
                                            incentive_claim_basic=claim_basic_data
                                        )
                                        if not claim_product_data:
                                            claim_product_data= IncentiveClaimProductDetail.objects.create(
                                                incentive_slec_product= slec_product_data,
                                                incentive_claim_basic=claim_basic_data,
                                                action_date=timezone.now(),
                                                apply_date = timezone.now(),
                                            )
                                sanction_date = parse_and_format_date(itm.sanctioned_date)
                                sanction_amount = itm.sanctioned_amount
                                check_sanction = False
                                if sanction_date and sanction_amount:
                                    incentive_sanction_order = IncentiveSanctionOrder.objects.filter(
                                        incentive_claim=claim_basic_data,
                                        sanction_order_created_date=sanction_date,
                                        total_sanctioned_assistance_amount= sanction_amount,
                                        intention = intention_data,
                                        year_of_claimed_assistance=claim_year,
                                        incentive_caf = caf_data
                                    ).first()
                                    if not incentive_sanction_order:
                                        incentive_sanction_order = IncentiveSanctionOrder.objects.create(
                                            incentive_claim=claim_basic_data,
                                            sanction_order_created_date=sanction_date,
                                            unit_name = unit_name,
                                            total_sanctioned_assistance_amount= sanction_amount,
                                            is_old_record = True,
                                            acknowledgement=True,
                                            status='Approved',
                                            action_date=timezone.now(),
                                            intention = intention_data,
                                            year_of_claimed_assistance = claim_year,
                                            incentive_caf = caf_data
                                        )
                                    check_sanction = True
                                if not check_sanction:
                                    incentive_sanction_order = IncentiveSanctionOrder.objects.filter(
                                        incentive_claim=claim_basic_data,
                                        intention = intention_data,
                                        year_of_claimed_assistance=claim_year
                                    ).first()
                                    if not incentive_sanction_order:
                                        incentive_sanction_order = IncentiveSanctionOrder.objects.create(
                                            incentive_claim=claim_basic_data,
                                            sanction_order_created_date=None,
                                            unit_name = unit_name,
                                            total_sanctioned_assistance_amount= 0,
                                            is_old_record = True,
                                            acknowledgement=True,
                                            status='Approved',
                                            action_date=timezone.now(),
                                            intention = intention_data,
                                            year_of_claimed_assistance = claim_year
                                        )
                                disbursement_date = parse_and_format_date(itm.disbursement_date)
                                disbursement_amount = itm.disbursed_amount
                                if disbursement_date and disbursement_amount:
                                    sanction_disbursement_data = IncentiveDisbursement.objects.filter(
                                        incentive_sanction_order=incentive_sanction_order,
                                        disbursement_date=disbursement_date,
                                        disbursed_amount= disbursement_amount,
                                        intention = intention_data,
                                        year_of_claimed_assistance=claim_year
                                    ).first()
                                    if not sanction_disbursement_data:
                                        incentive_sanction_order = IncentiveDisbursement.objects.create(
                                            incentive_sanction_order=incentive_sanction_order,
                                            disbursement_date=disbursement_date.strip(),
                                            disbursed_amount= disbursement_amount,
                                            intention = intention_data,
                                            year_of_claimed_assistance=claim_year,
                                            action_date=timezone.now()
                                        )
                self.stdout.write(self.style.SUCCESS("Import completed successfully."))
            except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Import failed: {e}"))
        return               


def parse_and_format_date(date_str): 
    try:
        dt = datetime.strptime(str(date_str), "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def get_year_from_date(date):
    try:
        dt = datetime.fromisoformat(str(date))
        return dt.strftime("%Y")
    except Exception:
        return None     

def get_current_financial_year():
    today = date.today()
    year = today.year
    if today.month >= 4:
        start_year = year
        end_year = year + 1
    else:  # Jan, Feb, Mar
        start_year = year - 1
        end_year = year
    return f"{start_year}-{str(end_year)[-2:]}"


def generate_financial_years(period_from: str):
    from_date = datetime.strptime(period_from, "%Y-%m-%d")
    start_year = from_date.year if from_date.month >= 4 else from_date.year - 1

    financial_years = []

    for i in range(7):
        fy = f"{start_year + i}-{str(start_year + i + 1)[-2:]}"
        financial_years.append(fy)

    return financial_years
