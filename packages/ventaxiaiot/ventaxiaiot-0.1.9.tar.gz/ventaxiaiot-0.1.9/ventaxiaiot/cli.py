# File: ventaxiaiot/cli.py
import asyncio
import argparse
import json
import os
import ssl
import sys
import logging

from ventaxiaiot.client import AsyncNativePskClient
from ventaxiaiot.messages import VentMessageProcessor
from ventaxiaiot.commands import VentClientCommands
from ventaxiaiot.pending_request_tracker import PendingRequestTracker

_LOGGER = logging.getLogger(__name__)

def load_config(path=None):
    if not path:
        path = "config.json"

    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)

    return {}

def setup_cli_logging(level: str = "DEBUG"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.DEBUG),
        format="%(levelname)s: %(message)s"
    )

def merge_config(cli_args, file_config):
    merged = file_config.copy()
    for key in vars(cli_args):
        value = getattr(cli_args, key)
        if value is not None:
            merged[key] = value
    return merged


def build_parser():
    parser = argparse.ArgumentParser(description="Vent-Axia IoT command-line interface")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="DEBUG",
        help="Logging level (default: INFO)"
    )
       

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Example: status command
    status_cmd = subparsers.add_parser("status", help="Query device network mode")
    status_cmd.add_argument("--host", help="Device host/IP")
    status_cmd.add_argument("--port", type=int, help="Port number")
    status_cmd.add_argument("--identity", help="Device identity string")
    status_cmd.add_argument("--psk_key", help="Pre-shared key")
    status_cmd.add_argument("--wifi_device_id", help="WiFi device ID")

    #Will add more subcommands here, like `subscribe`, `set`, `get`, etc.
    return parser


async def run_status(config):
    tracker = PendingRequestTracker()
    client = AsyncNativePskClient(
        config["wifi_device_id"],
        config["identity"],
        config["psk_key"],
        config["host"],
        config["port"],
        connection_lost_callback=on_disconnect
    )

    processor = VentMessageProcessor(tracker)
    commands = VentClientCommands(client.wifi_device_id, tracker)

    await client.connect()
    await commands.send_subscribe(client)    
    await commands.send_cfg_command(client, "netmode?")

    # Start background task to process messages
    async def process_messages(client, processor):
        try:
            async for msg in client:               
                await processor.process(msg)
        except asyncio.CancelledError:
            _LOGGER.debug("Message processing task cancelled")              
        except Exception as e:
            _LOGGER.error("Error processing message: %s", e)
        finally:
            _LOGGER.info("👋 Message processor exiting")

        
    message_task = asyncio.create_task(process_messages(client, processor)) 

    # Return objects for interactive use
    return client, commands, message_task


def on_disconnect():
     _LOGGER.warning("Ventaxia - Connection lost callback triggered!")


async def main(): 
    
    if len(sys.argv) == 1:
        sys.argv.append("status")  # Inject default command if none given
    
    parser = build_parser()
    cli_args = parser.parse_args()

    file_config = load_config(cli_args.config)
    config = merge_config(cli_args, file_config)
    setup_cli_logging(cli_args.log_level)

    # Validate required fields
    required_keys = ["host", "port", "identity", "psk_key", "wifi_device_id"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config value: {key}")

    if cli_args.command == "status":
        client, commands, message_task = await run_status(config)  
          
        # Start interactive loop
        try:
            await interactive_loop(config, client, commands)
        finally:
            message_task.cancel()
            _LOGGER.info("👋 Calling client.close()...") 
            await client.close()
            _LOGGER.info("Client.close() finished.")   
            
            
async def async_input(prompt: str = "") -> str:
    return await asyncio.to_thread(input, prompt)          
          
async def interactive_loop(config, client, commands):
    print("\nInteractive mode. Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            user_input = await async_input(">> ")
        except EOFError:
            break
        
        cmd = user_input.strip().lower()

        if cmd in ("exit", "quit"):
            print("Exiting interactive mode.")
            break        
        elif cmd == "help":
            print(
                "Available commands:\n"
                "  status     - Show status\n"
                "  update     - Send update request with JSON data\n"
                "  airflow    - Send airflow mode request\n"
                "  comm       - Start commissioning\n"
                "  stop       - Stop commissioning\n"
                "  exit       - Quit"
            )
        elif cmd == "status":
            await commands.send_cfg_command(client, "netmode?")
        elif cmd == "update":
            raw_data = input("Enter JSON data for update request:\n>> ")
            try:
                data = json.loads(raw_data)
                await commands.send_update_request(client, data)
                print("Update request sent successfully.")
            except json.JSONDecodeError as e:
                print(f"Invalid JSON: {e}")
            except Exception as e:
                print(f"Error sending update request: {e}")
        elif cmd == "airflow":
            mode = await async_input("Enter airflow mode (e.g., 'normal', 'boost', 'purge', 'reset'):\n>> ")
            duration_str = await async_input("Enter duration in seconds:\n>> ")
            try:
                duration = int(duration_str)
                await commands.send_airflow_mode_request(client, mode, duration)
                print(f"Airflow mode '{mode}' set for {duration} seconds.")
            except ValueError:
                print("Invalid duration. Must be an integer.")
        elif cmd == "comm":
            airflow = await async_input("Enter commissioning airflow mode ('normal' or 'boost'):\n>> ")
            airflow = airflow.strip() or "normal"
            try:
                await commands._commissioning_loop(client, airflow)
            except Exception as e:
                print(f"Error during commissioning: {e}")
        elif cmd == "stop":   
            try:
                await commands.stop_commissioning(client)
            except Exception as e:
                print(f"Error during stop_commissioning: {e}")
        else:
            print(f"Unknown command: {user_input}")       