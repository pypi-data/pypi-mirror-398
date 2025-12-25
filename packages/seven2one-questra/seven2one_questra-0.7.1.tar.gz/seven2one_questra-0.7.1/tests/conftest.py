"""
Global pytest fixtures für questra Umbrella Package Tests.

Stellt Mock-Clients and Fixtures für alle Sub-Packages bereit:
- Authentication (OAuth2, OIDC)
- Automation (Workflows, Executions)
- Data (GraphQL, REST)
"""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

# ========== Authentication Fixtures ==========


@pytest.fixture
def mock_auth_client():
    """
    Mock für QuestraAuthentication Client.

    Returns:
        MagicMock: Mock with is_authenticated() and get_access_token()
    """
    mock = MagicMock()
    mock.is_authenticated.return_value = True
    mock.get_access_token.return_value = "mock_token_12345"
    return mock


@pytest.fixture
def mock_oidc_config():
    """
    Mock OIDC Configuration für OAuth2 Tests.

    Returns:
        dict: OIDC Discovery Response
    """
    return {
        "issuer": "https://test.example.com",
        "authorization_endpoint": "https://test.example.com/authorize",
        "token_endpoint": "https://test.example.com/token",
        "userinfo_endpoint": "https://test.example.com/userinfo",
        "end_session_endpoint": "https://test.example.com/logout",
        "device_authorization_endpoint": "https://test.example.com/device",
    }


@pytest.fixture
def mock_token_response():
    """
    Mock OAuth2 Token Response (gültig).

    Returns:
        dict: Token Response with access_token, expires_in, etc.
    """
    expires_at = (datetime.now() + timedelta(hours=1)).timestamp()
    return {
        "access_token": "test_access_token_12345",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": expires_at,
        "refresh_token": "test_refresh_token_67890",
    }


@pytest.fixture
def mock_expired_token_response():
    """
    Mock OAuth2 Token Response (abgelaufen).

    Returns:
        dict: Token Response with expires_at in der Vergangenheit
    """
    expires_at = (datetime.now() - timedelta(hours=1)).timestamp()
    return {
        "access_token": "expired_access_token",
        "token_type": "Bearer",
        "expires_in": 0,
        "expires_at": expires_at,
        "refresh_token": "test_refresh_token",
    }


# ========== Automation Fixtures ==========


@pytest.fixture
def mock_automation_client():
    """
    Mock für QuestraAutomation Client.

    Returns:
        MagicMock: Mock with list_workspaces(), execute_automation(), etc.
    """
    mock = MagicMock()
    mock.list_workspaces.return_value = []
    mock.list_repositories.return_value = []
    mock.list_automations.return_value = []
    return mock


@pytest.fixture
def sample_workspace():
    """
    Beispiel Workspace für Automation Tests.

    Returns:
        dict: Workspace with id, name, description
    """
    return {
        "id": "ws_123",
        "name": "Test Workspace",
        "description": "Test workspace for automation",
        "created": "2025-01-15T10:00:00Z",
        "modified": "2025-01-15T10:00:00Z",
    }


@pytest.fixture
def sample_execution():
    """
    Beispiel Execution für Automation Tests.

    Returns:
        dict: Execution with id, status, output
    """
    return {
        "id": "exec_456",
        "automationId": "auto_789",
        "status": "SUCCESS",
        "output": {"result": "Test completed successfully"},
        "started": "2025-01-15T11:00:00Z",
        "finished": "2025-01-15T11:05:00Z",
    }


# ========== Data Fixtures ==========


@pytest.fixture
def mock_data_client():
    """
    Mock für QuestraData High-Level Client.

    Returns:
        MagicMock: Mock with list_items(), create_items(), etc.
    """
    mock = MagicMock()
    mock.list_items.return_value = []
    mock.create_items.return_value = []
    mock.list_inventories.return_value = []
    mock.list_namespaces.return_value = []
    return mock


@pytest.fixture
def mock_data_core_client():
    """
    Mock für QuestraDataCore Low-Level Client.

    Returns:
        MagicMock: Mock with queries and mutations
    """
    mock = MagicMock()
    mock.queries = MagicMock()
    mock.mutations = MagicMock()
    return mock


@pytest.fixture
def sample_inventory():
    """
    Beispiel Inventory für Data Tests.

    Returns:
        dict: Inventory with _id, name, properties
    """
    return {
        "_id": "100",
        "name": "TestInventory",
        "namespaceName": "default",
        "inventoryType": "STANDARD",
        "description": "Test inventory for integration tests",
        "properties": [
            {
                "name": "title",
                "dataType": "STRING",
                "required": True,
                "config": {"maxLength": 100},
            },
            {
                "name": "count",
                "dataType": "INT",
                "required": False,
            },
        ],
    }


@pytest.fixture
def sample_namespace():
    """
    Beispiel Namespace für Data Tests.

    Returns:
        dict: Namespace with name, description
    """
    return {
        "name": "default",
        "description": "Default namespace",
        "created": "2025-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_items():
    """
    Beispiel Items für Data Tests (mit IDs as string!).

    Returns:
        list[dict]: Items with _id (String), properties
    """
    return [
        {
            "_id": "1001",
            "_rowVersion": "1",
            "title": "Test Item 1",
            "count": 10,
        },
        {
            "_id": "1002",
            "_rowVersion": "1",
            "title": "Test Item 2",
            "count": 20,
        },
    ]


@pytest.fixture
def sample_timeseries():
    """
    Beispiel TimeSeries für Data Tests.

    Returns:
        dict: TimeSeries with id (String!), name, unit
    """
    return {
        "id": "9001",
        "name": "Temperature Sensor 1",
        "unit": "°C",
        "interval": "PT1M",
        "quotationEnabled": True,
        "auditEnabled": False,
    }


@pytest.fixture
def sample_timeseries_data():
    """
    Beispiel TimeSeries Data für REST Tests.

    Returns:
        list[dict]: TimeSeries Values with timestamp, value, quality
    """
    return [
        {"t": "2025-01-15T10:00:00Z", "v": 21.5, "q": "GOOD"},
        {"t": "2025-01-15T10:01:00Z", "v": 21.7, "q": "GOOD"},
        {"t": "2025-01-15T10:02:00Z", "v": 21.6, "q": "GOOD"},
    ]


# ========== GraphQL Response Fixtures ==========


@pytest.fixture
def graphql_success_response() -> dict[str, Any]:
    """
    Generische erfolgreiche GraphQL Response.

    Returns:
        dict: GraphQL Response with data and ohne errors
    """
    return {"data": {"result": "success"}}


@pytest.fixture
def graphql_error_response() -> dict[str, Any]:
    """
    Generische GraphQL Error Response.

    Returns:
        dict: GraphQL Response with errors
    """
    return {
        "errors": [
            {
                "message": "Test error message",
                "locations": [{"line": 1, "column": 1}],
                "path": ["testQuery"],
            }
        ]
    }


# ========== Integration Test Helpers ==========


@pytest.fixture
def full_stack_mocks(mock_auth_client, mock_data_client, mock_automation_client):
    """
    Kombinierte Mocks für Full-Stack Integration Tests.

    Args:
        mock_auth_client: Authentication Mock
        mock_data_client: Data Client Mock
        mock_automation_client: Automation Client Mock

    Returns:
        dict: Dictionary with allen Mocks
    """
    return {
        "auth": mock_auth_client,
        "data": mock_data_client,
        "automation": mock_automation_client,
    }
