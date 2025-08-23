from rest_framework import status
from rest_framework.test import APITestCase
from authentication.models import User
from sws.models import Sector

class StaticDataAPIViewTest(APITestCase):
    def test_get_static_data(self):
        """
        Test case for the GET request to /static-data/ endpoint.
        It should return static data with correct structure.
        """
        url = '/static-data/'  # assuming this is your endpoint for StaticDataAPIView

        # Sending a GET request to the static-data API endpoint
        response = self.client.get(url)

        # Assert the status code is 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that the response has a 'status' key with value True
        self.assertEqual(response.data['status'], True)

        # Assert that the response data contains 'data' key
        self.assertIn('data', response.data)

        # Assert the length of data returned is 2
        self.assertEqual(len(response.data['data']), 2)

        # Validate the structure of one item in the data list
        first_item = response.data['data'][0]
        self.assertIn('service_name', first_item)
        self.assertIn('department_name', first_item)
        self.assertIn('exemption', first_item)
        self.assertIn('phase_applied', first_item)

        # Validate values of the first record
        self.assertEqual(first_item['service_name'], "Service A")
        self.assertEqual(first_item['department_name'], "Department 1")
        self.assertEqual(first_item['exemption'], "Exemption 1")
        self.assertEqual(first_item['phase_applied'], "Phase 1")

    def test_get_static_data_no_data(self):
        """
        Test case where no data is available (optional, for example, if data was deleted).
        """
        url = '/static-data/'  # assuming this is your endpoint for StaticDataAPIView

        # Empty the static data (if you're mocking it)
        # This would be custom logic if you have the possibility of no data available.

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], True)
        self.assertEqual(len(response.data['data']), 0)

class ApprovalCreateAPIViewTest(APITestCase):

    def setUp(self):
        """
        Setup initial data before running tests. Creating dummy user and sector.
        """
        self.user = User.objects.create_user(
            username='testuser', password='testpassword'
        )
        self.sector = Sector.objects.create(name="Dummy Sector")
        self.url = '/create-approval/'  # assuming this is your endpoint for creating approval

    def test_create_service_exemption(self):
        """
        Test case for the POST request to /create-approval/ endpoint to create ServiceExemption.
        """
        data = {
            'service_exemption': {
                'sector': self.sector.id,
                'user': self.user.id,
                'sub_sector': 'Sub Sector 1',
                'line_of_business': 'Business A',
                'industry_scale': 'Large',
                'investment_amount': 500000,
                'land_needed': True,
                'land_applicability': 'High',
                'area': 'Area A',
                'change_land_use': 'Yes',
                'change_land_applicability': 'Applicable',
                'land_mutation': 'Yes',
                'land_mutation_applicability': 'Applicable',
                'temporary_service_connection': 'Yes',
                'water_connection': 'Yes',
                'permanent_service_connection': 'Yes'
            },
            'common_approval': {
                'is_property_registration': True,
                'tree_felling_noc': False,
                'tree_felling_applicability': 'Not Applicable',
                'tree_transit_noc': False,
                'tree_transit_applicability': False,
                'land_applicability': 'High',
                'fire_noc': 'N/A',
                'factory_plan': 'Factory A',
                'is_road_cutting_permission': True,
                'estabilish_consent': 'Consent A',
                'operate_consent': 'Consent B',
                'is_electric_installation': True,
                'is_inspection_approval': True
            },
            'license_contract': {
                'is_license_contract': True,
                'is_migrate_contract': False,
                'is_bocw_contract': True,
                'is_contract_labour': False,
                'is_boiler_registration': True,
                'is_labour_registration': True,
                'is_exporter': False
            },
            'sub_sector_approval': {
                'is_homologation_certificate': True,
                'certificate_type': 'Certificate A',
                'sale_certificate': 'Sale A',
                'road_certificate': 'Road A',
                'temporary_vehicle_registration': 'Temp Reg A',
                'permanenet_vehicle_registration': 'Perm Reg A',
                'internation_certification': 'Cert A',
                'inhouse_registartion': False
            }
        }
