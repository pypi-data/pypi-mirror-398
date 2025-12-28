import argparse
import webbrowser
from .server import app

def main():
    parser = argparse.ArgumentParser(prog="wlt-cert-gui")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    webbrowser.open(f"http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)

