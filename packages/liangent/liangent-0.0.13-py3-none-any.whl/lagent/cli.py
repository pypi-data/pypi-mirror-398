import sys
import argparse
import uvicorn
from lagent.config import init_config
from lagent.client import Lagent

def start_server(host, port):
    print(f"Starting Lagent Server on {host}:{port}")
    uvicorn.run("lagent.server:app", host=host, port=port, reload=False) 

def chat_interface():
    # Simple terminal chat using the SDK
    print("Initializing Lagent Client...")
    try:
        # Defaults will look for .env or environment variables
        client = Lagent() 
    except ValueError as e:
        print(f"Error: {e}")
        print("Please run 'lagent init' to setup configuration or set environment variables.")
        return

    print("=========================================")
    print("Lagent CLI Chat. Type 'exit' or 'quit' to leave.")
    print("=========================================")
    
    while True:
        try:
            query = input("\nUser: ")
            if query.lower() in ("exit", "quit"):
                break
            
            print("Agent: ", end="", flush=True)
            for event in client.stream(query):
                evt_type = event.get("event")
                
                if evt_type == "thought":
                    content = event.get("content", "")
                    if content:
                         print(f"\n[Thinking] {content}", end="", flush=True)
                
                elif evt_type == "item.started":
                    item = event.get("data", {}).get("item", {})
                    print(f"\n[Tool Call] {item.get('tool')}({item.get('args')})", end="", flush=True)
                
                elif evt_type == "item.completed":
                    item = event.get("data", {}).get("item", {})
                    output = item.get("aggregated_output", "")
                    if len(output) > 100:
                         output = output[:100] + "..."
                    print(f"\n[Tool Output] {output}", end="", flush=True)
                
                elif evt_type == "final_answer":
                    content = event.get("content", "")
                    print(f"\n\n{content}\n")
                
                elif evt_type == "error":
                    print(f"\nError: {event.get('content')}")
            print("-" * 40)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")

def main():
    parser = argparse.ArgumentParser(description="Lagent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")
    
    # Init
    subparsers.add_parser("init", help="Initialize configuration")
    
    # Start
    start_parser = subparsers.add_parser("start", help="Start the API Server")
    start_parser.add_argument("--host", default="0.0.0.0", help="Host address")
    start_parser.add_argument("--port", type=int, default=8000, help="Port number")
    
    # Chat
    subparsers.add_parser("chat", help="Start interactive chat")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_config()
    elif args.command == "start":
        start_server(args.host, args.port)
    elif args.command == "chat":
        chat_interface()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
