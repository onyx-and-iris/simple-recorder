import logging

import FreeSimpleGUI as fsg
import obsws_python as obsws

from .errors import SimpleRecorderError
from .start import Start
from .stop import Stop

logger = logging.getLogger(__name__)


class SimpleRecorderWindow(fsg.Window):
    def __init__(self, host, port, password, theme):
        self.logger = logger.getChild(self.__class__.__name__)
        self.host = host
        self.port = port
        self.password = password
        fsg.theme(theme)

        try:
            with obsws.ReqClient(
                host=self.host, port=self.port, password=self.password, timeout=3
            ) as client:
                resp = client.get_version()
                status_message = f"Connected to OBS {resp.obs_version} ✓"
        except (ConnectionRefusedError, TimeoutError):
            status_message = "Failed to connect to OBS. Is it running?"

        recorder_layout = [
            [fsg.Text("Enter recording filename:", key="-PROMPT-")],
            [fsg.InputText("default_name", key="-FILENAME-", focus=True, size=(45, 1))],
            [
                fsg.Button("Start", key="Start Recording", size=(10, 1)),
                fsg.Button("Stop", key="Stop Recording", size=(10, 1)),
                fsg.Button("Pause", key="Pause Recording", size=(10, 1)),
            ],
            [
                fsg.Button("Split", key="Split Recording", size=(10, 1)),
                fsg.Button("Add Chapter", key="Add Chapter", size=(10, 1)),
            ],
        ]

        frame = fsg.Frame(
            "",
            recorder_layout,
            relief=fsg.RELIEF_SUNKEN,
        )

        recorder_tab = fsg.Tab(
            "Recorder",
            [
                [frame],
                [
                    fsg.Text(
                        f"Status: {status_message}",
                        key="-OUTPUT-",
                        text_color="white"
                        if status_message.startswith("Connected")
                        else "red",
                    )
                ],
            ],
        )

        settings_layout = [
            [fsg.Text("Enter the filepath for the recording:")],
            [fsg.InputText("", key="-FILEPATH-", size=(45, 1))],
        ]

        settings_tab = fsg.Tab("Settings", settings_layout)

        mainframe = [
            [fsg.TabGroup([[recorder_tab, settings_tab]])],
        ]

        super().__init__("Simple Recorder", mainframe, finalize=True)
        self["-FILENAME-"].bind("<Return>", " || RETURN")
        self["Start Recording"].bind("<Return>", " || RETURN")
        self["Stop Recording"].bind("<Return>", " || RETURN")

        self["-FILENAME-"].bind("<KeyPress>", " || KEYPRESS")
        self["-FILENAME-"].update(select=True)
        self["Add Chapter"].bind("<FocusIn>", " || FOCUS")
        self["Add Chapter"].bind("<Enter>", " || FOCUS")
        self["Add Chapter"].bind("<FocusOut>", " || LEAVE")
        self["Add Chapter"].bind("<Leave>", " || LEAVE")
        self["Add Chapter"].bind("<Button-3>", " || RIGHT_CLICK")

    async def run(self):
        while True:
            event, values = self.read()
            self.logger.debug(f"Event: {event}, Values: {values}")
            if event == fsg.WIN_CLOSED:
                break

            match e := event.split(" || "):
                case ["Start Recording"] | ["Start Recording" | "-FILENAME-", "RETURN"]:
                    try:
                        await Start(
                            filename=values["-FILENAME-"],
                            host=self.host,
                            port=self.port,
                            password=self.password,
                        ).run()
                        self["-OUTPUT-"].update(
                            "Recording started successfully", text_color="green"
                        )
                    except SimpleRecorderError as e:
                        self["-OUTPUT-"].update(
                            f"Error: {e.raw_message}", text_color="red"
                        )

                case ["Stop Recording"] | ["Stop Recording", "RETURN"]:
                    try:
                        await Stop(
                            host=self.host, port=self.port, password=self.password
                        ).run()
                        self["-OUTPUT-"].update(
                            "Recording stopped successfully", text_color="green"
                        )
                    except SimpleRecorderError as e:
                        self["-OUTPUT-"].update(
                            f"Error: {e.raw_message}", text_color="red"
                        )

                case ["Add Chapter", "FOCUS" | "LEAVE" as focus_event]:
                    if focus_event == "FOCUS":
                        self["-OUTPUT-"].update(
                            "Right-click to set a chapter name", text_color="white"
                        )
                    else:
                        self["-OUTPUT-"].update("", text_color="white")

                case ["Add Chapter", "RIGHT_CLICK"]:
                    _ = fsg.popup_get_text(
                        "Enter chapter name:",
                        "Add Chapter",
                        default_text="unnamed",
                    )

                case ["Pause Recording" | "Split Recording" | "Add Chapter"]:
                    self["-OUTPUT-"].update(
                        "This feature is not implemented yet", text_color="orange"
                    )

                case _:
                    self.logger.debug(f"Unhandled event: {e}")

        self.close()
