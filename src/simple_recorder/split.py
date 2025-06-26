import obsws_python as obsws
from clypi import Command, arg

from .errors import SimpleRecorderError


class Split(Command):
    """Split recording."""

    host: str = arg(inherited=True)
    port: int = arg(inherited=True)
    password: str = arg(inherited=True)

    async def run(self):
        with obsws.ReqClient(
            host=self.host, port=self.port, password=self.password
        ) as client:
            resp = client.get_record_status()
            if not resp.output_active:
                raise SimpleRecorderError("Recording is not active.")
            if resp.output_paused:
                raise SimpleRecorderError(
                    "Recording is paused. Please resume before splitting."
                )

            client.split_record_file()
            print("Recording split successfully.")
