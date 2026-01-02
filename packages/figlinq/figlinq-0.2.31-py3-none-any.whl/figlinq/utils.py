"""
utils
=====

Low-level functionality NOT intended for users to EVER use.

"""

from __future__ import absolute_import

import os.path
import re
import threading
import warnings
import six
import json as _json
from _plotly_utils import exceptions
from _plotly_utils.optional_imports import get_module
from figlinq.api import v2
import figlinq

# Optional imports, may be None for users that only use our core functionality.
numpy = get_module("numpy")
pandas = get_module("pandas")
sage_all = get_module("sage.all")


### incase people are using threading, we lock file reads
lock = threading.Lock()


http_msg = (
    "The plotly_domain and plotly_api_domain of your config file must start "
    "with 'https', not 'http'. If you are not using On-Premise then run the "
    "following code to ensure your plotly_domain and plotly_api_domain start "
    "with 'https':\n\n\n"
    "import plotly\n"
    "plotly.tools.set_config_file(\n"
    "    plotly_domain='https://plotly.com',\n"
    "    plotly_api_domain='https://api.plotly.com'\n"
    ")\n\n\n"
    "If you are using On-Premise then you will need to use your company's "
    "domain and api_domain urls:\n\n\n"
    "import plotly\n"
    "plotly.tools.set_config_file(\n"
    "    plotly_domain='https://plotly.your-company.com',\n"
    "    plotly_api_domain='https://plotly.your-company.com'\n"
    ")\n\n\n"
    "Make sure to replace `your-company.com` with the URL of your Plotly "
    "On-Premise server.\nSee "
    "https://plotly.com/python/getting-started/#special-instructions-for-plotly-onpremise-users "
    "for more help with getting started with On-Premise."
)


### general file setup tools ###


def load_json_dict(filename, *args):
    """Checks if file exists. Returns {} if something fails."""
    data = {}
    if os.path.exists(filename):
        lock.acquire()
        with open(filename, "r") as f:
            try:
                data = _json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except:
                data = {}  # TODO: issue a warning and bubble it up
        lock.release()
        if args:
            return {key: data[key] for key in args if key in data}
    return data


def save_json_dict(filename, json_dict):
    """Save json to file. Error if path DNE, not a dict, or invalid json."""
    if isinstance(json_dict, dict):
        # this will raise a TypeError if something goes wrong
        json_string = _json.dumps(json_dict, indent=4)
        lock.acquire()
        with open(filename, "w") as f:
            f.write(json_string)
        lock.release()
    else:
        raise TypeError("json_dict was not a dictionary. not saving.")


def ensure_file_exists(filename):
    """Given a valid filename, make sure it exists (will create if DNE)."""
    if not os.path.exists(filename):
        head, tail = os.path.split(filename)
        ensure_dir_exists(head)
        with open(filename, "w") as f:
            pass  # just create the file


def ensure_dir_exists(directory):
    """Given a valid directory path, make sure it exists."""
    if dir:
        if not os.path.isdir(directory):
            os.makedirs(directory)


def get_first_duplicate(items):
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
        else:
            return item
    return None


### source key
def is_source_key(key):
    src_regex = re.compile(r".+src$")
    if src_regex.match(key) is not None:
        return True
    else:
        return False


### validation
def validate_world_readable_and_sharing_settings(option_set):
    if (
        "world_readable" in option_set
        and option_set["world_readable"] is True
        and "sharing" in option_set
        and option_set["sharing"] is not None
        and option_set["sharing"] != "public"
    ):
        raise exceptions.PlotlyError(
            "Looks like you are setting your plot privacy to both "
            "public and private.\n If you set world_readable as True, "
            "sharing can only be set to 'public'"
        )
    elif (
        "world_readable" in option_set
        and option_set["world_readable"] is False
        and "sharing" in option_set
        and option_set["sharing"] == "public"
    ):
        raise exceptions.PlotlyError(
            "Looks like you are setting your plot privacy to both "
            "public and private.\n If you set world_readable as "
            "False, sharing can only be set to 'private' or 'secret'"
        )
    elif "sharing" in option_set and option_set["sharing"] not in [
        "public",
        "private",
        "secret",
        None,
    ]:
        raise exceptions.PlotlyError(
            "The 'sharing' argument only accepts one of the following "
            "strings:\n'public' -- for public plots\n"
            "'private' -- for private plots\n"
            "'secret' -- for private plots that can be shared with a "
            "secret url"
        )


def validate_plotly_domains(option_set):
    domains_not_none = []
    for d in ["plotly_domain", "plotly_api_domain"]:
        if d in option_set and option_set[d]:
            domains_not_none.append(option_set[d])

    if not all(d.lower().startswith("https") for d in domains_not_none):
        warnings.warn(http_msg, category=UserWarning)


def set_sharing_and_world_readable(option_set):
    if "world_readable" in option_set and "sharing" not in option_set:
        option_set["sharing"] = "public" if option_set["world_readable"] else "private"

    elif "sharing" in option_set and "world_readable" not in option_set:
        if option_set["sharing"] == "public":
            option_set["world_readable"] = True
        else:
            option_set["world_readable"] = False


def validate_fid(test):
    """
    Validate a fid string in the format `username:idlocal`.

    :param test: The `username:idlocal` pair.
    :return: True if valid, False otherwise.
    :rtype: bool

    """

    USERNAME = r"[.a-zA-Z0-9_-]+"
    IDLOCAL = r"(?:-[1-2]|[0-9]|[1-9]\d+)"
    FID = rf"^({USERNAME}):({IDLOCAL})$"

    if isinstance(test, str) and re.match(FID, test):
        return True
    return False


def parse_file_id_args(file, file_url):
    """
    Return the file_id from the non-None input argument.

    Raise an error if more than one argument was supplied.

    """
    if file is not None:
        id_from_file = file.id
    else:
        id_from_file = None
    args = [id_from_file, file_url]
    arg_names = ("file", "file_url")

    supplied_arg_names = [
        arg_name for arg_name, arg in zip(arg_names, args) if arg is not None
    ]

    if not supplied_arg_names:
        raise exceptions.InputError(
            "One of the two keyword arguments is required:\n"
            "    `file` or `file_url`\n\n"
            "file: a file object that has already\n"
            "    been uploaded.\n\n"
            "file_url: the url where the file can be accessed, \n"
            "    e.g. 'https://plotly.com/~chris/3043'\n\n"
        )
    elif len(supplied_arg_names) > 1:
        raise exceptions.InputError(
            "Only one of `file` or `file_url` is required. \n" "You supplied both. \n"
        )
    else:
        supplied_arg_name = supplied_arg_names.pop()
        if supplied_arg_name == "file_url":
            path = six.moves.urllib.parse.urlparse(file_url).path
            file_owner, file_id = path.replace("/~", "").split("/")[0:2]
            return "{0}:{1}".format(file_owner, file_id)
        else:
            return file.id


def ensure_path_exists(filename):
    """
    Given a valid filename, make sure the path exists (will create if DNE).
    """

    parent_folder_path = os.environ.get("PARENT_FOLDER_PATH", None)
    if parent_folder_path:
        filename = os.path.join(parent_folder_path, filename)
    if filename[-1] == "/":
        filename = filename[0:-1]

    paths = filename.split("/")
    parent_path = "/".join(paths[0:-1])
    filename = paths[-1]

    if parent_path != "":
        try:
            v2.folders.create({"path": parent_path})
        except figlinq.exceptions.PlotlyRequestError as e:
            if "already exists" in e.message:
                pass
            else:
                raise ValueError(f"Failed to create folder {parent_path}: {e.message}")

    return (filename, parent_path)
