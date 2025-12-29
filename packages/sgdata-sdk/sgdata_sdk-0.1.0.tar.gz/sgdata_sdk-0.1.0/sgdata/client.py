"""SGData SDK Client implementation."""

from typing import Any, Dict, Optional
import requests


class SGDataClient:
    """Unified client for Singapore Government Data APIs.

    Provides access to 9 core endpoints covering weather, air quality, and carpark data.

    Args:
        base_url: Base URL for the API. Defaults to data.gov.sg API.
        timeout: Request timeout in seconds. Defaults to 30.

    Example:
        >>> client = SGDataClient()
        >>> psi_data = client.get_psi()
        >>> historical_psi = client.get_psi(date_time="2024-01-15T12:00:00")
    """

    BASE_URL = "https://api.data.gov.sg/v1"

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30) -> None:
        """Initialize the SGData client.

        Args:
            base_url: Custom base URL for the API (optional).
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "sgdata-sdk-python/0.1.0",
            "Accept": "application/json"
        })

    def _build_params(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, str]:
        """Build query parameters for API requests.

        Args:
            date_time: ISO 8601 datetime string (e.g., "2024-01-15T12:00:00").
            date: Date string in YYYY-MM-DD format (e.g., "2024-01-15").

        Returns:
            Dictionary of query parameters with non-None values.
        """
        params: Dict[str, str] = {}
        if date_time is not None:
            params["date_time"] = date_time
        if date is not None:
            params["date"] = date
        return params

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP GET request to the API.

        Args:
            endpoint: API endpoint path (e.g., "/environment/psi").
            params: Query parameters for the request.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            requests.HTTPError: If the request fails with 4xx or 5xx status.
            requests.RequestException: For other request-related errors.
        """
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    # Environment - Air Quality

    def get_psi(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get Pollutant Standards Index (PSI) readings.

        Returns hourly PSI readings across Singapore regions.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).
            date: Specific date for historical data (YYYY-MM-DD).

        Returns:
            PSI data including regional readings and timestamp.
        """
        params = self._build_params(date_time, date)
        return self._request("/environment/psi", params=params)

    def get_pm25(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get PM2.5 (fine particulate matter) readings.

        Returns PM2.5 concentration levels across Singapore regions.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).
            date: Specific date for historical data (YYYY-MM-DD).

        Returns:
            PM2.5 data including regional readings and timestamp.
        """
        params = self._build_params(date_time, date)
        return self._request("/environment/pm25", params=params)

    # Environment - Weather

    def get_2hour_weather_forecast(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get 2-hour weather forecast.

        Returns short-term weather forecasts for different areas of Singapore.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).
            date: Specific date for historical data (YYYY-MM-DD).

        Returns:
            2-hour weather forecast data with area-specific predictions.
        """
        params = self._build_params(date_time, date)
        return self._request("/environment/2-hour-weather-forecast", params=params)

    def get_24hour_weather_forecast(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get 24-hour weather forecast.

        Returns general weather forecast for the next 24 hours.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).
            date: Specific date for historical data (YYYY-MM-DD).

        Returns:
            24-hour weather forecast data including general conditions.
        """
        params = self._build_params(date_time, date)
        return self._request("/environment/24-hour-weather-forecast", params=params)

    def get_4day_weather_forecast(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get 4-day weather forecast.

        Returns extended weather forecast for the next 4 days.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).
            date: Specific date for historical data (YYYY-MM-DD).

        Returns:
            4-day weather forecast data with daily predictions.
        """
        params = self._build_params(date_time, date)
        return self._request("/environment/4-day-weather-forecast", params=params)

    def get_rainfall(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get rainfall measurements.

        Returns rainfall readings from weather stations across Singapore.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).
            date: Specific date for historical data (YYYY-MM-DD).

        Returns:
            Rainfall data from multiple weather stations.
        """
        params = self._build_params(date_time, date)
        return self._request("/environment/rainfall", params=params)

    def get_relative_humidity(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get relative humidity readings.

        Returns humidity measurements from weather stations across Singapore.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).
            date: Specific date for historical data (YYYY-MM-DD).

        Returns:
            Relative humidity data from multiple weather stations.
        """
        params = self._build_params(date_time, date)
        return self._request("/environment/relative-humidity", params=params)

    def get_air_temperature(
        self,
        date_time: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get air temperature readings.

        Returns temperature measurements from weather stations across Singapore.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).
            date: Specific date for historical data (YYYY-MM-DD).

        Returns:
            Air temperature data from multiple weather stations.
        """
        params = self._build_params(date_time, date)
        return self._request("/environment/air-temperature", params=params)

    # Transport - Carpark Availability

    def get_carpark_availability(
        self,
        date_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get carpark availability information.

        Returns real-time or historical carpark availability data for HDB carparks.
        Note: This endpoint only supports date_time parameter, not date.

        Args:
            date_time: Specific datetime for historical data (ISO 8601).

        Returns:
            Carpark availability data including lot counts and locations.
        """
        params = self._build_params(date_time, None)
        return self._request("/transport/carpark-availability", params=params)

    def close(self) -> None:
        """Close the HTTP session.

        Should be called when done using the client to clean up resources.
        """
        self.session.close()

    def __enter__(self) -> "SGDataClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
