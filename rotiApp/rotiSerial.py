import serial
import struct
import sys
import re

class rotiSerial:

	RECP_ORDER_OWF = 0x01
	RECP_ORDER_OFW = 0x02
	RECP_ORDER_WFO = 0x03
	RECP_ORDER_WOF = 0x04
	RECP_ORDER_FOW = 0x05
	RECP_ORDER_FWO = 0x06

	debug = False

	temps = {"top": {"platon": 0, "setpoint": 0, "ambient": 0 },
		"bottom": {"platon": 0, "setpoint": 0, "ambient": 0 }}

	def __init__(self, dev='/dev/roti'):
		self.serial = serial.Serial(
				port=dev,
				baudrate=115200,
				parity=serial.PARITY_NONE,
				stopbits=serial.STOPBITS_ONE,
				bytesize=serial.EIGHTBITS
			)
	

	def readLineSerial(self):
		return self.serial.readline()
	
	def getTemp(self):
		return self.temps

	def sendMessage(self, byteList):
		self.serial.write('^'.encode())
		if self.debug:
			sys.stdout.write('^')
		csum = 0x00
		for b in byteList:
			csum ^= b
			self.escapeWrite(b)
		self.escapeWrite(struct.pack("<B",csum))
		self.serial.write('\n'.encode())
		if self.debug:
			sys.stdout.write('\n')
	
	def escapeWrite(self,b):
		if (b == '^' or b == '\n' or b == '?'):
			self.serial.write("?")
			if self.debug:
				sys.stdout.write("?")
		self.serial.write(b)
		if self.debug:
			sys.stdout.write(format(ord(b),"02x"))

	def sendMakeRoti(self,qty=1):
		if (qty > 0 and qty < 255):
			packed = struct.pack("<cB","M",qty)
			self.sendMessage(packed)
	
	#thickness  - percentage between 0-255
	#loadheight - percentage between 0-255
	def sendRecipe(self,water=16.0,oil=2.5,flour=24.0, order=RECP_ORDER_OWF,thickness=33,loadheight=251):
		packed = struct.pack("<cfffHBB", "R".encode(), flour, water, oil, order, thickness, loadheight);
		self.sendMessage(packed)

	def sendMix(self,mixProfile):

		if type(mixProfile) is not dict:
			raise ValueError('setMix(): Expected a dictionary')
		if 'speeds' not in mixProfile.keys():
			raise ValueError('setMix(): Key "speeds" not defined in the dictionary')
		if 'times' not in mixProfile.keys():
			raise ValueError('setMix(): Key "times" not defined in the dictionary')

		if type(mixProfile["speeds"]) is not list:
			raise ValueError('setMix(): Value for key "speeds" is not a list')
		if type(mixProfile["times"]) is not list:
			raise ValueError('setMix(): Value for key "times" is not a list')

		if (len(mixProfile["speeds"]) != len(mixProfile["times"])):
			raise ValueError('setMix(): list size of "speeds" and "times" do not match')
		if (len(mixProfile["speeds"]) < 1 or len(mixProfile["times"]) < 1):
			raise ValueError('setMix(): lists of "speeds and "times" must contain at least 1 item')

		length = len(mixProfile["speeds"])
		packed = struct.pack("<cB","X".encode(),length)

		for spd in mixProfile["speeds"]:
			packed += struct.pack("<B", int(spd))
		for time in mixProfile["times"]:
			packed += struct.pack("<H", int(time))

		self.sendMessage(packed)
	
	def sendCook(self, cookProfile):
		if type(cookProfile) is not dict:
			raise ValueError('sendCook(): Expected a dictionary')

		if 'cook_top' not in cookProfile.keys():
			raise ValueError('sendCook(): Key "top" not defined in the dictionary')

		if 'cook_bottom' not in cookProfile.keys():
			raise ValueError('sendCook(): Key "bottom" not defined in the dictionary')

		if not self._verifyCookProfile(cookProfile["cook_top"]):
			raise ValueError('sendCook(): Top cook profile is not valid')

		if not self._verifyCookProfile(cookProfile["cook_bottom"]):
			raise ValueError('sendCook(): Bottom cook profile is not valid')

		packed = struct.pack("<c", "C".encode()) + self._packCookProfile(cookProfile['cook_top']) + self._packCookProfile(cookProfile['cook_bottom'])
		self.sendMessage(packed)

	def _verifyCookProfile(self,profile):
		if 'time' not in profile:
			return False
		if 'tempTop' not in profile:
			return False
		if 'tempBottom' not in profile:
			return False
		return True

	def _packCookProfile(self,profile):
		packed = struct.pack("<HHH",profile["time"],profile["tempBottom"],profile["tempTop"])
		return packed

	def sendStop(self):
		packed = struct.pack("<c","S")
		self.sendMessage(packed)

	def cancleRotis(self):
		packed = struct.pack("<c","Z")
		self.sendMessage(packed)

	def sendRemoveBowl(self):
		packed = struct.pack("<c","b")
		self.sendMessage(packed)

	def sendReturnedBowl(self):
		packed = struct.pack("<c","B")
		self.sendMessage(packed)

	def querryTemps(self):
		packed = struct.pack("<c","T")
		self.sendMessage(packed)

	def querryStats(self):
		packed = struct.pack("<c","Q")
		self.sendMessage(packed)

	def check_csum(self,msg):
		s = ''.join(msg)
		sent_csum = ord(s[-1])
		s = ''.join(s[:-1])
		our_csum = 0x00
		for c in s:
			our_csum ^= ord(c)
		return our_csum == sent_csum

	def parseMsg(self, msg):
		s = ''.join(msg)
		emsg = ""
		escape = False

		for c in s:
			if not escape:
				if c == '?':
					escape = True
				else:
					emsg += c
			else:
				emsg += c
				escape = False
		if self.debug:
			print("".join("{:02x}".format(ord(c)) for c in emsg))
			print("".join("{:02x}".format(ord(c)) for c in s))

		if self.check_csum(emsg):
			cmd = emsg[0]
			payload = emsg[1:]
			if cmd == 'T':
				#Temp data
				self._updateTemps(payload[:-1])
	
	def _updateTemps(self,data):
		if len(data) == 24:
			numbers = struct.unpack("<ffffff",data)
			self.temps["top"]["platon"]      = numbers[0]
			self.temps["top"]["setpoint"]    = numbers[1]
			self.temps["top"]["ambient"]     = numbers[2]
			self.temps["bottom"]["platon"]   = numbers[3]
			self.temps["bottom"]["setpoint"] = numbers[4]
			self.temps["bottom"]["ambient"]  = numbers[5]



#David
### This is not how you parse info from the machine
### also why did you not just use "readlineserial that I implemented"
#### Spaces where used instead of tabs
#divaD
      
	def getFeedback(self):
		response = self.serial.read(self.serial.inWaiting())
		#print("Return - " + str(response))
		return str(response)
