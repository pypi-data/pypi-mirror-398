from typing import Any, Literal, Optional, TextIO
import sys
import threading
import os
from datetime import datetime as dt
import json
import itertools
import threading
import time

template = 'Please install the package {p} (e.g. run "pip install {p}") .'
try:
    import requests
except ImportError:
    raise ImportError(template.format(p="requests"))
try:
    import colorama
except ImportError:
    raise ImportError(template.format(p="colorama"))


def print_message(
    message_str: str,
    message_time: Optional[str] = None,
    message_level: Literal["debug", "info", "warning", "error"] = "info",
) -> None:
    if message_time is None:
        message_time = dt.now().strftime("%Y-%m-%d %H:%M:%S")

    DATE = colorama.Style.BRIGHT
    RESET = colorama.Style.RESET_ALL
    if message_level == "error":
        STYLE = colorama.Fore.RED + colorama.Style.BRIGHT
    elif message_level == "warning":
        STYLE = colorama.Fore.YELLOW
    elif message_level == "info":
        STYLE = colorama.Fore.GREEN
    else:
        STYLE = colorama.Style.DIM

    print(DATE + message_time + ": " + RESET + STYLE + message_str + RESET)


def inform(message: str) -> None:
    print_message(message_str=message, message_level="info")


def warn(message: str) -> None:
    print_message(message_str=message, message_level="warning")


WORK_DONE = threading.Event()
WORK_DONE.set()

def work_animation(work_done: threading.Event, msg: str) -> None:
    for c in itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
        if work_done.is_set():
            sys.stdout.write("\r " + " " * len(msg) + "\r")
            sys.stdout.flush()
            work_done.clear()
            return
        sys.stdout.write(f"\r{c} {msg}              ")
        sys.stdout.flush()
        time.sleep(0.15)


def show_working(msg) -> None:
    WORK_DONE.clear()
    t = threading.Thread(target=work_animation, args=(WORK_DONE, msg))
    t.daemon = True
    t.start()


def hide_working():
    wait = not WORK_DONE.is_set()
    WORK_DONE.set()
    if wait:
        while WORK_DONE.is_set():
            time.sleep(0.01)


class ServerError(EnvironmentError):
    pass


class NumParallelError(EnvironmentError):
    pass

class ServerShutdownError(EnvironmentError):
    pass

def _get_value(expr: str) -> Any:
    if expr == "true":
        return True
    if expr == "false":
        return False
    if expr.startswith("'") and expr.endswith("'"):
        return expr.strip("'")
    if expr.startswith('"') and expr.endswith('"'):
        return expr.strip('"')
    if expr.isdigit():
        return int(expr)
    try:
        return float(expr)
    except ValueError:
        raise SyntaxError


def parse_yaml(f: TextIO) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line_num, line in enumerate(f.readlines()):
        if line.startswith("#"):
            continue
        line = line.strip()
        if not line:
            continue
        try:
            key, *rest = line.split(":")
            value_exp = (":".join(rest)).strip()
            if not value_exp:
                continue
            value = _get_value(value_exp)
        except ValueError:
            raise ValueError(
                f"Invalid format of config file "
                f"at {f.name}:{line_num + 1}.\n"
                "Expected format: key:value\n"
                f"Found format: {line}"
            )
        except SyntaxError as e:
            raise SyntaxError(
                f"Invalid format of config file "
                f"at {f.name}:{line_num + 1}.\n"
                f"Cannot parse expression: {value_exp}\n"
                "Maybe you forgot to put it in quotation marks "
                f"('{value_exp}')?"
            )
        data[key.strip()] = value
    return data


def read_yml_config_files() -> dict[str, Any]:
    """Read YAML config files in home directory and current directory"""
    config: dict[str, Any] = {}
    if os.path.exists(os.path.expanduser("~/.jcmoptimizer.conf.yml")):
        with open(os.path.expanduser("~/.jcmoptimizer.conf.yml")) as f:
            config.update(parse_yaml(f))

    if os.path.exists(".jcmoptimizer.conf.yml"):
        with open(".jcmoptimizer.conf.yml") as f:
            config.update(parse_yaml(f))

    return config


