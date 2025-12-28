import unittest
from datetime import datetime
from unittest.mock import patch

from pygeai.core.base.mappers import ModelMapper, ErrorMapper
from pygeai.core.common.exceptions import APIError
from pygeai.core.models import UsageLimit
from pygeai.organization.limits.managers import UsageLimitManager
from pygeai.core.handlers import ErrorHandler


class TestUsageLimitManager(unittest.TestCase):
    """
    python -m unittest pygeai.tests.organization.limits.test_managers.TestUsageLimitManager
    """

    def setUp(self):
        self.manager = UsageLimitManager(organization_id="4aa15b61-d3c7-4a5c-99b8-052d18a04ff2")
        self.usage_limit = UsageLimit(
            id="4bb78b5a-07ea-4d15-84d6-e0baee53ff61",
            hard_limit=2000.0,
            related_entity_name="Pia.Data.Organization",
            remaining_usage=2000.0,
            renewal_status="Renewable",
            soft_limit=1000.0,
            status=1,
            subscription_type="Monthly",
            usage_unit="Cost",
            used_amount=0.0,
            valid_from=datetime(2025, 2, 20, 19, 33, 0),
            valid_until=datetime(2025, 3, 1, 0, 0, 0)
        )
        self.project_id = "1956c032-3c66-4435-acb8-6a06e52f819f"
        self.error_response = {"errors": [{"code": "400", "message": "Invalid request"}]}

    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_organization_usage_limit")
    def test_set_organization_usage_limit(self, mock_set_limit):
        mock_set_limit.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.set_organization_usage_limit(self.usage_limit)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_set_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            usage_limit=self.usage_limit.to_dict()
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_organization_usage_limit")
    def test_set_organization_usage_limit_error(self, mock_set_limit):
        mock_set_limit.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.set_organization_usage_limit(self.usage_limit)

        self.assertIn("Error received while setting organization usage limit", str(context.exception))
        mock_set_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            usage_limit=self.usage_limit.to_dict()
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_organization_latest_usage_limit")
    def test_get_latest_usage_limit_from_organization(self, mock_get_limit):
        mock_get_limit.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.get_latest_usage_limit_from_organization()

        self.assertEqual(result.id, self.usage_limit.id)
        mock_get_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_organization_latest_usage_limit")
    def test_get_latest_usage_limit_from_organization_error(self, mock_get_limit):
        mock_get_limit.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_latest_usage_limit_from_organization()

        self.assertIn("Error received while retrieving latest organization usage limit", str(context.exception))
        mock_get_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_all_usage_limits_from_organization")
    def test_get_all_usage_limits_from_organization_success(self, mock_get_limits):
        response_data = {"limits": [self.usage_limit.to_dict()]}
        usage_limit_list = [self.usage_limit]
        mock_get_limits.return_value = response_data

        with patch.object(ModelMapper, 'map_to_usage_limit_list', return_value=usage_limit_list):
            result = self.manager.get_all_usage_limits_from_organization()

        self.assertEqual(result, usage_limit_list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, self.usage_limit.id)
        mock_get_limits.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_all_usage_limits_from_organization")
    def test_get_all_usage_limits_from_organization_error(self, mock_get_limits):
        mock_get_limits.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_all_usage_limits_from_organization()

        self.assertIn("Error received while retrieving all organization usage limits", str(context.exception))
        mock_get_limits.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_organization_hard_limit")
    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_organization_soft_limit")
    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_organization_renewal_status")
    def test_update_organization_usage_limit(self, mock_renewal, mock_soft, mock_hard):
        mock_hard.return_value = self.usage_limit.to_dict()
        mock_soft.return_value = self.usage_limit.to_dict()
        mock_renewal.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.update_organization_usage_limit(self.usage_limit)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_hard.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            limit_id=self.usage_limit.id,
            hard_limit=self.usage_limit.hard_limit
        )
        mock_soft.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            limit_id=self.usage_limit.id,
            soft_limit=self.usage_limit.soft_limit
        )
        mock_renewal.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            limit_id=self.usage_limit.id,
            renewal_status=self.usage_limit.renewal_status
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_organization_hard_limit")
    def test_update_organization_usage_limit_error(self, mock_hard):
        error_usage_limit = UsageLimit(
            id=self.usage_limit.id,
            hard_limit=2000.0,
            related_entity_name="Pia.Data.Organization",
            status=1,
            subscription_type="Monthly",
            usage_unit="Cost",
            valid_from=datetime(2025, 2, 20, 19, 33, 0),
            valid_until=datetime(2025, 3, 1, 0, 0, 0)
        )
        mock_hard.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.update_organization_usage_limit(error_usage_limit)

        self.assertIn("Error received while updating organization usage limit", str(context.exception))
        mock_hard.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            limit_id=error_usage_limit.id,
            hard_limit=error_usage_limit.hard_limit
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.delete_usage_limit_from_organization")
    def test_delete_usage_limit_from_organization(self, mock_delete):
        mock_delete.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.delete_usage_limit_from_organization(self.usage_limit.id)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_delete.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            limit_id=self.usage_limit.id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.delete_usage_limit_from_organization")
    def test_delete_usage_limit_from_organization_error(self, mock_delete):
        mock_delete.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.delete_usage_limit_from_organization(self.usage_limit.id)

        self.assertIn("Error received while deleting organization usage limit", str(context.exception))
        mock_delete.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            limit_id=self.usage_limit.id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_project_usage_limit")
    def test_set_project_usage_limit(self, mock_set_limit):
        mock_set_limit.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.set_project_usage_limit(self.project_id, self.usage_limit)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_set_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id,
            usage_limit=self.usage_limit.to_dict()
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_project_usage_limit")
    def test_set_project_usage_limit_error(self, mock_set_limit):
        mock_set_limit.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.set_project_usage_limit(self.project_id, self.usage_limit)

        self.assertIn("Error received while setting project usage limit", str(context.exception))
        mock_set_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id,
            usage_limit=self.usage_limit.to_dict()
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_all_usage_limits_from_project")
    def test_get_all_usage_limits_from_project_success(self, mock_get_limits):
        mock_get_limits.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.get_all_usage_limits_from_project(self.project_id)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_get_limits.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_all_usage_limits_from_project")
    def test_get_all_usage_limits_from_project_error(self, mock_get_limits):
        mock_get_limits.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_all_usage_limits_from_project(self.project_id)

        self.assertIn("Error received while retrieving all project usage limits", str(context.exception))
        mock_get_limits.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_latest_usage_limit_from_project")
    def test_get_latest_usage_limit_from_project(self, mock_get_limit):
        mock_get_limit.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.get_latest_usage_limit_from_project(self.project_id)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_get_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_latest_usage_limit_from_project")
    def test_get_latest_usage_limit_from_project_error(self, mock_get_limit):
        mock_get_limit.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_latest_usage_limit_from_project(self.project_id)

        self.assertIn("Error received while retrieving latest project usage limit", str(context.exception))
        mock_get_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_active_usage_limit_from_project")
    def test_get_active_usage_limit_from_project_success(self, mock_get_limit):
        mock_get_limit.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.get_active_usage_limit_from_project(self.project_id)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_get_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.get_active_usage_limit_from_project")
    def test_get_active_usage_limit_from_project_error(self, mock_get_limit):
        mock_get_limit.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_active_usage_limit_from_project(self.project_id)

        self.assertIn("Error received while retrieving active project usage limit", str(context.exception))
        mock_get_limit.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.delete_usage_limit_from_project")
    def test_delete_usage_limit_from_project(self, mock_delete):
        mock_delete.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.delete_usage_limit_from_project(self.project_id, self.usage_limit)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_delete.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id,
            limit_id=self.usage_limit.id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.delete_usage_limit_from_project")
    def test_delete_usage_limit_from_project_error(self, mock_delete):
        mock_delete.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.delete_usage_limit_from_project(self.project_id, self.usage_limit)

        self.assertIn("Error received while deleting project usage limit", str(context.exception))
        mock_delete.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id,
            limit_id=self.usage_limit.id
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_hard_limit_for_active_usage_limit_from_project")
    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_soft_limit_for_active_usage_limit_from_project")
    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_project_renewal_status")
    def test_update_project_usage_limit(self, mock_renewal, mock_soft, mock_hard):
        mock_hard.return_value = self.usage_limit.to_dict()
        mock_soft.return_value = self.usage_limit.to_dict()
        mock_renewal.return_value = self.usage_limit.to_dict()

        with patch.object(ModelMapper, 'map_to_usage_limit', return_value=self.usage_limit):
            result = self.manager.update_project_usage_limit(self.project_id, self.usage_limit)

        self.assertEqual(result.id, self.usage_limit.id)
        mock_hard.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id,
            limit_id=self.usage_limit.id,
            hard_limit=self.usage_limit.hard_limit
        )
        mock_soft.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id,
            limit_id=self.usage_limit.id,
            soft_limit=self.usage_limit.soft_limit
        )
        mock_renewal.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id,
            limit_id=self.usage_limit.id,
            renewal_status=self.usage_limit.renewal_status
        )

    @patch("pygeai.organization.limits.clients.UsageLimitClient.set_hard_limit_for_active_usage_limit_from_project")
    def test_update_project_usage_limit_error(self, mock_hard):
        error_usage_limit = UsageLimit(
            id=self.usage_limit.id,
            hard_limit=2000.0,
            related_entity_name="Pia.Data.Organization",
            status=1,
            subscription_type="Monthly",
            usage_unit="Cost",
            valid_from=datetime(2025, 2, 20, 19, 33, 0),
            valid_until=datetime(2025, 3, 1, 0, 0, 0)
        )
        mock_hard.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Invalid request"):
                with self.assertRaises(APIError) as context:
                    self.manager.update_project_usage_limit(self.project_id, error_usage_limit)

        self.assertIn("Error received while updating project usage limit", str(context.exception))
        mock_hard.assert_called_once_with(
            organization=self.manager._UsageLimitManager__organization_id,
            project=self.project_id,
            limit_id=error_usage_limit.id,
            hard_limit=error_usage_limit.hard_limit
        )
