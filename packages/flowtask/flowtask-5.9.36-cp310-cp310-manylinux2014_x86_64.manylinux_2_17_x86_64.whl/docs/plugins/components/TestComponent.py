from flowtask.components import UserComponent

class TestComponent(UserComponent):

    async def start(self, **kwargs):
        """
        start.
            Initialize (if needed) a task
        """
        print('CALLING START METHOD')

    async def run(self):
        """
        run.
            Close (if needed) a task
        """
        print('CALLING RUN METHOD')
        return True

    async def close(self):
        """
        close.
            Close (if needed) a task
        """
        print('CALLING CLOSE METHOD')
