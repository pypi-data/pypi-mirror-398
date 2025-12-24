import json
from jsonpath_ng import jsonpath, parse
from robomotion.runtime import IsLMOCapable
from robomotion.lmo import IsLMO, SerializeLMO, UnpackMessageBytes, PackMessageBytes, DeserializeFromDict
class Context:
    def get_id(self) -> str:
        pass

    def set(self, key: str, value: object):
        pass

    def get(self, key: str) -> object:
        pass

    def get_string(self, key: str) -> str:
        """Get a value as string."""
        pass

    def get_bool(self, key: str) -> bool:
        """Get a value as boolean."""
        pass

    def get_int(self, key: str) -> int:
        """Get a value as integer."""
        pass

    def get_float(self, key: str) -> float:
        """Get a value as float."""
        pass

    def get_raw(self) -> bytes:
        pass

    def set_raw(self, data: bytes):
        pass

    def is_empty(self) -> bool:
        pass

    def clone(self) -> 'Context':
        """Create and return a new Context instance with the same data."""
        return Context()

class Message(Context):
    def __init__(self, data: bytes):
        msg = json.loads(data.decode("utf-8"))
        self.id = msg["id"]
        self.data = data

    def get_id(self) -> str:
        return str(self.id)

    def clone(self) -> 'Message':
        """Create and return a new Message instance with the same data."""
        return Message(self.get_raw())

    def set(self, key: str, value: object):
        if IsLMOCapable():            
            serialized_value, err = SerializeLMO(value)
            if serialized_value:
                value = serialized_value                    
        msg = json.loads(self.data.decode("utf-8"))
        msg[key] = value
        self.data = json.dumps(msg).encode("utf-8")
    def get(self, key: str) -> object:
        msg = json.loads(self.data.decode("utf-8"))
        val = parse("$.%s" % key).find(msg)
        if len(val) == 0:
            return None
        result = val[0].value
        if  IsLMOCapable() and IsLMO(result):
            res = DeserializeFromDict(result)
            if res:
                result = res.Value()
            else:
                return None
        return result

    def get_string(self, key: str) -> str:
        """Get a value as string."""
        val = self.get(key)
        if val is None:
            return ""
        return str(val)

    def get_bool(self, key: str) -> bool:
        """Get a value as boolean."""
        val = self.get(key)
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val > 0
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        return bool(val)

    def get_int(self, key: str) -> int:
        """Get a value as integer."""
        val = self.get(key)
        if val is None:
            return 0
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            try:
                return int(val)
            except ValueError:
                return 0
        return 0

    def get_float(self, key: str) -> float:
        """Get a value as float."""
        val = self.get(key)
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                return float(val)
            except ValueError:
                return 0.0
        return 0.0

    def delete(self, key: str):
        msg = json.loads(self.data.decode("utf-8"))
        del msg[key]
        self.data = json.dumps(msg).encode("utf-8")

    def get_raw(self) -> bytes:
        return self.data

    def set_raw(self, data: bytes):
        self.data = data

    def is_empty(self) -> bool:
        return self.data == None or len(self.data) == 0
