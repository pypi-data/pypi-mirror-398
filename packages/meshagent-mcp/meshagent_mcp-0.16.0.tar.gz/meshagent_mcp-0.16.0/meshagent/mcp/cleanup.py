_OPTIONAL_PROPERTIES = "optional_properties"


def replace_optional_parameters(arguments: dict):
    for p, pv in list(arguments.items()):
        if p == _OPTIONAL_PROPERTIES:
            for parameter in arguments[_OPTIONAL_PROPERTIES]:
                for k, v in parameter.items():
                    if v != "":
                        arguments[k] = v

            del arguments[_OPTIONAL_PROPERTIES]

        elif isinstance(pv, dict):
            replace_optional_parameters(pv)

    return arguments


def cleanup(data: dict, root: bool):
    examples = None

    # rewrite refs to point to $defs since OpenAI requires them to be in $defs
    if "$ref" in data:
        ref: str = data["$ref"]
        data["$ref"] = ref.replace("/components/schemas", "/$defs")

    # move schemas to $defs since OpenAI requires them to be in $defs
    if root:
        if "components" in data:
            components = data.pop("components")
            if "schemas" in components:
                schemas = components.pop("schemas")
                data["$defs"] = schemas

    if "x-fal-order-properties" in data:
        data.pop("x-fal-order-properties")

    if "examples" in data:
        examples = data.pop("examples")
        description = ""
        if "description" in data:
            description = data["description"]

        description = f"{description}. examples: {examples}"
        data["description"] = description

    if "properties" in data:
        optional_properties = []
        required = data.get("required", [])

        for k, v in data["properties"].items():
            description = ""
            if "description" in v:
                description = v["description"]

            # these props are not supported by oai at the moment, so let's add them to the description
            if "minimum" in v:
                minimum = v.pop("minimum")
                description = f"{description}. minimum: {minimum}"
                v["description"] = description

            if "exclusiveMinimum" in v:
                exclusiveMinimum = v.pop("exclusiveMinimum")
                description = f"{description}. exclusiveMinimum: {exclusiveMinimum}"
                v["description"] = description

            if "exclusiveMaximum" in v:
                exclusiveMaximum = v.pop("exclusiveMaximum")
                description = f"{description}. exclusiveMaximum: {exclusiveMaximum}"
                v["description"] = description

            if "minLength" in v:
                minLength = v.pop("minLength")
                description = f"{description}. minLength: {minLength}"
                v["description"] = description

            if "maxLength" in v:
                maxLength = v.pop("maxLength")
                description = f"{description}. maxLength: {maxLength}"
                v["description"] = description

            if "maximum" in v:
                maximum = v.pop("maximum")
                description = f"{description}. maximum: {maximum}"
                v["description"] = description

            if "default" in v:
                default = v.pop("default")
                description = f"{description}. unless otherwise specified, this default value should be used: {default}"
                v["description"] = description

            if "examples" in data:
                examples = data.pop("examples")
                description = f"{description}. examples: {examples}"
                v["description"] = description

            if k not in required and k != "sync_mode" and k != "num_images":
                optional_properties.append(k)

        if len(optional_properties) > 0:
            anyOf = []
            optional_schema = {"type": "array", "items": {"anyOf": anyOf}}
            for k in optional_properties:
                anyOf.append(
                    {
                        "type": "object",
                        "required": [k],
                        "additionalProperties": False,
                        "properties": {k: data["properties"][k]},
                    }
                )
                del data["properties"][k]

            data["properties"][_OPTIONAL_PROPERTIES] = optional_schema

        data["additionalProperties"] = False
        data["required"] = list(data["properties"].keys())

    if "type" in data:
        if data["type"] == "object" and "properties" not in data:
            data["additionalProperties"] = False
            data["required"] = []

    for k, v in data.items():
        if isinstance(v, dict):
            cleanup(v, False)

        if isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    cleanup(i, False)
