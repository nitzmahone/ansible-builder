from voluptuous import Schema, Coerce, Required, Invalid

from ansible_builder.exceptions import DefinitionError


def _str_or_list():
    """
    Schema validation function for types that may be either a `str` or a `list`.
    """
    def f(v):
        if type(v) != str and type(v) != list:
            raise Invalid('expected str or list')
    return f


############
# Version 1
############

schema_v1 = Schema({
    "version": Required(Coerce(int), default=1),

    "build_arg_defaults": {
        "EE_BASE_IMAGE": str,
        "EE_BUILDER_IMAGE": str,
        "ANSIBLE_GALAXY_CLI_COLLECTION_OPTS": str,
    },

    "ansible_config": str,

    "dependencies": {
        "python": str,
        "galaxy": str,
        "system": str,
    },

    "additional_build_steps": {
        "prepend": _str_or_list(),
        "append": _str_or_list(),
    },
})


############
# Version 2
############

schema_v2 = Schema({
    "version": Required(Coerce(int, msg="'version' must be an integer")),

    "build_arg_defaults": {
        "ANSIBLE_GALAXY_CLI_COLLECTION_OPTS": str,
    },

    "ansible_config": str,

    "dependencies": {
        "python": str,
        "galaxy": str,
        "system": str,
    },

    "additional_build_steps": {
        "prepend": _str_or_list(),
        "append": _str_or_list(),
    },

    "images": {
        "base_image": {
            "name": str,
            "signature_original_name": str,
        },
        "builder_image": {
            "name": str,
            "signature_original_name": str,
        },
    },
})


def validate_schema(ee_def):
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
            schema_v1(ee_def)
        elif schema_version == 2:
            schema_v2(ee_def)
    except Invalid as e:
        msg = str(e)
        raise DefinitionError(msg=msg, path=e.path)
