import csv
import os
import re
import sys
from typing import Dict, List, Set

import yaml

from .core import debug
from .exceptions import SQLArrayMalformedValue, SQLInconsistentArrayLen, SQLInvalidArray

# Address fix CSV columns
ADDR_FIX_BUILT_ADDR = "Hito-based email"
ADDR_FIX_FIXED_ADDR = "Fixed email"


def get_config_path_default(input_file_dir=None, main_script=None):
    """
    Compute the default location to use for the configuration file path, using the directory of
    the input file if the configuration file exists in it else the script directory. The file name
    is based on the script name with the .cfg extension. The file path returned is an
    absolute path so that it is handled properly by load_config_file (that adds the current
    script directory if the path is relative).

    :param input_file_dir: directory where the input file resides
    :param main_script: path of the main script, defaults to sys.modules["__main__"]
    :return: actual default for the configuration file absolute path + default file name
    """
    if main_script is None:
        main_script = sys.modules["__main__"].__file__
    config_file_name = "{}.cfg".format(os.path.splitext(os.path.basename(main_script))[0])
    if input_file_dir is None:
        config_file_path = None
    else:
        if input_file_dir == "":
            input_file_dir = os.getcwd()
        config_file_path = os.path.join(input_file_dir, config_file_name)
    if config_file_path is None or not os.path.exists(config_file_path):
        config_file_path = os.path.join(os.path.dirname(main_script), config_file_name)
    config_file_path = os.path.abspath(config_file_path)
    debug("DEBUG: using configuration file {}".format(config_file_path))
    return config_file_path, config_file_name


def load_config_file(config_file: str, required: bool = False):
    """
    Load the config file, apply defaults and return the corresponding dict.
    If config file is not absolute, prefix with directory where this script resides

    :param config_file: config file name
    :param required: if True and the file is missing, raise an Exception
    :return: dict containing the options
    """

    if not os.path.isabs(config_file):
        this_script_dir = os.path.dirname(sys.modules["__main__"].__file__)
        if len(this_script_dir) == 0:
            this_script_dir = os.path.curdir
        config_file = os.path.join(this_script_dir, config_file)
    else:
        config_file = config_file
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_options = yaml.safe_load(f)
    except IOError as e:
        if e.errno == 2:
            if required:
                print("ERROR: Configuration file ({}) is missing.".format(config_file))
                raise e
            else:
                print("WARNING: Configuration file ({}) is missing.".format(config_file))
                # Return an empty dict if config file is missing
                config_options = {}
        else:
            raise Exception(
                "Error opening configuration file ({}): {} (errno={})".format(
                    config_file, e.strerror, e.errno
                )
            )
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as e:
        raise Exception(
            "Configuration file ({}) has an invalid format: ({})".format(config_file, e)
        )
    except:  # noqa: E722
        raise

    return config_options


def load_email_fixes(file: str) -> Dict[str, str]:
    """
    Read a CSV file mapping the email defined in Hito to theIJCLab (prenom.nom@ijclab.in2p3.fr)
    adresses for persons who the IJCLab address cannot be guessed from the firstname/lastname
    defined in Hito. Returns a dict where the key is the address built from Hito name and the
    value the actual address to use.

    :param file: CSV file name
    :return: dict with the mapping to the correct email address
    """

    address_fixes: Dict[str, str] = {}

    try:
        with open(file, "r", encoding="utf-8") as f:
            fix_reader = csv.DictReader(f, delimiter=";")
            for e in fix_reader:
                if (
                    re.match(r"\w[\w\-\.]+@.+\..+", e[ADDR_FIX_FIXED_ADDR])
                    or e[ADDR_FIX_FIXED_ADDR] == "-"
                ):
                    address_fixes[e[ADDR_FIX_BUILT_ADDR]] = e[ADDR_FIX_FIXED_ADDR]
                elif len(e[ADDR_FIX_FIXED_ADDR]) == 0:
                    print(f"WARNING: fixed address empty for {e[ADDR_FIX_BUILT_ADDR]}")
                else:
                    print(f"ERROR: invalid fixed address for {e[ADDR_FIX_BUILT_ADDR]}")
    except:  # noqa: E722
        print(f"Error reading address fixes CSV ({file})")
        raise

    return address_fixes


def str_to_list(string: str) -> List[str]:
    """
    Tokenize a string using / as a separator. Used to transform an Hito office or phone numer
    into a list. Return an empty list is the string is empty.

    :param string: string to parse
    :return: list of string
    """
    if len(string) == 0:
        return []

    tokens = string.split("/")
    str_list = [tokens[0].strip()]
    if len(tokens) > 1:
        m = re.match(r"(?P<prefix>(?:\d\d(?:\.| )*){4})\d\d$", str_list[0])
        if not m:
            m = re.match(r"(?P<prefix>\w+\-)\w+$", str_list[0])
        if m:
            prefix = m.group("prefix")
        else:
            prefix = ""
        for tok in tokens[1:]:
            tok = tok.strip()
            if re.match(r"\w+$", tok):
                str_list.append(f"{prefix}{tok}")
            else:
                str_list.append(tok)
    return str_list


def list_to_str(object_list: List[str], separator: str = "|") -> str:
    """
    Take a list of strings and returns a string with each element separated by the given separator.

    :param object_list: the list of strings to convert
    :param separator: the separator to use in the return string
    :return: input list as a string
    """
    if object_list is None:
        return ""
    else:
        return separator.join(object_list)


def sql_serialize_list(values: Set[str]) -> str:
    """
    Build a SQL longtext value from a list of string

    :param values: set of strings to serialize
    :return: string in SQL longtext format
    """
    # Add an empty value if none are present
    if len(values) == 0:
        values.add("")
    longtext = f"a:{len(values)}:{{"
    i = 0
    for v in values:
        longtext += f'i:{i};s:{len(v)}:"{v}";'
        i += 1
    longtext += "}"
    return longtext


def sql_longtext_to_list(value: str) -> List[str]:
    """
    Deserialize a SQL longtext value and return it as a list. If the value is NULL or (null),
    return an empty list: this value will be updated only if there is a non-null value in Hito.

    :param value: SQL longtext string
    :return: list of string
    """

    if re.match(r"\(*null", value.lower()):
        return []

    m = re.match(r"a:(?P<list_len>\d+):\{(?P<list>.*)\}", value)
    if not m:
        raise SQLInvalidArray(value)

    try:
        list_length = int(m.group("list_len"))
        tokens = m.group("list").split(";")
    except Exception as e:
        print(repr(e))
        raise SQLInvalidArray(value)

    # The string tokens is separated by ';' and there is one ';' at the end.
    # Each token is made of two parts separated also by a ';' : the index and the value
    actual_length = (len(tokens) - 1) / 2.0
    if list_length != actual_length:
        raise SQLInconsistentArrayLen(value, list_length, actual_length)

    i = 0
    value_list = []
    for i in range(1, 2 * list_length, 2):
        m = re.match(
            (
                r"s:(\d+):(?P<backslashes>\\\\)*(?:(?P<sq>')|(?P<dq>\"))(?P<string>.*)"
                r"(?(backslashes)P=backslashes)(?(sq)(?P<fsq>')|(?(dq)(?P<fdq>\")))$"
            ),
            tokens[i],
        )
        if not m:
            raise SQLArrayMalformedValue(value, tokens[i], i / 2)
        # Do not add empty values
        if len(m.group("string")) > 0:
            value_list.append(m.group("string"))

    return value_list
