import zlib
from pyzbar import pyzbar
import qrcode
from PIL import Image
from io import StringIO
import gzip
import zxing
from itertools import groupby
import json

def gzip_compress(buf):
    out = StringIO()
    with gzip.GzipFile(fileobj=out, mode="wb") as f:
        f.write(buf)
    return out.getvalue()


def gzip_decompress(buf):
    obj = StringIO(buf)
    with gzip.GzipFile(fileobj=obj) as f:
        result = f.read()
    return result

raw_data = "{OPT\":[{\"TTL\":\"Chapati\",\"INS\":[{\"ERR\":1001,\"POS\":0,\"VRB\":\"PRP\",\"CND\":[\"FLR\",\"WTR\",\"OIL\"],\"SQ\":1},{\"OIL\":2,\"ERR\":1002,\"WTR\":14,\"VRB\":\"DPN\",\"RPT\":\"Y\",\"CND\":[\"FLR\",\"WTR\",\"OIL\",\"BWL\",{\"SQ\":[\"3C\",\"4C\"]}],\"SLT\":0.1,\"FLR\":20,\"SQ\":2},{\"ERR\":1003,\"SPD\":160,\"VAR\":\"N\",\"VRB\":\"KND\",\"CND\":[{\"SQ\":[\"2C\"]}],\"TIM\":45,\"SQ\":3},{\"OPA\":45,\"OPS\":30,\"ERR\":1004,\"VRB\":\"DIP\",\"CND\":[{\"SQ\":[\"3C\",\"5E\"]}],\"SQ\":4},{\"ERR\":1005,\"PL1\":{\"POS\":\"B\",\"TMP\":\"220\"},\"THK\":1,\"VRB\":\"FLT\",\"PL2\":{\"POS\":\"T\",\"TMP\":\"200\"},\"CND\":[\"SFT\"],\"TIM\":2,\"SQ\":5},{\"OPS\":30,\"ERR\":1006,\"PL1\":{\"POS\":\"T\",\"TMP\":220},\"VRB\":\"FLP\",\"PL2\":{\"POS\":\"B\",\"TMP\":200},\"CND\":[{\"SQ\":[\"5C\"]}],\"TIM\":2,\"SQ\":6},{\"OPS\":30,\"ERR\":1007,\"PL1\":{\"POS\":\"T\",\"TMP\":200},\"VRB\":\"BKG\",\"PL2\":{\"POS\":\"B\",\"TMP\":550},\"CND\":[{\"SQ\":[\"6C\"]}],\"TIM\":20,\"SQ\":7},{\"OPS\":30,\"ERR\":1008,\"PL1\":{\"POS\":\"T\",\"TMP\":550},\"VRB\":\"BKG\",\"PL2\":{\"POS\":\"B\",\"TMP\":200},\"CND\":[{\"SQ\":[\"7P\"]},{\"TIM\":15}],\"TIM\":5,\"SQ\":8},{\"OPS\":1,\"ERR\":1009,\"PL1\":{\"POS\":\"B\",\"TMP\":550},\"VRB\":\"FLP\",\"PL2\":{\"POS\":\"T\",\"TMP\":200},\"CND\":[{\"SQ\":[\"8C\"]}],\"SQ\":9},{\"OPS\":30,\"ERR\":1010,\"PL1\":{\"POS\":\"B\",\"TMP\":550},\"VRB\":\"BKG\",\"PL2\":{\"POS\":\"T\",\"TMP\":200},\"CND\":[{\"SQ\":[\"9C\"]}],\"TIM\":20,\"SQ\":10},{\"OPA\":-45,\"OPS\":30,\"ERR\":1011,\"PL1\":{\"POS\":\"B\",\"TMP\":220},\"VRB\":\"DIP\",\"PL2\":{\"POS\":\"T\",\"TMP\":200},\"CND\":[{\"SQ\":[\"10C\"]}],\"SQ\":11}]}],\"CNT\":{\"MD\":\"01\/04\/2017\",\"QTY\":\"900\",\"MF\":\"iYukti\",\"SN\":\"111111\"}}"
raw_data = {"OPT":[{"TTL":"Chapati",
                    "INS":[
                        {"ERR":1001,"POS":0,"VRB":"PRP","CND":["FLR","WTR","OIL"],"SQ":1},
                        {"OIL":2,"ERR":1002,"WTR":14,"VRB":"DPN","RPT":"Y","CND":["FLR","WTR","OIL","BWL",{"SQ":["3C","4C"]}],"SLT":0.1,"FLR":20,"SQ":2},
                        {"ERR":1003,"SPD":160,"VAR":"N","VRB":"KND","CND":[{"SQ":["2C"]}],"TIM":45,"SQ":3},
                        {"OPA":45,"OPS":30,"ERR":1004,"VRB":"DIP","CND":[{"SQ":["3C","5E"]}],"SQ":4},
                        {"ERR":1005,"PL1":{"POS":"B","TMP":"220"},"THK":1,"VRB":"FLT","PL2":{"POS":"T","TMP":200},"CND":["SFT"],"TIM":2,"SQ":5},
                        {"OPS":30,"ERR":1006,"PL1":{"POS":"T","TMP":220},"VRB":"FLP","PL2":{"POS":"B","TMP":200},"CND":[{"SQ":["5C"]}],"TIM":2,"SQ":6},
                        {"OPS":30,"ERR":1007,"PL1":{"POS":"T","TMP":200},"VRB":"BKG","PL2":{"POS":"B","TMP":550},"CND":[{"SQ":["6C"]}],"TIM":20,"SQ":7},
                        {"OPS":30,"ERR":1008,"PL1":{"POS":"T","TMP":550},"VRB":"BKG","PL2":{"POS":"B","TMP":200},"CND":[{"SQ":["7P"]},{"TIM":15}],"TIM":5,"SQ":8},
                        {"OPS":1,"ERR":1009,"PL1":{"POS":"B","TMP":550},"VRB":"FLP","PL2":{"POS":"T","TMP":200},"CND":[{"SQ":["8C"]}],"SQ":9},
                        {"OPS":30,"ERR":1010,"PL1":{"POS":"B","TMP":550},"VRB":"BKG","PL2":{"POS":"T","TMP":200},"CND":[{"SQ":["9C"]}],"TIM":20,"SQ":10},
                        {"OPA":-45,"OPS":30,"ERR":1011,"PL1":{"POS":"B","TMP":220},"VRB":"DIP","PL2":{"POS":"T","TMP":200},"CND":[{"SQ":["10C"]}],"SQ":11}
                    ]}],
            "CNT":{"MD":"01/04/2017","QTY":"900","MF":"iYukti","SN":"111111"}}

