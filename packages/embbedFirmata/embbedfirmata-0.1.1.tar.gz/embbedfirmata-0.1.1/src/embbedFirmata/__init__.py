import serial.tools.list_ports
from sys import platform
import threading
import serial
import time

# FIRMATA CONSTANTS
SET_PIN_MODE    = 0xF4
DIGITAL_MESSAGE = 0x90
ANALOG_MESSAGE  = 0xE0
REPORT_ANALOG   = 0xC0
START_SYSEX     = 0xF0
END_SYSEX       = 0xF7
SAMPLING_INT    = 0x7A
SYSTEM_RESET    = 0xFF
ANALOG_MAPPING_QUERY = 0x69
REPORT_DIGITAL = 0xD0
PIN_STATE_QUERY = 0x6D

SYSEX_PROGRAM_CONTROL = 0x75

INPUT  = 0x00
OUTPUT = 0x01
ANALOG = 0x02

# Boards

try:
    class ArduinoUno:
        AUTODETECT = "AUTO"

        def __init__(self, port=AUTODETECT):
            self.analogs = {}
            self.digitals = {}
            self.current_command = None
            self.buffer = []

            self.port_state = [0] * 16

            if port == self.AUTODETECT:
                l = serial.tools.list_ports.comports()

                if l:
                    if platform == "linux" or platform == "linux2":
                        for d in l:
                            if 'ACM' in d.device or 'usbserial' in d.device or 'ttyUSB' in d.device:
                                port = str(d.device)
                    elif platform == "win32":
                        comports = []

                        for d in l:
                            if d.device:
                                if ("USB" in d.description) or (not d.description) or ("Arduino" in d.description):
                                    devname = str(d.device)

                                    comports.append(devname)

                        comports.sort()

                        if len(comports) > 0:
                            port = comports[0]
                    else:
                        for d in l:
                            if d.vid:
                                port = str(d.device)
        
            self.ser = serial.Serial(port=port, baudrate=57600, timeout=0.1)
            time.sleep(0.2)

            self.ser.write(bytes([SYSTEM_RESET]))
            time.sleep(0.2)

            self.ser.write(bytes([START_SYSEX, ANALOG_MAPPING_QUERY, END_SYSEX]))
            time.sleep(0.3)

        # Functions

        def send_sysex_c(self, cmd):
            self.ser.write(bytes([
                START_SYSEX,
                SYSEX_PROGRAM_CONTROL,
                cmd,
                END_SYSEX
            ]))

        def pinMode(self, pin, mode):
            real_pin = pin

            if mode == ANALOG and 0 <= pin <= 5:
                real_pin += 14

            self.ser.write(bytes([SET_PIN_MODE, real_pin, mode]))
            time.sleep(0.05)

            if mode == ANALOG:
                self.ser.write(bytes([REPORT_ANALOG | pin, 1]))
                time.sleep(0.05)
            elif mode == INPUT:
                port = pin // 8

                self.ser.write(bytes([
                    REPORT_DIGITAL | port,
                    1
                ]))
                time.sleep(0.05)

        def pwmWrite(self, pin, value):
            value = max(0, min(255, value))

            self.ser.write(bytes([
                ANALOG_MESSAGE | pin,
                value & 0x7F,
                (value >> 7) & 0x7F
            ]))

        def digitalWrite(self, pin, value):
            port = pin // 8
            bit  = pin % 8

            if value:
                self.port_state[port] |= (1 << bit)
            else:
                self.port_state[port] &= ~(1 << bit)

            val = self.port_state[port]

            self.ser.write(bytes([
                DIGITAL_MESSAGE | port,
                val & 0x7F,
                (val >> 7) & 0x7F
            ]))

        def analogRead(self, pin):
            return self.analogs.get(pin, None)

        def digitalRead(self, pin):
            return self.digitals.get(pin, None)

        def parse_firmata(self, byte):
            if (byte & 0xF0) == ANALOG_MESSAGE:
                self.current_command = byte
                self.buffer = []

                return

            if (byte & 0xF0) == DIGITAL_MESSAGE:
                self.current_command = byte
                self.buffer = []

                return


            if self.current_command is None:
                return

            self.buffer.append(byte)

            if len(self.buffer) == 2:
                cmd = self.current_command & 0xF0

                if cmd == ANALOG_MESSAGE:
                    ch = self.current_command & 0x0F
                    value = self.buffer[0] | (self.buffer[1] << 7)

                    self.analogs[ch] = value

                elif cmd == DIGITAL_MESSAGE:
                    port = self.current_command & 0x0F
                    port_value = self.buffer[0] | (self.buffer[1] << 7)

                    for i in range(8):
                        pin = port * 8 + i

                        self.digitals[pin] = (port_value >> i) & 1

                self.current_command = None
                self.buffer = []

        def reader_loop(self):
            while True:
                data = self.ser.read()

                if data:
                    self.parse_firmata(data[0])

        def start(self):
            threading.Thread(target=self.reader_loop, daemon=True).start()

        def sample(self, interval=20):
            self.ser.write(bytes([START_SYSEX, SAMPLING_INT, interval, 0, END_SYSEX]))
            time.sleep(0.05)

        def setup_start(self):
            self.ser.write(bytes([0xF0, 0x75, 0x01, 0xF7]))

        def setup_end(self):
            self.ser.write(bytes([0xF0, 0x75, 0x02, 0xF7]))

        def loop_start(self):
            self.ser.write(bytes([0xF0, 0x75, 0x03, 0xF7]))

        def loop_end(self):
            self.ser.write(bytes([0xF0, 0x75, 0x04, 0xF7]))

        def clear_f_prog(self):
            self.ser.write(bytes([0xF0, 0x75, 0x05, 0xF7]))

        def delay(self, sec):
            ms = int(sec * 1000)

            b0 = ms & 0x7F
            b1 = (ms >> 7) & 0x7F
            b2 = (ms >> 14) & 0x7F

            self.ser.write(bytes([
                0xF0, 0x75, 0x06,
                b0, b1, b2,
                0xF7
            ]))

        def setup(self, func):
            def wrapper(*args, **kwargs):
                self.setup_start()

                res = func(*args, **kwargs)

                self.setup_end()

                return res

            return wrapper(self)

        def loop(self, func):
            def wrapper(*args, **kwargs):
                self.loop_start()

                res = func(*args, **kwargs)

                self.loop_end()

                return res

            return wrapper(self)
except:
    raise Exception("Port disconnected or not found.")
