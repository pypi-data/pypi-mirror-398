from typing import Any, Optional, Union, Callable, Literal, TextIO
from io import BufferedRandom
import os
import sys
import json
import tempfile
import time
import subprocess
from datetime import datetime
import atexit
import requests

from .requestor import (
    read_yml_config_files,
    warn,
    inform,
    CloudRequestor,
    show_working,
    hide_working,
)
from .client import Client
from .version import __version__


def _server_response(log_file: Any, error_file: Any, max_lines: int = 10) -> str:
    """Get stdout and stderr from server"""
    log_file.seek(0)
    error_file.seek(0)
    log = [line.decode("charmap") for line in log_file.readlines()]
    errs = [line.decode("charmap") for line in error_file.readlines()]
    return "".join(log[-max_lines:]) + " " + "".join(errs[-max_lines:])


STARTUP_TIMEOUT = 5


class TimeoutError(Exception):
    pass


class Popen(subprocess.Popen):
    def __del__(self, _maxsize: Any = sys.maxsize, _warn: Any = None) -> None:
        # capture ResourceWarning: subprocess XXX is still running
        def warn(*args: Any, **kwargs: Any) -> None:
            pass

        super().__del__(_maxsize, _warn=warn)  # type: ignore


class Server:
    """This class allows to start a local or cloud-based optimization server.
    If the :ref:`Configuration` is fully set up, the server can be
    initialized without any arguments. Example::

       server = Server()
       client = Client(host=server.host)
       study = client.create_study(...)

    .. note::
      If you know the ID of a running cloud-based server, you can 
      directly connect to it via ``client = Client(server_id='leonardo')``.
      Likewise, if you know the port of a local server you can connect via
      ``client = Client(host=http://locahost:4554')``.
    
    General Arguments
    ~~~~~~~~~~~~~~~~~~
    The following arguments are available for all server instances.

    Args:
       server_location: Location of JCMoptimzier server. If ``'cloud'``,
          a server instance is started in the cloud.
          If ``'local'``, a local JCMoptimizer installation is used.
          If not specified, the location is retrieved from the
          :ref:`Configuration` file.
       persistent: If true, the server continues to run even after
          the Python script has finished. To shutdown a server
          later on, one can reconnect to it::

              client = Client(host="http://localhost:4554")
              client.shutdown_server()

    Cloud Server Arguments
    ~~~~~~~~~~~~~~~~~~~~~~~
    The following arguments are available for a server instance running in the
    cloud (i.e. ``server_location='cloud'``).

    Args:
       server_id: The ID of the new server. If a cloud server with the given ID exists,
          an error is raised.
          Example::

              server = Server(server_location='cloud', server_id="my_server")
              client = Client(server_id=server.id)

       server_name: Some descriptive name of the server. If not specified,
          the server name is chosen automatically.
       shutdown_at: The time when the server should automatically shut down.
          If not specified, the shutdown time is chosen automatically.
          Example::

              import datetime as dt
              server = Server(
                  server_location='cloud',
                  shutdown_at=dt.datetime.now() + dt.timedelta(hours=3)
              )
       token: API access token. This is required for cloud servers.
          In order to create a token, visit the
          `JCMoptimizer Cloud <https://optimizer.jcmwave.com/cloud/tokens/list>`_
          website. If not specified, the token is retrieved from the
          :ref:`Configuration` file.
       cloud_endpoint: The URL of the cloud API endpoint. This argument should be
          usually left at its default value.
       version: The version of the cloud optimizer to use. This argument should be
          usually not set. I is set automatically based on the version of the
          Python package.

    Local Server Arguments
    ~~~~~~~~~~~~~~~~~~~~~~~
    The following arguments are available for a server instance running
    locally (i.e. ``server_location='local'``).

    Args:
       jcmoptimizer_dir: The path of the JCMoptimizer installation.
          If not specified, the directory is retrieved from the
          :ref:`Configuration` file.
       license_dir: Directory containing license information for JCMsuite,
          e.g. ``/path/to/JCMsuite/license``.
          If not specified, the directory is retrieved from the
          :ref:`Configuration` file.
       port: The port that the optimization server is listening to.
          If not specified, the port is chosen automatically.
       timeout: The maximum amount of time to wait for the server startup.
       max_retries: The maximum number of attempts to start the server
          after a timeout.


    """

    def __init__(
        self,
        server_location: Literal["cloud", "local"] | None = None,
        persistent: bool = False,
        server_id: Optional[str] = None,
        server_name: Optional[str] = None,
        shutdown_at: Optional[datetime] = None,
        token: Optional[str] = None,
        cloud_endpoint: str = "https://optimizer.jcmwave.com/cloud/api/",
        version: Optional[str] = None,
        jcmoptimizer_dir: Optional[str] = None,
        license_dir: Optional[str] = None,
        port: Optional[int] = None,
        timeout: float = 40.0,
        max_retries: int = 1,
        jcm_optimizer_path: Optional[str] = None,
    ) -> None:

        self._id: Optional[str] = None
        self._pid: Optional[int] = None
        self._host: Optional[str] = None

        config = read_yml_config_files()

        if jcm_optimizer_path is not None:
            raise ValueError(
                "The 'jcm_optimizer_path' argument has been renamed to "
                "'jcmoptimizer_dir'."
            )

        if token is None:
            token = config.get("token", None)
        if version is None:
            version = __version__
        if jcmoptimizer_dir is None:
            jcmoptimizer_dir = config.get("jcmoptimizer_dir", None)
        if license_dir is None:
            license_dir = config.get("license_dir", None)
        if server_location is None:
            server_location = config.get("server_location", None)
        if server_location is None:
            if token is not None:
                server_location = "cloud"
            elif jcmoptimizer_dir is not None:
                server_location = "local"
            else:
                raise ValueError(
                    "Either 'token' or 'jcmoptimizer_dir' must be specified "
                    "when server_location is not set."
                )
        self.server_location = server_location
        self.token = token
        if self.server_location == "cloud":
            if token is None:
                raise ValueError(
                    "Server location 'cloud' requires 'token' to be specified."
                )
            shutdown_at_str = None
            if shutdown_at is not None:
                if not isinstance(shutdown_at, datetime):
                    raise ValueError(
                        f"'shutdown_at' must be a {type(datetime)} object. "
                        f"Got {shutdown_at} of type {type(shutdown_at)}."
                    )
                shutdown_at_str = shutdown_at.astimezone().isoformat()

            self._start_cloud_server(
                persistent=persistent,
                server_id=server_id,
                server_name=server_name,
                shutdown_at=shutdown_at_str,
                token=token,
                cloud_endpoint=cloud_endpoint,
                version=version,
            )

        elif self.server_location == "local":
            if jcmoptimizer_dir is None:
                jcmoptimizer_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "..")
                )

            jcmoptimizer_dir = os.path.abspath(os.path.expanduser(jcmoptimizer_dir))
            if "WIN" in sys.platform.upper():
                jcmoptimizer_exe = os.path.join(
                    jcmoptimizer_dir, "server", "JCMoptimizer.exe"
                )
            else:
                jcmoptimizer_exe = os.path.join(
                    jcmoptimizer_dir, "server", "bin", "JCMoptimizer.bin"
                )

            if not os.path.exists(jcmoptimizer_exe):
                raise ValueError(
                    f"The path {jcmoptimizer_dir} does not contain a valid "
                    "JCMoptimizer installation."
                )

            self._start_local_server(
                max_retries=max_retries,
                jcmoptimizer_exe=jcmoptimizer_exe,
                license_dir=license_dir,
                persistent=persistent,
                timeout=timeout,
                port=port,
            )
        else:
            raise ValueError(
                f"Invalid server_location {self.server_location!r} specified. "
                "Expected 'cloud' or 'local'."
            )

    def _start_cloud_server(
        self,
        persistent: bool,
        server_id: Optional[str],
        server_name: Optional[str],
        shutdown_at: Optional[str],
        token: str,
        cloud_endpoint: str,
        version: str,
    ) -> None:

        cloud_requestor = CloudRequestor(
            cloud_endpoint=cloud_endpoint,
            token=token,
        )
        response = cloud_requestor.request(
            method="POST",
            purpose="start JCMoptimizer server",
            path="servers/",
            data=dict(
                server_id=server_id,
                name=server_name,
                shutdown_at=shutdown_at,
                version=version,
            ),
        )
        data = response.json()
        self._optimizer_id = data["optimizer_id"]
        self._host = data["url"]
        self._id = data["server_id"]

        prev_state_key: Optional[str] = None
        state = json.loads(data["state"])
        while state["key"] != "running":
            if prev_state_key != state["key"]:
                hide_working()
                show_working(state["description"])
                prev_state_key = state["key"]
            time.sleep(0.5)
            r = cloud_requestor.request(
                method="GET",
                purpose="check JCMoptimizer server state",
                path=f"servers/{self._id}/",
            )
            data = r.json()
            state = json.loads(data["state"])

        # Try to connect with client
        t0 = time.time()
        while time.time() - t0 < STARTUP_TIMEOUT:
            try:
                client = Client(
                    host=self._host,
                    verbose=False,
                    cloud_endpoint=cloud_endpoint,
                    token=token,
                )
            except ConnectionError:
                time.sleep(0.1)
            else:
                break

        hide_working()

        inform(f"JCMoptimizer {self._id!r} started. Host: {self._host}")

        if not persistent:
            atexit.register(lambda: self.shutdown(force=True))

    def _start_local_server(
        self,
        max_retries: int,
        jcmoptimizer_exe: str,
        license_dir: Optional[str],
        persistent: bool,
        timeout: float,
        port: Optional[int],
    ) -> None:
        for trial in range(1 + max_retries):
            try:
                self._try_start_server(
                    jcmoptimizer_exe=jcmoptimizer_exe,
                    license_dir=license_dir,
                    persistent=persistent,
                    timeout=timeout,
                    port=port,
                )
                break
            except TimeoutError as err:
                if trial == max_retries:
                    raise EnvironmentError(
                        f"Could not start optimization server after {timeout:.0f}s "
                        f"for {1 + max_retries} attempts. "
                        f"{'Server response: ' + str(err) if str(err) else ''}"
                    ) from err

    def _try_start_server(
        self,
        jcmoptimizer_exe: str,
        license_dir: Optional[str],
        persistent: bool,
        timeout: float,
        port: Optional[int],
    ) -> None:

        # get clean environment
        env = os.environ.copy()
        env.pop("PYTHONDEVMODE", None)
        if license_dir is not None:
            env["JCM_LICENSE_DIR"] = license_dir

        # Start JCMoptimizer
        cmd: list[str] = [f'"{jcmoptimizer_exe}"']
        if port is not None:
            cmd.append(f"--port {port}")
        cmd.append("--print_json")
        if not persistent:
            cmd.append(f"--calling_pid {os.getpid()}")
        close_fds = os.name != "nt"

        # Generate temporary files for errors and log
        with (
            tempfile.TemporaryFile() as error_file,
            tempfile.TemporaryFile() as log_file,
        ):
            Popen(
                " ".join(cmd),
                shell=True,
                stdout=log_file,
                stderr=error_file,
                close_fds=close_fds,
                universal_newlines=True,
                bufsize=1,
                start_new_session=True,
                env=env,
            )

            # Poll process for new output until first line with port information
            line = b""
            for _ in range(round(10 * timeout)):
                error_file.seek(0)
                if len(error_file.readlines()):
                    response = _server_response(log_file, error_file)
                    raise EnvironmentError(
                        "Could not start optimization server. "
                        f"Server response: \n{response}"
                    )

                log_file.seek(0)
                for line in iter(log_file.readline, b""):
                    if line[:17] == b'{"optimizer_port"':
                        break
                else:
                    time.sleep(0.1)
                    continue
                break
            else:
                response = _server_response(log_file, error_file)
                raise TimeoutError(response)
            try:
                info = json.loads(line)
            except Exception as err:
                response = _server_response(log_file, error_file)
                raise EnvironmentError(
                    "Could not start optimization server. "
                    f"Server response: \n{response}"
                ) from err

        self._port = int(info["optimizer_port"])
        self._pid = int(info["pid"])

    @property
    def port(self) -> int:
        """The port that the server is listening on."""
        if self.server_location == "cloud":
            if self.host.startswith("http://"):
                return 80
            return 443
        assert self._port is not None
        return self._port

    @property
    def host(self) -> str:
        """The host name of the server"""
        if self.server_location == "local":
            return f"http://localhost:{self.port}"
        assert self._host is not None
        return self._host

    @property
    def id(self) -> str:
        """The ID of the cloud server.

        Raises:
          AttributeError: If the server is not running in the cloud.
        """
        if self.server_location == "local":
            raise AttributeError("A local server does not have an ID.")
        assert self._id is not None
        return self._id

    @property
    def pid(self) -> int:
        """The process id of the server.

        Raises:
           AttributeError: If the server is not running locally.
        """
        if self.server_location == "cloud":
            raise AttributeError("A cloud server does not have a process ID.")
        assert self._pid is not None
        return self._pid

    def shutdown(self, force: bool = False) -> None:
        """Shuts down the optimization server.

        Args:
          force: If true, the optimization server is closed even if a study
            is not yet finished.
        """
        Client(host=self.host, token=self.token, check=False).shutdown_server(force)