class Requestor:

    def __init__(self, endpoint: str, token: str) -> None:
        is_in_notebook = False
        try:
            shell = get_ipython().__class__.__name__  # type: ignore
            is_in_notebook = shell == "ZMQInteractiveShell"
        except NameError:
            pass
        if not is_in_notebook:
            colorama.init()
        self.token = token
        self.session = requests.Session()
        self.session.headers = {"Authorization": f"Token {self.token}"}
        self.endpoint = endpoint.rstrip("/") + "/"
        self.lock = threading.Lock()

    def encode_data(self, data: dict[str, Any]) -> dict[str, Any]:
        return data

    def request(
        self,
        method: Literal["GET", "POST"],
        purpose: str,
        path: str,
        data: Optional[dict[str, Any]] = None,
    ) -> requests.Response:
        """Make a request and return vaidated response.
        Args:
            method: HTTP method ("POST", "GET")
            purpose: purpose of the request
            path: path of the request
            data: data of the request
        """
        url = self.endpoint + path.lstrip("/")
        try:
            with self.lock:
                if method == "GET":
                    response = self.session.get(url)
                elif method == "POST":
                    response = self.session.post(
                        url,
                        data=self.encode_data(data),
                    )
                else:
                    raise NotImplementedError

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Could not connect to server at URL {self.endpoint}. "
                "Please, check your internet connection and that the server is running."
            )

        if response.status_code == 401:
            raise ConnectionError(
                f"Authorization error at URL {self.endpoint}. "
                "Please, confirm that your token is correct."
            )

        if response.status_code == 502:
            raise ConnectionError(
                f"Could not connect to server at URL {url}. "
                "Please, check that the server is running."
            )
        try:
            response_data = response.json()
        except requests.exceptions.JSONDecodeError as err:
            raise EnvironmentError(
                f"Cannot decode answer: {err}"
                f"\nRequest: {method} {url} {data}"
                f"\nResponse: {response.status_code} {response.reason}"
                f"\n{response._content[:1000]!r}"
            ) from err

        self.check_status_code(
            purpose, response.status_code, data=data, response_data=response_data
        )
        return response

    def check_status_code(
        self,
        purpose: str,
        status_code: int,
        data: dict[str, Any],
        response_data: dict[str, Any],
    ) -> None:
        if status_code >= 500:
            raise ServerError(
                "An internal server error occured. Please, check your entries."
                f"\nRequest: {data}"
                f"\nResponse: {status_code} {response_data}"
            )
        if status_code >= 400:
            if (error := self.extract_error(response_data)) is not None:
                raise ServerError(f"Could not {purpose}. {error}")
            else:
                raise ServerError(f"Could not {purpose}.\nResponse: {response_data}")

    def extract_error(self, data: dict[str, Any]) -> Optional[str]:
        return data.get("detail", None)


class CloudRequestor(Requestor):

    def __init__(self, cloud_endpoint: str, token: str) -> None:
        super().__init__(endpoint=cloud_endpoint, token=token)

    def extract_error(self, data: dict[str, Any]) -> Optional[str]:
        error = super().extract_error(data)
        if error is None:
            non_field_errors = data.get("non_field_errors", None)
            if non_field_errors is not None:
                return non_field_errors[0]
        return error


class OptimizerRequestor(Requestor):

    def __init__(
        self,
        host: str,
        token: str,
        verbose: bool = True,
    ) -> None:
        super().__init__(endpoint=host, token=token)
        self.verbose = verbose
        self._server_shutdown = False

    def encode_data(self, data: dict[str, Any]) -> dict[str, Any]:
        return {key: json.dumps(val) for key, val in data.items()}

    def check_status_code(
        self,
        purpose: str,
        status_code: int,
        data: dict[str, Any],
        response_data: dict[str, Any],
    ) -> None:
        if status_code == 202:
            if (error := self.extract_error(response_data)) is not None:
                raise NumParallelError(f"Could not {purpose}. {error}")
            else:
                raise NumParallelError(f"Could not {purpose}")
        elif status_code == 503:
            self._server_shutdown = True
            ServerShutdownError(f"Could not {purpose}. The server is shutting down.")
        else:
            super().check_status_code(purpose, status_code, data, response_data)

    def _print_messages(self, response: requests.Response) -> None:
        if not self.verbose:
            return
        if response.status_code >= 200 and response.status_code < 300:
            answer = response.json()
            if "messages" in answer:
                messages = json.loads(answer["messages"])
                for idx in sorted(messages["message"]):
                    message_str = messages["message"][idx]
                    message_level = messages["level"][idx]
                    message_time = messages["datetime"][idx]
                    print_message(message_str, message_time, message_level)

    def _handle_server_shutdown(self, purpose: str) -> None:
        if self._server_shutdown:
            raise ServerShutdownError(
                f"Could not {purpose}. The server is shutting down."
            )
            
            
    def get(
        self,
        purpose: str,
        object: Optional[str] = None,
        type: Optional[str] = None,
        id: Optional[str] = None,
    ) -> dict[str, Any]:
        self._handle_server_shutdown(purpose)
        url = ""
        if object is not None:
            url += "/" + object
        if type is not None:
            url += "/" + type
        if id is not None:
            url += "/" + id

        r = self.request("GET", purpose, url)
        self._print_messages(r)
        return r.json()

    def post(
        self,
        purpose: str,
        object: str,
        operation: str,
        id: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        self._handle_server_shutdown(purpose)
        # make dummy data to ensure this is interpreted as post request by server
        if data is None:
            data = {"a": 0}
        url = f"/{object}/{operation}"
        if id is not None:
            url += "/" + id
        r = self.request("POST", purpose, url, data=data)
        self._print_messages(r)
        return r.json()
