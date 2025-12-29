import pprint
from asyncdb.utils.types import SafeDict
from flowtask.components import UserComponent
from settings.settings import WORKPLACE_ACCESS_TOKEN

class Workplace(UserComponent):
    _messages_url = 'https://graph.facebook.com/{thread_id}/messages?access_token={access_token}&limit=20&user={member_id}&fields=id,message,created_time,attachments,from,to,tags'
    _members_url = 'https://graph.facebook.com/community/members?access_token={access_token}&limit=100&fields=member_id,first_name,last_name,name,email,title,organization,division,department,primary_phone,primary_address,picture,link,locale,updated_time,account_invite_time,account_claim_time,account_deactivate_time,external_id,start_date,about,cost_center,work_locale,frontline,active'
    _member_threads = 'https://graph.facebook.com/{member_id}/conversations/?access_token={access_token}&limit=100&fields=id,name,subject,participants,updated_time,messages'
    accept = 'application/json'

    async def start(self, **kwargs):
        ## Access Token
        if hasattr(self, 'access_token'):
            access_token = self.access_token
        else:
            access_token = WORKPLACE_ACCESS_TOKEN
        # Workplaces APIs.
        if self.type == 'messages':
            self.member_id = self.set_variables(self.member_id)
            self.thread_id = self.set_variables(self.thread_id)
            self.messages_url = self._messages_url.format_map(
                SafeDict(
                    access_token=access_token,
                    member_id=self.member_id,
                    thread_id=self.thread_id,
                )
            )
            self._kwargs = {
                "url": self.messages_url,
                "method": "get"
            }
        elif self.type == 'members':
            self.members_url = self._members_url.format_map(SafeDict(access_token=access_token))
            self._kwargs = {
                "url": self.members_url,
                "method": "get"
            }
        elif self.type == 'member_threads':
            self.member_id = self.set_variables(self.member_id)
            self.member_threads_url = self._member_threads.format_map(
                SafeDict(access_token=access_token, member_id=self.member_id)
            )
            self._kwargs = {
                "url": self.member_threads_url,
                "method": "get"
            }

    async def run(self):
        results = []
        result = await self.session(
            **self._kwargs
        )
        if not result:
            return False
        if 'data' in result:
            results += result['data']
        if 'paging' in result:
            url = result['paging']['next'] if 'next' in result['paging'] else None
            while url is not None:
                self._kwargs['url'] = url
                resultset = await self.session(
                    **self._kwargs
                )
                results += resultset['data']
                if 'paging' in result:
                    url = resultset['paging']['next'] if 'next' in resultset['paging'] else None
                else:
                    url = None
        # Iterate over a field to download more results:
        if hasattr(self, 'page_over'):
            columns = self.page_over
            for row in results:
                for column in columns:
                    try:
                        rw = row[column]
                    except KeyError:
                        # there is no messages in this thread
                        continue
                    if 'data' in rw:
                        # replacing "data" with current value of data:
                        row[column] = row[column]['data']
                    if 'paging' in row[column]:
                        url = row[column]['paging']['next'] if 'next' in row[column]['paging'] else None
                        while url is not None:
                            resultset = await self.session(
                                url=url,
                                method='get'
                            )
                            row[column] += resultset['data']
                            if 'paging' in result:
                                url = resultset['paging']['next'] if 'next' in resultset['paging'] else None
                            else:
                                url = None
        if hasattr(self, 'flatten_cols'):
            columns = self.flatten_cols
            for row in results:
                for column in columns:
                    try:
                        if 'data' in row[column]:
                            # replacing "data" with current value of data:
                            row[column] = row[column]['data']
                    except KeyError:
                        # there is no column in this thread
                        continue
        # Create a Dataframe from Results:
        self._result = self.create_dataframe(results)
        if self.type == 'member_threads':
            # add the value of member_id over all rows:
            self._result['member_id'] = self.member_id
        elif self.type == 'messages':
            self._result['member_id'] = self.member_id
            self._result['thread_id'] = self.thread_id
        return self._result

    async def close(self):
        pass
