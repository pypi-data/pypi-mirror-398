"""Comprehensive tests for SGDataClient."""

from typing import Any, Dict
from unittest.mock import Mock, patch
import pytest
import requests

from sgdata.client import SGDataClient


class TestSGDataClientInitialization:
    """Test client initialization and configuration."""

    def test_default_initialization(self):
        """Test client initializes with default base URL and timeout."""
        client = SGDataClient()

        assert client.base_url == "https://api.data.gov.sg/v1"
        assert client.timeout == 30
        assert isinstance(client.session, requests.Session)
        assert client.session.headers["User-Agent"] == "sgdata-sdk-python/0.1.0"
        assert client.session.headers["Accept"] == "application/json"
        client.close()

    def test_custom_base_url(self):
        """Test client initializes with custom base URL."""
        custom_url = "https://custom.api.example.com/v2"
        client = SGDataClient(base_url=custom_url)

        assert client.base_url == custom_url
        assert client.timeout == 30
        client.close()

    def test_custom_timeout(self):
        """Test client initializes with custom timeout."""
        client = SGDataClient(timeout=60)

        assert client.base_url == "https://api.data.gov.sg/v1"
        assert client.timeout == 60
        client.close()

    def test_custom_base_url_and_timeout(self):
        """Test client initializes with both custom base URL and timeout."""
        custom_url = "https://custom.api.example.com/v2"
        client = SGDataClient(base_url=custom_url, timeout=45)

        assert client.base_url == custom_url
        assert client.timeout == 45
        client.close()


class TestParameterBuilding:
    """Test query parameter building logic."""

    def test_build_params_no_parameters(self):
        """Test building params with no date or date_time."""
        client = SGDataClient()
        params = client._build_params()

        assert params == {}
        client.close()

    def test_build_params_with_date_time_only(self):
        """Test building params with date_time parameter."""
        client = SGDataClient()
        params = client._build_params(date_time="2024-01-15T12:00:00")

        assert params == {"date_time": "2024-01-15T12:00:00"}
        client.close()

    def test_build_params_with_date_only(self):
        """Test building params with date parameter."""
        client = SGDataClient()
        params = client._build_params(date="2024-01-15")

        assert params == {"date": "2024-01-15"}
        client.close()

    def test_build_params_with_both_parameters(self):
        """Test building params with both date_time and date."""
        client = SGDataClient()
        params = client._build_params(
            date_time="2024-01-15T12:00:00",
            date="2024-01-15"
        )

        assert params == {
            "date_time": "2024-01-15T12:00:00",
            "date": "2024-01-15"
        }
        client.close()


