import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from incentive.models import IncentiveOfflineApplications
from datetime import datetime
from django.db import transaction
from master.models import ConfigurationsModel


class Command(BaseCommand):
    help = 'import_excel'

    def handle(self, *args, **kwargs):
        # Path to Excel file inside media folder
        get_file_name = ConfigurationsModel.objects.filter(parameter_name="incentiveOfflineApplication").first()
        if get_file_name:
            excel_file = os.path.join(settings.MEDIA_ROOT, get_file_name.value)
            if os.path.exists(excel_file):
                self.stdout.write(f"Reading data from: {excel_file}")
                df = pd.read_excel(excel_file)
                try:
                    with transaction.atomic():
                        for index, row in df.iterrows():
                            intention_id = row['intention_id'].strip()
                            slec_meeting_no = row['slec_meeting_no'].strip()
                            checkData = IncentiveOfflineApplications.objects.filter(
                                intention_id = intention_id,
                                slec_meeting_no=slec_meeting_no).first()
                            if not checkData:
                                priority_block = "Non Priority"
                                if row['block_priority'].lower() == 'y' or row['block_priority'].lower() == 'yes':
                                    priority_block = "Priority"
                                IncentiveOfflineApplications.objects.create(
                                    intention_id=intention_id,
                                    intention_date=pd.to_datetime(row['intention_date'], errors='coerce'),
                                    unit_name=row['unit_name'],
                                    unit_type=row['unit_type'],
                                    activity='Manufacturing',
                                    sector=row['sector'],
                                    block_priority=priority_block,
                                    date_of_production=pd.to_datetime(row['date_of_production'], errors='coerce'),
                                    slec_meeting_date=pd.to_datetime(row['slec_meeting_date'], errors='coerce'),
                                    slec_meeting_no=slec_meeting_no,
                                    eligible_investment=row['eligible_investment'],
                                    bipa=row['bipa'],
                                    ybipa=row['ybipa'],
                                    eligibility_start_date = row['eligibility_start_date'],
                                    eligibility_end_date =row['eligibility_end_date']
                                )
                                self.stdout.write(f"Imported row {index + 1}")
                    self.stdout.write(self.style.SUCCESS("Import completed successfully."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Import failed: {e}"))
            else:
                self.stdout.write(self.style.ERROR(f"File not found: {excel_file}"))
        else:
            self.stdout.write(self.style.ERROR(f"Parameter need to set in configuratiosn"))
        return