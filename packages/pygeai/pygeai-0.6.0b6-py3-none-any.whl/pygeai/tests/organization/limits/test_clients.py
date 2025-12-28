import unittest
from json import JSONDecodeError
from unittest.mock import patch
from pydantic import ValidationError

from pygeai.organization.limits.clients import UsageLimitClient
from pygeai.core.common.exceptions import InvalidAPIResponseException, APIError
from pygeai.core.models import UsageLimit
from pygeai.organization.limits.endpoints import SET_ORGANIZATION_USAGE_LIMIT_V2, GET_ORGANIZATION_LATEST_USAGE_LIMIT_V2, \
    GET_ALL_ORGANIZATION_USAGE_LIMITS_V2, DELETE_ORGANIZATION_USAGE_LIMIT_V2, SET_ORGANIZATION_HARD_LIMIT_V2, \
    SET_ORGANIZATION_SOFT_LIMIT_V2, SET_ORGANIZATION_RENEWAL_STATUS_V2, SET_PROJECT_USAGE_LIMIT_V2, \
    GET_ALL_PROJECT_USAGE_LIMIT_V2, GET_LATEST_PROJECT_USAGE_LIMIT_V2, GET_PROJECT_ACTIVE_USAGE_LIMIT_V2, \
    DELETE_PROJECT_USAGE_LIMIT_V2, SET_PROJECT_HARD_LIMIT_V2, SET_PROJECT_SOFT_LIMIT_V2, \
    SET_PROJECT_RENEWAL_STATUS_V2


class TestUsageLimitClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.organization.limits.test_clients.TestUsageLimitClient
    """

    def setUp(self):
        self.client = UsageLimitClient()
        self.organization = "org-123"
        self.project = "proj-456"
        self.limit_id = "limit-789"
        self.valid_usage_limit = {
            "subscriptionType": "Monthly",
            "usageUnit": "Requests",
            "softLimit": 1000.0,
            "hardLimit": 2000.0,
            "renewalStatus": "Renewable"
        }
        self.valid_response = {
            "id": self.limit_id,
            "subscriptionType": "Monthly",
            "usageUnit": "Requests",
            "softLimit": 1000.0,
            "hardLimit": 2000.0,
            "renewalStatus": "Renewable",
            "status": 1,
            "validFrom": "2025-05-28T12:00:00Z",
            "validUntil": "2025-06-28T12:00:00Z"
        }

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_organization_usage_limit_success(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = self.valid_response

        result = self.client.set_organization_usage_limit(self.organization, self.valid_usage_limit)

        mock_post.assert_called_once_with(
            endpoint=SET_ORGANIZATION_USAGE_LIMIT_V2.format(organization=self.organization),
            data=self.valid_usage_limit
        )
        self.assertEqual(result, self.valid_response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_organization_usage_limit_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.set_organization_usage_limit(self.organization, self.valid_usage_limit)

        mock_post.assert_called_once_with(
            endpoint=SET_ORGANIZATION_USAGE_LIMIT_V2.format(organization=self.organization),
            data=self.valid_usage_limit
        )
        self.assertEqual(str(context.exception), f"Unable to set usage limit for organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_organization_usage_limit_invalid_usage_limit(self, mock_post):
        invalid_usage_limit = self.valid_usage_limit.copy()
        invalid_usage_limit["renewalStatus"] = "InvalidStatus"
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"error": "Invalid renewal status"}

        result = self.client.set_organization_usage_limit(self.organization, invalid_usage_limit)

        mock_post.assert_called_once_with(
            endpoint=SET_ORGANIZATION_USAGE_LIMIT_V2.format(organization=self.organization),
            data=invalid_usage_limit
        )
        self.assertEqual(result, {"error": "Invalid renewal status"})
        with self.assertRaises(ValidationError):
            UsageLimit.model_validate(invalid_usage_limit)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_organization_latest_usage_limit_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = self.valid_response

        result = self.client.get_organization_latest_usage_limit(self.organization)

        mock_get.assert_called_once_with(
            endpoint=GET_ORGANIZATION_LATEST_USAGE_LIMIT_V2.format(organization=self.organization)
        )
        self.assertEqual(result, self.valid_response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_organization_latest_usage_limit_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_organization_latest_usage_limit(self.organization)

        mock_get.assert_called_once_with(
            endpoint=GET_ORGANIZATION_LATEST_USAGE_LIMIT_V2.format(organization=self.organization)
        )
        self.assertEqual(str(context.exception), f"Unable to get latest usage limit for organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_all_usage_limits_from_organization_success(self, mock_get):
        response = {"limits": [self.valid_response]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = response

        result = self.client.get_all_usage_limits_from_organization(self.organization)

        mock_get.assert_called_once_with(
            endpoint=GET_ALL_ORGANIZATION_USAGE_LIMITS_V2.format(organization=self.organization)
        )
        self.assertEqual(result, response)
        for limit in result["limits"]:
            UsageLimit.model_validate(limit)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_all_usage_limits_from_organization_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_all_usage_limits_from_organization(self.organization)

        mock_get.assert_called_once_with(
            endpoint=GET_ALL_ORGANIZATION_USAGE_LIMITS_V2.format(organization=self.organization)
        )
        self.assertEqual(str(context.exception), f"Unable to get all usage limits for organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_usage_limit_from_organization_success(self, mock_delete):
        response = {"status": "deleted"}
        mock_response = mock_delete.return_value
        mock_response.json.return_value = response

        result = self.client.delete_usage_limit_from_organization(self.organization, self.limit_id)

        mock_delete.assert_called_once_with(
            endpoint=DELETE_ORGANIZATION_USAGE_LIMIT_V2.format(organization=self.organization, id=self.limit_id)
        )
        self.assertEqual(result, response)

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_usage_limit_from_organization_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_usage_limit_from_organization(self.organization, self.limit_id)

        mock_delete.assert_called_once_with(
            endpoint=DELETE_ORGANIZATION_USAGE_LIMIT_V2.format(organization=self.organization, id=self.limit_id)
        )
        self.assertEqual(str(context.exception), f"Unable to delete usage limit with ID '{self.limit_id}' from organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_organization_hard_limit_success(self, mock_put):
        hard_limit = 3000.0
        response = self.valid_response.copy()
        response["hardLimit"] = hard_limit
        mock_response = mock_put.return_value
        mock_response.json.return_value = response

        result = self.client.set_organization_hard_limit(self.organization, self.limit_id, hard_limit)

        mock_put.assert_called_once_with(
            endpoint=SET_ORGANIZATION_HARD_LIMIT_V2.format(organization=self.organization, id=self.limit_id),
            data={"hardLimit": hard_limit}
        )
        self.assertEqual(result, response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_organization_hard_limit_json_decode_error(self, mock_put):
        hard_limit = 3000.0
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.set_organization_hard_limit(self.organization, self.limit_id, hard_limit)

        mock_put.assert_called_once_with(
            endpoint=SET_ORGANIZATION_HARD_LIMIT_V2.format(organization=self.organization, id=self.limit_id),
            data={"hardLimit": hard_limit}
        )
        self.assertEqual(str(context.exception), f"Unable to set hard limit for usage limit ID '{self.limit_id}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_organization_soft_limit_success(self, mock_put):
        soft_limit = 1500.0
        response = self.valid_response.copy()
        response["softLimit"] = soft_limit
        mock_response = mock_put.return_value
        mock_response.json.return_value = response

        result = self.client.set_organization_soft_limit(self.organization, self.limit_id, soft_limit)

        mock_put.assert_called_once_with(
            endpoint=SET_ORGANIZATION_SOFT_LIMIT_V2.format(organization=self.organization, id=self.limit_id),
            data={"softLimit": soft_limit}
        )
        self.assertEqual(result, response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_organization_soft_limit_json_decode_error(self, mock_put):
        soft_limit = 1500.0
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.set_organization_soft_limit(self.organization, self.limit_id, soft_limit)

        mock_put.assert_called_once_with(
            endpoint=SET_ORGANIZATION_SOFT_LIMIT_V2.format(organization=self.organization, id=self.limit_id),
            data={"softLimit": soft_limit}
        )
        self.assertEqual(str(context.exception), f"Unable to set soft limit for usage limit ID '{self.limit_id}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_organization_renewal_status_success(self, mock_put):
        renewal_status = "NonRenewable"
        response = self.valid_response.copy()
        response["renewalStatus"] = renewal_status
        mock_response = mock_put.return_value
        mock_response.json.return_value = response

        result = self.client.set_organization_renewal_status(self.organization, self.limit_id, renewal_status)

        mock_put.assert_called_once_with(
            endpoint=SET_ORGANIZATION_RENEWAL_STATUS_V2.format(organization=self.organization, id=self.limit_id),
            data={"renewalStatus": renewal_status}
        )
        self.assertEqual(result, response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_organization_renewal_status_json_decode_error(self, mock_put):
        renewal_status = "NonRenewable"
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.set_organization_renewal_status(self.organization, self.limit_id, renewal_status)

        mock_put.assert_called_once_with(
            endpoint=SET_ORGANIZATION_RENEWAL_STATUS_V2.format(organization=self.organization, id=self.limit_id),
            data={"renewalStatus": renewal_status}
        )
        self.assertEqual(str(context.exception), f"Unable to set renewal status for usage limit ID '{self.limit_id}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_project_usage_limit_success(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = self.valid_response

        result = self.client.set_project_usage_limit(self.organization, self.project, self.valid_usage_limit)

        mock_post.assert_called_once_with(
            endpoint=SET_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project),
            data=self.valid_usage_limit
        )
        self.assertEqual(result, self.valid_response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_project_usage_limit_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.set_project_usage_limit(self.organization, self.project, self.valid_usage_limit)

        mock_post.assert_called_once_with(
            endpoint=SET_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project),
            data=self.valid_usage_limit
        )
        self.assertEqual(str(context.exception), f"Unable to set usage limit for project '{self.project}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_project_usage_limit_invalid_usage_limit(self, mock_post):
        invalid_usage_limit = self.valid_usage_limit.copy()
        invalid_usage_limit["subscriptionType"] = "InvalidType"
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"error": "Invalid subscription type"}

        result = self.client.set_project_usage_limit(self.organization, self.project, invalid_usage_limit)

        mock_post.assert_called_once_with(
            endpoint=SET_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project),
            data=invalid_usage_limit
        )
        self.assertEqual(result, {"error": "Invalid subscription type"})
        with self.assertRaises(ValidationError):
            UsageLimit.model_validate(invalid_usage_limit)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_all_usage_limits_from_project_success(self, mock_get):
        response = {"limits": [self.valid_response]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = response

        result = self.client.get_all_usage_limits_from_project(self.organization, self.project)

        mock_get.assert_called_once_with(
            endpoint=GET_ALL_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project)
        )
        self.assertEqual(result, response)
        for limit in result["limits"]:
            UsageLimit.model_validate(limit)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_all_usage_limits_from_project_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_all_usage_limits_from_project(self.organization, self.project)

        mock_get.assert_called_once_with(
            endpoint=GET_ALL_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project)
        )
        self.assertEqual(str(context.exception), f"Unable to get all usage limits for project '{self.project}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_latest_usage_limit_from_project_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = self.valid_response

        result = self.client.get_latest_usage_limit_from_project(self.organization, self.project)

        mock_get.assert_called_once_with(
            endpoint=GET_LATEST_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project)
        )
        self.assertEqual(result, self.valid_response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_latest_usage_limit_from_project_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_latest_usage_limit_from_project(self.organization, self.project)

        mock_get.assert_called_once_with(
            endpoint=GET_LATEST_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project)
        )
        self.assertEqual(str(context.exception), f"Unable to get latest usage limit for project '{self.project}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_active_usage_limit_from_project_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = self.valid_response

        result = self.client.get_active_usage_limit_from_project(self.organization, self.project)

        mock_get.assert_called_once_with(
            endpoint=GET_PROJECT_ACTIVE_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project)
        )
        self.assertEqual(result, self.valid_response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_active_usage_limit_from_project_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_active_usage_limit_from_project(self.organization, self.project)

        mock_get.assert_called_once_with(
            endpoint=GET_PROJECT_ACTIVE_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project)
        )
        self.assertEqual(str(context.exception), f"Unable to get active usage limit for project '{self.project}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_usage_limit_from_project_success(self, mock_delete):
        response = {"status": "deleted"}
        mock_response = mock_delete.return_value
        mock_response.json.return_value = response

        result = self.client.delete_usage_limit_from_project(self.organization, self.project, self.limit_id)

        mock_delete.assert_called_once_with(
            endpoint=DELETE_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project, id=self.limit_id)
        )
        self.assertEqual(result, response)

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_usage_limit_from_project_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_usage_limit_from_project(self.organization, self.project, self.limit_id)

        mock_delete.assert_called_once_with(
            endpoint=DELETE_PROJECT_USAGE_LIMIT_V2.format(organization=self.organization, project=self.project, id=self.limit_id)
        )
        self.assertEqual(str(context.exception), f"Unable to delete usage limit with ID '{self.limit_id}' for project '{self.project}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_hard_limit_for_active_usage_limit_from_project_success(self, mock_put):
        hard_limit = 4000.0
        response = self.valid_response.copy()
        response["hardLimit"] = hard_limit
        mock_response = mock_put.return_value
        mock_response.json.return_value = response

        result = self.client.set_hard_limit_for_active_usage_limit_from_project(
            self.organization, self.project, self.limit_id, hard_limit
        )

        mock_put.assert_called_once_with(
            endpoint=SET_PROJECT_HARD_LIMIT_V2.format(organization=self.organization, project=self.project, id=self.limit_id),
            data={"hardLimit": hard_limit}
        )
        self.assertEqual(result, response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_hard_limit_for_active_usage_limit_from_project_json_decode_error(self, mock_put):
        hard_limit = 4000.0
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.set_hard_limit_for_active_usage_limit_from_project(
                self.organization, self.project, self.limit_id, hard_limit
            )

        mock_put.assert_called_once_with(
            endpoint=SET_PROJECT_HARD_LIMIT_V2.format(organization=self.organization, project=self.project, id=self.limit_id),
            data={"hardLimit": hard_limit}
        )
        self.assertEqual(str(context.exception), f"Unable to set hard limit for usage limit ID '{self.limit_id}' for project '{self.project}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_soft_limit_for_active_usage_limit_from_project_success(self, mock_put):
        soft_limit = 2000.0
        response = self.valid_response.copy()
        response["softLimit"] = soft_limit
        mock_response = mock_put.return_value
        mock_response.json.return_value = response

        result = self.client.set_soft_limit_for_active_usage_limit_from_project(
            self.organization, self.project, self.limit_id, soft_limit
        )

        mock_put.assert_called_once_with(
            endpoint=SET_PROJECT_SOFT_LIMIT_V2.format(organization=self.organization, project=self.project, id=self.limit_id),
            data={"softLimit": soft_limit}
        )
        self.assertEqual(result, response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_soft_limit_for_active_usage_limit_from_project_json_decode_error(self, mock_put):
        soft_limit = 2000.0
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.set_soft_limit_for_active_usage_limit_from_project(
                self.organization, self.project, self.limit_id, soft_limit
            )

        mock_put.assert_called_once_with(
            endpoint=SET_PROJECT_SOFT_LIMIT_V2.format(organization=self.organization, project=self.project, id=self.limit_id),
            data={"softLimit": soft_limit}
        )
        self.assertEqual(str(context.exception), f"Unable to set soft limit for usage limit ID '{self.limit_id}' for project '{self.project}' in organization '{self.organization}': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_project_renewal_status_success(self, mock_put):
        renewal_status = "Renewable"
        response = self.valid_response.copy()
        response["renewalStatus"] = renewal_status
        mock_response = mock_put.return_value
        mock_response.json.return_value = response

        result = self.client.set_project_renewal_status(self.organization, self.project, self.limit_id, renewal_status)

        mock_put.assert_called_once_with(
            endpoint=SET_PROJECT_RENEWAL_STATUS_V2.format(organization=self.organization, project=self.project, id=self.limit_id),
            data={"renewalStatus": renewal_status}
        )
        self.assertEqual(result, response)
        UsageLimit.model_validate(result)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_set_project_renewal_status_json_decode_error(self, mock_put):
        renewal_status = "Renewable"
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.set_project_renewal_status(self.organization, self.project, self.limit_id, renewal_status)

        mock_put.assert_called_once_with(
            endpoint=SET_PROJECT_RENEWAL_STATUS_V2.format(organization=self.organization, project=self.project, id=self.limit_id),
            data={"renewalStatus": renewal_status}
        )
        self.assertEqual(str(context.exception), f"Unable to set renewal status for usage limit ID '{self.limit_id}' for project '{self.project}' in organization '{self.organization}': Invalid JSON response")
