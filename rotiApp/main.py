from rotiScreenManager import rotiScreenManager, MainScreen, ScanScreen, WarningScreen, RecipeScreen
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import ButtonBehavior
from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.core.window import Window
from contextlib import ExitStack


class ScreenManagerApp(App):
    def build(self):
        Builder.load_file("main.kv")
        self.manager = rotiScreenManager()
        return self.manager

    def on_stop(self):
        self.manager.on_stop()


if __name__ == "__main__":
    Window.size = (800, 480)
    ScreenManagerApp().run()
