"""
Tests for the _get_by_dot_notation method in UsageFlowMiddleware
"""
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from usageflow.fastapi import UsageFlowMiddleware


class TestDotNotation(unittest.TestCase):
    """Test cases for _get_by_dot_notation method"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = FastAPI()
        # Mock the UsageFlowClient to avoid actual WebSocket connections
        with patch('usageflow.fastapi.UsageFlowClient') as mock_client:
            mock_client_instance = Mock()
            mock_client_instance.connect = Mock()
            mock_client_instance.is_endpoint_whitelisted = Mock(return_value=False)
            mock_client_instance.is_endpoint_monitored = Mock(return_value=True)
            mock_client_instance.is_endpoint_blocked = Mock(return_value=False)
            mock_client_instance.allocate_request = Mock(return_value=(True, {'allocationId': 'test-id'}))
            mock_client_instance.get_config = Mock(return_value={'extractResponseSchema': True})
            mock_client_instance.extract_schema = Mock(return_value={})
            mock_client_instance.fulfill_request = Mock()
            mock_client_instance.get_policies_map = Mock(return_value={})
            mock_client.return_value = mock_client_instance

            self.middleware = UsageFlowMiddleware(self.app, api_key="test-key", pool_size=1)

    def test_simple_property_access(self):
        """Test accessing a simple property"""
        obj = {"name": "John"}
        result = self.middleware._get_by_dot_notation(obj, "name")
        self.assertEqual(result, "John")

    def test_nested_property_access(self):
        """Test accessing nested properties"""
        obj = {"user": {"name": "John", "age": 30}}
        result = self.middleware._get_by_dot_notation(obj, "user.name")
        self.assertEqual(result, "John")

        result = self.middleware._get_by_dot_notation(obj, "user.age")
        self.assertEqual(result, 30)

    def test_deeply_nested_property_access(self):
        """Test accessing deeply nested properties"""
        obj = {
            "data": {
                "user": {
                    "profile": {
                        "email": "john@example.com"
                    }
                }
            }
        }
        result = self.middleware._get_by_dot_notation(obj, "data.user.profile.email")
        self.assertEqual(result, "john@example.com")

    def test_array_iteration_simple(self):
        """Test iterating over an array with [*] - returns first match"""
        obj = {
            "users": [
                {"name": "John"},
                {"name": "Jane"},
                {"name": "Bob"}
            ]
        }
        result = self.middleware._get_by_dot_notation(obj, "users[*].name")
        self.assertEqual(result, "John")  # Returns first matching element

    def test_array_iteration_with_missing_values(self):
        """Test array iteration when some items don't have the property - returns first match"""
        obj = {
            "users": [
                {"name": "John"},
                {"age": 30},  # Missing name
                {"name": "Bob"}
            ]
        }
        result = self.middleware._get_by_dot_notation(obj, "users[*].name")
        self.assertEqual(result, "John")  # Returns first matching element

    def test_array_iteration_no_remaining_path(self):
        """Test array iteration when there's no remaining path after [*] - returns first element"""
        obj = {
            "items": [1, 2, 3, 4, 5]
        }
        result = self.middleware._get_by_dot_notation(obj, "items[*]")
        self.assertEqual(result, 1)  # Returns first element

    def test_array_iteration_nested_path(self):
        """Test array iteration with nested path after [*] - returns first match"""
        obj = {
            "data": {
                "items": [
                    {"id": 1, "value": "a"},
                    {"id": 2, "value": "b"},
                    {"id": 3, "value": "c"}
                ]
            }
        }
        result = self.middleware._get_by_dot_notation(obj, "data.items[*].id")
        self.assertEqual(result, 1)  # Returns first matching element

        result = self.middleware._get_by_dot_notation(obj, "data.items[*].value")
        self.assertEqual(result, "a")  # Returns first matching element

    def test_array_iteration_deeply_nested(self):
        """Test array iteration with deeply nested paths - returns first match"""
        obj = {
            "users": [
                {
                    "profile": {
                        "contact": {
                            "email": "john@example.com"
                        }
                    }
                },
                {
                    "profile": {
                        "contact": {
                            "email": "jane@example.com"
                        }
                    }
                }
            ]
        }
        result = self.middleware._get_by_dot_notation(obj, "users[*].profile.contact.email")
        self.assertEqual(result, "john@example.com")  # Returns first matching element

    def test_array_iteration_multiple_arrays(self):
        """Test accessing nested arrays - returns first match"""
        obj = {
            "departments": [
                {
                    "name": "Engineering",
                    "employees": [
                        {"name": "Alice"},
                        {"name": "Bob"}
                    ]
                },
                {
                    "name": "Sales",
                    "employees": [
                        {"name": "Charlie"}
                    ]
                }
            ]
        }
        # Get first employee name from first department
        dept = obj["departments"][0]
        result = self.middleware._get_by_dot_notation(dept, "employees[*].name")
        self.assertEqual(result, "Alice")  # Returns first matching element

    def test_none_value_returns_none(self):
        """Test that None values return None"""
        obj = {"user": None}
        result = self.middleware._get_by_dot_notation(obj, "user.name")
        self.assertIsNone(result)

    def test_missing_key_returns_none(self):
        """Test that missing keys return None"""
        obj = {"user": {"age": 30}}
        result = self.middleware._get_by_dot_notation(obj, "user.name")
        self.assertIsNone(result)

    def test_array_not_list_returns_none(self):
        """Test that non-list arrays return None"""
        obj = {"users": "not a list"}
        result = self.middleware._get_by_dot_notation(obj, "users[*].name")
        self.assertIsNone(result)

    def test_array_key_not_in_dict_returns_none(self):
        """Test that missing array key returns None"""
        obj = {"other": "data"}
        result = self.middleware._get_by_dot_notation(obj, "users[*].name")
        self.assertIsNone(result)

    def test_empty_array_returns_none(self):
        """Test that empty array with path returns None"""
        obj = {"users": []}
        result = self.middleware._get_by_dot_notation(obj, "users[*].name")
        self.assertIsNone(result)

    def test_empty_array_no_path_returns_none(self):
        """Test that empty array without path returns None"""
        obj = {"items": []}
        result = self.middleware._get_by_dot_notation(obj, "items[*]")
        self.assertIsNone(result)

    def test_array_iteration_all_none_values(self):
        """Test array iteration when all values are None - returns None"""
        obj = {
            "users": [
                {"name": None},
                {"name": None}
            ]
        }
        result = self.middleware._get_by_dot_notation(obj, "users[*].name")
        self.assertIsNone(result)  # All values are None, so returns None

    def test_array_iteration_mixed_types(self):
        """Test array iteration with mixed value types - returns first match"""
        obj = {
            "items": [
                {"value": "string"},
                {"value": 123},
                {"value": True},
                {"value": None}
            ]
        }
        result = self.middleware._get_by_dot_notation(obj, "items[*].value")
        self.assertEqual(result, "string")  # Returns first matching element

    def test_path_with_array_in_middle(self):
        """Test path where array is in the middle of the path - returns first match"""
        obj = {
            "data": {
                "users": [
                    {"id": 1},
                    {"id": 2}
                ]
            }
        }
        result = self.middleware._get_by_dot_notation(obj, "data.users[*].id")
        self.assertEqual(result, 1)  # Returns first matching element

    def test_result_is_list_accessing_property_returns_none(self):
        """Test that accessing a property on a list returns None"""
        obj = {"items": [1, 2, 3]}
        result = self.middleware._get_by_dot_notation(obj, "items.name")
        self.assertIsNone(result)

    def test_result_is_not_dict_returns_none(self):
        """Test that accessing property on non-dict returns None"""
        obj = {"user": "string_value"}
        result = self.middleware._get_by_dot_notation(obj, "user.name")
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

