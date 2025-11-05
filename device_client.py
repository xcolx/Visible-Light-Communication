from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Callable, List, Optional
from datetime import datetime

import serial

class DeviceClient:

	STARTUP_DELAY = 2.0

	def __init__(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 1.0):

		self._listeners: List[Callable[[str]]] = []
		self._history_listeners: List[Callable[[str, str]]] = []

		self._stop_event = Event()
		self._log_path = Path(__file__).with_name("log.txt")
		

		self._serial = serial.Serial(port, baudrate, timeout=timeout)
		sleep(self.STARTUP_DELAY)
		self._reader_thread: Optional[Thread] = Thread(target=self._serial_reader, daemon=True)
		self._reader_thread.start()

	def close(self):
		self._stop_event.set()
		if self._reader_thread and self._reader_thread.is_alive():
			self._reader_thread.join(timeout=0.5)
		if self._serial and self._serial.is_open:
			self._serial.close()

	def add_listener(self, callback: Callable[[str]]):
		self._listeners.append(callback)

	def add_history_listeners(self, callback: Callable[[str, str]]):
		self._history_listeners.append(callback)

	def reset(self):
		self._write_command("r")

	def request_version(self):
		self._write_command("p")

	def request_address(self):
		self._write_command("a")

	def set_device_address(self, address: str):
		self._write_command(f"a[{address}]")

	def send_text(self, message: str, destination: str):
		dest = destination
		command = f"m[{message}\0,{dest}]"
		self._write_command(command)

	def configure(self, group: int, parameter: int, value: int):
		command = f"c[{group},{parameter},{value}]"
		self._write_command(command)

	def _write_command(self, command: str):
		data = f"{command}\n".encode("ascii", errors="replace")
		self._serial.write(data)
		self._serial.flush()
		self._append_to_log_and_history("to device", command)

	def _emit(self, message: str):
		for callback in self._listeners:
			callback(message)

	def _serial_reader(self):
		assert self._serial is not None
		while not self._stop_event.is_set():
			try:
				line = self._serial.readline()
			except serial.SerialException:
				if self._stop_event.is_set():
					break
				continue
			except Exception:
				break
			if not line:
				continue
			text = line.decode("ascii", errors="replace").strip()
			if text:
				self._append_to_log_and_history("from device", text)
				self._emit(text)

	def _append_to_log_and_history(self, direction: str, payload: str):
		timestamp = datetime.now().strftime("%H:%M:%S")
		line = f"[{timestamp}] [{direction}]: {payload}"
		with self._log_path.open("a", encoding="ascii", errors="replace") as handle:
			handle.write(line.replace("\0", "<NUL>") + "\n")

		for callback in self._history_listeners:
			callback(direction, payload)