import io
import os
import signal
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from types import FrameType
from typing import override

from rich import print
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from zona import util
from zona.builder import ZonaBuilder
from zona.log import get_logger
from zona.websockets import WebSocketServer

logger = get_logger()


def _into_path(p: bytes | str) -> Path:
	return Path(str(p))


def make_reload_script(host: str, port: int, scroll_tolerance: int) -> str:
	"""Generates the JavaScript that must be injected into HTML pages for the live reloading to work."""
	js = util.get_resource("server/inject.js").contents
	js = util.minify_js(js)
	address = f"ws://{host}:{port}"
	for placeholder, value in (
		("__SOCKET_ADDRESS__", address),
		("__SCROLL_TOLERANCE__", scroll_tolerance),
	):
		if placeholder not in js:
			raise ValueError(f"{placeholder} missing from reload script template!")
		js = js.replace(placeholder, str(value))
	return f"<script>{js}</script>"


def make_handler_class(script: str, lock: Lock):
	"""Build the live reload handler with the script as an attribute."""

	class CustomHandler(LiveReloadHandler):
		pass

	CustomHandler.script = script
	CustomHandler.lock = lock
	return CustomHandler


class LiveReloadHandler(SimpleHTTPRequestHandler):
	"""
	Request handler implementing live reloading.
	All logs are suppressed.
	HTML files have the reload script injected before </body>.
	"""

	script: str = ""
	lock: "Lock | None" = None

	@override
	def log_message(self, format, *args):  # type: ignore
		pass

	@override
	def send_head(self):
		# wait for build to finish
		if self.lock:
			self.lock.acquire()
			self.lock.release()

		path = Path(self.translate_path(self.path))
		# check if serving path/index.html
		if path.is_dir():
			index_path = path / "index.html"
			if index_path.is_file():
				path = index_path
		# check if serving html file
		if path.suffix in {".html", ".htm"} and self.script != "":
			try:
				logger.debug(f"Injecting reload script: {path}")
				# read the html
				with open(path, "rb") as f:
					content = f.read().decode("utf-8")
				# inject script at the end of body
				if r"</body>" in content:
					content = content.replace("</body>", self.script + "</body>")
				else:
					# if no </body>, add to the end
					content += self.script
				# reencode, prepare headers, serve file
				encoded = content.encode("utf-8")
				self.send_response(200)
				self.send_header("Content-type", "text/html; charset=utf-8")
				self.send_header("Content-Length", str(len(encoded)))
				self.end_headers()
				return io.BytesIO(encoded)
			except Exception:
				self.send_error(404, "File not found")
				return None
		return super().send_head()


class QuietHandler(SimpleHTTPRequestHandler):
	"""SimpleHTTPRequestHandler with logs suppressed."""

	@override
	def log_message(self, format, *args):  # type: ignore
		pass


class ZonaServer(ThreadingHTTPServer):
	"""HTTP server implementing live reloading via a WebSocket server.
	Suppresses BrokenPipeError and ConnectionResetError.
	"""

	ws_server: WebSocketServer | None = None

	def set_ws_server(self, ws_server: WebSocketServer):
		self.ws_server = ws_server

	@override
	def handle_error(self, request, client_address):  # type: ignore
		_, exc_value = sys.exc_info()[:2]
		if not isinstance(exc_value, (BrokenPipeError, ConnectionResetError)):
			super().handle_error(request, client_address)


