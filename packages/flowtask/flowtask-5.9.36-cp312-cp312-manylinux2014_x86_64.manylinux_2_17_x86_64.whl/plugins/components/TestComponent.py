from flowtask.components import UserComponent

class TestComponent(UserComponent):

    async def start(self, **kwargs):
        """
        start.
            Initialize (if needed) a task
        """
        self.hola = 'Hello World'
        print('CALLING START METHOD')
        print('Service: ', self.service)

    async def run(self):
        """
        run.
            Close (if needed) a task
        """
        print('CALLING RUN METHOD')
        print(f'===== {self.hola} =======')
        return True

    async def close(self):
        """
        close.
            Close (if needed) a task
        """
        print('CALLING CLOSE METHOD')
