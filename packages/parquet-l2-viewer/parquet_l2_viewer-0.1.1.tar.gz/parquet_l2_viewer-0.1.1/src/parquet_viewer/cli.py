from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

import uvicorn
from .server import create_app


def main():
    p = argparse.ArgumentParser(prog="parquet-viewer")
    p.add_argument("--data-dir", required=True, help="Directory containing .pqt/.parquet files")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args()

    data_dir = Path(args.data_dir).expanduser()
    app = create_app(data_dir)

    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        webbrowser.open(url)

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    
if __name__ == "__main__":
    main()
