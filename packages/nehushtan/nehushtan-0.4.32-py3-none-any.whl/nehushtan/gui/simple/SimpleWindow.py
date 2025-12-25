from abc import abstractmethod

import PySimpleGUI as PySimpleGUI

from nehushtan.gui.simple.constants.SimpleGuiTheme import SimpleGuiTheme


class SimpleWindow:
    def __init__(
            self,
            title: str,
            theme: SimpleGuiTheme = None
    ):
        if theme is not None:
            # Add a touch of color
            PySimpleGUI.theme(theme.get_theme_name())

        # Create the Window
        self.__window = PySimpleGUI.Window(title)

    def get_window(self):
        return self.__window

    @abstractmethod
    def get_current_layout(self) -> list[list]:
        pass

    def set_window_layout(self, layout: list[list]):
        # All the stuff inside your window.
        self.__window.layout(layout)
        return self

    @abstractmethod
    def should_continue_loop_after_event(self, event, values) -> bool:
        """
        if return false, exit event loop
        """
        pass

    def start_loop(self):
        # initialize layout
        self.set_window_layout(self.get_current_layout())
        # Event Loop to process "events" and get the "values" of the inputs
        while True:
            event, values = self.__window.read()
            print(event, values)
            # if event == PySimpleGUI.WIN_CLOSED \
            #         or event == 'Cancel' or event == 'Ok':
            #     # if user closes window or clicks cancel
            #     break
            # print('You entered ', values[0])
            if not self.should_continue_loop_after_event(event, values):
                break

        self.__window.close()
