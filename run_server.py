"""
Convenience launcher for the Disaster Relief Coordination Camp Node Server.
"""

import uvicorn
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run Disaster Relief Coordination Node Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Auto-reload on code change")
    args = parser.parse_args()

    print(f"Starting Disaster Relief Coordination Camp Node on http://{args.host}:{args.port}")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
