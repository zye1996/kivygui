import re
import struct
import json


START_FLAG  = ord('^')
END_FLAG    = ord('\n')
ESCAPE_FLAG = ord('?')

ROTI_MSG_ID_INFO    = 0
ROTI_MSG_ID_STATE   = 1
ROTI_MSG_ID_WARN    = 2
ROTI_MSG_ID_ERR     = 3
ROTI_MSG_ID_RESP    = 4
ROTI_MSG_ID_CMD     = 5

# STATE
# Flour Water Oil
MESSAGE_FORMAT = {
    "INFO": re.compile("^INFO:"),
    "STATE": re.compile('^{"STATE":\d,"FLR":-?\d,"WTR":-?\d,"OIL":-?\d}'),
    "WARN": re.compile("^WARN:"),
    "ERR": re.compile("^ERR:"),
    "RESP": re.compile("^RESP:")
}

# protocol help functions
def calc_checksum(bytelist):
    csum = 0x00
    for byte in bytelist:
        csum ^= byte
    return csum

def msg_decode(msg):
    msgId = struct.unpack('>B', msg[0].to_bytes(1, 'little'))[0]
    payload = msg[1:-1]
    # check sum check
    if calc_checksum(msg[0:-1]) != msg[-1]:
        raise ValueError
    else:
        decoded_data = MESSAGE_CLS_MAP[msgId].unpack(payload)
        # get json
        return MESSAGE_CLS_MAP[msgId].to_json(decoded_data)


# protocol classes
class roti_header:

    def __init__(self, id):
        self.id = id

    def pack(self):
        return struct.pack('>B', self.id)


class roti_message:

    fieldnames = []
    format = ""

    def __init__(self, id, name):
        # generate data packet
        self._id        = id
        self._header = roti_header(self._id)
        self._payload   = None
        self._fieldnames = []
        self._type      = name
        self._crc       = None

    def pack(self, payload):
        self._payload = payload
        self._msgbuf = self._header.pack() + payload
        print(self._msgbuf)
        csum = calc_checksum(self._msgbuf)
        self._msgbuf += struct.pack('>B', csum)
        return self._msgbuf

    @classmethod
    def to_dict(cls, args):
        d = dict({})
        for i in range(len(cls.fieldnames)):
            d[cls.fieldnames[i]] = args[i]
        return d

    @classmethod
    def to_json(cls, args):
        return json.dumps(cls.to_dict(args))

    @classmethod
    def unpack(cls, payload):
        return struct.unpack(cls.format, payload)


class info_message(roti_message):

    fieldnames = ["info_msg"]
    field_types = ["char[32]"]
    format = '>32s'

    def __init__(self, info_msg):
        super().__init__(ROTI_MSG_ID_INFO, "INFO_MESSAGE")
        self.info_msg = info_msg
        self._fieldnames = info_message.fieldnames

    def pack(self):
        return super().pack(struct.pack(self.format, self.info_msg.encode('utf-8')))


class state_message(roti_message):

    fieldnames = ["next_state", "flour", "water", "oil", "bowl"]
    format = '>Bfff?'

    def __init__(self, next_state, flour, water, oil, bowl):
        super().__init__(ROTI_MSG_ID_STATE, "STATE_MESSAGE")
        self._fieldnames = state_message.fieldnames
        self.next_state = next_state
        self.flour = flour
        self.water = water
        self.oil = oil
        self.bowl = bowl

    def pack(self):
        return super().pack(struct.pack(self.format, self.next_state, self.flour, self.water, self.oil, self.bowl))


class warn_message(roti_message):
    pass

class err_message(roti_message):
    pass

class resp_message(roti_message):
    pass

# CMD message sent from master
class cmd_message(roti_message):

    fieldnames = []
    format = ""
    pass


MESSAGE_CLS_MAP = {
    0: info_message,
    1: state_message,
    2: warn_message,
    3: err_message,
    4: resp_message,
    5: cmd_message
}

if __name__ == "__main__":
    state_msg = state_message(1, 0.1, 0.1, 0.1, False)
    print(msg_decode(state_msg.pack()))
    info_msg = info_message("Hello")
    print(info_msg.pack())



