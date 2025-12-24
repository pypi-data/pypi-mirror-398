"""The typerconf module and config subcommand"""

import appdirs
import argparse
import io
import json
import logging
import os
import pathlib
import sys
import typer
import typing
from typing_extensions import Annotated

normalized_path = os.path.normpath(sys.argv[0])
basename = os.path.basename(normalized_path)
dirs = appdirs.AppDirs(basename)


class Config:
    """Navigates nested JSON structures by dot-separated addressing."""

    def __init__(self, json_data: dict = None, conf_file=None):
        """
        Constructs a config object to navigate from JSON data `json_data`.

        `conf_file` takes a path to a file which will be used as a config file. If this
        argument is supplied, the data will be read from the file.

        Also, if `conf_file` is not None, we will enable automatic write back. So
        that any changes (invokations of the `.set` method) will be written to the
        config file immediately.

        To not enable write back, load file contents with the `.read_config` method.
        """
        if not json_data:
            self.__data = {}
        else:
            self.__data = json_data
        if isinstance(conf_file, io.IOBase):
            try:
                self.__conf_file = conf_file.name
            except AttributeError:
                raise ValueError(
                    f"can't enable writeback when `conf_file` is "
                    f"a file-like object without a name: {conf_file}"
                )
        else:
            self.__conf_file = conf_file

        if self.__conf_file:
            self.read_config(self.__conf_file)

    def get(self, path: str = "") -> typing.Any:
        """
        Returns object at `path`.
        Example:
        - `path = "courses.datintro22.url"` and
        - Config contains `{"courses": {"datintro22": {"url": "https://..."}}}`
          will return "https://...".

        Any part of the path that can be converted to an integer, will be converted
        to an integer. This way we can access elements of lists too.
        """
        structure = self.__data

        if not path:
            return structure

        for part in path.split("."):
            try:
                part = int(part)
            except ValueError:
                pass
            try:
                structure = structure[part]
            except KeyError:
                raise KeyError(f"{part} along {path} doesn't exist")

        return structure

    def set(self, path: str, value: typing.Any):
        """
        Sets `value` at `path`. Any parts along the path that don't exist will be
        created.

        Example:
        - `value = "https://..."`,
        - `path = "courses.datintro22.url"`
        will create `{"courses": {"datintro22": {"url": "https://..."}}}`.

        Any part of the path that can be converted to an integer, will be converted
        to an integer. This way we can access elements of lists too. However, we
        cannot create index 3 in a list if it doesn't exist (we can't expand
        lists).

        If `value` is `None`, the entry at `path` will be deleted, if it exists.

        If write back is set (see `.__init__` and `.read_config`), a successful set
        will also update the original config file.
        """
        structure = self.__data

        parts = path.split(".")

        for part in parts[:-1]:
            try:
                part = int(part)
            except ValueError:
                pass
            try:
                structure = structure[part]
            except KeyError:
                if value is None:
                    return
                else:
                    structure[part] = {}
                    structure = structure[part]

        part = parts[-1]
        try:
            part = int(part)
        except ValueError:
            pass

        if value is None:
            try:
                del structure[part]
            except KeyError:
                pass
        else:
            structure[part] = value
        if self.__conf_file:
            self.write_config(self.__conf_file)

    def paths(self, from_root: str = ""):
        """
        Returns all existing paths.

        The optional argument `from_root` is a path and the method return all
        subpaths rooted at that point.
        """
        paths = []
        root = self.get(from_root)

        if isinstance(root, dict):
            for part in root:
                if from_root:
                    path = f"{from_root}.{part}"
                else:
                    path = part

                paths.append(path)
                paths += self.paths(from_root=path)
        elif isinstance(root, list):
            paths += [f"{from_root}.{x}" for x in range(len(root))]

        return paths

    def read_config(
        self,
        conf_file: pathlib.Path = f"{dirs.user_config_dir}/config.json",
        writeback=False,
    ):
        """
        Reads the config data structure (JSON) into the Config object.

        `conf_file` is an optional argument providing one of the following:
        - an already opened file object (anything derived from `io.IOBase`);
        - anything that `open` can handle, for instance:
          - a string, which is the path to the config file;
          - an integer, which is a file descriptor (see `os.open`).

        If `writeback` is set to True, store the `conf_file` object and turn on
        automatic write back. This means that any changes using the `.set` method will
        cause the config being written back to the file.

        Note that write back cannot be enabled with already opened files (as the mode
        is already fixed).

        Errors:

        - The first is that the file doesn't exist (FileNotFoundError). We silently
          fail this error. The reason is that the file doesn't exist, which means it's
          an empty config. We fail silently as a later write would succeed.
        - There is also a related one, NotADirectoryError. The problem of
          NotADirectoryError occurs when a file on the path is used as a directory ---
          but only for reading, when trying to create a directory hierarchy, it will
          yield FileExistsError. We can't recover from this error, as an attempt to
          write to the file will also fail. We will reraise the exception with a better
          error message.
        - Finally, the file exists, but it's not proper JSON (JSONDecodeError). This is
          also a fatal error, we don't want a subsequent write to overwrite a corrupted
          config. We reraise the exception with a better error message.
        """
        if isinstance(conf_file, io.IOBase):
            self.__data = merge_dictionaries(self.__data, json.load(conf_file))
        else:
            try:
                with open(conf_file) as conf_file:
                    self.__data = merge_dictionaries(self.__data, json.load(conf_file))
            except FileNotFoundError as err:
                pass
            except NotADirectoryError as err:
                raise NotADirectoryError(
                    f"A part of the path is a file, " f"but used as directory: {err}"
                )
            except json.decoder.JSONDecodeError as err:
                raise ValueError(
                    f"Config file {conf_file} " f"could not be decoded: {err}"
                )

        if writeback:
            if isinstance(conf_file, io.IOBase):
                try:
                    self.__conf_file = conf_file.name
                except AttributeError:
                    raise ValueError(
                        f"can't enable writeback when `conf_file` is "
                        f"a file-like object without a name: {conf_file}"
                    )
            else:
                self.__conf_file = conf_file

    def write_config(
        self, conf_file: pathlib.Path = f"{dirs.user_config_dir}/config.json"
    ):
        """
        Stores the config data (as JSON) in the config file.
        `conf_file` is an optional argument providing one of the following:
        - an already opened file object (anything derived from `io.IOBase`);
        - anything that `open` can handle, for instance:
          - a string, which is the path to the config file;
          - an integer, which is a file descriptor (see `os.open`).
        """
        if isinstance(conf_file, io.IOBase):
            json.dump(self.__data, conf_file)
        else:
            conf_dir = os.path.dirname(conf_file)
            if conf_dir and not os.path.isdir(conf_dir):
                os.makedirs(conf_dir)

            with open(conf_file, "w") as conf_file:
                json.dump(self.__data, conf_file)