data = "Chapati\n" \
       "1001,0,\"PRP\",\"FIR\",\"WTR\",\"OIL\",1\n" \
       "2,1002,14,\"DPN\",\"Y\",\"FLR\",\"WTR\",\"OIL\",\"BWL\",\"3C\",\"4C\",0.1,20,2\n" \
       "1003,160,\"N\",\"KND\",\"2C\",45,3\n" \
       "45,30,1004,\"DIP\",\"3C\",\"5E\",4\n" \
       "1005,\"B\",220,1,\"FLT\",\"T\",200,\"SFT\",2,5\n" \
       "30,1006,\"T\",220,\"FLP\",\"B\",200,\"5C\",2,6\n" \
       "30,1007,\"T\",200,\"BKG\",\"B\",550,\"6C\",20,7\n" \
       "30,1008,\"T\",550,\"BKG\",\"B\",200,\"YP\",15,5,8\n" \
       "1,1009,\"B\",550,\"FLP\",\"T\",200,\"8C\",9\n" \
       "30,1010,\"B\",550,\"BKG\",\"T\",200,\"9C\",20,10\n" \
       "-45,30,1011,\"B\",220,\"DIP\",\"T\",200,\"10C\",11\n" \
       "\"01/04/2017\",900,iYukti,111111"

import importlib

