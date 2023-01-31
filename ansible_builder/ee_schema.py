from jsonschema import validate, SchemaError, ValidationError

from ansible_builder.exceptions import DefinitionError


TYPE_StringOrListOfStrings = {
    "anyOf": [
        {"type": "string"},
        {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    ]
}


############
# Version 1
############

schema_v1 = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "version": {
            "description": "The EE schema version number",
            "type": "number",
        },

        "ansible_config": {
            "type": "string",
        },

        "build_arg_defaults": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "EE_BASE_IMAGE": {
                    "type": "string",
                },
                "EE_BUILDER_IMAGE": {
                    "type": "string",
                },
                "ANSIBLE_GALAXY_CLI_COLLECTION_OPTS": {
                    "type": "string",
                },
            },
        },

        "dependencies": {
            "description": "The dependency stuff",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "python": {
                    "description": "The python dependency file",
                    "type": "string",
                },
                "galaxy": {
                    "description": "The Galaxy dependency file",
                    "type": "string",
                },
                "system": {
                    "description": "The system dependency file",
                    "type": "string",
                },
            },
        },

        "additional_build_steps": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "prepend": TYPE_StringOrListOfStrings,
                "append": TYPE_StringOrListOfStrings,
            },
        },
    },
}


############
# Version 2
############

schema_v2 = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "version": {
            "description": "The EE schema version number",
            "type": "number",
        },

        "ansible_config": {
            "type": "string",
        },

        "build_arg_defaults": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "ANSIBLE_GALAXY_CLI_COLLECTION_OPTS": {
                    "type": "string",
                },
            },
        },

        "dependencies": {
            "description": "The dependency stuff",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "python": {
                    "description": "The python dependency file",
                    "type": "string",
                },
                "galaxy": {
                    "description": "The Galaxy dependency file",
                    "type": "string",
                },
                "system": {
                    "description": "The system dependency file",
                    "type": "string",
                },
            },
        },

        "images": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "base_image": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                        },
                        "signature_original_name": {
                            "type": "string",
                        },
                    },
                },
                "builder_image": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                        },
                        "signature_original_name": {
                            "type": "string",
                        },
                    },
                }
            },
        },

        "additional_build_steps": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "prepend_base": TYPE_StringOrListOfStrings,
                "append_base": TYPE_StringOrListOfStrings,
                "prepend_galaxy": TYPE_StringOrListOfStrings,
                "append_galaxy": TYPE_StringOrListOfStrings,
                "prepend_builder": TYPE_StringOrListOfStrings,
                "append_builder": TYPE_StringOrListOfStrings,
                "prepend_final": TYPE_StringOrListOfStrings,
                "append_final": TYPE_StringOrListOfStrings,
            },
        },
    },
}


def validate_schema(ee_def: dict):
    schema_version = 1
    if 'version' in ee_def:
        try:
            schema_version = int(ee_def['version'])
        except ValueError:
            raise DefinitionError(f"Schema version not an integer: {ee_def['version']}")

    if schema_version not in (1, 2):
        raise DefinitionError(f"Unsupported schema version: {schema_version}")

    try:
        if schema_version == 1:
            validate(instance=ee_def, schema=schema_v1)
        elif schema_version == 2:
            validate(instance=ee_def, schema=schema_v2)
    except (SchemaError, ValidationError) as e:
        raise DefinitionError(msg=e.message, path=e.absolute_schema_path)

    _handle_aliasing(ee_def)


def _handle_aliasing(ee_def: dict):
    """
    Upgrade EE keys into standard keys across schema versions.

    Some EE keys are renamed across schema versions. So that we don't need to
    check schema version, or do some other hackery, in the builder code when
    accessing the values, just do the key name upgrades/aliasing here.
    """

    if 'additional_build_steps' in ee_def:
        # V1 'prepend' == V2 'prepend_final'
        if 'prepend' in ee_def['additional_build_steps']:
            ee_def['additional_build_steps']['prepend_final'] = ee_def['additional_build_steps']['prepend']

        # V1 'append' == V2 'append_final'
        if 'append' in ee_def['additional_build_steps']:
            ee_def['additional_build_steps']['append_final'] = ee_def['additional_build_steps']['append']
