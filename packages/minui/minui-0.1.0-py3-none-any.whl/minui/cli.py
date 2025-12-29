import sys
import os
import argparse
import logging
from threading import Timer
from pathlib import Path
from waitress import serve

from .web import create_app, open_browser

def main():
    parser = argparse.ArgumentParser(description="MinUI - AI Maintenance Assistant")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("path", nargs="?", default=".", help="Target repository path")

    args = parser.parse_args()

    target_path = Path(args.path).resolve()
    if not target_path.exists():
        print(f"Error: Path {target_path} does not exist.")
        sys.exit(1)

    # Setup Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    logger = logging.getLogger("minui")
    logger.info(f"Analyzing path: {target_path}")

    # Create App
    app = create_app(root_path=str(target_path))

    url = f"http://{args.host}:{args.port}"
    print(f"\nMUI")
    print(f"Server: {url}")
    print(f"Target: {target_path}")
    print(f"Press Ctrl+C to stop.\n")

    if not args.no_browser:
        Timer(1.5, open_browser, [url]).start()

    # Use Waitress for production-grade serving (no more Flask dev warning)
    serve(app, host=args.host, port=args.port, threads=6)

if __name__ == "__main__":
    main()