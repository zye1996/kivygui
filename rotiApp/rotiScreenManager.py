from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.properties import StringProperty, ObjectProperty
from kivy.app import App
from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.core.window import Window
from Services import QRScanner, SerialMonitor
from StateMachine import StateMachine
from functools import wraps
import queue
import threading
import time



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


class MainScreen(Screen):
    pass


class RunningScreen(Screen):
    pass


class RecipeScreen(Screen):

    def update_recipe(self, recipe):
        for k in recipe.keys():
            self.ids[k].value = recipe[k]


class ScanScreen(Screen):
    pass


# TODO: Change the image for different messages
class WarningScreen(Screen):

    warning_text = StringProperty()

    def change_warning_text(self, text):
        self.warning_text = str(text)


class rotiScreenManager(ScreenManager):

    last = None

    # buffers
    rotisToMake = 0
    possibleToMake = 100

    class GuiUpdater:

        def __init__(self, UI_handler):
            self.lock = threading.Lock()
            self.handler = UI_handler

        def lock_update(func):
            @wraps(func)
            def with_lock(self, *args, **kwargs):
                self.lock.acquire()
                func(self, *args, **kwargs)
                self.lock.release()
            return with_lock

        @lock_update
        def make_button_update(self, disable):
            self.handler.disable_make(disable)

        @lock_update
        def possibleToMake_update(self, num):
            self.handler.set_possible_make(num)

        @lock_update
        def recipe_update(self, recipe):
            pass

        @lock_update
        def warning_update(self, warn_msg):
            self.handler.warn(warn_msg)

        @lock_update
        def rotiCount_update(self, num):
            self.handler.set_roti_count(num)

        @lock_update
        def to_running(self):
            self.handler.set_roti_count(0)
            self.handler.to_running_screen()

    def __init__(self):
        #self.startEventHandler()
        super().__init__()
        self.QRScanner = QRScanner()
        self.GuiUpdater = self.GuiUpdater(self)
        # TODO queue
        self.state_machine_q = queue.Queue()
        self.info_q = queue.Queue()
        # TODO initialize recipe screen
        initial_recipe = {option: self.ids.recipe_screen.ids[option].value for option in self.ids.recipe_screen.ids
                          if isinstance(self.ids.recipe_screen.ids[option], RGSlider)}
        self.stateMachine = StateMachine(self.GuiUpdater, initial_recipe, self.state_machine_q)
        self.SerialMonitor = SerialMonitor(self.state_machine_q, self.info_q, dev="COM8")

        self.stateMachine.start()

    # sync methods
    # Main Screen
    def rotiSub(self):
        if self.rotisToMake > 0:
            self.rotisToMake -= 1
            self.ids.main_screen.ids.rotiNumber.text = "{:0>2d}".format(self.rotisToMake)

    def rotiAdd(self):
        if self.rotisToMake < min(99, self.possibleToMake):
            self.rotisToMake += 1
            self.ids.main_screen.ids.rotiNumber.text = "{:0>2d}".format(self.rotisToMake)

    def rotiMake(self):
        if self.rotisToMake > 0:
            request = {"CMD": "MAKE", "QTY": self.rotisToMake}
            self.SerialMonitor.send_data(request)
            self.rotisToMake = 0
            self.ids.main_screen.ids.rotiNumber.text = "{:0>2d}".format(self.rotisToMake)

    def to_recipe_screen(self):
        self.update_recipe(self.stateMachine.get_recipe())
        self.current = "recipe_screen"

    # Recipe Screen
    def QR_scan(self):
        result, recipe = self.QRScanner.scan(5)
        if result != "OK":
            self.warn(result)
        else:
            # update
            self.warn(result)
            self.update_recipe(recipe)

    def apply_recipe(self):
        print(self.ids.recipe.content.ids)
        recipe = self.ids.recipe.content
        cookProfileA = {"cook_top": {"time": recipe.ids.top_cook_time.value, "tempTop": recipe.ids.top_cook_temp.value,
                                     "tempBottom": recipe.ids.bottom_uncook_temp.value},
                        "cook_bottom": {"time": recipe.ids.bottom_cook_time.value,
                                        "tempTop": recipe.ids.top_uncook_temp.value,
                                        "tempBottom": recipe.ids.bottom_cook_temp.value},
                        "platen_opening": recipe.ids.wedge_opening.value}
        kneadProfile = {"speeds": recipe.ids.knead_speed.text.split(","),
                        "times": recipe.ids.knead_time.text.split(",")}

        request = {"CMD": "RECIPE", "cookProfile": cookProfileA, "kneadProfile": kneadProfile,
                   "qty": [recipe.ids.qty_water.value, recipe.ids.qty_flour.value, recipe.ids.qty_oil.value]}
        # check whether the message is sent successfully
        if self.SerialMonitor.send_data(request) != -1:
            self.stateMachine.machine_status.recipe = recipe
        pass

    def to_main_screen(self):
        self.current = "main_screen"

    # Warning Screen
    def ok(self):
        self.current = self.last
        pass

    def cancel(self):
        pass

    # async methods
    def warn(self, msg):
        self.last = self.current if self.current != self.last else self.last
        self.ids["warning_screen"].change_warning_text(msg)
        self.current = "warning_screen"

    def set_possible_make(self, num):
        self.possibleToMake = num
        self.rotisToMake = num if num < self.rotisToMake else self.rotisToMake
        self.ids.main_screen.ids.rotiNumber.text = "{:0>2d}".format(self.rotisToMake)
        self.ids["main_screen"].ids.possibleToMake.text = "/" + str(num)
        # TODO add possibleToMake Label

    def disable_make(self, disable):
        self.ids["main_screen"].ids.buttonMake.disable = disable

    # TODO update the recipe display
    def update_recipe(self, recipe):
        self.ids.recipe_screen.update_recipe(recipe)
        pass

    def set_roti_count(self, num):
        self.ids.running_screen.rotiCount.text = num

    def to_running_screen(self):
        self.current = 'running_screen'

    # exit method
    def on_stop(self):
        self.QRScanner.close()
        self.SerialMonitor.close()
        self.stateMachine.close()
        pass

'''
    # response method
    def on_touch_down(self, touch):
        self.initial_touch = touch.x

    def on_touch_up(self, touch):
        if touch.x > self.initial_touch:
            if self.current == "recipe_screen":
                self.current = "main_screen"
        elif touch.x < self.initial_touch:
            if self.current == "main_screen":
                self.current = "recipe_screen"'''