def add_config_cmd(
    cli: typing.Union[typer.Typer, argparse._SubParsersAction], conf_path: str = None
):
    """
    Add config command to a command-line interface `cli`.

    `cli` can be either a Typer instance or an argparse subparser.

    If `conf_path` is not None, use that file instead of the default.
    """
    if isinstance(cli, typer.Typer):
        add_config_typer(cli, conf_path)
    elif isinstance(cli, argparse._SubParsersAction):
        add_config_argparse(cli, conf_path)
    else:
        raise TypeError(
            f"cli must be a Typer instance or an argparse subparser, "
            f"not {type(cli)}"
        )


def merge_dictionaries(dict1: dict, dict2: dict):
    """
    Returns a copy of dir1 with values in dir1 updated from dir2 for keys that
    exist. Keys that exist in dir2 are created in dir, with the proper values.

    The merge recurses through values that are dictionaries, which makes this
    different from `dir1 | dir2` and `{**dir1, **dir2}`. Using those would replace
    entire subdictionaries instead of merging them.
    """
    new_dict = dict1.copy()

    for key, value in dict2.items():
        try:
            if isinstance(value, dict) and isinstance(
                current_value := new_dict[key], dict
            ):
                new_dict[key] = merge_dictionaries(current_value, value)
            else:
                new_dict[key] = value
        except KeyError:
            new_dict[key] = value

    return new_dict


def get(path: str = "") -> typing.Any:
    """
    Returns the value stored at `path` in the config.

    By default, `path = ""`, which returns the entire configuration as a Config
    object.
    """
    conf = Config()
    conf.read_config()
    return conf.get(path)


def set(path: str, value: typing.Any):
    """
    Sets `value` at `path` in the config. `value` will be interpreted as JSON, if
    conversion to JSON fails, it will be used as is.

    If `value` is `None`, the entry referenced by `path` will be deleted, if it
    exists.
    """
    conf = Config()
    conf.read_config()
    conf.set(path, value)
    conf.write_config()


