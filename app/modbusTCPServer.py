import argparse
import logging
from pyModbusTCP.server import ModbusServer

# parse args
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action='store_true', help='set debug mode')
args = parser.parse_args()


def run_server():
    print("Server running...")

    # init server
    server = ModbusServer(host="0.0.0.0", port=502)

    # logging setup
    logging.basicConfig()
    if args.debug:
        logging.getLogger('pyModbusTCP.server').setLevel(logging.DEBUG)

    try:
        server.start()
        # server.start() blocks here, but will now respond to stop()
        while True:
            pass  # keep the script alive if needed
    except KeyboardInterrupt:
        print("Server received Ctrl+C, shutting down...")
        server.stop()  # stop the Modbus server cleanly


if __name__ == "__main__":
    run_server()
