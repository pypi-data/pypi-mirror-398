import inspect
import json
import sys
from robomotion.node import Node
from robomotion.variable import (
    Variable,
    InVariable,
    OptVariable,
    OutVariable,
    Credentials,
    ECategory,
)
from re import sub
from robomotion.port import Port
from robomotion.tool import Tool
import base64


class NodeSpec:
    def __init__(
        self,
        id: str,
        icon: str = "",
        name: str = "",
        color: str = "",
        editor: str = None,
        inputs: int = 0,
        outputs: int = 0,
        filters: str = None,
        custom_ports: list = None,
    ):
        self.id = id
        self.icon = icon
        self.name = name
        self.color = color
        self.editor = editor
        self.inputs = inputs
        self.inputs = self.inputs[0]
        self.outputs = outputs
        self.outputs = self.outputs[0]
        self.filters = filters
        self.customPorts = custom_ports or []
        self.properties = []


class Property:
    def __init__(self, schema):
        self.schema = schema
        self.formData = {}
        self.uiSchema = {}


class Schema:
    def __init__(self, type: str, title: str):
        self.type = type
        self.title = title
        self.properties = {}


class SProperty:
    type = ""
    title = ""
    description = None
    subtitle = None
    category = None
    properties = None
    csScope = None
    jsScope = None
    customScope = None
    messageScope = None
    messageOnly = None
    aiScope = None
    multiple = None
    variableType = None
    enum = []
    enumNames = []


class VarDataProperty:
    def __init__(self, name: str, scope: str):
        self.scope = scope
        self.name = name


