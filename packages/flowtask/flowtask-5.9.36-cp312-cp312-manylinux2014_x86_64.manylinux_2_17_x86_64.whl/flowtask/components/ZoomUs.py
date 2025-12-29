"""
Zoom Phone Component for FlowTask
Concrete implementation of ZoomPhoneInterface using HTTPService
"""
from typing import List, Optional, Dict, Any, Callable
import asyncio
import aiohttp
from ..interfaces.zoom import ZoomInterface
from .flow import FlowComponent
from ..conf import (
    ZOOM_ACCESS_TOKEN,
    ZOOM_CLIENT_ID,
    ZOOM_CLIENT_SECRET,
    ZOOM_ACCOUNT_ID,
)


class ZoomUs(ZoomInterface, FlowComponent):
    """
    Concrete implementation of Zoom Phone interface for FlowTask.

    This component extends the ZoomInterface and implements the HTTP
    communication layer using aiohttp (or you can use your HTTPService).

    The interface implements:
        ✅ download_call_metadata_by_extension - Get call history by extension number
        ✅ download_recording_by_call_id - Download recording files
        ✅ list_phone_numbers - List all phone numbers
        ✅ get_phone_number - Get specific phone number details
        ✅ download_recording_transcript - Get call transcripts
        ✅ get_user_recordings - Get user's recordings
        ✅ get_user_profile - Get user's profile
        ✅ list_phone_users - List all phone users

    Usage in a FlowTask YAML:

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          name: Download Zoom Call Recordings
          description: Download recordings for specific extensions
          steps:
          - ZoomUs:
          action: get_user_recordings
          user_id: "user@example.com"
          from_date: "2024-01-01"
          to_date: "2024-12-31"
          output_var: recordings

          - ZoomUs:
          action: download_recording_by_call_id
          call_id: "{recordings.0.call_id}"
          save_to: /path/to/recording.mp3
        ```
    """
    _version = "1.0.0"
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop = None,
        job: Callable = None,
        stat: Callable = None,
        **kwargs,
    ):
        """
        Initialize the Zoom Phone component.

        Args:
            access_token: OAuth access token (if already obtained)
            client_id: OAuth client ID (for getting new tokens)
            client_secret: OAuth client secret
            account_id: Zoom account ID
            timeout: Request timeout in seconds
        """
        self.access_token = kwargs.pop("access_token", ZOOM_ACCESS_TOKEN)
        self.client_id = kwargs.pop("client_id", ZOOM_CLIENT_ID)
        self.client_secret = kwargs.pop("client_secret", ZOOM_CLIENT_SECRET)
        self.account_id = kwargs.pop("account_id", ZOOM_ACCOUNT_ID)
        self.timeout = kwargs.get("timeout", 30)
        self.session: Optional[aiohttp.ClientSession] = None
        super().__init__(loop=loop, job=job, stat=stat, **kwargs)

    async def run(self) -> List[Dict[str, Any]]:
        """
        Execute the specified action with parameters.

        Returns:
            Result of the action
        """
        if not self.action:
            raise ValueError("No action specified in ZoomUs component")

        # Get the method
        method = getattr(self, self.action, None)
        if not method:
            raise ValueError(f"Unknown action: {self.action}")

        # Execute with params
        result = await method(**self.params)

        # Handle special cases
        if self.action.startswith("download_"):
            # If downloading, save to file if specified
            save_to = self.params.get("save_to")
            if save_to and isinstance(result, bytes):
                with open(save_to, "wb") as f:
                    f.write(result)
                return [{"status": "saved", "path": save_to, "size": len(result)}]

        self._result = result
        return result
