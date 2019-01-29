'''

Service classes to handle information

'''
from protoc import MESSAGE_FORMAT
from imutils.video import VideoStream
from pyzbar import pyzbar
from rotiSerial import rotiSerial
import importlib
import imutils
import queue
import threading
import time
import serial
import re
import os
import json


os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "1"


class Service:

    def __init__(self):
        self._requests = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            request = self._requests.get()
            if request is None:
                self.shutdown()
                break
            self.process(request)
            self._requests.task_done()

    def process(self, request):
        pass

    def shutdown(self):
        pass

    def submit(self, request):
        self._requests.put(request)

    def close(self):
        self._requests.put(None)
        self._thread.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()


'''
QR code service
'''

class QRScanner(Service):

    ERROR_CODE = {
        -2: "FAIL",
        -1: "TIMEOUT",
        0: "OK"
    }

    def __init__(self):
        super().__init__()
        self.buf = []
        self.err_flag = 0
        self.condition = threading.Condition()
        self.scan_done = False


    def process(self, request):
        self.condition.acquire()
        time_out = request
        # vs = VideoStream(usePiCamera=True).start()
        # vs = VideoStream(src=0).start()
        self.buf = []
        current_time = time.time()
        vs = VideoStream(src=0).start()
        #vs = cv2.VideoCapture(0)
        while True:
            # grab the frame from the threaded video stream and resize it to
            # have a maximum width of 400 pixels
            frame = vs.read()
            frame = imutils.resize(frame, 400)

            # find the barcodes in the frame and decode each of the barcodes
            barcodes = pyzbar.decode(frame)

            # loop over the detected barcodes
            result = True
            for barcode in barcodes:
                # the barcode data is a bytes object so if we want to draw it
                # on our output image we need to convert it to a string first
                barcodeData = barcode.data.decode("utf-8")
                result, decoded_data = self.decode(barcodeData)
                if result:
                    self.buf.append(barcodeData)

            # time_out
            if time.time() - current_time > time_out:
                self.err_flag = self.ERROR_CODE[-2] if (not result) else self.ERROR_CODE[-1]
                self.scan_done = True
                break
            elif len(self.buf) > 0:
                self.err_flag = self.ERROR_CODE[0]
                self.scan_done = True
                break

        vs.stop()
        self.condition.notify()
        self.condition.release()

    # external calling
    def scan(self, time_out=5):
        self.submit(time_out)
        self.condition.acquire()
        while not self.scan_done:
            self.condition.wait()
        self.condition.release()
        self.scan_done = False
        return self.err_flag, self.buf

    # TODO UPDATE TO ANOTHER VERSION
    # here is the method to interpret data
    def decode(self, msg):
        try:
            lines = msg.split("\n")
            # extract CNT and Type
            CNT = lines[-1].split(',')
            TYPE = lines[0]
            recipe_name = CNT[-2] + "_" + TYPE
            # load template
            Tempelate = importlib.import_module('RecipeTemplate')
            recipe_template = Tempelate.RecipeTemplate[recipe_name]

            recipe = {"INS": []}

            for i in range(len(lines[1:-1])):
                instruction = recipe_template[i].format(*lines[i + 1].split(','))
                instruction = json.loads(instruction)
                recipe["INS"].append(instruction)
        except Exception as e:
            print(e)
            return (False, None)

        return (True, recipe)


# Service to monitor the data from serial
class SerialMonitor(Service):

    # a thread to continuously listen on the serial
    class ListenThread(threading.Thread):

        def __init__(self, state_queue, info_queue):
            super().__init__()
            # a dict of queues for dispatching messages
            self.queues = {
                "STATE": state_queue,
                "INFO": info_queue
                           }
            self.done = False

        def attach(self, port):
            self.port = port

        def shutdown(self):
            self.done = True
            self.port.close()

        def run(self):
            if not self.port.isOpen():
                return
            while not self.done:
                msg = self.port.readLineSerial()
                if self.done:
                    break
                self.dispatch(msg)

        # here dispatch all the messages to other threads
        def dispatch(self, msg):
            # start up cause transmission of trash information
            try:
                msg = msg.decode("UTF-8").strip()
                print(msg)
            except UnicodeDecodeError:
                pass
            for key in MESSAGE_FORMAT.keys():
                if re.match(MESSAGE_FORMAT[key], msg):
                    self.queues[key].put(json.loads(msg))

    def __init__(self, state_queue, info_queue, dev=None):
        super().__init__()
        try:
            if dev is None:
                self.serial_comm = rotiSerial()
            else:
                self.serial_comm = rotiSerial(dev)
        except serial.SerialException:
            print("Serial start fails.")

        # add condition so it can return the value
        self.condition = threading.Condition()
        self.read_done = False

        # set of queues
        self.last_feedback = None
        self.feedback = queue.Queue()

        # start listener
        self.listener = self.ListenThread(state_queue, info_queue)
        self.listener.attach(self.serial_comm)
        self.listener.start()

        # list of threads
        self.threads = [self.listener]

    def process(self, request):
        self.condition.acquire()
        # read data
        if isinstance(request, int):
            self.buf = []
            if request == -1:
                while self.serial_comm.check_avail():
                    self.buf.append(self.serial_comm.readLineSerial())
            else:
                for i in range(request):
                    self.buf.append(self.serial_comm.readLineSerial())
            self.read_done = True

        # send data
        else:
            self.feedback = None
            # make CMD
            if request["CMD"] == "MAKE":
                self.serial_comm.sendMakeRoti(request["QTY"])
            # recipe CMD
            elif request["CMD"] == "RECIPE":
                self.serial_comm.sendCook(request["cookProfile"])
                self.serial_comm.sendMix(request["kneadProfile"])
                self.serial_comm.sendRecipe(request["qty"][0], request["qty"][1], request["qty"][2])
            # toggle CMD
            elif request["CMD"] == "TOGGLE":
                if request["DIR"] == "CLOSE":
                    self.serial_comm.sendRemoveBowl()
                elif request["DIR"] == "OPEN":
                    self.serial_comm.sendReturnedBowl()
            else:
                pass
            # check whether received
            try:
                self.last_feedback = self.feedback.get()
            except serial.SerialTimeoutException:
                print("No feedback, lost connection!")
                self.last_feedback = -1

        self.condition.notify()
        self.condition.release()

    # send data called by external
    def send_data(self, data):
        self.submit(data)
        self.condition.acquire()
        while self.feedback is None:
            self.condition.wait()
        self.condition.release()
        return self.last_feedback

    # read data from slave
    def read_data(self, num_lines):
        self.submit(num_lines)
        self.condition.acquire()
        while not self.read_done:
            self.condition.wait()
        self.condition.release()
        self.read_done = False
        return self.buf

    # TODO
    def close(self):
        for thread in self.threads:
            thread.shutdown()
            thread.join()
        super().close()


if __name__ == "__main__":

    #state_queue = queue.Queue()
    #with SerialMonitor(state_queue, "COM3") as monitor:
    #    while True:
     #       print(state_queue.get())

    with QRScanner() as scanner:
         print(scanner.scan(1))