import iso8601
from .Azure import Azure
from ..exceptions import ComponentError, DataNotFound

class AzureUsers(Azure):
    """
    AzureUsers Component

        Overview

        This component retrieves a list of users from Azure Active Directory (AAD) using the Microsoft Graph API.

            :widths: auto

    | credentials            |   Yes    | Dictionary placeholder for Azure AD application credentials.                                |
    | most_recent (optional) |    No    | ISO 8601-formatted date and time string to filter users created on or after that date/time. |                                                                                                                                |

    **Returns**

        A pandas DataFrame containing the retrieved user information. Each row represents an Azure user, and columns might include properties like:

        - `objectId`: Unique identifier for the user in AAD.
        - `displayName`: User's display name.
        - `userPrincipalName`: User's email address (usually the primary login).
        - ... (other user properties depending on the AAD response)

    **Error Handling**

        - The component raises a `ComponentError` with a detailed message in case of errors during authentication, API calls, or data processing. This error will be surfaced within your Flowtask workflow.


        Example:

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          AzureUsers:
          recent: '2023-10-01'
        ```
    """
    _version = "1.0.0"
    accept: str = 'application/json'

    async def get_users(self, most_recent: str = None):
        async def fetch_users(url: str, all_users: list):
            result, error = await self.async_request(url, self.method)
            if error:
                raise ComponentError(
                    f"{__name__}: Error in AzureUsers: {error}"
                )

            all_users.extend(result.get("value", []))

            next_link = result.get("@odata.nextLink")
            if next_link:
                await fetch_users(next_link, all_users)

        all_users = []
        if most_recent:
            utc_datetime = (
                iso8601.parse_date(most_recent).isoformat().replace("+00:00", "Z")
            )
            url = f"{self.users_info}?$filter=createdDateTime ge {utc_datetime}"
        else:
            url = f"{self.users_info}"
        await fetch_users(url, all_users)
        return all_users

    async def run(self):
        """Run Azure Connection for getting Users Info."""
        self._logger.info(
            f"<{__name__}>: Starting Azure Connection for getting Users Info."
        )
        self.app = self.get_msal_app()
        token, self.token_type = self.get_token()
        self.auth["apikey"] = token
        self.headers["Content-Type"] = "application/json"
        self.method = "GET"
        try:
            more_recent = None
            if hasattr(self, "recent"):
                more_recent = self.mask_replacement(self.recent)
            result = await self.get_users(more_recent)
            self._logger.info(f"<{__name__}>: Successfully got Users Info.")
            self._result = await self.create_dataframe(result)
            if self._result is None:
                raise DataNotFound(
                    "No data found for Azure Users."
                )
        except Exception as err:
            self._logger.error(err)
            raise ComponentError(f"{__name__}: Error in AzureUsers: {err}") from err
        numrows = len(self._result.index)
        self.add_metric("NUM_USERS", numrows)
        if self._debug is True:
            print(self._result)
            print("::: Printing Column Information === ")
            for column, t in self._result.dtypes.items():
                print(column, "->", t, "->", self._result[column].iloc[0])
        return self._result
