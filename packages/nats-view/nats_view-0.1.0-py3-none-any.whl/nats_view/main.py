import argparse
import asyncio
import json
import os
import signal
import sys
import datetime
import re
from nats.aio.client import Client as NATS
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text
import nats.errors
import nats.js.api

async def run(args):
    nc = NATS()
    
    # Options dict for connect
    connect_opts = {
        "servers": [f"nats://{args.host}:{args.port}"],
        "name": "nats-view"
    }

    # Auth: User/Pass
    if args.user and args.password:
        connect_opts["user"] = args.user
        connect_opts["password"] = args.password
    
    # Auth: Token
    if args.token:
        connect_opts["token"] = args.token

    # Auth: Creds
    if args.creds:
        connect_opts["user_credentials"] = args.creds

    # TLS
    if args.tls or args.tls_cert or args.tls_key or args.tls_ca:
        # Construct SSL context if args provided
        import ssl
        ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        
        if args.tls_ca:
            ssl_ctx.load_verify_locations(cafile=args.tls_ca)
        
        if args.tls_cert and args.tls_key:
            ssl_ctx.load_cert_chain(certfile=args.tls_cert, keyfile=args.tls_key)
            
        connect_opts["tls"] = ssl_ctx
        
        # If user explicitly asked for tls but didn't provide files, nats-py might default to system trust?
        # But usually we need to set protocol to tls://? 
        # nats-py handles 'nats://' with tls context correctly (upgrades).
        # But let's check if we need to change scheme to tls://
        # Usually not strictly required if we pass tls context.

    # Context Loading (Basic)
    if args.context:
        # Try to load context file
        # Standard location: ~/.config/nats/context/{name}.json
        # Windows: %AppData%\nats\context\{name}.json? 
        # Let's assume standard XDG or user provided path if it looks like a path.
        
        ctx_path = args.context
        if not os.path.exists(ctx_path):
            # Try looking in default config dir
            home = os.path.expanduser("~")
            # Linux/Mac
            config_dir = os.path.join(home, ".config", "nats", "context")
            # Windows?
            if sys.platform == "win32":
                # The 'nats' CLI on windows might use different paths, but often it follows unix-like structure or AppData.
                # Let's check AppData/Local/nats/context ??
                # For now, let's stick to .config/nats/context as a convention or user explicit path.
                pass
            
            potential_path = os.path.join(config_dir, f"{args.context}.json")
            if os.path.exists(potential_path):
                ctx_path = potential_path
        
        if os.path.exists(ctx_path):
            try:
                with open(ctx_path, 'r') as f:
                    ctx_data = json.load(f)
                    # Parse context data
                    # "url": "nats://..."
                    # "user", "password", "token", "creds", "nkey", "cert", "key", "ca"
                    
                    if "url" in ctx_data:
                        connect_opts["servers"] = [ctx_data["url"]]
                    if "user" in ctx_data:
                        connect_opts["user"] = ctx_data["user"]
                    if "password" in ctx_data:
                        connect_opts["password"] = ctx_data["password"]
                    if "token" in ctx_data:
                        connect_opts["token"] = ctx_data["token"]
                    if "creds" in ctx_data:
                         connect_opts["user_credentials"] = ctx_data["creds"]
                    # ... add more mapping as needed
            except Exception as e:
                print(f"Error loading context {ctx_path}: {e}")
                sys.exit(1)
        else:
             print(f"Context file not found: {args.context}")
             # We won't exit, maybe user just passed a name that doesn't exist but provided other args?
             # But usually context implies "use this config".
             sys.exit(1)

    try:
        await nc.connect(**connect_opts)
    except Exception as e:
        print(f"Error connecting to NATS: {e}")
        sys.exit(1)

    # Check NO_COLOR
    no_color = os.environ.get("NO_COLOR")
    enable_color = True
    if no_color:
        enable_color = False
        
    console = Console(no_color=not enable_color, highlight=False)

    # Compile filter regex if provided
    filter_pattern = None
    if args.filter:
        try:
            filter_pattern = re.compile(args.filter)
        except re.error as e:
            print(f"Invalid regex for filter: {e}")
            sys.exit(1)

    message_count = 0
    stop_event = asyncio.Event()

    async def message_handler(msg):
        nonlocal message_count
        subject = msg.subject
        try:
            data_str = msg.data.decode()
        except UnicodeDecodeError:
            data_str = str(msg.data)

        # Apply content filter
        if filter_pattern and not filter_pattern.search(data_str):
            if args.js:
                try:
                    await msg.ack()
                except:
                    pass
            return

        # Prepare prefix parts
        prefix_parts = []
        
        # 1. Timestamp
        if args.timestamp:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            prefix_parts.append(Text(f"[{timestamp}] ", style="dim"))

        # 2. Subject
        prefix_parts.append(Text(f"[{subject}] ", style="bold cyan"))
        
        # 3. Headers
        if args.headers and msg.headers:
             headers_str = str(msg.headers)
             prefix_parts.append(Text(f"[headers={headers_str}] ", style="magenta"))

        prefix = Text.assemble(*prefix_parts)

        # Output Logic
        if args.raw:
             console.print(prefix, Text(data_str))
        else:
            try:
                json_data = json.loads(data_str)
                if args.pretty:
                    formatted_json = json.dumps(json_data, indent=2)
                else:
                    formatted_json = json.dumps(json_data)
                
                if enable_color:
                    syntax = Syntax(formatted_json, "json", theme="monokai", background_color="default", code_width=None, word_wrap=False)
                    console.print(prefix, syntax)
                else:
                    console.print(prefix + Text(formatted_json))
            except json.JSONDecodeError:
                console.print(prefix, Text(data_str))

        # JetStream Ack
        if args.js:
            try:
                await msg.ack()
            except:
                pass

        # Check limit
        if args.count:
            message_count += 1
            if message_count >= args.count:
                stop_event.set()

    subjects = args.subjects if args.subjects else [">"]
    
    # JetStream Context
    js = None
    if args.js or args.deliver_all or args.deliver_last or args.since:
        args.js = True
        js = nc.jetstream()

    for subject in subjects:
        if args.js:
            config = {}
            if args.deliver_all:
                config['deliver_policy'] = nats.js.api.DeliverPolicy.ALL
            elif args.deliver_last:
                config['deliver_policy'] = nats.js.api.DeliverPolicy.LAST
            elif args.deliver_new:
                 config['deliver_policy'] = nats.js.api.DeliverPolicy.NEW
            elif args.since:
                 delta = parse_duration(args.since)
                 if delta:
                    config['deliver_policy'] = nats.js.api.DeliverPolicy.BY_START_TIME
                    config['opt_start_time'] = datetime.datetime.now(datetime.timezone.utc) - delta
                 else:
                    print(f"Invalid duration format: {args.since}")
                    sys.exit(1)
            
            queue = args.queue if args.queue else None
            try:
                await js.subscribe(subject, cb=message_handler, queue=queue, config=None if not config else nats.js.api.ConsumerConfig(**config))
            except Exception as e:
                print(f"Error subscribing to {subject} with JetStream: {e}")
        else:
            await nc.subscribe(subject, queue=args.queue if args.queue else "", cb=message_handler)

    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        await nc.close()