def decode(msg):
    lines = msg.split("\n")

    # extract CNT and Type
    CNT = lines[-1].split(',')
    TYPE = lines[0]
    recipe_name = CNT[-2] + "_" + TYPE
    # load template
    Tempelate = importlib.import_module('RecipeTemplate')
    recipe_template = Tempelate.RecipeTemplate[recipe_name]

    recipe = {"INS": []}
    try:
        for i in range(len(lines[1:-1])):
            instruction = recipe_template[i].format(*lines[i+1].split(','))
            instruction = json.loads(instruction)
            recipe["INS"].append(instruction)
    except Exception as e:
        print(e)
        pass

decode(data)



print(data.split("\n"))
raw_data_template = '{{"OPT":[{{"TTL":{0},"INS":[{{"ERR":{1},"POS":{2},"VRB":{3},"CND":[{4},{5},{6}],"SQ":{7}}}},' \
                    '{{"OIL":{8},"ERR":{9},"WTR":{10},"VRB":{11},"RPT":{12},"CND":[{13},{14},{15},{16},{{"SQ":[{17},{18}]}}],"SLT":{19},"FLR":{20},"SQ":{21}}},' \
                    '{{"ERR":{22},"SPD":{23},"VAR":{24},"VRB":{25},"CND":[{{"SQ":[{26}]}}],"TIM":{27},"SQ":{28}}},' \
                    '{{"OPA":{29},"OPS":{30},"ERR":{31},"VRB":{32},"CND":[{{"SQ":[{33},{34}]}}],"SQ":{35}}},}'
'''               '{{"ERR":{36},"PL1":{"POS":{37},"TMP":{38}},"THK":{39},"VRB":{40},"PL2":{{"POS":{41},"TMP":{42}}},"CND":[{43}],"TIM":{44},"SQ":{45}}},' \
                    '{{"OPS":{46},"ERR":{47},"PL1":{"POS":{48},"TMP":{49}},"VRB":{50},"PL2":{"POS":{51},"TMP":{52}},"CND":[{"SQ":[{53}]}],"TIM":{54},"SQ":{55}},' \
                    '{"OPS":{56},"ERR":{57},"PL1":{"POS":{58},"TMP":{59}},"VRB":{60},"PL2":{"POS":{61},"TMP":{62}},"CND":[{"SQ":[{63}]}],"TIM":{64},"SQ":{65}},' \
                    '{"OPS":{66},"ERR":{67},"PL1":{"POS":{68},"TMP":{69}},"VRB":{70},"PL2":{"POS":{71},"TMP":{72}},"CND":[{"SQ":[{73}]},{"TIM":{74}}],"TIM":{75},"SQ":{76}},' \
                    '{"OPS":{77},"ERR":{78},"PL1":{"POS":{79},"TMP":{80}},"VRB":{81},"PL2":{"POS":{82},"TMP":{83}},"CND":[{"SQ":[{84}]}],"SQ":{85}},' \
                    '{"OPS":{86},"ERR":{87},"PL1":{"POS":{88},"TMP":{89}},"VRB":{90},"PL2":{"POS":{91},"TMP":{92}},"CND":[{"SQ":[{93}]}],"TIM":{94},"SQ":{95}},' \
                    '{"OPA":{96},"OPS":{97},"ERR":{98},"PL1":{"POS":{99},"TMP":{100}},"VRB":{101},"PL2":{"POS":{102},"TMP":{103}},"CND":[{"SQ":[{104}]}],"SQ":{105}}]}],' \
                    '"CNT":{"MD":{106},"QTY":{107},"MF":{108},"SN":{109}}}'''''


import re
'''
exp = re.compile(r"\'[a-zA-Z]*\'")
result = re.findall(exp, str(raw_data))
print(len(str(raw_data)))
print(set(result))

processed = []
for key in set(result):
    key = key.strip("\'")
    if len(key) > 1:
        processed.append(key)

print(processed)

str_raw_data = str(raw_data)
for i in range(len(processed)):
    print(chr(ord('a') + i))
    str_raw_data = str_raw_data.replace("\'" + processed[i] + "\'", chr(ord('a')+i))

print(len(str_raw_data))
print(str_raw_data)
'''
img = qrcode.make(data)
img.save("test_2.png")

