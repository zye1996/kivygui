from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanelItem
from kivy.uix.widget import Widget

import threading

class ModeWidget(BoxLayout):
    pass


class QRWidget(Widget):


    pass


class ManualWidget(GridLayout):
    pass


# Recipe Tab class
class Recipe(TabbedPanelItem):

    def switchModelSel(self):
        self.clear_widgets()
        self.add_widget(ModeWidget())

    def switchQR(self):
        self.clear_widgets()
        self.add_widget(QRWidget(id="qr"))

    def switchManual(self):
        self.clear_widgets()
        self.add_widget(ManualWidget(id="manual"))


