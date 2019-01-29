'''

The state machine thread implementation

'''

import threading


class StateMachine(threading.Thread):

    # class to keep track of the remaining of ingredient
    class MachineStatus:

        def __init__(self, recipe):
            self._remain = {"FLR": -1, "WTR": -1, "OIL": -1}
            self._recipe = recipe
            self._possibleToMake = 100

        @property
        def remain(self):
            return self._remain

        def set_remain(self, flour, water, oil):
            if not (isinstance(flour, int) and isinstance(water, int) and isinstance(oil, int)):
                raise ValueError('score must be an integer!')
            else:
                self._remain.update({"FLR": flour, "WTR": water, "OIL": oil})
            updated = self.calc_possible_roti()
            if updated != self._possibleToMake:
                self._possibleToMake = updated
                return True
            else:
                return False

        @property
        def recipe(self):
            return self._recipe

        @recipe.setter
        def recipe(self, recipe):
            self._recipe = recipe
            self._possibleToMake = self.calc_possible_roti()

        @property
        def possibleToMake(self):
            return self._possibleToMake

        # TODO calculated possible roti
        def calc_possible_roti(self):
            return 1


    STATE = {
        "INIT": 0,
        "SUSPEND": 1,
        "READY": 2,
        "RUNNING": 3,
        "DONE": 4,
        "PAUSED": 5
    }

    def __init__(self, gui_handler, initial_recipe, state_queue):

        super().__init__()
        self.state = self.STATE["INIT"]
        self.state_queue = state_queue
        self.lock = threading.Lock()
        self.machine_status = self.MachineStatus(initial_recipe)
        self.gui_handler = gui_handler

    def run(self):

        while True:
            new_state = self.state_queue.get()
            if new_state is None:
                break
            self.state_update(new_state)

    def state_update(self, state_msg):
        self.lock.acquire()

        next_state = state_msg["STATE"]

        # TODO
        if self.state == self.STATE["INIT"]:
            if next_state == self.STATE["READY"]:
                # here to update the possible roti make by calculating by recipe
                if self.machine_status.set_remain(state_msg["FLR"], state_msg["WTR"], state_msg["OIL"]):
                    self.gui_handler.possibleToMake_update(self.machine_status.possibleToMake)  # update possible to make
                self.gui_handler.make_button_update(False)
                # self.updateUI()

        elif self.state == self.STATE["READY"]:
            if next_state == self.STATE["READY"]:
                # here to update the possible roti make by calculating by recipe if value changes a lot
                if self.machine_status.set_remain(state_msg["FLR"], state_msg["WTR"], state_msg["OIL"]):
                    self.gui_handler.possibleToMake_update(self.machine_status.possibleToMake)
                    # self.updateUI()
            # todo change the format of warning message
            elif next_state == self.STATE["INIT"]:
                warning_msg = [status for status in state_msg.keys() if state_msg[status] < 0]
                self.gui_handler.warning_update("error")
                self.gui_handler.make_button_update(True)
                pass
            elif next_state == self.STATE["RUNNING"]:
                # start to update number of roti in making
                # self.updateUI()
                self.gui_handler.to_running()
                pass
        elif self.state == self.STATE["RUNNING"]:
            if next_state == self.STATE["INIT"]:
                # raise up warning:
                warning_msg = [status for status in state_msg.keys() if state_msg[status] < 0]
                self.gui_handler.warning_update(warning_msg)
                self.gui_handler.make_button_update(True)
                pass
            elif next_state == self.STATE["RUNNING"]:
                # start to update number of roti in making
                self.gui_handler.rotiCount_update(state_msg["CNT"])
                pass
            elif next_state == self.STATE["DONE"]:
                # raise up warning to done!
                self.gui_handler.warning_update("DONE!")
                pass

        elif self.state == self.STATE["DONE"]:
            if next_state == self.STATE["INIT"]:
                # raise up warning
                warning_msg = [status for status in state_msg.keys() if state_msg[status] < 0]
                self.gui_handler.warning_update(warning_msg)
                self.gui_handler.make_button_update(True)
            elif next_state == self.STATE["READY"]:
                # here to update the possible roti make by calculating by recipe
                if self.machine_status.set_remain(state_msg["FLR"], state_msg["WTR"], state_msg["OIL"]):
                    self.gui_handler.possibleToMake_update(self.machine_status.possibleToMake)  # update possible to make
                self.gui_handler.make_button_update(False)

        self.state = next_state
        print(self.state)
        self.lock.release()

    def close(self):
        self.state_queue.put(None)
        self.join()

    def get_state(self):
        self.lock.acquire()
        yield self.state
        self.lock.release()

    def get_recipe(self):
        return self.machine_status.recipe


if __name__ == "__main__":

    import queue
    q = queue.Queue()
    q2 = queue.Queue()
    StateMachine = StateMachine(q, q2)
    StateMachine.start()
    result = StateMachine.get_state()
    for r in result:
        print(r)
