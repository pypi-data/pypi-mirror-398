import qrcode
from pathlib import Path
from flowtask.components import UserComponent
from flowtask.exceptions import ComponentError


class CreateQR(UserComponent):
    async def start(self, **kwargs):
        self.data = None
        if self.previous:
            self.data = self.input
        if self.data.empty:
            raise ComponentError(
                "There is no data to work with."
            )
        if hasattr(self, 'args'):
            for k, v in self.args.items():
                print('ARGS > ', k, v)
                value = self.mask_replacement(v)
                self.args[k] = value
            print('ARGS > ', self.args)

    async def run(self):
        content = self.content
        for index, row in self.data.iterrows():
            employee = row.to_dict()
            contenido = content.format(**employee)
            directory = str(self.directory).format(**employee)
            qr = qrcode.make(contenido)
            filename = str(self.filename).format(**employee)
            directory = Path(directory)
            if not directory.exists():
                directory.mkdir(parents=True)
            with open(directory.joinpath(filename), 'wb') as f:
                qr.save(f)
        return True

    async def close(self):
        print('CERRAR COMPONENTE')
