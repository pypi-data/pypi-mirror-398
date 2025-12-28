import argparse
import platform
import sys
import os

def find_abs_path(frac, rt="/" if platform.system() == "Linux" else "C:/"):
    norm_frac = os.path.normpath(frac)

    for root, dirs, files in os.walk(rt):
        for d in dirs:
            current = os.path.join(root, d)

            if current.endswith(norm_frac):
                return os.path.abspath(current)

        for f in files:
            current = os.path.join(root, f)

            if current.endswith(norm_frac):
                return os.path.abspath(current)

    return

def main():
    parser = argparse.ArgumentParser(prog="embffload", description="EmbbedFirmata firmware loader")

    parser.add_argument("--device", help="The embbed system to load firmware")
    parser.add_argument("--port", help="The port of the embbed sistem")
    parser.add_argument("--conf", help="Avrdude conf file path")

    args = parser.parse_args()

    if args.device:
        device = args.device

        if device == "ArduinoUnor3":
            os.system(f'avrdude -C {args.conf} -c arduino -p atmega328p -P {args.port} -b 115200 -U flash:w:{find_abs_path("embbedFirmata/firmware/ArduinoUnor3.hex")}:i')
        else:
            print(f'This device does not exist in this command: {device}')

            sys.exit(-1)

if __name__ == "__main__":
    main()
