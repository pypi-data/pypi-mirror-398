#!/usr/bin/env python3
import argparse
import asyncio
import sys
import os
from chekml_blackemperor import ChekMLServer, ChekMLWorker

def main():
    parser = argparse.ArgumentParser(description="ChekML - Cross-machine training system")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start ChekML server")
    server_parser.add_argument("--config", help="Path to config file")
    server_parser.add_argument("--host", default="0.0.0.0", help="Server host")
    server_parser.add_argument("--port", type=int, default=8080, help="Server port")
    
    # Worker command
    worker_parser = subparsers.add_parser("worker", help="Start ChekML worker")
    worker_parser.add_argument("--config", help="Path to config file")
    worker_parser.add_argument("--server", help="Server URL (overrides CHEKML_EMPERROR)")
    
    args = parser.parse_args()
    
    if args.command == "server":
        # Start server
        server = ChekMLServer(args.config)
        
        # Override config if provided via CLI
        if args.host:
            server.config.host = args.host
        if args.port:
            server.config.port = args.port
        
        asyncio.run(server.run())
    
    elif args.command == "worker":
        # Start worker
        worker = ChekMLWorker(args.config)
        
        # Override server URL if provided
        if args.server:
            worker.config.server_url = args.server
        
        asyncio.run(worker.run())
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
