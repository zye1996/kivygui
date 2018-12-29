from kivy.app import App
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.config import Config
from rotiSerial import rotiSerial
from RecipeUI import Recipe, ManualWidget, QRWidget
import json

Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '480')


class Container(RelativeLayout):
    display = ObjectProperty()
    rotisToMake = 0
    bowlState = True
    # pass "COM5" for windows
    rotiComs = rotiSerial("COM8")

    def rotiSub(self):
        if self.rotisToMake > 0:
            self.rotisToMake -= 1
            self.ids.rotiNumber.text = "{:0>2d}".format(self.rotisToMake)

    def rotiAdd(self):
        if self.rotisToMake < 99:
            self.rotisToMake += 1
            self.ids.rotiNumber.text = "{:0>2d}".format(self.rotisToMake)

    def rotiMake(self):
        if self.rotisToMake > 0:
            self.rotiComs.sendMakeRoti(self.rotisToMake)
            self.rotisToMake = 0
            self.ids.rotiNumber.text = "{:0>2d}".format(self.rotisToMake)

    def rotiSendRecp(self):
        print(self.ids.recipe.content.ids)
        recipe = self.ids.recipe.content
        cookProfileA = {"cook_top": {"time": recipe.ids.top_cook_time.value, "tempTop": recipe.ids.top_cook_temp.value,
                                    "tempBottom": recipe.ids.bottom_uncook_temp.value},
                      "cook_bottom": {"time": recipe.ids.bottom_cook_time.value,
                                     "tempTop": recipe.ids.top_uncook_temp.value,
                                    "tempBottom": recipe.ids.bottom_cook_temp.value},
                   "platen_opening": recipe.ids.wedge_opening.value}
        kneadProfile = {"speeds": recipe.ids.knead_speed.text.split(","), "times": recipe.ids.knead_time.text.split(",")}

        # print(cookProfileA)
        # print(kneadProfile)
        # print(str(self.ids.qty_flour.value),str(self.ids.qty_water.value),str(self.ids.qty_oil.value))
        self.rotiComs.sendCook(cookProfileA)
        # Take speed and time from text field and convert to array
        self.rotiComs.sendMix(kneadProfile)
        self.rotiComs.sendRecipe(recipe.ids.qty_water.value, recipe.ids.qty_flour.value, recipe.ids.qty_oil.value)

    def bowlToggle(self):
        if self.bowlState:
            self.rotiComs.sendRemoveBowl()
            self.ids.buttonBowl.text = "Close Bowl"
        else:
            self.rotiComs.sendReturnedBowl()
            self.ids.buttonBowl.text = "Open Bowl"
        self.bowlState = not self.bowlState

    def rotiCancel(self):
        pass

    def feedbackCaller(self, arg):
        responseStr = self.rotiComs.readLineSerial()
        print(responseStr)
        if responseStr:
            self.ids.logwindow.text += "\n" + responseStr.decode("UTF-8")

    def startEventHandler(self):
        self.event = Clock.schedule_interval(self.feedbackCaller, 5)


class Tooltip(Label):
    pass


class RGSlider(Slider):
    tooltip = Tooltip(text='Hello world')
    label_text = StringProperty('')
    tooltip_ref = ObjectProperty(None)

    def __init__(self, **kwargs):
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(Slider, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]

    # Uncomment below lines for tooltip. Need to fix tooltip display position
    #        self.tooltip.pos = pos
    #        Clock.unschedule(self.display_tooltip) # cancel scheduled event since I moved the cursor
    #        self.close_tooltip() # close if it's opened
    #        if self.collide_point(*self.to_widget(*pos)):
    #            Clock.schedule_once(self.display_tooltip, 1)

    def close_tooltip(self, *args):
        Window.remove_widget(self.tooltip)

    def display_tooltip(self, *args):
        self.tooltip.text = self.label_text
        Window.add_widget(self.tooltip)


class MainApp(App):

    def build(self):
        self.title = 'RotiGenie'
        c = Container()
        c.startEventHandler()
        return c

    #def on_start(self):
     #   self.root_window.maximize()


if __name__ == "__main__":
    app = MainApp()
    app.run()