class ZonaReloadHandler(FileSystemEventHandler):
	"""FileSystemEventHandler that rebuilds the website
	and triggers the browser into refreshing over WebSocket."""

	def __init__(
		self,
		builder: ZonaBuilder,
		output: Path,
		lock: Lock,
		ws_server: WebSocketServer | None,
	):
		self.builder: ZonaBuilder = builder
		self.output: Path = output.resolve()
		self.ws_server: WebSocketServer | None = ws_server
		self._lock: Lock = lock

	def _trigger_rebuild(self, event: FileSystemEvent) -> None:
		if self._should_ignore(event):
			return

		# don't rebuild if a build is already happening
		if not self._lock.acquire(blocking=False):
			return
		try:
			src = _into_path(event.src_path)
			dest = _into_path(event.dest_path)
			etype = event.event_type
			changed: set[Path] = set()
			deleted: set[Path] = set()
			added: set[Path] = set()
			match etype:
				case "modified":
					changed.add(src)
					logger.info(f"{src} modified")
				case "created":
					added.add(src)
					logger.info(f"{src} created")
				case "deleted":
					deleted.add(src)
					logger.info(f"{src} deleted")
				case "moved":
					deleted.add(src)
					added.add(dest)
					logger.info(f"{src} moved to {dest}")
				case _:
					logger.error(f"Unexpected file event encountered: {event}")

			self.builder.rebuild(changed, deleted, added)
			if self.ws_server:
				# trigger browser refresh
				self.ws_server.notify_all()
		finally:
			self._lock.release()

	def _should_ignore(self, event: FileSystemEvent) -> bool:
		path = Path(str(event.src_path)).resolve()
		# ignore if the output directory has been changed
		# to avoid infinite loop
		return self.output in path.parents or path == self.output or event.is_directory

	@override
	def on_modified(self, event: FileSystemEvent):
		self._trigger_rebuild(event)

	@override
	def on_created(self, event: FileSystemEvent):
		self._trigger_rebuild(event)

	@override
	def on_deleted(self, event: FileSystemEvent):
		self._trigger_rebuild(event)

	@override
	def on_moved(self, event: FileSystemEvent):
		self._trigger_rebuild(event)


def serve(
	root: Path | None = None,
	output: Path | None = None,
	draft: bool = True,
	host: str = "localhost",
	port: int = 8000,
	user_reload: bool | None = None,
	strict: bool = False,
):
	"""Serve preview website with live reload and automatic rebuild."""
	# create temp dir, automatic cleanup
	with tempfile.TemporaryDirectory() as tmp:
		builder = ZonaBuilder(root, Path(tmp), draft)
		config = builder.config
		# initial site build
		builder.build(strict)
		# use discovered paths if none provided
		if output is None:
			output = builder.layout.output
		if root is None:
			root = builder.layout.root

		# create a thread lock:
		# only one build or serve should happen at a time
		lock = Lock()
		# use config value unless overridden by user
		reload = config.server.reload.enabled
		if user_reload is not None:
			reload = user_reload
		if reload:
			print("Live reloading is enabled.")
			# spin up websocket server for live reloading
			ws_port = port + 1
			ws_server = WebSocketServer(host, ws_port)
			ws_server.start()
			# generate reload script for injection
			scroll_tolerance = config.server.reload.scroll_tolerance
			reload_script = make_reload_script(host, ws_port, scroll_tolerance)
			# generate handler with reload script as attribute
			handler = make_handler_class(reload_script, lock)
		else:
			handler = QuietHandler
			ws_server = None
		# serve the output directory
		os.chdir(output)
		# initialize http server
		httpd = ZonaServer(server_address=(host, port), RequestHandlerClass=handler)
		# link websocket server
		if ws_server:
			httpd.set_ws_server(ws_server)
		# provide link to user
		print(f"Serving {output} at http://{host}:{port}")
		print("Exit with <c-c>")

		# start server in a thread
		server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
		server_thread.start()

		# initialize reload handler
		event_handler = ZonaReloadHandler(
			builder=builder,
			output=output,
			ws_server=ws_server,
			lock=lock,
		)
		observer = Observer()
		observer.schedule(event_handler, path=str(root / "content"), recursive=True)
		templates = root / "templates"
		if templates.is_dir():
			observer.schedule(
				event_handler,
				path=str(templates),
				recursive=True,
			)
		observer.start()

		# function to shut down gracefully
		def shutdown_handler(_a: int, _b: FrameType | None):
			print("Shutting down...")
			observer.stop()
			httpd.shutdown()

		# register shutdown handler
		signal.signal(signal.SIGINT, shutdown_handler)
		signal.signal(signal.SIGTERM, shutdown_handler)

		# start file change watcher
		observer.join()
