import datetime
import inspect
import json
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from cerberus import Validator


class Config:
    """Base class for configuration files."""

    @staticmethod
    def validate(
        config_dict: dict | None = None,
        config_file: str | None = None,
        schema_dict: dict | None = None,
        schema_file: str | None = None,
        allow_unknown: bool = False,
        require_all: bool = False,
    ):
        """Validate the config file with the schema file.

        Args:
            config_dict (dict, optional): config dictionary. Defaults to None.
            config_file (str, optional): path to the YAML config file, will override `config_dict`. Defaults to None.
            schema_dict (dict, optional): schema dictionary. Defaults to None.
            schema_file (str, optional): path to the YAML schema file, will override `schema_dict`. Defaults to None.
            allow_unknown (bool, optional): whether to allow unknown fields in the config file. Defaults to False.
            require_all (bool, optional): whether to require all fields in the schema file to be present in the config file. Defaults to False.

        Raises:
            ValueError: if the config file does not match the schema
        """
        if not config_dict and config_file:
            with open(config_file) as f:
                config_dict = yaml.safe_load(f)
        if not schema_dict and schema_file:
            with open(schema_file) as f:
                schema_dict = yaml.safe_load(f)

        if not config_dict:
            raise ValueError("`config_dict` is empty. Must provide `config_dict` or `config_file`")
        if not schema_dict:
            raise ValueError("`schema_dict` is empty. Must provide `schema_dict` or `schema_file`")

        ## validate
        v = Validator(allow_unknown=allow_unknown, require_all=require_all)  # type: ignore
        v.schema = schema_dict  # set the schema separately to ensure it is valid # type: ignore
        is_valid = v.validate(config_dict)  # type: ignore
        if not is_valid:
            config_path = Path(config_file).as_posix() if config_file else "<input dict>"
            schema_path = Path(schema_file).as_posix() if schema_file else "<input dict>"
            raise ValueError(
                f"Incorrect configurations:\n"
                f"  Config: {config_path}\n"
                f"  Schema: {schema_path}\n"
                f"  Error:\n{v.errors}\n"  # type: ignore
            )
        return

    @staticmethod
    def loadconfig(filename: str | Path) -> dict:
        """Load data from a JSON or YAML file.

        Args:
        filename (Union[str, Path]): The filename to load data from, whose suffix should be .json, jsonc, .yml, or .yml

        Returns:
            jdata: (dict) The data loaded from the file

        Notes:
            - The YAML file can contain variable-interpolation, will be processed by [OmegaConf](https://omegaconf.readthedocs.io/en/2.2_branch/usage.html#variable-interpolation). Example input YAML file:
                ```yaml
                server:
                host: localhost
                port: 80

                client:
                url: http://${server.host}:${server.port}/
                server_port: ${server.port}
                # relative interpolation
                description: Client of ${.url}
                ```
        """
        if Path(filename).suffix in [".json", ".jsonc"]:
            jdata = Config._load_jsonc(filename)
        elif Path(filename).suffix in [".yml", ".yml"]:
            from omegaconf import OmegaConf

            conf = OmegaConf.load(filename)
            jdata = OmegaConf.to_container(conf, resolve=True)
        else:
            raise ValueError(f"Unsupported file format: {filename}")

        if not jdata:
            jdata = {}
            warnings.warn(f"Empty config file: {filename}")
        return jdata  # type: ignore[type-mixed]

    @staticmethod
    def _load_jsonc(filename: str | Path) -> Any:
        """Load data from a JSON file that allow comments."""
        with open(filename) as f:
            lines = f.readlines()
        cleaned_lines = [line.strip().split("//", 1)[0] for line in lines if line.strip()]
        text = "\n".join(cleaned_lines)
        jdata = json.loads(text)
        return jdata


#####ANCHOR: Function agruments
def get_default_args(func: Callable) -> dict:
    """Get dict of default values of arguments of a function.

    Args:
        func (Callable): function to inspect
    """
    argspec = inspect.getfullargspec(func)
    no_default_args = ["no_default_value"] * (len(argspec.args) - len(argspec.defaults))  # type: ignore
    all_values = no_default_args + list(argspec.defaults)  # type: ignore
    argdict = dict(zip(argspec.args, all_values))
    return argdict


def argdict_to_schemadict(func: Callable) -> dict:
    """Convert a function's type-annotated arguments into a cerberus schema dict.

    Handles:
        - Single types
        - Union types (as list of types)
        - Nullable types (`None` in Union)
        - Only checks top-level types (no recursion into `list[int]`, `dict[str, float]`, etc.)
        - Supports multiple types in cerberus (e.g. `{"type": ["integer", "string"]}`) when a `Union` is given.

    Args:
        func (callable): function to inspect

    Returns:
        schemadict (dict): cerberus schema dictionary
    """
    from types import UnionType
    from typing import Union, get_args, get_origin

    ### Mapping Python types to cerberus types: https://docs.python-cerberus.org/validation-rules.html
    TYPE_MAP = {
        int: "integer",
        float: "float",
        str: "string",
        bool: "boolean",
        list: "list",
        set: "set",
        dict: "dict",
        bytes: "binary",
        bytearray: "binary",
        datetime.datetime: "datetime",
        datetime.date: "date",
    }

    sig = inspect.signature(func)
    schemadict = {}

    for name, param in sig.parameters.items():
        nullable = False
        types_list = []
        if param.annotation is inspect._empty:
            types_list = list(TYPE_MAP.values())  # allow all types if no annotation
        else:
            ann = param.annotation
            origin = get_origin(ann)
            args = get_args(ann)

            # Handle Union types (e.g., Union[int, str, None], and PEP 604 X | Y syntax)
            if origin is Union or isinstance(ann, UnionType):
                if not args:  # fallback for | syntax in some cases
                    args = ann.__args__ if hasattr(ann, "__args__") else []
                for a in args:
                    if a is type(None):
                        nullable = True
                    else:
                        t = TYPE_MAP.get(a)
                        if t:
                            types_list.append(t)
            else:
                t = TYPE_MAP.get(ann)
                if t:
                    types_list.append(t)

        ### Ensure types is list of strings
        types_list = [item for t in types_list for item in (t if isinstance(t, list) else [t])]

        ### Deduplicate types while preserving order ("list(set(types))" does not preserve order)
        types_list = list(dict.fromkeys(types_list))

        ### If no type found, allow all types
        if not types_list:
            types_list = list(TYPE_MAP.values())

        ### Build schema entry
        entry = {"type": types_list[0]} if len(types_list) == 1 else {"type": types_list}
        if param.default is not inspect._empty:
            entry["default"] = param.default
        if nullable:
            entry["nullable"] = True  # type: ignore

        schemadict[name] = entry
    return schemadict