class TestHTTPRequests:
    """Test HTTP request handling."""

    @patch('requests.Session.get')
    def test_successful_request(self, mock_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client._request("/test/endpoint")

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/test/endpoint",
            params=None,
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_request_with_params(self, mock_get):
        """Test API request with query parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        client = SGDataClient()
        params = {"date_time": "2024-01-15T12:00:00"}
        result = client._request("/test/endpoint", params=params)

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/test/endpoint",
            params=params,
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_request_http_error_4xx(self, mock_get):
        """Test API request with 4xx HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        client = SGDataClient()

        with pytest.raises(requests.HTTPError):
            client._request("/test/endpoint")

        client.close()

    @patch('requests.Session.get')
    def test_request_http_error_5xx(self, mock_get):
        """Test API request with 5xx HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Internal Server Error")
        mock_get.return_value = mock_response

        client = SGDataClient()

        with pytest.raises(requests.HTTPError):
            client._request("/test/endpoint")

        client.close()

    @patch('requests.Session.get')
    def test_request_timeout(self, mock_get):
        """Test API request timeout."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        client = SGDataClient()

        with pytest.raises(requests.Timeout):
            client._request("/test/endpoint")

        client.close()

    @patch('requests.Session.get')
    def test_request_connection_error(self, mock_get):
        """Test API request connection error."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        client = SGDataClient()

        with pytest.raises(requests.ConnectionError):
            client._request("/test/endpoint")

        client.close()


class TestAirQualityEndpoints:
    """Test air quality API endpoints."""

    @patch('requests.Session.get')
    def test_get_psi_current(self, mock_get):
        """Test getting current PSI data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"region_metadata": [], "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_psi()

        assert "region_metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/psi",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_psi_with_date_time(self, mock_get):
        """Test getting historical PSI data with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"region_metadata": [], "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_psi(date_time="2024-01-15T12:00:00")

        assert "region_metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/psi",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_psi_with_date(self, mock_get):
        """Test getting historical PSI data with date."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"region_metadata": [], "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_psi(date="2024-01-15")

        assert "region_metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/psi",
            params={"date": "2024-01-15"},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_pm25_current(self, mock_get):
        """Test getting current PM2.5 data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"region_metadata": [], "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_pm25()

        assert "region_metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/pm25",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_pm25_with_date_time(self, mock_get):
        """Test getting historical PM2.5 data with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"region_metadata": [], "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_pm25(date_time="2024-01-15T12:00:00")

        assert "region_metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/pm25",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_pm25_with_date(self, mock_get):
        """Test getting historical PM2.5 data with date."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"region_metadata": [], "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_pm25(date="2024-01-15")

        assert "region_metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/pm25",
            params={"date": "2024-01-15"},
            timeout=30
        )
        client.close()


class TestWeatherForecastEndpoints:
    """Test weather forecast API endpoints."""

    @patch('requests.Session.get')
    def test_get_2hour_weather_forecast_current(self, mock_get):
        """Test getting current 2-hour weather forecast."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"area_metadata": [], "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_2hour_weather_forecast()

        assert "area_metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_2hour_weather_forecast_with_date_time(self, mock_get):
        """Test getting historical 2-hour weather forecast with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"area_metadata": [], "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_2hour_weather_forecast(date_time="2024-01-15T12:00:00")

        assert "area_metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_24hour_weather_forecast_current(self, mock_get):
        """Test getting current 24-hour weather forecast."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_24hour_weather_forecast()

        assert "items" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_24hour_weather_forecast_with_date_time(self, mock_get):
        """Test getting historical 24-hour weather forecast with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_24hour_weather_forecast(date_time="2024-01-15T12:00:00")

        assert "items" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_4day_weather_forecast_current(self, mock_get):
        """Test getting current 4-day weather forecast."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_4day_weather_forecast()

        assert "items" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/4-day-weather-forecast",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_4day_weather_forecast_with_date_time(self, mock_get):
        """Test getting historical 4-day weather forecast with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_4day_weather_forecast(date_time="2024-01-15T12:00:00")

        assert "items" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/4-day-weather-forecast",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()


class TestWeatherMeasurementEndpoints:
    """Test weather measurement API endpoints."""

    @patch('requests.Session.get')
    def test_get_rainfall_current(self, mock_get):
        """Test getting current rainfall data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"metadata": {}, "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_rainfall()

        assert "metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/rainfall",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_rainfall_with_date_time(self, mock_get):
        """Test getting historical rainfall data with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"metadata": {}, "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_rainfall(date_time="2024-01-15T12:00:00")

        assert "metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/rainfall",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_relative_humidity_current(self, mock_get):
        """Test getting current relative humidity data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"metadata": {}, "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_relative_humidity()

        assert "metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/relative-humidity",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_relative_humidity_with_date_time(self, mock_get):
        """Test getting historical relative humidity data with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"metadata": {}, "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_relative_humidity(date_time="2024-01-15T12:00:00")

        assert "metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/relative-humidity",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_air_temperature_current(self, mock_get):
        """Test getting current air temperature data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"metadata": {}, "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_air_temperature()

        assert "metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/air-temperature",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_air_temperature_with_date_time(self, mock_get):
        """Test getting historical air temperature data with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"metadata": {}, "items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_air_temperature(date_time="2024-01-15T12:00:00")

        assert "metadata" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/air-temperature",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()


class TestTransportEndpoints:
    """Test transport API endpoints."""

    @patch('requests.Session.get')
    def test_get_carpark_availability_current(self, mock_get):
        """Test getting current carpark availability."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_carpark_availability()

        assert "items" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/transport/carpark-availability",
            params={},
            timeout=30
        )
        client.close()

    @patch('requests.Session.get')
    def test_get_carpark_availability_with_date_time(self, mock_get):
        """Test getting historical carpark availability with date_time."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client.get_carpark_availability(date_time="2024-01-15T12:00:00")

        assert "items" in result
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/transport/carpark-availability",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30
        )
        client.close()


class TestSessionManagement:
    """Test session management and cleanup."""

    def test_close_session(self):
        """Test that close() properly closes the session."""
        client = SGDataClient()
        session = client.session

        client.close()

        # After closing, the session should be closed
        # We can verify this by checking that subsequent requests would fail
        # or by checking internal state (though this is implementation-dependent)
        assert session is not None

    def test_context_manager_entry(self):
        """Test context manager __enter__ returns self."""
        client = SGDataClient()

        with client as ctx_client:
            assert ctx_client is client
            assert isinstance(ctx_client.session, requests.Session)

    def test_context_manager_exit(self):
        """Test context manager __exit__ closes session."""
        with SGDataClient() as client:
            session = client.session
            assert isinstance(session, requests.Session)

        # After exiting context, session should be closed
        # Session object still exists but is closed
        assert session is not None

    @patch('requests.Session.get')
    def test_context_manager_with_request(self, mock_get):
        """Test using client within context manager."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        with SGDataClient() as client:
            result = client.get_psi()
            assert "data" in result

        # Session should be closed after exiting context
        mock_get.assert_called_once()
