# ezmsg-peripheraldevice

Short description of your ezmsg package.

## Installation

```bash
pip install ezmsg-peripheraldevice
```

## Dependencies

- `ezmsg`
- `ezmsg-baseproc`
- `numpy`
- `pynput`

## Usage

### Mouse Examples

**Event-driven mouse listener** - captures every mouse movement event:

```bash
python examples/mouse_listen.py
```

**Polling mouse position** - reads mouse position at a fixed rate:

```bash
python examples/mouse_poll.py --rate 60
```

### Programmatic Usage

```python
import ezmsg.core as ez
from ezmsg.peripheraldevice import MouseListener, MouseListenerSettings
from ezmsg.peripheraldevice import MousePoller, MousePollerSettings
```

> Note: MouseListener requires extra permissions.

## Development

We use [`uv`](https://docs.astral.sh/uv/getting-started/installation/) for development.

1. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) if not already installed.
2. Fork this repository and clone your fork locally.
3. Open a terminal and `cd` to the cloned folder.
4. Run `uv sync` to create a `.venv` and install dependencies.
5. (Optional) Install pre-commit hooks: `uv run pre-commit install`
6. After making changes, run the test suite: `uv run pytest tests`

## License

MIT License - see [LICENSE](LICENSE) for details.
