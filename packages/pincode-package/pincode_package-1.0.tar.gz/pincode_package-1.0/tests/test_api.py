import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import RequestException
from pincode_package import fetch_by_pincode, fetch_by_postoffice_name
from pincode_package.exceptions import (
    APIUnavailableError,
    PincodeNotFoundError,
    PostOfficeNotFoundError
)

# -------------------------
# SUCCESS CASES
# -------------------------

@patch("pincode_package.api.save_cached_pincode")
@patch("pincode_package.api.get_cached_pincode", return_value=None)
@patch("pincode_package.api.requests.get")
def test_fetch_by_pincode_success(mock_get, mock_cache, mock_save):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "Status": "Success",
            "PostOffice": [
                {
                    "Name": "Ernakulam",
                    "Region": "Kochi",
                    "District": "Ernakulam",
                    "State": "Kerala",
                    "Division": "Ernakulam",
                    "Pincode": "682001",
                }
            ]
        }
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_by_pincode("682001")

    assert isinstance(result, list)
    assert result[0]["Name"] == "Ernakulam"
    mock_save.assert_called_once()


@patch("pincode_package.api.requests.get")
def test_fetch_by_postoffice_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "Status": "Success",
            "PostOffice": [
                {
                    "Name": "Ernakulam",
                    "Region": "Kochi",
                    "District": "Ernakulam",
                    "State": "Kerala",
                    "Division": "Ernakulam",
                    "Pincode": "682001",
                }
            ]
        }
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = fetch_by_postoffice_name("Ernakulam")
    assert result[0]["State"] == "Kerala"


# -------------------------
# EXCEPTION CASES
# -------------------------

@patch("pincode_package.api.get_cached_pincode", return_value=None)
@patch("pincode_package.api.requests.get")
def test_fetch_by_pincode_api_failure_raises_error(mock_get, mock_cache):
    mock_get.side_effect = RequestException("Network error")

    with pytest.raises(APIUnavailableError):
        fetch_by_pincode("682001")


@patch("pincode_package.api.requests.get")
def test_fetch_by_pincode_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "Status": "Success",
            "PostOffice": []
        }
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with pytest.raises(PincodeNotFoundError):
        fetch_by_pincode("000000")


@patch("pincode_package.api.requests.get")
def test_fetch_by_postoffice_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "Status": "Success",
            "PostOffice": []
        }
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    with pytest.raises(PostOfficeNotFoundError):
        fetch_by_postoffice_name("InvalidOffice")