def add_config_typer(cli: typer.Typer, conf_path: str = None):
    """
    Add config command to Typer instance `cli`.

    If `conf_path` is not None, use that file instead of the default.
    """
    conf = Config()
    try:
        if conf_path:
            conf.read_config(conf_path, writeback=True)
        else:
            conf.read_config(writeback=True)
    except ValueError:
        pass
    path_arg = typer.Argument(
        help="Path in config, e.g. 'courses.datintro22'. "
        "Empty string is root of config. Defaults to "
        "the empty string.",
        autocompletion=complete_path_callback,
    )
    value_arg = typer.Option(
        "-s",
        "--set",
        help="Values to store. "
        "More than one value makes a list. "
        "Values are treated as JSON if possible.",
    )

    def config_cmd(
        path: Annotated[str, path_arg] = "",
        values: Annotated[typing.List[str], value_arg] = [],
    ):
        """
        Reads values from or writes values to the config.
        """
        if values:
            if len(values) == 1:
                values = values[0]
            if values == "":
                values = None
            conf.set(path, values)
        else:
            print_config(conf.get(path), path)

    def config_argparse(args: argparse.Namespace):
        """
        Calls the config command with the args from the command line.
        `args` is what the [[parser.parse_args()]] function returns.
        """
        config_cmd(args.path, args.set)

    # decorator hack to reuse config_cmd
    cli.command(name="config")(config_cmd)


def add_config_argparse(subparsers: argparse._SubParsersAction, conf_path: str = None):
    """
    Adds the config command to the `parser` instance.

    If `conf_path` is not None, use that file instead of the default.
    """
    conf = Config()
    try:
        if conf_path:
            conf.read_config(conf_path, writeback=True)
        else:
            conf.read_config(writeback=True)
    except ValueError:
        pass
    path_arg = typer.Argument(
        help="Path in config, e.g. 'courses.datintro22'. "
        "Empty string is root of config. Defaults to "
        "the empty string.",
        autocompletion=complete_path_callback,
    )
    value_arg = typer.Option(
        "-s",
        "--set",
        help="Values to store. "
        "More than one value makes a list. "
        "Values are treated as JSON if possible.",
    )

    def config_cmd(
        path: Annotated[str, path_arg] = "",
        values: Annotated[typing.List[str], value_arg] = [],
    ):
        """
        Reads values from or writes values to the config.
        """
        if values:
            if len(values) == 1:
                values = values[0]
            if values == "":
                values = None
            conf.set(path, values)
        else:
            print_config(conf.get(path), path)

    def config_argparse(args: argparse.Namespace):
        """
        Calls the config command with the args from the command line.
        `args` is what the [[parser.parse_args()]] function returns.
        """
        config_cmd(args.path, args.set)

    config_parser = subparsers.add_parser(
        "config", help="Reads values from or writes values to the config."
    )
    config_parser.add_argument(
        "path",
        help="Path in config, e.g. 'courses.datintro22'. "
        "Empty string is root of config. Defaults to "
        "the empty string.",
        type=str,
        nargs="?",
        default="",
    )
    config_parser.add_argument(
        "-s",
        "--set",
        help="Values to store. "
        "More than one value makes a list. "
        "Values are treated as JSON if possible.",
        type=str,
        nargs="*",
        default=[],
    )
    config_parser.set_defaults(func=config_argparse)


def complete_path(initial_path: str, conf: Config = None):
    """
    Returns all valid paths in the config starting with `initial_path`.
    If `conf` is not None, use that instead of the actual config.
    """
    if not conf:
        conf = Config(get())

    return filter(lambda x: x.startswith(initial_path), conf.paths())


def complete_path_callback(initial_path: str):
    return complete_path(initial_path)


def print_config(conf: Config, path: str = ""):
    """
    Prints the config tree contained in `conf` to stdout.
    Optional `path` is prepended.
    """
    try:
        for key in conf.keys():
            if path:
                print_config(conf[key], f"{path}.{key}")
            else:
                print_config(conf[key], key)
    except AttributeError:
        print(f"{path} = {conf}")


def main():
    cli = typer.Typer()
    add_config_cmd(cli)
    cli()


if __name__ == "__main__":
    main()
