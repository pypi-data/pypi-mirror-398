from PySimpleGUI import PySimpleGUI

from nehushtan.gui.simple.SimpleWindow import SimpleWindow


class SimpleGuiB(SimpleWindow):

    def __init__(self):
        super().__init__('SimpleGuiB')

        self.__graph = PySimpleGUI.Graph(
            graph_bottom_left=(0, 0),
            graph_top_right=(200, 100),
            background_color='orange',
            canvas_size=(200, 100)
        )

    def get_current_layout(self) -> list[list]:
        # # All the stuff inside your window.

        layout = [
            [
                # PySimpleGUI.Text('Some text on Row 1')
                self.__graph
            ],
            [PySimpleGUI.Text('y='), PySimpleGUI.InputText(default_text="x", key="formula")],
            [
                PySimpleGUI.Text('Ready', key='msg'),
                PySimpleGUI.Button('Draw'),
                # PySimpleGUI.Button('Cancel')
            ]
        ]
        return layout

    def should_continue_loop_after_event(self, event, values) -> bool:
        print('should_continue_loop_after_event', event, values)
        if event == PySimpleGUI.WIN_CLOSED:
            return False
        # if event == 'Cancel':
        #     print("cancelled")
        #     return False
        if event == 'Draw':
            self.get_window().set_title(values[0])

            try:
                x = 0
                while x <= 200:
                    s: str = values['formula']
                    s.replace("x", f'{x}')
                    y = eval(s)
                    self.__graph.draw_point((x, y))
                    x += 0.1
            except Exception as e:
                print(e)
                self.get_window()['msg'].update(e.__str__())

            return True


if __name__ == '__main__':
    sw = SimpleGuiB()
    sw.start_loop()
