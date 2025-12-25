import logging
import os
import signal
import socket
import sys
from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path, PurePath
from typing import Any, Callable, Match, Optional, Pattern, List

import py_eureka_client.eureka_client as EurekaClient
import requests
import xml.etree.ElementTree as ET

"""
## pip deploy
<https://packaging.python.org/en/latest/tutorials/packaging-projects/>

### Deploy to pip
# update version number in pyproject.toml first.
cd ~/bin/app/python-service
source venv/bin/activate
rm dist/ *.egg-info/ build/ -rf
python -m pip install --upgrade build
python -m build
python -m pip install --upgrade twine
python -m twine upload dist/*
pip install jiesu_service -U

API token (password) for uploading to pypi is in my password manager.
"""


def register_eureka(eureka_server: str, name: str, port: int, instance: str, routerIP: str) -> None:
    # get hostname explicitly to avoid ambiguity, e.g, acer vs. acer.lan.
    #  hostname: str = socket.gethostname()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((routerIP, 1))
    ip: str = s.getsockname()[0]
    return EurekaClient.init(  # type: ignore
        eureka_server=eureka_server,
        app_name=name,
        instance_port=port,
        instance_host=ip,
        instance_ip=ip,
        instance_id=name + "_" + instance,
        metadata={"name": instance},
    )


def get_log_file(log_base: str, name: str) -> PurePath:
    log_dir = PurePath(log_base, name)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    return PurePath(log_dir, name + ".log")


def setup_log(log_file: PurePath) -> logging.Logger:
    # disable web server logging
    web_logger = logging.getLogger("werkzeug")
    web_logger.disabled = True

    log_handler = RotatingFileHandler(
        log_file, mode="a", maxBytes=200 * 1024, backupCount=10, encoding=None
    )
    # logger name is not printed.
    log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.addHandler(log_handler)
    return log


class Regex:
    def match(self, re: Pattern[str], string: str) -> bool:
        self.m: Optional[Match[str]] = re.match(string)
        return self.m is not None

    def group(self, index: int) -> str:
        if self.m is None:
            raise Exception("No match found")
        else:
            return self.m.group(index)


@dataclass
class Email:
    subject: str
    recipient: str
    content: str
    html: bool


@dataclass
class EurekaServiceInstance:
    id: str
    name: Optional[str]
    url: str
    ip: str
    port: str


class BaseHttpHandler:
    def set_log(self, log: logging.Logger) -> None:
        self.log = log

    def set_request_handler(self, request_handler: BaseHTTPRequestHandler) -> None:
        self.request_handler: BaseHTTPRequestHandler = request_handler

    def header(self, content_type: str = "application/json") -> None:
        self.request_handler.send_response(200)
        self.request_handler.send_header("Content-type", content_type)
        self.request_handler.end_headers()

    def body(self, content: Any) -> None:
        s = content if isinstance(content, str) else str(content)
        self.request_handler.wfile.write(s.encode("utf-8"))

    def get_body(self) -> bytes:
        content_len: int = int(self.request_handler.headers.get("Content-Length"))  # type: ignore
        return self.request_handler.rfile.read(content_len)

    def invalid(self) -> None:
        self.request_handler.send_response(404)
        self.request_handler.end_headers()

    def path(self) -> str:
        return self.request_handler.path

    def get(self) -> None:
        self.invalid()

    def post(self) -> None:
        self.invalid()

    def delete(self) -> None:
        self.invalid()

    def put(self) -> None:
        self.invalid()


class HttpRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, handler: BaseHttpHandler, log: logging.Logger, *args: Any) -> None:
        self.handler = handler
        self.log = log
        self.handler.set_request_handler(self)
        BaseHTTPRequestHandler.__init__(self, *args)

    def log_message(self, format, *args) -> None:  # type: ignore
        return

    def do_GET(self) -> None:
        try:
            # Called by Eureka when clicking the instance link on Eureka web UI.
            if self.path == "/info":
                self.handler.header()
                self.handler.body("A Python Service")
            elif self.path == "/health":
                self.handler.header()
                self.handler.body('{"status":"UP"}')
            else:
                self.handler.get()
        except socket.error:
            pass
        except Exception as ex:
            self.log.exception(ex)

    def do_POST(self) -> None:
        self.log.info("Received POST request " + self.path)
        try:
            if self.path == "/shutdown":
                os.kill(os.getpid(), signal.SIGTERM)
            else:
                self.handler.post()
        except socket.error:
            pass
        except Exception as ex:
            self.log.exception(ex)

    def do_DELETE(self) -> None:
        self.log.info("Received DELETE request " + self.path)
        try:
            self.handler.delete()
        except socket.error:
            pass
        except Exception as ex:
            self.log.exception(ex)

    def do_PUT(self) -> None:
        self.log.info("Received PUT request " + self.path)
        try:
            self.handler.put()
        except socket.error:
            pass
        except Exception as ex:
            self.log.exception(ex)


