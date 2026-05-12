import tkinter as tk
from tkinter import font as tkfont
import serial
import threading
import time
import numpy as np
from PIL import Image, ImageDraw

PORT         = "COM3"
BAUD         = 115200
BOOT_WAIT    = 10          # seconds to wait for ESP32 boot
CANVAS_SIZE  = 280
BRUSH_RADIUS = 14

class DigitDrawer:
    def __init__(self, root):
        self.root    = root
        self.ser     = None
        self.ready   = False
        self.drawing = False
        self.pil_img = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
        self.root.title("ESP32 Digit Recogniser")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)
        self._build_ui()
        threading.Thread(target=self._connect, daemon=True).start()

    def _build_ui(self):
        tf = tkfont.Font(family="Courier", size=15, weight="bold")
        lf = tkfont.Font(family="Courier", size=11)
        rf = tkfont.Font(family="Courier", size=48, weight="bold")
        bf = tkfont.Font(family="Courier", size=11, weight="bold")

        tk.Label(self.root, text="[ DRAW A DIGIT ]",
                 font=tf, fg="#e0e0e0", bg="#1a1a2e").pack(pady=(16,4))

        self.status_var = tk.StringVar(value="Connecting...")
        tk.Label(self.root, textvariable=self.status_var,
                 font=lf, fg="#888", bg="#1a1a2e").pack()

        cf = tk.Frame(self.root, bg="#00d4ff", padx=2, pady=2)
        cf.pack(padx=16, pady=10)
        self.canvas = tk.Canvas(cf, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                bg="black", cursor="crosshair",
                                highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        bf2 = tk.Frame(self.root, bg="#1a1a2e")
        bf2.pack(padx=16, pady=10)

        self.send_btn = tk.Button(bf2, text="SEND  ▶", font=bf,
                  bg="#444", fg="#888",
                  relief="flat", padx=18, pady=6,
                  state="disabled",
                  command=self._send)
        self.send_btn.pack(side="left", padx=6)

        tk.Button(bf2, text="CLEAR  ✕", font=bf,
                  bg="#2a2a4e", fg="#e0e0e0",
                  activebackground="#3a3a6e", relief="flat",
                  padx=18, pady=6,
                  command=self._clear).pack(side="left", padx=6)

        self.result_var = tk.StringVar(value="?")
        tk.Label(self.root, textvariable=self.result_var,
                 font=rf, fg="#00d4ff", bg="#1a1a2e").pack(pady=(4,2))

        self.scores_var = tk.StringVar(value="scores: —")
        tk.Label(self.root, textvariable=self.scores_var,
                 font=lf, fg="#555", bg="#1a1a2e",
                 wraplength=CANVAS_SIZE+32).pack(pady=(0,16))

    def _on_press(self, e):
        self.drawing = True
        self._paint(e.x, e.y)

    def _on_drag(self, e):
        if self.drawing:
            self._paint(e.x, e.y)

    def _on_release(self, e):
        self.drawing = False

    def _paint(self, x, y):
        r = BRUSH_RADIUS
        self.canvas.create_oval(x-r, y-r, x+r, y+r,
                                fill="white", outline="white")
        d = ImageDraw.Draw(self.pil_img)
        d.ellipse([x-r, y-r, x+r, y+r], fill=255)

    def _clear(self):
        self.canvas.delete("all")
        self.pil_img = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), 0)
        self.result_var.set("?")
        self.scores_var.set("scores: —")

    def _connect(self):
        try:
            self.ser = serial.Serial(
                port     = PORT,
                baudrate = BAUD,
                timeout  = 3,
                dsrdtr   = False,
                rtscts   = False
            )

            # Count down so user sees progress
            for i in range(BOOT_WAIT, 0, -1):
                self.root.after(0, lambda s=i: self.status_var.set(
                    f"Waiting for ESP32 boot... {s}s"))
                time.sleep(1)

            self.ser.reset_input_buffer()
            self.ready = True

            # Enable send button
            self.root.after(0, lambda: self.send_btn.config(
                state="normal", bg="#00d4ff", fg="#1a1a2e",
                activebackground="#00ffff"))
            self.root.after(0, lambda: self.status_var.set(
                f"ESP32 ready on {PORT}  ✓  — draw a digit and hit SEND"))

        except Exception as ex:
            self.root.after(0, lambda: self.status_var.set(f"Error: {ex}"))

    def _send(self):
        if not self.ready or self.ser is None:
            return
        self.status_var.set("Sending...")
        self.result_var.set("…")
        threading.Thread(target=self._do_send, daemon=True).start()

    def _do_send(self):
        small  = self.pil_img.resize((28, 28), Image.LANCZOS)
        pixels = np.array(small, dtype=np.uint8).flatten()

        try:
            self.ser.reset_input_buffer()
            self.ser.write(pixels.tobytes())
            self.ser.flush()

            deadline = time.time() + 6
            buf = bytearray()
            while time.time() < deadline:
                if self.ser.in_waiting:
                    buf.extend(self.ser.read(self.ser.in_waiting))
                if len(buf) >= 12:
                    break
                time.sleep(0.02)

            for i in range(len(buf) - 1):
                if buf[i] == 0xFE:
                    digit  = buf[i+1]
                    scores = list(buf[i+2:i+12])
                    score_str = "  ".join(
                        f"{j}:{v-128:+d}" for j, v in enumerate(scores)
                    ) if scores else "no scores"
                    self.root.after(0, lambda d=digit, s=score_str:
                                    self._show_result(d, s))
                    return

            self.root.after(0, lambda: self.status_var.set(
                f"No response — got {len(buf)}b: {buf[:12].hex(' ')}"))
            self.root.after(0, lambda: self.result_var.set("?"))

        except Exception as ex:
            self.root.after(0, lambda: self.status_var.set(f"Error: {ex}"))

    def _show_result(self, digit, scores):
        self.result_var.set(str(digit))
        self.scores_var.set(scores)
        self.status_var.set("Done ✓  — draw another digit")

if __name__ == "__main__":
    root = tk.Tk()
    app  = DigitDrawer(root)
    root.mainloop()