class Spec:
    @staticmethod
    def generate(plugin_name, version):
        frm = inspect.stack()[2]
        mod = inspect.getmodule(frm[0])
        clsmembers = inspect.getmembers(sys.modules[mod.__name__], inspect.isclass)

        pspec = {"name": plugin_name, "version": version}

        nodes = []

        for c in clsmembers:
            cls = c[1]
            if issubclass(cls, Node) and cls is not Node:
                node = {}
                inst = cls()
                node["id"] = inst.name
                node["name"] = inst.title
                node["icon"] = inst.icon
                node["color"] = inst.color
                node["editor"] = inst.editor
                node["inputs"] = inst.inputs
                node["outputs"] = inst.outputs

                # --- customPorts support ---
                custom_ports = []
                for attr in dir(cls):
                    value = getattr(cls, attr, None)
                    if isinstance(value, Port):
                        port_spec = {
                            "direction": value.direction,
                            "position": value.position,
                            "name": value.name,
                            "icon": value.icon,
                            "color": value.color,
                        }
                        if value.filters:
                            port_spec["filters"] = value.filters
                        # Attach order for sorting, but do not include in output
                        port_spec["_order"] = value.order if hasattr(value, "order") and value.order is not None else float('inf')
                        custom_ports.append(port_spec)
                # Sort by _order, then remove _order from output
                custom_ports.sort(key=lambda p: p["_order"])
                for p in custom_ports:
                    p.pop("_order", None)
                if custom_ports:
                    node["customPorts"] = custom_ports

                # --- filters support ---
                if hasattr(inst, "filters") and inst.filters:
                    node["filters"] = inst.filters

                # --- Tool support for AI tools ---
                for attr in dir(cls):
                    value = getattr(cls, attr, None)
                    if isinstance(value, Tool) and value.name:
                        node["tool"] = {
                            "name": value.name,
                            "description": value.description or ""
                        }
                        break

                properties = []
                inputVars = Spec.get_inputs_vars(cls)
                inputs = Spec.get_inputs(cls)

                # Merge and sort inputVars and inputs by order
                all_inputs = inputVars + inputs
                all_inputs = sorted(all_inputs, key=lambda x: getattr(x['val'], 'order', float('inf')) if hasattr(x['val'], 'order') and x['val'].order is not None else float('inf'))

                if len(all_inputs) > 0:
                    prop = {}

                    pSchema, pUISchema = {}, {}
                    pSchema["title"] = "Input"
                    pSchema["type"] = "object"

                    inProperties, formData = {}, {}
                    uiOrder = []

                    for _input in all_inputs:
                        input = _input["val"]
                        name = Spec.lower_first_letter(_input["key"])
                        # Special case for func: always output as type string

                        # --- b64: decoding for variable names ---
                        n = getattr(input, "name", "")
                        if isinstance(n, str) and n.startswith("b64:"):
                            try:
                                n = base64.b64decode(n[4:]).decode("utf-8")
                            except Exception:
                                pass

                        if name == "func":
                            inObject = {
                                "type": "string",
                                "title": input.title
                            }
                            pUISchema[name] = {"ui:widget": "hidden"}
                            inProperties[name] = inObject
                            formData[name] = n if name == "func" else {"scope": input.scope, "name": n} if isinstance(input, InVariable) else input.default
                        elif isinstance(input, InVariable):
                            inObject = {
                                "title": input.title,
                                "variableType": input.type,
                            }
                            if input.arrayFields is not None:
                                inObject["type"] = "array"
                                arrProps = {}
                                arr_fields = input.arrayFields
                                if isinstance(arr_fields, str):
                                    arr_fields = [arr_fields]
                                for arrField in arr_fields:
                                    arrProps[Spec.to_snake_case(arrField)] = {
                                        "type": "string",
                                        "title": arrField,
                                    }
                                inObject["items"] = {
                                    "type": "object",
                                    "properties": {
                                        "scope": {"type": "string"},
                                        "name": {"properties": arrProps},
                                    },
                                }
                            else:
                                inObject["type"] = "object"
                                inObject["properties"] = {
                                    "scope": {"type": "string"},
                                    "name": {"type": "string"},
                                }
                            if input.customScope:
                                inObject["customScope"] = True
                            if input.messageScope:
                                inObject["messageScope"] = True
                            if input.messageOnly:
                                inObject["messageOnly"] = True
                            if input.jsScope:
                                inObject["jsScope"] = True
                            if input.pyScope:
                                inObject["pyScope"] = True
                            if input.aiScope:
                                inObject["aiScope"] = True
                            if input.description != "":
                                inObject["description"] = input.description
                            if input.format != "":
                                inObject["format"] = input.format
                                pUISchema[name] = {"ui:field": input.format}
                            else:
                                if input.arrayFields is not None:
                                    pUISchema[name] = {"ui:field": "array"}
                                else:
                                    pUISchema[name] = {"ui:field": "variable"}
                            inProperties[name] = inObject
                            if input.arrayFields is not None:
                                formData[name] = []
                            else:
                                formData[name] = {"scope": input.scope, "name": input.name}
                        else:
                            inObject = {"type": input.type, "title": input.title}
                            if input.hidden:
                                pUISchema[name] = {"ui:widget": "hidden"}
                            if input.description != "":
                                inObject["description"] = input.description
                                pUISchema[name] = {"ui:field": "input"}
                            if input.format != "":
                                inObject["format"] = input.format
                                pUISchema[name] = {"ui:field": input.format}
                            inProperties[name] = inObject
                            formData[name] = input.default
                        uiOrder.append(name)

                    pSchema["properties"] = inProperties
                    pUISchema["ui:order"] = uiOrder

                    prop["schema"] = pSchema
                    prop["uiSchema"] = pUISchema
                    prop["formData"] = formData

                    properties.append(prop)

                outputVars = Spec.get_output_vars(cls)
                outputs = Spec.get_outputs(cls)

                # Merge and sort outputVars and outputs by order
                all_outputs = outputVars + outputs
                all_outputs = sorted(all_outputs, key=lambda x: getattr(x['val'], 'order', float('inf')) if hasattr(x['val'], 'order') and x['val'].order is not None else float('inf'))

                if len(all_outputs) > 0:
                    prop = {}

                    pSchema, pUISchema = {}, {}
                    pSchema["title"] = "Output"
                    pSchema["type"] = "object"

                    outProperties, formData = {}, {}
                    uiOrder = []

                    for _output in all_outputs:
                        output = _output["val"]
                        name = Spec.lower_first_letter(_output["key"])
                        if isinstance(output, OutVariable):
                            outObject = {
                                "type": "object",
                                "title": output.title,
                                "variableType": output.type,
                                "properties": {
                                    "scope": {"type": "string"},
                                    "name": {"type": "string"},
                                },
                            }
                            if output.messageScope:
                                outObject["messageScope"] = True
                            if output.messageOnly:
                                outObject["messageOnly"] = True
                            if output.aiScope:
                                outObject["aiScope"] = True
                            if output.description != "":
                                outObject["description"] = output.description
                            pUISchema[name] = {"ui:field": "variable"}
                            formData[name] = {"scope": output.scope, "name": output.name}
                        else:
                            outObject = {"type": output.type, "title": output.title}
                            if output.hidden:
                                pUISchema[name] = {"ui:widget": "hidden"}
                            if output.description != "":
                                outObject["description"] = output.description
                                pUISchema[name] = {"ui:field": "input"}
                            formData[name] = output.default
                        outProperties[name] = outObject
                        uiOrder.append(name)

                    pSchema["properties"] = outProperties
                    pUISchema["ui:order"] = uiOrder

                    prop["schema"] = pSchema
                    prop["uiSchema"] = pUISchema
                    prop["formData"] = formData

                    properties.append(prop)

                optionVars = Spec.get_option_vars(cls)
                options = Spec.get_options(cls)
                credentials = Spec.get_credentials(cls)

                # Merge and sort optionVars, options, and credentials by order
                all_options = optionVars + options + credentials
                all_options = sorted(all_options, key=lambda x: getattr(x['val'], 'order', float('inf')) if hasattr(x['val'], 'order') and x['val'].order is not None else float('inf'))

                if len(all_options) > 0:
                    prop = {}

                    pSchema, pUISchema = {}, {}
                    pSchema["title"] = "Options"
                    pSchema["type"] = "object"

                    optProperties, formData = {}, {}
                    uiOrder = []

                    for _option in all_options:
                        option = _option["val"]
                        name = Spec.lower_first_letter(_option["key"])
                        # OptVariable
                        if isinstance(option, OptVariable):
                            optObject = {
                                "title": option.title,
                                "variableType": option.type,
                            }
                            if option.arrayFields is not None:
                                optObject["type"] = "array"
                                arrProps = {}
                                arr_fields = option.arrayFields
                                if isinstance(arr_fields, str):
                                    arr_fields = [arr_fields]
                                for arrField in arr_fields:
                                    arrProps[Spec.to_snake_case(arrField)] = {
                                        "type": "string",
                                        "title": arrField,
                                    }
                                optObject["items"] = {
                                    "type": "object",
                                    "properties": {
                                        "scope": {"type": "string"},
                                        "name": {"properties": arrProps},
                                    },
                                }
                            else:
                                optObject["type"] = "object"
                                optObject["properties"] = {
                                    "scope": {"type": "string"},
                                    "name": {"type": "string"},
                                }
                            if option.customScope:
                                optObject["customScope"] = True
                            if option.messageScope:
                                optObject["messageScope"] = True
                            if option.messageOnly:
                                optObject["messageOnly"] = True
                            if option.jsScope:
                                optObject["jsScope"] = True
                            if option.pyScope:
                                optObject["pyScope"] = True
                            if option.aiScope:
                                optObject["aiScope"] = True
                            if option.description != "":
                                optObject["description"] = option.description
                            if option.format != "":
                                optObject["format"] = option.format
                                pUISchema[name] = {"ui:field": option.format}
                            else:
                                if option.arrayFields is not None:
                                    pUISchema[name] = {"ui:field": "array"}
                                else:
                                    pUISchema[name] = {"ui:field": "variable"}
                            optProperties[name] = optObject
                            if option.arrayFields is not None:
                                formData[name] = []
                            else:
                                formData[name] = {"scope": option.scope, "name": option.name}
                        # Credentials
                        elif isinstance(option, Credentials):
                            optObject = {
                                "type": "object",
                                "title": option.title,
                                "subtitle": option.title,
                                "category": int(option.category),
                                "customScope": True,
                                "messageScope": True,
                                "properties": {
                                    "scope": {
                                        "type": "string",
                                    },
                                    "name": {
                                        "type": "object",
                                        "properties": {
                                            "vaultId": {"type": "string"},
                                            "itemId": {"type": "string"},
                                        },
                                    },
                                },
                            }
                            if option.description != "":
                                optObject["description"] = option.description
                            pUISchema[name] = {"ui:field": "vault"}
                            formData[name] = {
                                "scope": "Custom",
                                "name": {"vaultId": "_", "itemId": "_"},
                            }
                            optProperties[name] = optObject
                        # Variable (plain option)
                        else:
                            optObject = {"type": option.type, "title": option.title}
                            category = option.category
                            if category != ECategory.Null:
                                optObject["category"] = int(category)
                            if option.description != "":
                                optObject["description"] = option.description
                                pUISchema[name] = {"ui:field": "input"}
                            if option.format != "":
                                optObject["format"] = option.format
                                pUISchema[name] = {"ui:field": option.format}
                            if option.enum is not None:
                                enums = option.enum.enums
                                if enums is not None and len(enums) > 0:
                                    enumNames = option.enum.enumNames
                                    optObject["enum"] = enums
                                    optObject["enumNames"] = enumNames
                            if option.hidden:
                                pUISchema[name] = {"ui:widget": "hidden"}
                            if option.default is not None:
                                formData[name] = option.default
                            optProperties[name] = optObject
                        uiOrder.append(name)

                    pSchema["properties"] = optProperties
                    pUISchema["ui:order"] = uiOrder

                    prop["schema"] = pSchema
                    prop["uiSchema"] = pUISchema
                    prop["formData"] = formData

                    properties.append(prop)

                node["properties"] = properties
                nodes.append(node)

        pspec["nodes"] = nodes
        print(json.dumps(pspec, indent=2))

    @staticmethod
    def cleandict(d):
        if not isinstance(d, dict):
            return d
        return dict((k, Spec.cleandict(v)) for k, v in d.iteritems() if v is not None)

    @staticmethod
    def jsonKeys2int(x):
        if isinstance(x, dict):
            return {int(k): v for k, v in x.items()}
        return x

    @staticmethod
    def get_variable_type(val) -> str:
        if isinstance(val, Variable):
            return Spec.upper_first_letter(val.type)

        return "String"

    @staticmethod
    def lower_first_letter(text: str) -> str:
        if len(text) < 2:
            return text.lower()
        return text[:1].lower() + text[1:]

    @staticmethod
    def upper_first_letter(text: str) -> str:
        if len(text) < 2:
            return text.upper()
        return text[:1].upper() + text[1:]

    @staticmethod
    def get_inputs(cls) -> list[any]:
        inputs = []
        fields = cls().cls().__dict__
        for key in fields.keys():
            val = fields[key]
            # Special case for inFunc
            if key == "inFunc":
                prop_key = "Func"
            else:
                prop_key = key
            if (
                isinstance(val, Variable)
                and not isinstance(val, InVariable)
                and not isinstance(val, OutVariable)
                and not isinstance(val, OptVariable)
                and val.input
            ):
                inputs.append({"key": prop_key, "val": val})
            elif (
                not isinstance(val, InVariable)
                and not isinstance(val, OutVariable)
                and not isinstance(val, OptVariable)
                and key.lower().startswith("in")
            ):
                inputs.append(
                    {
                        "key": prop_key,
                        "val": Variable(
                            title=Spec.camel_case_to_text(key.lstrip("in")),
                            type=Spec.get_type(val),
                            default=val,
                        ),
                    }
                )

        return inputs

    @staticmethod
    def get_inputs_vars(cls) -> list[any]:
        inputs = []
        fields = cls().cls().__dict__
        for key in fields.keys():
            val = fields[key]
            # Special case for inFunc
            if key == "inFunc":
                prop_key = "Func"
            else:
                prop_key = key
            if isinstance(val, InVariable):
                inputs.append({"key": prop_key, "val": val})

        return inputs

    @staticmethod
    def get_outputs(cls) -> list[any]:
        outputs = []
        fields = cls().cls().__dict__
        for key in fields.keys():
            val = fields[key]
            if (
                isinstance(val, Variable)
                and not isinstance(val, InVariable)
                and not isinstance(val, OutVariable)
                and not isinstance(val, OptVariable)
                and val.output
            ):
                outputs.append({"key": key, "val": val})
            elif (
                not isinstance(val, InVariable)
                and not isinstance(val, OutVariable)
                and not isinstance(val, OptVariable)
                and key.lower().startswith("out")
            ):
                outputs.append(
                    {
                        "key": key,
                        "val": Variable(
                            title=Spec.camel_case_to_text(key.lstrip("out")),
                            type=Spec.get_type(val),
                            default=val,
                        ),
                    }
                )

        return outputs

    @staticmethod
    def get_output_vars(cls) -> list[any]:
        outputs = []
        fields = cls().cls().__dict__
        for key in fields.keys():
            val = fields[key]
            if isinstance(val, OutVariable):
                outputs.append({"key": key, "val": val})

        return outputs

    @staticmethod
    def get_options(cls) -> list[any]:
        options = []
        fields = cls().cls().__dict__
        for key in fields.keys():
            val = fields[key]
            if (
                isinstance(val, Variable)
                and not isinstance(val, InVariable)
                and not isinstance(val, OutVariable)
                and not isinstance(val, OptVariable)
                and val.option
            ):
                options.append({"key": key, "val": val})
            elif (
                not isinstance(val, InVariable)
                and not isinstance(val, OutVariable)
                and not isinstance(val, OptVariable)
                and not isinstance(val, Credentials)
                and key.lower().startswith("opt")
            ):
                options.append(
                    {
                        "key": key,
                        "val": Variable(
                            title=Spec.camel_case_to_text(key.lstrip("opt")),
                            type=Spec.get_type(val),
                            default=val,
                        ),
                    }
                )

        return options

    @staticmethod
    def get_credentials(cls) -> list[any]:
        credentials = []
        fields = cls().cls().__dict__
        for key in fields.keys():
            val = fields[key]
            if isinstance(val, Credentials):
                credentials.append({"key": key, "val": val})

        return credentials

    @staticmethod
    def get_option_vars(cls) -> list[any]:
        options = []
        fields = cls().cls().__dict__
        for key in fields.keys():
            val = fields[key]
            if isinstance(val, OptVariable):
                options.append({"key": key, "val": val})

        return options

    @staticmethod
    def camel_case_to_text(str):
        words = [[str[0].upper()]]

        for c in str[1:]:
            if words[-1][-1].islower() and c.isupper():
                words.append(list(c))
            else:
                words[-1].append(c)

        word_arr = ["".join(word) for word in words]
        return " ".join(word_arr)

    @staticmethod
    def get_type(val):
        if isinstance(val, bool):
            return "boolean"
        elif isinstance(val, int) or isinstance(val, float):
            return "number"
        return "string"

    @staticmethod
    def to_snake_case(s):
        return "_".join(
            sub(
                "([A-Z][a-z]+)", r" \1", sub("([A-Z]+)", r" \1", s.replace("-", " "))
            ).split()
        ).lower()
