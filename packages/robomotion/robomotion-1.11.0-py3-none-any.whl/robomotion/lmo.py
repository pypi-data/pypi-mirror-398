import json
import os
import base64
import uuid
import robomotion.runtime  as runtime
from robomotion.utils import get_temp_path
LMO_MAGIC = 0x1343B7E
LMO_LIMIT = 256 << 10  # 256kb
LMO_VERSION = 0x01
LMO_HEAD = 100

enableLMO = False

def SetLMOFag(flag):
    global enableLMO
    enableLMO = flag
def GetLMOFlag():
    return enableLMO

class LargeMessageObject:
    def __init__(self, id, head, size,data):
        self.Magic = LMO_MAGIC
        self.Version = LMO_VERSION
        self.ID = id
        self.Head = head 
        self.Size = size
        self.Data = data

    def Value(self):
        return self.Data
    
    def ToJSON(self):        
        return {        
            "magic":self.Magic,
            "version":self.Version,
            "id": self.ID,
            "head" : self.Head,
            "size": self.Size,
            "data": self.Data        
        }
    

def NewId() -> str:
    uid = uuid.uuid4().bytes
    encoded = base64.b32encode(uid).decode('utf-8')
    return encoded.replace('=', '')[:26]

def IsLMOCapable():
    return True # düzelt
def SerializeLMO(value):
    global LMO_MAGIC, LMO_VERSION, LMO_HEAD, LMO_LIMIT
    if not IsLMOCapable():
        return None
    data = json.dumps(value).encode()
    dataLen = len(data)

    if dataLen < LMO_LIMIT:
        return None
    
    id = NewId()
    head = data[:LMO_HEAD].decode()
    lmo = LargeMessageObject(id, head, dataLen, value)
    robot_info = runtime.Runtime.get_robot_info()    
    robotID = robot_info["id"]

    tempPath = get_temp_path()
    
    if not robotID or not tempPath:
        return None
    dir_path = os.path.join(tempPath, "robots", robotID)
    os.makedirs(dir_path, exist_ok=True, mode=0o755)

    file_path = os.path.join(dir_path, id + ".lmo")
    with open(file_path, "w") as file:
        lmo_json = json.dumps(lmo.__dict__)
        file.write(lmo_json)
    
    lmo.Data = None
    lmo = lmo.ToJSON()
    return lmo

def DeserializeLMO(id):
    robotInfo = runtime.Runtime.get_robot_info()    

    robotID = robotInfo["id"]
    tempPath = get_temp_path()

    if not robotID or not tempPath:
        return None

    dir_path = os.path.join(tempPath, "robots", robotID)
    file_path = os.path.join(dir_path, id + ".lmo")

    try:
        with open(file_path, "r") as file:
            file_content = file.read()
            lmo_dict =  json.loads(file_content)
            
            lmo = LargeMessageObject(lmo_dict["id"], lmo_dict["head"], lmo_dict["size"], lmo_dict["data"]) #check et
            return lmo
    except FileNotFoundError as e:
        return None
    
def DeserializeFromDict(d):
    if IsLMOCapable():
        id = d["id"]
        if not id:
            return None
        return DeserializeLMO(id)
    return None
def PackMessageBytes(inMsg):
    global LMO_LIMIT

    if not IsLMOCapable() or len(inMsg) < LMO_LIMIT:
        return inMsg, None

    try:
        msg = json.loads(inMsg.decode())
        msg = PackMessage(msg)
        packed = json.dumps(msg).encode()
        return packed, None
    except json.JSONDecodeError as e:
        return None, e

def PackMessage(msg):
    if not IsLMOCapable():
        return

    for key, value in msg.items():
        lmo, e = SerializeLMO(value)
        if e:
            return None

        if lmo:
            msg[key] = lmo
        else:
            msg[key] = value
        
    return msg

def UnpackMessageBytes(inMsg):
    try:
        msg = json.loads(inMsg.decode())
        UnpackMessage(inMsg, msg)
        return json.dumps(msg).encode(), None
    except json.JSONDecodeError as e:
        return None, e
    


def UnpackMessage(inMsg, msg):
    if not IsLMOCapable():
        return

    try:
        msg = json.loads(inMsg.decode())
        for key, value in msg.items():
            lmo = value

            if "magic" in lmo and lmo["magic"] == LMO_MAGIC:
                idValue = lmo.get("id")
                if idValue:
                    result, err = DeserializeLMO(idValue)
                    if err:
                        return err
                    msg[key] = result.Value()
    except AttributeError as e:
        return e

def IsLMO(value):
    global LMO_MAGIC

    if not IsLMOCapable() or type(value) != dict:
        return False

    return value.get("magic") == LMO_MAGIC

def DeleteLMObyID(id):
    robot_info = runtime.Runtime.get_robot_info()    

    robotID = robot_info["id"]
    tempPath = get_temp_path()

    if not robotID or not tempPath:
        return
    
    dir_path = os.path.join(tempPath, "robots", robotID, id)
    os.remove(dir_path)