def parse_duration(duration_str):
    match = re.match(r'^(\d+)([hms])$', duration_str)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    if unit == 'h':
        return datetime.timedelta(hours=value)
    elif unit == 'm':
        return datetime.timedelta(minutes=value)
    elif unit == 's':
        return datetime.timedelta(seconds=value)
    return None

def main():
    parser = argparse.ArgumentParser(description="Watch NATS JetStream topics.", add_help=False)
    parser.add_argument("--help", action="help", help="show this help message and exit")
    
    # Connection args
    parser.add_argument("-h", "--host", default="localhost", help="NATS host (default: localhost)")
    parser.add_argument("-p", "--port", default="4222", help="NATS port (default: 4222)")
    parser.add_argument("--context", help="Load configuration from a context file or name")
    
    # Auth
    parser.add_argument("--user", help="User")
    parser.add_argument("--password", help="Password")
    parser.add_argument("--token", help="Token")
    parser.add_argument("--creds", help="User Credentials File (.creds)")
    
    # TLS
    parser.add_argument("--tls", action="store_true", help="Enable TLS/SSL")
    parser.add_argument("--tls-ca", help="TLS CA Certificate")
    parser.add_argument("--tls-cert", help="TLS Client Certificate")
    parser.add_argument("--tls-key", help="TLS Client Key")
    
    # JetStream & Subscription
    parser.add_argument("--js", action="store_true", help="Use JetStream context")
    parser.add_argument("--deliver-all", action="store_true", help="Deliver all messages (JetStream)")
    parser.add_argument("--deliver-last", action="store_true", help="Deliver last message (JetStream)")
    parser.add_argument("--deliver-new", action="store_true", help="Deliver new messages only (JetStream)")
    parser.add_argument("--since", type=str, help="Deliver messages since duration (e.g. 1h, 30m) (JetStream)")
    parser.add_argument("--queue", type=str, help="Join a queue group")
    
    # Output Control
    parser.add_argument("--timestamp", action="store_true", help="Prepend timestamp to output")
    parser.add_argument("--headers", action="store_true", help="Display message headers")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON (multiline)")
    parser.add_argument("--raw", action="store_true", help="Print raw payload (no JSON parsing)")
    
    # Logic Control
    parser.add_argument("-n", "--count", type=int, help="Exit after receiving N messages")
    parser.add_argument("--filter", type=str, help="Regex to filter message payloads")
    
    parser.add_argument("subjects", nargs="*", help="Subjects to watch (default: all '>')")
    
    args = parser.parse_args()
    
    try:
        if sys.platform == 'win32':
             asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(run(args))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
