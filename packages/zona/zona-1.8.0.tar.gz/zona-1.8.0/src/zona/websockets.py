import asyncio
from threading import Thread

from websockets.legacy.server import WebSocketServerProtocol, serve


class WebSocketServer:
	"""
	Async WebSocket server for live reloading.
	Notifies clients when they should reload.
	"""

	host: str
	port: int
	clients: set[WebSocketServerProtocol]
	loop: asyncio.AbstractEventLoop | None
	thread: Thread | None

	def __init__(self, host: str = "localhost", port: int = 8765):
		self.host = host
		self.port = port
		self.clients = set()
		self.loop = None
		self.thread = None

	async def _handler(self, ws: WebSocketServerProtocol):
		"""Handle incoming connections by adding to client set."""
		self.clients.add(ws)
		try:
			await ws.wait_closed()
		finally:
			self.clients.remove(ws)

	def start(self):
		"""Spin up server."""

		def run():
			# set up async event loop
			self.loop = asyncio.new_event_loop()
			asyncio.set_event_loop(self.loop)
			# start server
			ws_server = serve(
				ws_handler=self._handler,
				host=self.host,
				port=self.port,
			)
			# add server to event loop
			self.loop.run_until_complete(ws_server)
			self.loop.run_forever()

		# spawn async serever in a thread
		self.thread = Thread(target=run, daemon=True)
		self.thread.start()

	async def _broadcast(self, message: str):
		"""Broadcast message to all connected clients."""
		for ws in self.clients.copy():
			try:
				await ws.send(message)
			except Exception:
				self.clients.discard(ws)

	def notify_all(self, message: str = "reload"):
		"""Notify all connected clients."""
		if self.loop and self.clients:
			asyncio.run_coroutine_threadsafe(
				coro=self._broadcast(message), loop=self.loop
			)
