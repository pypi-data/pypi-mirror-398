"""
Zoom Phone Interface for FlowTask
Provides a clean interface to interact with Zoom Phone API
"""
from typing import Optional, Dict, List, Any
from datetime import datetime
from abc import ABC
from enum import Enum
import aiohttp
from .http import HTTPService


class CallStatus(Enum):
    """Call status enumeration"""
    ALL = "all"
    ACTIVE = "active"
    MISSED = "missed"
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class RecordingType(Enum):
    """Recording type enumeration"""
    ON_DEMAND = "on_demand"
    AUTOMATIC = "automatic"
    ALL = "all"


class ZoomInterface(HTTPService, ABC):
    """
    Abstract interface for Zoom Phone operations.
    This interface should be implemented by components that interact with Zoom Phone API.

    The implementing class should extend HTTPService (or a similar HTTP client)
    to handle the actual HTTP requests with proper authentication.
    """

    BASE_URL = "https://api.zoom.us/v2"

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _get_access_token(self) -> str:
        """
        Get or refresh OAuth access token.

        Returns:
            Valid access token
        """
        if self.access_token:
            return self.access_token

        # If no token but have credentials, get a new one
        if self.client_id and self.client_secret and self.account_id:
            auth_url = "https://zoom.us/oauth/token"

            await self._ensure_session()

            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            data = {
                "grant_type": "account_credentials",
                "account_id": self.account_id
            }

            async with self.session.post(auth_url, auth=auth, data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    self.access_token = result["access_token"]
                    return self.access_token
                else:
                    error = await resp.text()
                    raise Exception(f"Failed to get access token: {error}")

        raise ValueError("No access token available and credentials not provided")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        raw_response: bool = False,
        **kwargs
    ) -> Any:
        """
        Make HTTP request to Zoom API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body
            raw_response: Return raw bytes instead of JSON
            **kwargs: Additional arguments

        Returns:
            Response data
        """
        await self._ensure_session()

        # Get access token
        token = await self._get_access_token()

        # Build full URL
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.BASE_URL}{endpoint}"

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Make request
        async with self.session.request(
            method,
            url,
            params=params,
            json=json_data,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as resp:
            if resp.status >= 400:
                error = await resp.text()
                raise Exception(
                    f"Zoom API error ({resp.status}): {error}"
                )

            if raw_response:
                return await resp.read()

            return await resp.json()

    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def get_call_metadata_by_extension(
        self,
        extension_number: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page_size: int = 30,
        next_page_token: Optional[str] = None,
        call_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download call metadata by extension number.

        Args:
            extension_number: The extension number to query
            from_date: Start date for call history
            to_date: End date for call history
            page_size: Number of records per page (max 100)
            next_page_token: Token for pagination
            call_type: Filter by call type (incoming, outgoing, missed, etc.)

        Returns:
            Call metadata including call logs, durations, participants, etc.
        """
        params = {
            "page_size": min(page_size, 100),
            "extension_number": extension_number
        }

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")
        if next_page_token:
            params["next_page_token"] = next_page_token
        if call_type:
            params["type"] = call_type

        return await self._make_request("GET", "/phone/call_history", params=params)

    async def get_call_by_id(self, call_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific call.

        Args:
            call_id: The unique call identifier

        Returns:
            Detailed call information
        """
        return await self._make_request("GET", f"/phone/call_history/{call_id}")

    # ==========================================
    # Call Recordings
    # ==========================================

    async def download_recording_by_call_id(
        self,
        call_id: str,
        download_access_token: Optional[str] = None
    ) -> bytes:
        """
        Download call recording by call ID.

        Args:
            call_id: The call ID
            download_access_token: Optional access token for download

        Returns:
            Recording file as bytes
        """
        # First get recording details
        recording_info = await self._make_request(
            "GET",
            f"/phone/call_history/{call_id}/recordings"
        )

        # Extract download URL
        if recording_info and "recordings" in recording_info:
            recording = recording_info["recordings"][0]
            download_url = recording.get("download_url")

            if download_url:
                # Download the actual file
                return await self._make_request(
                    "GET",
                    download_url,
                    raw_response=True
                )

        raise ValueError(f"No recording found for call ID: {call_id}")

    async def list_recordings(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page_size: int = 30,
        next_page_token: Optional[str] = None,
        recording_type: Optional[RecordingType] = None
    ) -> Dict[str, Any]:
        """
        List all call recordings.

        Args:
            from_date: Start date for recordings
            to_date: End date for recordings
            page_size: Number of records per page
            next_page_token: Token for pagination
            recording_type: Filter by recording type

        Returns:
            List of recordings with metadata
        """
        params = {"page_size": min(page_size, 100)}

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")
        if next_page_token:
            params["next_page_token"] = next_page_token
        if recording_type:
            params["type"] = recording_type.value

        return await self._make_request("GET", "/phone/recordings", params=params)

    async def get_user_recordings(
        self,
        user_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page_size: int = 30
    ) -> Dict[str, Any]:
        """
        Get recordings for a specific user.

        Args:
            user_id: Zoom user ID or email
            from_date: Start date
            to_date: End date
            page_size: Number of records per page

        Returns:
            User's recordings
        """
        params = {"page_size": min(page_size, 100)}

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")

        return await self._make_request(
            "GET",
            f"/phone/users/{user_id}/recordings",
            params=params
        )

    # ==========================================
    # Recording Transcripts
    # ==========================================

    async def download_recording_transcript(
        self,
        call_id: str,
        recording_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download phone recording transcript.

        Args:
            call_id: The call ID
            recording_id: Optional specific recording ID

        Returns:
            Transcript data with timestamps and text
        """
        endpoint = f"/phone/call_history/{call_id}/recordings"

        if recording_id:
            endpoint = f"{endpoint}/{recording_id}/transcript"

        return await self._make_request("GET", endpoint)

    async def get_recording_transcript_by_id(
        self,
        recording_id: str
    ) -> Dict[str, Any]:
        """
        Get transcript for a specific recording.

        Args:
            recording_id: The recording identifier

        Returns:
            Transcript with speaker labels and timestamps
        """
        return await self._make_request(
            "GET",
            f"/phone/recordings/{recording_id}/transcript"
        )

    # ==========================================
    # Phone Numbers
    # ==========================================

    async def list_phone_numbers(
        self,
        page_size: int = 30,
        next_page_token: Optional[str] = None,
        site_id: Optional[str] = None,
        extension_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all phone numbers in the account.

        Args:
            page_size: Number of records per page
            next_page_token: Token for pagination
            site_id: Filter by site ID
            extension_type: Filter by extension type (user, callQueue, autoReceptionist, etc.)

        Returns:
            List of phone numbers with assignments
        """
        params = {"page_size": min(page_size, 100)}

        if next_page_token:
            params["next_page_token"] = next_page_token
        if site_id:
            params["site_id"] = site_id
        if extension_type:
            params["extension_type"] = extension_type

        return await self._make_request("GET", "/phone/numbers", params=params)

    async def get_phone_number(self, phone_number_id: str) -> Dict[str, Any]:
        """
        Get details of a specific phone number.

        Args:
            phone_number_id: The phone number ID

        Returns:
            Phone number details including assignment and capabilities
        """
        return await self._make_request("GET", f"/phone/numbers/{phone_number_id}")

    async def get_phone_number_by_number(self, number: str) -> Dict[str, Any]:
        """
        Get phone number details by actual phone number.

        Args:
            number: The phone number (e.g., "+15551234567")

        Returns:
            Phone number details
        """
        # List all numbers and filter
        result = await self.list_phone_numbers(page_size=100)

        for phone in result.get("phone_numbers", []):
            if phone.get("number") == number:
                return await self.get_phone_number(phone.get("id"))

        raise ValueError(f"Phone number not found: {number}")

    # ==========================================
    # Users & Profiles
    # ==========================================

    async def list_phone_users(
        self,
        page_size: int = 30,
        next_page_token: Optional[str] = None,
        site_id: Optional[str] = None,
        calling_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all phone users in the account.

        Args:
            page_size: Number of records per page
            next_page_token: Token for pagination
            site_id: Filter by site
            calling_type: Filter by calling type (internal, external, etc.)
            status: Filter by status (active, inactive)

        Returns:
            List of phone users
        """
        params = {"page_size": min(page_size, 100)}

        if next_page_token:
            params["next_page_token"] = next_page_token
        if site_id:
            params["site_id"] = site_id
        if calling_type:
            params["calling_type"] = calling_type
        if status:
            params["status"] = status

        return await self._make_request("GET", "/phone/users", params=params)

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user's phone profile.

        Args:
            user_id: Zoom user ID or email

        Returns:
            User's phone profile including extensions, settings, and numbers
        """
        return await self._make_request("GET", f"/phone/users/{user_id}")

    async def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Get a user's phone settings.

        Args:
            user_id: Zoom user ID or email

        Returns:
            User's phone settings and preferences
        """
        return await self._make_request("GET", f"/phone/users/{user_id}/settings")

    # ==========================================
    # Voicemail
    # ==========================================

    async def list_voicemails(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page_size: int = 30,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List voicemails.

        Args:
            from_date: Start date
            to_date: End date
            page_size: Number of records per page
            status: Filter by status (read, unread)

        Returns:
            List of voicemails
        """
        params = {"page_size": min(page_size, 100)}

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")
        if status:
            params["status"] = status

        return await self._make_request("GET", "/phone/voicemails", params=params)

    async def get_user_voicemails(
        self,
        user_id: str,
        page_size: int = 30,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get voicemails for a specific user.

        Args:
            user_id: Zoom user ID or email
            page_size: Number of records per page
            status: Filter by status

        Returns:
            User's voicemails
        """
        params = {"page_size": min(page_size, 100)}

        if status:
            params["status"] = status

        return await self._make_request(
            "GET",
            f"/phone/users/{user_id}/voicemails",
            params=params
        )

    # ==========================================
    # Sites & Extensions
    # ==========================================

    async def list_sites(
        self,
        page_size: int = 30,
        next_page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all sites (locations).

        Args:
            page_size: Number of records per page
            next_page_token: Token for pagination

        Returns:
            List of sites
        """
        params = {"page_size": min(page_size, 100)}

        if next_page_token:
            params["next_page_token"] = next_page_token

        return await self._make_request("GET", "/phone/sites", params=params)

    async def get_extension_details(
        self,
        extension_id: str
    ) -> Dict[str, Any]:
        """
        Get details about a specific extension.

        Args:
            extension_id: The extension ID

        Returns:
            Extension details and configuration
        """
        return await self._make_request(
            "GET",
            f"/phone/extension/{extension_id}"
        )

    # ==========================================
    # SMS Messages
    # ==========================================

    async def list_sms_messages(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page_size: int = 30,
        phone_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List SMS messages.

        Args:
            from_date: Start date
            to_date: End date
            page_size: Number of records per page
            phone_number: Filter by phone number

        Returns:
            List of SMS messages
        """
        params = {"page_size": min(page_size, 100)}

        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")
        if phone_number:
            params["phone_number"] = phone_number

        return await self._make_request("GET", "/phone/sms", params=params)

    async def send_sms(
        self,
        to_number: str,
        from_number: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send an SMS message.

        Args:
            to_number: Recipient phone number
            from_number: Sender phone number
            message: Message content

        Returns:
            Sent message details
        """
        data = {
            "to_number": to_number,
            "from_number": from_number,
            "message": message
        }

        return await self._make_request("POST", "/phone/sms", json_data=data)

    # ==========================================
    # Call Queues
    # ==========================================

    async def list_call_queues(
        self,
        page_size: int = 30,
        next_page_token: Optional[str] = None,
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all call queues.

        Args:
            page_size: Number of records per page
            next_page_token: Token for pagination
            site_id: Filter by site

        Returns:
            List of call queues
        """
        params = {"page_size": min(page_size, 100)}

        if next_page_token:
            params["next_page_token"] = next_page_token
        if site_id:
            params["site_id"] = site_id

        return await self._make_request("GET", "/phone/call_queues", params=params)

    async def get_call_queue(self, queue_id: str) -> Dict[str, Any]:
        """
        Get details of a specific call queue.

        Args:
            queue_id: The call queue ID

        Returns:
            Call queue configuration and members
        """
        return await self._make_request("GET", f"/phone/call_queues/{queue_id}")

    # ==========================================
    # Utility Methods
    # ==========================================

    async def get_all_paginated_results(
        self,
        method_func,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Helper to get all results from a paginated endpoint.

        Args:
            method_func: The async method to call
            **kwargs: Arguments to pass to the method

        Returns:
            Combined list of all results
        """
        all_results = []
        next_page_token = None

        while True:
            if next_page_token:
                kwargs["next_page_token"] = next_page_token

            response = await method_func(**kwargs)

            # Extract items based on common response patterns
            items = None
            for key in [
                "phone_numbers", "users", "recordings", "call_history", "voicemails", "sites", "call_queues"
            ]:
                if key in response:
                    items = response[key]
                    break

            if items:
                all_results.extend(items)

            # Check for next page
            next_page_token = response.get("next_page_token")
            if not next_page_token:
                break

        return all_results
