from flowtask.components import UserComponent


class Use1(UserComponent):
    async def start(self, **kwargs):
        print('START DE MI COMPONENTE')

    async def run(self):
        print('RUN DE MI COMPONENTE')
        return True

    async def close(self):
        print('CERRAR COMPONENTE')
