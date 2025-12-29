# hegel-ip-client

Python client library for Hegel amplifiers with async support and push notifications.

## Features

- **Async/await support** - Built on asyncio for non-blocking I/O
- **Push notifications** - Real-time state updates from the amplifier
- **Automatic reconnection** - Resilient connection management with exponential backoff
- **Command queuing** - FIFO queue for command responses
- **Full protocol support** - Power, volume, mute, input selection, and more

## Installation

```bash
pip install hegel-ip-client
```

## Quick Start

```python
import asyncio
from hegel_ip_client import HegelClient, COMMANDS

async def main():
    # Create client
    client = HegelClient("192.168.1.100", 50001)

    # Register callback for push messages
    def on_push(message):
        print(f"Received push: {message}")

    client.add_push_callback(on_push)

    # Start connection manager
    await client.start()

    # Send commands
    power_state = await client.send(COMMANDS["power_query"])
    print(f"Power state: {power_state.power}")

    # Set volume
    await client.send(COMMANDS["volume_set"](50), expect_reply=False)

    # Stop client when done
    await client.stop()

asyncio.run(main())
```

## API Reference

### HegelClient

#### `__init__(host: str, port: int = 50001)`

Create a new Hegel client.

#### `async start()`

Start the connection manager. Automatically handles reconnection.

#### `async stop()`

Stop the client and close the connection.

#### `async send(command: str, expect_reply: bool = True, timeout: float = 5.0) -> Optional[HegelStateUpdate]`

Send a command to the amplifier.

- `command`: Command string (use `COMMANDS` dict for convenience)
- `expect_reply`: Whether to wait for a reply
- `timeout`: Maximum time to wait for reply
- Returns: `HegelStateUpdate` with parsed state changes, or `None` if `expect_reply=False`

#### `add_push_callback(callback: Callable[[str], None])`

Register a callback for push messages from the amplifier.

### HegelStateUpdate

Dataclass representing state changes from the amplifier:

- `power: Optional[bool]` - Power state (True=on, False=off)
- `volume: Optional[float]` - Volume level (0.0 to 1.0)
- `mute: Optional[bool]` - Mute state (True=muted)
- `input: Optional[int]` - Selected input number (1-20)
- `reset: Optional[str]` - Reset/heartbeat message

### COMMANDS

Dictionary of pre-defined commands:

- `power_on`, `power_off`, `power_query`
- `volume_set(level)`, `volume_query`, `volume_up`, `volume_down`
- `mute_on`, `mute_off`, `mute_query`
- `input_set(idx)`, `input_query`
- `reset_query`

## Protocol Details

The Hegel TCP protocol uses carriage return (`\r`) as the line terminator. Commands and replies are text-based.

### Example Commands

- `-p.?` - Query power state
- `-p.1` - Power on
- `-p.0` - Power off
- `-v.?` - Query volume
- `-v.50` - Set volume to 50
- `-v.u` - Volume up
- `-v.d` - Volume down
- `-m.1` - Mute on
- `-m.0` - Mute off
- `-i.?` - Query input
- `-i.1` - Select input 1

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/boazca/hegel-ip-client/issues).