class Service:
    def __init__(
        self,
        addMoreArgs: Callable[[ArgumentParser], None] = lambda a: None,
        cleanup: Callable[[Any, Any, Logger], None] = lambda a, b, c: None,
    ) -> None:
        self.cleanup: Callable[[Any, Any, Logger], None] = cleanup
        argparser = ArgumentParser()
        argparser.add_argument("-name", type=str, required=True, help="Service name")
        argparser.add_argument("-log", type=str, required=True, help="Base dir for log")
        argparser.add_argument("-port", type=int, required=True, help="Service port")
        argparser.add_argument("-routerIP", type=str, required=True, help="Router IP")
        argparser.add_argument(
            "-instance",
            type=str,
            required=False,
            default="default",
            help="Eureka instance name",
        )
        argparser.add_argument(
            "-eureka", type=str, required=True, help="Eureka server url"
        )
        argparser.add_argument(
            "-service_monitor", type=str, required=False, help="Service monitor URL"
        )
        addMoreArgs(argparser)
        self.args: Any = argparser.parse_args()
        self.name: str = self.args.name
        self.instance: str = self.args.instance
        self.port: int = self.args.port
        self.routerIP: str = self.args.routerIP
        self.eureka_server: str = self.args.eureka
        self.log_file: PurePath = get_log_file(
            self.args.log, self.name + "_" + self.instance
        )
        self.log: logging.Logger = setup_log(self.log_file)

    def ping_monitor(self, name: str) -> None:
        if self.args.service_monitor is None:
            self.log.warning("Can't ping monitor, monitor service URL was not provided.")
        else:
            try:
                requests.post(self.args.service_monitor + "/" + name)
            except Exception:
                self.log.warning(
                    "Failed to ping service monitor - %s, with name %s.",
                    self.args.service_monitor,
                    name)

    def send_email(self, email: Email) -> None:
        try:
            response = requests.get(self.eureka_server + '/eureka/apps/gmail')
            root = ET.fromstring(response.content)
            host = root.find("./instance/hostName")
            port = root.find("./instance/port")
            if host is not None and port is not None:
                hostText = host.text
                portText = port.text
                if hostText is not None and portText is not None:
                    requests.post("http://" + hostText + ":" + portText, json=asdict(email))
        except Exception as e:
            self.log.warning("Failed to send email.")
            self.log.exception(e)

    def get_eureka_service_instances(self, service_name: str) -> List[EurekaServiceInstance]:
        response = requests.get(self.eureka_server + '/eureka/apps/' + service_name)
        root = ET.fromstring(response.content)
        instances = root.findall("./instance")
        results: List[EurekaServiceInstance] = []
        for instance in instances:
            id = instance.find("instanceId")
            ip = instance.find("ipAddr")
            port = instance.find("port")
            id_text = None if id is None else id.text
            ip_text = None if ip is None else ip.text
            port_text = None if port is None else port.text
            if ip_text is not None and port_text is not None and id_text is not None:
                url = "http://" + ip_text + ":" + port_text
                name = instance.find("./metadata/name")
                results.append(EurekaServiceInstance(
                    id=id_text,
                    ip=ip_text,
                    name=None if name is None else name.text,
                    port=port_text,
                    url=url
                ))
        return results

    def start(self, create_handler: Callable[[], BaseHttpHandler]) -> None:
        eureka_client = register_eureka(
            self.eureka_server, self.name, self.port, self.instance, self.routerIP
        )

        def unregister_eureka(signal: Any, frame: Any) -> None:
            self.log.info("Cleanup before shutdown.")
            if callable(self.cleanup):
                self.cleanup(signal, frame, self.log)
            eureka_client.stop()  # type: ignore
            sys.exit(0)

        signal.signal(signal.SIGINT, unregister_eureka)
        signal.signal(signal.SIGTERM, unregister_eureka)

        def handler(*args: Any) -> BaseHTTPRequestHandler:
            httpHandler = create_handler()
            httpHandler.set_log(self.log)
            return HttpRequestHandler(httpHandler, self.log, *args)

        httpServer = ThreadingHTTPServer(("", self.port), handler)
        self.log.info("Serving at " + str(self.port))
        httpServer.serve_forever()
