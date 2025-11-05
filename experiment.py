import tkinter as tk
from pathlib import Path
from time import monotonic, sleep
from threading import Thread
from device_client import DeviceClient

class ExperimentUI(tk.Tk):

    THRESHOLD_TIMEOUT = 10

    def __init__(self):
        super().__init__()
        self.title("Experiment Control Panel")
        self.geometry("550x350")

        self.filename_var = tk.StringVar()
        self.payload_size_var = tk.IntVar(value=0)
        self.counter = tk.IntVar(value=0)
        self.port_var = tk.StringVar(value="/dev/tty.usbmodem101")

        self.config_group_var = tk.StringVar(value="0")
        self.config_param_var = tk.StringVar(value="2")
        self.config_value_var = tk.StringVar(value="20")

        self.config_group_var2 = tk.StringVar(value="0")
        self.config_param_var2 = tk.StringVar(value="1")
        self.config_value_var2 = tk.StringVar(value="0")

        self._client = None
        self.payload_int = 0
        self.counter_int = 0
        self.filename = "output.txt"
        self.running = False
        self.sending = False
        self.file = None
        self._sender_thread = None

        self._destination = "00"

        tk.Label(self, text="Serial port:").grid(row=0, column=0, sticky="w")
        self.port_entry = tk.Entry(self, textvariable=self.port_var, width=40)
        self.port_entry.grid(row=0, column=1, sticky="w")

        tk.Label(self, text="Filename:").grid(row=1, column=0, sticky="w")
        self.filename_entry = tk.Entry(self, textvariable=self.filename_var, width=40)
        self.filename_entry.insert(0, "output.txt")
        self.filename_entry.grid(row=1, column=1, sticky="w")

        tk.Label(self, text="Payload size:").grid(row=2, column=0, sticky="w", pady=(8,0))
        self.payload_entry = tk.Entry(self, textvariable=self.payload_size_var, width=15)
        self.payload_entry.grid(row=2, column=1, sticky="w", pady=(8,0))

        self.configure_box = tk.LabelFrame(self, text="Configure: channel busy threshold")
        self.configure_box.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        self.configure_box.columnconfigure(0, weight=0)
        self.configure_box.columnconfigure(1, weight=0)
        self.configure_box.columnconfigure(2, weight=0)
        self.configure_box.columnconfigure(3, weight=1)

        self.group_entry = tk.Entry(self.configure_box, textvariable=self.config_group_var, width=6)
        self.group_entry.grid(row=0, column=0, padx=(0, 6), pady=4)
        self.param_entry = tk.Entry(self.configure_box, textvariable=self.config_param_var, width=6)
        self.param_entry.grid(row=0, column=1, padx=(0, 6), pady=4)
        self.value_entry = tk.Entry(self.configure_box, textvariable=self.config_value_var, width=8)
        self.value_entry.grid(row=0, column=2, padx=(0, 8), pady=4)

        self.configure_box2 = tk.LabelFrame(self, text="Configure: Forward Error Correction")
        self.configure_box2.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        self.configure_box2.columnconfigure(0, weight=0)
        self.configure_box2.columnconfigure(1, weight=0)
        self.configure_box2.columnconfigure(2, weight=0)
        self.configure_box2.columnconfigure(3, weight=1)

        self.group_entry2 = tk.Entry(self.configure_box2, textvariable=self.config_group_var2, width=6)
        self.group_entry2.grid(row=0, column=0, padx=(0, 6), pady=4)
        self.param_entry2 = tk.Entry(self.configure_box2, textvariable=self.config_param_var2, width=6)
        self.param_entry2.grid(row=0, column=1, padx=(0, 6), pady=4)
        self.value_entry2 = tk.Entry(self.configure_box2, textvariable=self.config_value_var2, width=8)
        self.value_entry2.grid(row=0, column=2, padx=(0, 8), pady=4)

        self.start_button = tk.Button(self, text="Start", width=12, command=self.toggle)
        self.start_button.grid(row=5, column=0, columnspan=3, pady=(12,6))

        tk.Label(self, text="Counter:").grid(row=6, column=0, sticky="w")
        self.counter_label = tk.Label(self, textvariable=self.counter, font=("Helvetica", 16))
        self.counter_label.grid(row=6, column=1, sticky="w")

    def toggle(self):
        if not self.running:

            self.running = True
            self.start_button.config(text="Stop")
            self.filename_entry.config(state="disabled")
            self.payload_entry.config(state="disabled")
            self.port_entry.config(state="disabled")

            port = self.port_var.get().strip()
            self._client = DeviceClient(port=port)

            sleep(2)

            self._client.configure(self.config_group_var.get(),self.config_param_var.get(),self.config_value_var.get())
            self._client.configure(self.config_group_var2.get(),self.config_param_var2.get(),self.config_value_var2.get())

            self.filename = self.filename_var.get().strip()
            self.payload_int = int(self.payload_size_var.get())
            self.counter_int = 0
            self.counter.set(self.counter_int)

            self._entry_filename = Path("output") / self.filename
            try:
                self._entry_filename.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            try:
                self.file = self._entry_filename.open("w", encoding="ascii", errors="replace")
            except Exception:
                self.file = None

            self._client.add_listener(self._on_device_message)
            t = Thread(target=self._sender_loop, daemon=True)
            t.start()
            self._sender_thread = t

        else:
            self.running = False
            self.start_button.config(text="Start")
            self.filename_entry.config(state="normal")
            self.payload_entry.config(state="normal")
            self.port_entry.config(state="normal")

            if self._client:
                self._client.close()
                self._client = None

            if self.file:
                self.file.close()
                self.file = None

            self.sending = False
            if self._sender_thread and self._sender_thread.is_alive():
                try:
                    self._sender_thread.join(timeout=1.0)
                except Exception:
                    pass
            self._sender_thread = None


    def _on_device_message(self, message: str):
        if not message.startswith("m["):
            return
        body = message[2:-1] if message.endswith("]") else message[2:]
        parts = body.split(",", 2)
        if len(parts) < 2:
            return
        if parts[0] == "R" and parts[1] == "A":
            receive_time = monotonic()
            rtt = (receive_time - getattr(self, "time", receive_time)) * 1000
            log_line = f"{rtt:.5f}\n"
            if self.file:
                self.file.write(log_line)
                self.file.flush()
            self.sending = False

    def _sender_loop(self):
        while self.running:
            if self.payload_int > 0 and not self.sending:
                sleep(0.01)
                message = "A" * self.payload_int
                self.sending = True
                self.time = monotonic()
                self._client.send_text(message, self._destination)
                self.counter_int += 1
                self.counter.set(self.counter_int)
            if self.sending and hasattr(self, "time"):
                if monotonic() - self.time > self.THRESHOLD_TIMEOUT:
                    now = monotonic()
                    if self.file:
                        self.file.write(f"{self.THRESHOLD_TIMEOUT}\n")
                        self.file.flush()
                    self.time = now
                    self.sending = False

app = ExperimentUI()
app.mainloop()