from robomotion.runtime import Runtime
from robomotion import plugin_pb2
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct
from robomotion.message import Context
from robomotion.error import RuntimeNotInitializedError
import json
from enum import IntEnum


class ECategory(IntEnum):
    Null = 0
    Login = 1
    Email = 2
    CreditCard = 3
    Token = 4
    Database = 5
    Document = 6


class _DefVal:
    def __init__(self, default: object):
        self.default = default

    def __init__(self, scope: str, name: str):
        self.default = {scope: scope, name: name}


class _Enum:
    def __init__(self, enums: list = [], enumNames: list = [], description: str = ""):
        self.__description = description
        self.__enums = enums
        self.__enumNames = enumNames

    @property
    def description(self) -> str:
        return self.__description

    @property
    def enums(self):
        return self.__enums

    @property
    def enumNames(self):
        return self.__enumNames


class Variable:
    def __init__(
        self,
        scope: str = "",
        name: str = "",
        title: str = "",
        description: str = "",
        type: str = "",
        jsScope: bool = False,
        pyScope: bool = False,
        customScope: bool = False,
        messageScope: bool = False,
        messageOnly: bool = False,
        aiScope: bool = False,
        hidden: bool = False,
        input: bool = False,
        output: bool = False,
        option: bool = False,
        default: _DefVal = None,
        enum: _Enum = None,
        format: str = "",
        arrayFields: str = None,
        order: int = None,
    ):
        self.__scope = scope
        self.__name = name
        self.__title = title
        self.__type = type
        self.__description = description
        self.__jsScope = jsScope
        self.__pyScope = pyScope
        self.__customScope = customScope
        self.__messageScope = messageScope
        self.__messageOnly = messageOnly
        self.__aiScope = aiScope
        self.__hidden = hidden
        self.__isinput = input
        self.__isoutput = output
        self.__isoption = option
        self.__default = default
        self.__enum = enum
        self.__format = format
        self.__arrayFields = arrayFields
        self.__order = order

    @property
    def scope(self) -> str:
        return self.__scope

    @property
    def name(self) -> str:
        return self.__name

    @property
    def title(self) -> str:
        return self.__title

    @property
    def description(self) -> str:
        return self.__description

    @property
    def type(self) -> str:
        return self.__type

    @property
    def jsScope(self) -> bool:
        return self.__jsScope

    @property
    def pyScope(self) -> bool:
        return self.__pyScope

    @property
    def customScope(self) -> bool:
        return self.__customScope

    @property
    def messageScope(self) -> bool:
        return self.__messageScope

    @property
    def messageOnly(self) -> bool:
        return self.__messageOnly

    @property
    def aiScope(self) -> bool:
        return self.__aiScope

    @property
    def hidden(self) -> bool:
        return self.__hidden

    @property
    def input(self) -> bool:
        return self.__isinput

    @property
    def output(self) -> bool:
        return self.__isoutput

    @property
    def option(self) -> bool:
        return self.__isoption

    @property
    def default(self) -> _DefVal:
        return self.__default

    @property
    def enum(self) -> _Enum:
        return self.__enum

    @property
    def category(self) -> ECategory:
        return ECategory.Null

    @property
    def format(self) -> str:
        return self.__format

    @property
    def arrayFields(self) -> list[str]:
        if self.__arrayFields is None:
            return None

        return self.__arrayFields.split("|")

    @property
    def order(self) -> int:
        return self.__order


class InVariable(Variable):
    def get(self, ctx: Context):
        return Runtime.get_variable(self, ctx)


class OutVariable(Variable):
    def set(self, ctx: Context, value: object):
        Runtime.set_variable(self, ctx, value)


class OptVariable(Variable):
    def get(self, ctx: Context):
        return Runtime.get_variable(self, ctx)


class Credentials:
    def __init__(
        self,
        description: str = "",
        vaultId: str = "",
        itemId: str = "",
        title: str = "",
        category: ECategory = ECategory.Null,
        scope: str = "",
        name: str = "",
        order: int = None,
    ):
        self.__description = description
        self.__vaultId = vaultId
        self.__itemId = itemId
        self.__title = title
        self.__category = category
        self.__scope = scope
        self.__name = name
        self.__order = order

    @property
    def description(self) -> str:
        return self.__description

    @property
    def vaultId(self) -> str:
        return self.__vaultId

    @property
    def itemId(self) -> str:
        return self.__itemId

    @property
    def title(self) -> str:
        return self.__title

    @property
    def category(self) -> ECategory:
        return self.__category

    @property
    def scope(self) -> str:
        return self.__scope

    @property
    def name(self) -> str:
        return self.__name

    @property
    def order(self) -> int:
        return self.__order

    def get_vault_item(self, ctx: Context = None):
        if Runtime.client is None:
            raise RuntimeNotInitializedError

        creds = None
        if self.vaultId != "" and self.itemId != "":
            creds = credentials(vaultId=self.vaultId, itemId=self.itemId)
        else:
            cr = self.name
            if self.scope == "Message":
                v = InVariable(name=self.name, scope=self.scope)
                cr = v.get(ctx=ctx)

            creds = credentials(vaultId=cr["vaultId"], itemId=cr["itemId"])

        request = plugin_pb2.GetVaultItemRequest(
            vaultId=creds.vaultId, ItemId=creds.itemId
        )
        response = Runtime.client.GetVaultItem(request)
        return json_format.MessageToDict(response.item)["value"]

    def set_vault_item(self, ctx: Context = None, data: bytes = []):
        if Runtime.client is None:
            raise RuntimeNotInitializedError

        creds = None
        if self.vaultId != "" and self.itemId != "":
            creds = credentials(vaultId=self.vaultId, itemId=self.itemId)
        else:
            cr = self.name
            if self.scope == "Message":
                v = InVariable(name=self.name, scope=self.scope)
                cr = v.get(ctx=ctx)

            creds = credentials(vaultId=cr["vaultId"], itemId=cr["itemId"])

        request = plugin_pb2.SetVaultItemRequest(
            vaultId=creds.vaultId,
            ItemId=creds.itemId,
            Data=data,
        )
        response = Runtime.client.SetVaultItem(request)
        return json_format.MessageToDict(response.item)["value"]


class credentials:
    def __init__(self, vaultId: str = "", itemId: str = ""):
        self.__vaultId = vaultId
        self.__itemId = itemId

    @property
    def vaultId(self) -> str:
        return self.__vaultId

    @property
    def itemId(self) -> str:
        return self.__itemId
