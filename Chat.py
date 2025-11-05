import threading
import tkinter as tk
from datetime import datetime
from typing import Optional, Tuple

from device_client import DeviceClient


class ChatUI(tk.Tk):

	def __init__(self):
		super().__init__()
		self.title("Visible Light Communication")
		self.configure(padx=12, pady=12)
		self.columnconfigure(0, weight=3)
		self.columnconfigure(1, weight=2)

		self.client = None

		self.port_var = tk.StringVar(value = "")
		self.device_address_var = tk.StringVar(value=self.client.device_address if self.client else "00")
		self.destination_address_var = tk.StringVar(value=self.client.destination_address if self.client else "FF")
		self.config_group_var = tk.StringVar(value="")
		self.config_param_var = tk.StringVar(value="")
		self.config_value_var = tk.StringVar(value="")
		
		if self.client:
			self.client.add_listener(self._on_device_event)
			self.client.add__history_listeners(self._on_history_event)

		self._build_chat_panel()
		self._build_control_panel()

	def _build_chat_panel(self):
		chat_container = tk.Frame(self)
		chat_container.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
		chat_container.columnconfigure(0, weight=1)
		chat_container.rowconfigure(1, weight=3)
		chat_container.rowconfigure(3, weight=1)

		header = tk.Label(chat_container, text="Chat", font=("Helvetica", 14, "bold"))
		header.grid(row=0, column=0, sticky="w", pady=(0, 8))

		chat_frame = tk.Frame(chat_container)
		chat_frame.grid(row=1, column=0, sticky="nsew")
		chat_frame.columnconfigure(0, weight=1)
		chat_frame.rowconfigure(0, weight=1)

		self.chat_text = tk.Text(chat_frame, wrap="word", state="disabled", height=15)
		self.chat_text.tag_configure("sent", background="#CCE5FF", foreground="#0B284D")
		self.chat_text.tag_configure("received", background="#D3F8D3", foreground="#0A3D0A")
		self.chat_text.tag_configure("system", background="#F0F0F0", foreground="#606060")

		self._append_chat_message("Welcome to the Visible Light Communication Chat! To find the Serial port on mac/linux use ls /dev/tty.*", False, True)

		self.chat_text.grid(row=0, column=0, sticky="nsew")

		input_frame = tk.Frame(chat_container)
		input_frame.grid(row=2, column=0, sticky="ew", pady=(12, 8))
		input_frame.columnconfigure(0, weight=1)

		self.chat_entry = tk.Entry(input_frame)
		self.chat_entry.grid(row=0, column=0, sticky="ew")
		self.chat_entry.bind("<Return>", self._send_chat_message)

		self.send_button = tk.Button(input_frame, text="Send", command=self._send_chat_message)
		self.send_button.grid(row=0, column=1, padx=(8, 0))

		history_frame = tk.Frame(chat_container)
		history_frame.grid(row=3, column=0, sticky="nsew")
		history_frame.columnconfigure(0, weight=1)
		history_frame.rowconfigure(1, weight=1)

		tk.Label(history_frame, text="History", font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 4))

		history_text_frame = tk.Frame(history_frame)
		history_text_frame.grid(row=1, column=0, sticky="nsew")
		history_text_frame.columnconfigure(0, weight=1)
		history_text_frame.rowconfigure(0, weight=1)

		self.history_text = tk.Text(history_text_frame, wrap="none", state="disabled", height=10)
		self.history_text.grid(row=0, column=0, sticky="nsew")

	def _build_control_panel(self):
		control_panel = tk.Frame(self)
		control_panel.grid(row=0, column=1, sticky="nsew")
		control_panel.columnconfigure(0, weight=1)

		title = tk.Label(control_panel, text="Controls", font=("Helvetica", 14, "bold"))
		title.grid(row=0, column=0, sticky="w", pady=(0, 12))

		connection_box = tk.LabelFrame(control_panel, text="Connection")
		connection_box.grid(row=1, column=0, sticky="ew", pady=(0, 12))
		connection_box.columnconfigure(1, weight=1)
		tk.Label(connection_box, text="Serial port").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
		port_entry = tk.Entry(connection_box, textvariable=self.port_var)
		port_entry.grid(row=0, column=1, sticky="ew", pady=4)
		tk.Button(connection_box, text="Connect", command=self._handle_connect).grid(row=0, column=2, sticky="ew", padx=(8,0))

		button_box = tk.Frame(control_panel)
		button_box.grid(row=2, column=0, sticky="ew", pady=(0, 16))
		button_box.columnconfigure(0, weight=1)

		tk.Button(button_box, text="Reset Device", command=self._handle_reset).grid(row=0, column=0, sticky="ew", pady=4)
		tk.Button(button_box, text="Show Software Version", command=self._handle_show_version).grid(row=1, column=0, sticky="ew", pady=4)
		tk.Button(button_box, text="Get Device Address", command=self._handle_get_address).grid(row=2, column=0, sticky="ew", pady=4)

		address_box = tk.LabelFrame(control_panel, text="Addresses")
		address_box.grid(row=2, column=0, sticky="ew", pady=(0, 16))
		address_box.columnconfigure(1, weight=1)

		
		address_box.grid_configure(row=3)

		tk.Label(address_box, text="Device").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
		device_entry = tk.Entry(address_box, textvariable=self.device_address_var, width=6)
		device_entry.grid(row=0, column=1, sticky="ew", pady=4)

		tk.Label(address_box, text="Destination").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
		destination_entry = tk.Entry(address_box, textvariable=self.destination_address_var, width=6)
		destination_entry.grid(row=1, column=1, sticky="ew", pady=4)

		tk.Button(address_box, text="Apply", command=self._handle_apply_device_address).grid(row=0, column=2, padx=(8, 0))

		configure_box = tk.LabelFrame(control_panel, text="Configure")
		configure_box.grid(row=4, column=0, sticky="ew", pady=(0, 16))
		configure_box.columnconfigure(0, weight=0)
		configure_box.columnconfigure(1, weight=0)
		configure_box.columnconfigure(2, weight=0)
		configure_box.columnconfigure(3, weight=1)

		group_entry = tk.Entry(configure_box, textvariable=self.config_group_var, width=6)
		group_entry.grid(row=0, column=0, padx=(0, 6), pady=4)
		param_entry = tk.Entry(configure_box, textvariable=self.config_param_var, width=6)
		param_entry.grid(row=0, column=1, padx=(0, 6), pady=4)
		value_entry = tk.Entry(configure_box, textvariable=self.config_value_var, width=8)
		value_entry.grid(row=0, column=2, padx=(0, 8), pady=4)
		tk.Button(configure_box, text="Apply", command=self._handle_configure).grid(row=0, column=3, sticky="w")

	def _handle_connect(self):
		port = self.port_var.get()
		if self.client:
			self.client.close()
		self.client = DeviceClient(port=port)
		self.client.add_listener(self._on_device_event)
		self.client.add_history_listeners(self._on_history_event)

	def _append_chat_message(self, message: str, is_self: bool, system_message: bool = False):
		label = "sent" if is_self else "received"
		if system_message:
			label = "system"
		line = f"[{label}] {message}\n"
		self.chat_text.configure(state="normal")
		self.chat_text.insert("end", line, label)
		self.chat_text.see("end")
		self.chat_text.configure(state="disabled")

	def _send_chat_message(self, event=None):
		message = self.chat_entry.get().strip()
		destination = self.destination_address_var.get()
		self._append_chat_message(message, True)
		self.chat_entry.delete(0, "end")

		threading.Thread(
			target=self._send_chat_message_async,
			args=(message, destination),
			daemon=True,
		).start()

	def _send_chat_message_async(self, message: str, destination: str):
		self.client.send_text(message, destination)

	def _handle_reset(self):
		self.client.reset()

	def _handle_show_version(self):
		self.client.request_version()

	def _handle_get_address(self):
		self.client.request_address()

	def _handle_apply_device_address(self):
		self.client.set_device_address(self.device_address_var.get())

	def _handle_configure(self):
		g_raw = self.config_group_var.get().strip()
		p_raw = self.config_param_var.get().strip()
		v_raw = self.config_value_var.get().strip()
		try:
			group = int(g_raw, 0) if g_raw else 0
			parameter = int(p_raw, 0) if p_raw else 0
			value = int(v_raw, 0) if v_raw else 0
		except ValueError:
			self._append_chat_message("Configure values must be integers", False, True)
			return

		self.client.configure(group, parameter, value)

		self.config_group_var.set("")
		self.config_param_var.set("")
		self.config_value_var.set("")

	def _on_device_event(self, message: str):
		self.after(0, self._deliver_device_event, message)

	def _on_history_event(self, direction: str, payload: str):
		self.after(0, self._deliver_history_event, direction, payload)

	def _deliver_device_event(self, raw: str):
		system_message, message = self._extract_incoming_message(raw)
		if message is not None:
			self._append_chat_message(message, False, system_message)

	def _deliver_history_event(self, direction: str, payload: str):
		timestamp = datetime.now().strftime("%H:%M:%S")
		line = f"[{timestamp}] [{direction}]: {payload}\n"
		self.history_text.configure(state="normal")
		self.history_text.insert("end", line)
		self.history_text.see("end")
		self.history_text.configure(state="disabled")		

	def _extract_incoming_message(self, raw: str) -> Optional[Tuple[bool, str]]:
		if not raw.startswith("m["):
			if raw == "r":
				# Reset acknowledgment
				return True, "Device has been reset"
			if raw.startswith("p["):
				# Version response
				return True, f"You use version {raw[2:-1]}"
			if raw.startswith("a["):
				# Version response
				return True, f"Your address is {raw[2:-1]}"
			if raw.startswith("c["):
				# Version or address response
				return True, self._get_configuration_string(raw[2:-1])
			return None, None
		body = raw[2:-1] if raw.endswith("]") else raw[2:]
		parts = body.split(",", 2)
		if len(parts) < 3:
			#ACK
			if parts[0] == "R" and parts[1] == "A":
				return True, "Sending was successful (ACK received)"
			return None, None
		if parts[0] != "R" or parts[1] != "D":
			return None, None
		payload = parts[2]
		if not payload:
			return None, None
		#normal message
		return False, payload
	
	def _get_configuration_string(self, raw: str) -> str:
		parameters = [
			[
				"PHY preamble length",
				"FEC threshold (default: disabled)",
				"Channel busy threshold (default: 20)",
				"light emission (enable/disable)",
			],
			[
				"# of re-transmissions",
				"DIFS",
				"CWmin (use power of two)",
				"CWmax (use power of two)",
				"RTS threshold (default: disabled)",
				"MAC address",
			],
			[
				"logging level (0: none, 7: silly)",
				"logger prefix character (default: disabled)",
			],
		]
		groups = ["PHY", "MAC", "LOG"]

		parts = [p.strip() for p in raw.split(",")]
		try:
			g = int(parts[0], 0)
			p = int(parts[1], 0)
			v = int(parts[2], 0)
		except ValueError:
			return "Unexpected error parsing configuration response"

		if g < 0 or g >= len(parameters):
			return f"There are 3 groups (0-2): {g} leads to undefined behaviour"
		if p < 0 or p >= len(parameters[g]):
			return f"There are {len(parameters[g])} parameters (0-{len(parameters[g]) - 1}) in group {groups[g]}: {p} leads to undefined behaviour"

		return f"You set {parameters[g][p]} to be {v}"

app = ChatUI()
app.mainloop()
