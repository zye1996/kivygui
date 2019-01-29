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


def calc_checksum(bytelist):
    csum = 0x00
    for byte in bytelist:
        csum ^= byte
    return csum

def msg_decode(msg):
    print(msg[1])
    msgId = struct.unpack('>B', msg[1].to_bytes(1, 'little'))[0]
    payload = msg[1:-1]
    # check sum check
    if calc_checksum(payload) != payload[-2]:
        raise ValueError
    else:
        decoded_data = MESSAGE_CLS_MAP[msgId].unpack(payload[0:-1])
        # get json
        print(decoded_data)
        return MESSAGE_CLS_MAP[msgId].to_json(decoded_data)



class roti_header:

    def __init__(self, id):
        self.id = id

    def pack(self):
        return struct.pack('>BB', START_FLAG, self.id)


class roti_message:

    fieldnames = []

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
        csum = calc_checksum(self._msgbuf[1:])
        self._msgbuf += struct.pack('>B', csum)
        self._msgbuf += struct.pack('>B', END_FLAG)
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





class info_message(roti_message):

    fieldnames = ["info_msg"]
    ordered_fieldnames = ["info_msg"]
    field_types = ["char[32]"]
    format = '>32s'

    def __init__(self, info_msg):
        super().__init__(ROTI_MSG_ID_INFO, "INFO_MESSAGE")
        self.info_msg = info_msg
        self._fieldnames = info_message.fieldnames

    def pack(self):
        return super().pack(struct.pack(self.format, self.info_msg))

    @classmethod
    def unpack(cls, payload):
        return struct.unpack(cls.format, payload)


class state_message(roti_message):

    fieldnames = ["next_state", "flour", "water", "oil", "bowl"]
    format = '>Bfff?'

    def __init__(self, next_state, flour, water, oil, bowl):
        super().__init__(ROTI_MSG_ID_INFO, "INFO_MESSAGE")
        self._fieldnames = state_message.fieldnames
        self.next_state = next_state
        self.flour = flour
        self.water = water
        self.oil = oil
        self.bowl = bowl

    def pack(self):
        return super().pack(struct.pack(self.format, self.next_state, self.flour, self.water, self.oil, self.bowl))

    @classmethod
    def unpack(cls, payload):
        return struct.unpack(cls.format, payload)


MESSAGE_CLS_MAP = {
    0: info_message,
    1: state_message,
    "WARN": 2,
    "ERR": 3,
    "RESP": 4
}

if __name__ == "__main__":
    state_msg = state_message(1, 0.1, 0.1, 0.1, False)
    print(msg_decode(state_msg.pack()[1:]))


