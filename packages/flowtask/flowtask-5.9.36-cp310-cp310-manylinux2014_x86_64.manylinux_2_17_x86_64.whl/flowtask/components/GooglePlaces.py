import asyncio
import re
import urllib
import pandas as pd
import orjson
from ..exceptions import DataNotFound, ComponentError
from .google import GoogleBase


class GooglePlaces(GoogleBase):
    """
    GooglePlaces.

    |---|---|---|
    | version | No | version of component |


        Example:

        | Name | Required | Summary |
    |---|---|---|
    | version | No | version of component |


        Example:

        ```yaml
          GooglePlaces:
          # attributes here
        ```
    """
    _version = "1.0.0"
    _base_url: str = "https://maps.googleapis.com/maps/api/"

    async def rating_reviews(
        self,
        idx: int,
        row: pd.Series
    ):
        """Getting Place Reviews using the Google Places API.

        Args:
            idx: row index
            row: pandas row

        Returns:
            Review Information.
        

        Example:

        ```yaml
        GooglePlaces:
          type: traffic
          paid_proxy: true
        ```

    """
        url = self._base_url + 'place/details/json'
        # url = "https://places.googleapis.com/v1/places/{place_id}?"
        async with self.semaphore:
            place_id = row['place_id']
            if not place_id:
                return idx, None
            params = {
                "placeid": place_id,
                "fields": "rating,reviews,user_ratings_total,name",
                "key": self.api_key
            }
            self._logger.notice(
                f"Looking for {place_id}"
            )
            # url = url.format(place_id=place_id)
            session_args = self._get_session_args()
            response = await self._google_session(
                url=url,
                session_args=session_args,
                params=params,
                use_proxies=True
            )
            if not response:
                return idx, None
            place_info = response.get('result', {})
            self._counter += 1
            return idx, place_info

    async def run(self):
        """Run the Google Places API."""
        if 'place_id' not in self.data.columns:
            raise DataNotFound(
                "Missing 'place_id' column in the input DataFrame."
            )
        if self._type == 'rating_reviews':
            self.column_exists('rating')
            self.column_exists('reviews')
            self.column_exists('user_ratings_total')
            self.column_exists('name')
        elif self._type == 'traffic':
            # 'address_components', 'formatted_address', 'geometry', 'name',
            # 'place_id', 'types', 'vicinity', 'rating', 'rating_n',
            # 'current_popularity', 'popular_times', 'time_spent'
            self.column_exists('address_components')
            self.column_exists('formatted_address')
            self.column_exists('geometry')
            self.column_exists('name')
            self.column_exists('place_id')
            self.column_exists('types')
            self.column_exists('vicinity')
            self.column_exists('rating')
            self.column_exists('rating_n')
            self.column_exists('current_popularity')
            self.column_exists('popular_times')
            self.column_exists('traffic')
            self.column_exists('time_spent')
        self._logger.notice(
            f"Google Places API: Looking for {len(self.data)} places."
        )
        return await super().run()

    def convert_populartimes(self, popular_times: dict):
        # Map day numbers to day names
        day_mapping = {
            "1": "Monday",
            "2": "Tuesday",
            "3": "Wednesday",
            "4": "Thursday",
            "5": "Friday",
            "6": "Saturday",
            "7": "Sunday"
        }
        # Dictionary to hold the final structured data
        converted_data = {}
        # Iterate through each day and its hours
        for day_number, hours in popular_times.items():
            # Get the day name from the mapping
            day_name = day_mapping.get(day_number, "Unknown")
            converted_data[day_name] = {}

            for hour, data in hours.items():
                # Convert the hour to HH:MM:SS format
                # Ensure leading zeroes for single-digit hours
                time_str = f"{int(hour):02}:00:00"
                # Create the structured dictionary
                converted_data[day_name][time_str] = {
                    "hour": int(hour),
                    "human_hour": data["human_hour"],
                    "traffic": data["traffic"],
                    "traffic_status": data["traffic_status"]
                }
        return converted_data

    async def traffic(
        self,
        idx: int,
        row: pd.Series
    ):
        """get the current status of popular times (Traffic).

        Args:
            idx: row index
            row: pandas row

        Returns:
            Place information with Traffic.
        """
        url = self._base_url + 'place/details/json'
        async with self.semaphore:
            place_id = row['place_id']
            if not place_id:
                return idx, None
            params = {
                "placeid": place_id,
                "key": self.api_key,
                "fields": "name,place_id,address_components,formatted_address,geometry,types,vicinity"
            }
            self._logger.notice(
                f"Looking for {place_id}"
            )
            session_args = self._get_session_args()
            response = await self._google_session(
                url,
                session_args,
                params,
                use_proxies=True
            )
            if not response:
                return idx, None
            place_info = response.get('result', {})
            _name = place_info.get('name')
            _address = place_info.get('formatted_address', place_info.get("vicinity", ""))
            address = _name + ', ' + _address
            popular_times = None
            try:
                pdata = await self.make_google_search(address)
            except ValueError:
                pdata = None
            if pdata:
                self.get_populartimes(place_info, pdata)
                popular_times = place_info['popular_times']
            # Convert popular_times into a dictionary
            if popular_times is not None:
                popular_times = {str(item[0]): item[1] for item in popular_times}
                for k, v in popular_times.items():
                    new_dict = {}
                    for traffic in v:
                        hour = str(traffic[0])
                        new_dict[hour] = {
                            "human_hour": traffic[4],
                            "traffic": traffic[1],
                            "traffic_status": traffic[2]
                        }
                    popular_times[k] = new_dict
                place_info['popular_times'] = popular_times
                try:
                    place_info['traffic'] = self.convert_populartimes(
                        popular_times
                    )
                except Exception as e:
                    place_info['traffic'] = {}
                    print('Error Formatting Traffic: ', e)
            self._counter += 1
            return idx, place_info

    def index_get(self, array, *argv):
        """
        checks if a index is available in the array and returns it
        :param array: the data array
        :param argv: index integers
        :return: None if not available or the return value
        """

        try:
            for index in argv:
                array = array[index]
            return array
        # there is either no info available or no popular times
        # TypeError: rating/rating_n/populartimes wrong of not available
        except (IndexError, TypeError):
            return None

    def get_populartimes(self, place_info, data):
        # get info from result array, has to be adapted if backend api changes
        info = self.index_get(data, 0, 1, 0, 14)
        rating = self.index_get(info, 4, 7)
        rating_n = self.index_get(info, 4, 8)
        popular_times = self.index_get(info, 84, 0)
        # current_popularity is also not available if popular_times isn't
        current_popularity = self.index_get(info, 84, 7, 1)
        time_spent = self.index_get(info, 117, 0)
        # extract wait times and convert to minutes
        if time_spent:
            nums = [float(f) for f in re.findall(r'\d*\.\d+|\d+', time_spent.replace(",", "."))]
            contains_min, contains_hour = "min" in time_spent, "hour" in time_spent or "hr" in time_spent
            time_spent = None
            if contains_min and contains_hour:
                time_spent = [nums[0], nums[1] * 60]
            elif contains_hour:
                time_spent = [nums[0] * 60, (nums[0] if len(nums) == 1 else nums[1]) * 60]
            elif contains_min:
                time_spent = [nums[0], nums[0] if len(nums) == 1 else nums[1]]

            time_spent = [int(t) for t in time_spent]
        # Update the current Place_info Dictionary
        place_info.update(
            **{
                "rating": rating,
                "rating_n": rating_n,
                "current_popularity": current_popularity,
                "popular_times": popular_times,
                "time_spent": time_spent
            }
        )

    async def make_google_search(self, query_string: str):
        params_url = {
            "tbm": "map",
            "tch": 1,
            "hl": "en",
            "q": urllib.parse.quote_plus(query_string),
            "pb": "!4m12!1m3!1d4005.9771522653964!2d-122.42072974863942!3d37.8077459796541!2m3!1f0!2f0!3f0!3m2!1i1125!2i976"
                  "!4f13.1!7i20!10b1!12m6!2m3!5m1!6e2!20e3!10b1!16b1!19m3!2m2!1i392!2i106!20m61!2m2!1i203!2i100!3m2!2i4!5b1"
                  "!6m6!1m2!1i86!2i86!1m2!1i408!2i200!7m46!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e3!2b0!3e3!"
                  "1m3!1e4!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e3!2b1!3e2!1m3!1e9!2b1!3e2!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e"
                  "10!2b0!3e4!2b1!4b1!9b0!22m6!1sa9fVWea_MsX8adX8j8AE%3A1!2zMWk6Mix0OjExODg3LGU6MSxwOmE5ZlZXZWFfTXNYOGFkWDh"
                  "qOEFFOjE!7e81!12e3!17sa9fVWea_MsX8adX8j8AE%3A564!18e15!24m15!2b1!5m4!2b1!3b1!5b1!6b1!10m1!8e3!17b1!24b1!"
                  "25b1!26b1!30m1!2b1!36b1!26m3!2m2!1i80!2i92!30m28!1m6!1m2!1i0!2i0!2m2!1i458!2i976!1m6!1m2!1i1075!2i0!2m2!"
                  "1i1125!2i976!1m6!1m2!1i0!2i0!2m2!1i1125!2i20!1m6!1m2!1i0!2i956!2m2!1i1125!2i976!37m1!1e81!42b1!47m0!49m1"
                  "!3b1"
        }
        search_url = "https://www.google.com/search?" + "&".join(k + "=" + str(v) for k, v in params_url.items())
        # self._logger.debug(
        #     f':: SEARCH URL {search_url} '
        # )
        try:
            session_args = self._get_session_args()
            response = await self._google_session(
                search_url,
                session_args,
                method='GET',
                as_json=False,
                use_proxies=True,
                google_search=True
            )
            await asyncio.sleep(0.5)
            if not response:
                raise ValueError(
                    "Unable to get Google Search"
                )
            result = response.decode('utf-8')
            # Decode response and ensure it's not empty
            data = result.split('/*""*/')[0].strip()
            if not data:
                raise ValueError(
                    "Empty response from Google Search"
                )
        except Exception as e:
            raise ValueError(e)

        try:
            # find eof json
            jend = data.rfind("}")
            if jend >= 0:
                data = data[:jend + 1]
            # Attempt to load the JSON data
            jdata = orjson.loads(data)["d"]
            return orjson.loads(jdata[4:])

        except orjson.JSONDecodeError as e:
            self._logger.error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            self._logger.error(
                f"An error occurred during Google Search: {e}"
            )
            raise ComponentError(
                f"Google Search Error: {e}"
            ) from e
