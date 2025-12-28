"""Mouse input via pynput."""

import queue
import time

import ezmsg.core as ez
import numpy as np
from ezmsg.baseproc import (
    BaseProducerUnit,
    BaseStatefulProducer,
    BaseStatefulTransformer,
    BaseTransformerUnit,
    processor_state,
)
from ezmsg.util.messages.axisarray import AxisArray, replace
from pynput.mouse import Controller, Listener

# =============================================================================
# Polled Mouse Transformer (takes LinearAxis from Clock, like Counter)
# =============================================================================


class MousePollerSettings(ez.Settings):
    """Settings for MousePollerTransformer."""

    pass


@processor_state
class MousePollerState:
    """State for MousePollerTransformer."""

    controller: Controller | None = None
    template: AxisArray | None = None


class MousePollerTransformer(
    BaseStatefulTransformer[
        MousePollerSettings,
        AxisArray.LinearAxis,
        AxisArray,
        MousePollerState,
    ]
):
    """
    Reads current mouse position when triggered by clock tick.

    Takes LinearAxis input (from Clock) and outputs the current mouse position
    as a single sample with the clock's timestamp.

    Input: LinearAxis (from Clock - provides timing info)
    Output: AxisArray with shape (1, 2) - single sample with x, y channels
    """

    def _reset_state(self, message: AxisArray.LinearAxis) -> None:
        """Initialize mouse controller."""
        self._state.controller = Controller()

        # Pre-construct template AxisArray
        self._state.template = AxisArray(
            data=np.zeros((1, 2), dtype=np.float64),
            dims=["time", "ch"],
            axes={
                "time": AxisArray.CoordinateAxis(
                    data=np.array([message.offset]),
                    dims=["time"],
                    unit="s",
                ),
                "ch": AxisArray.CoordinateAxis(
                    data=np.array(["x", "y"]),
                    dims=["ch"],
                ),
            },
            key="mouse",
        )

    def _process(self, message: AxisArray.LinearAxis) -> AxisArray:
        """Read current mouse position and return as AxisArray."""
        pos = self._state.controller.position

        # Create output with single sample
        data = np.array([[pos[0], pos[1]]], dtype=np.float64)
        time_axis = replace(
            self._state.template.axes["time"],
            data=np.array([message.offset]),
        )

        return replace(
            self._state.template,
            data=data,
            axes={"time": time_axis, "ch": self._state.template.axes["ch"]},
        )


class MousePoller(
    BaseTransformerUnit[
        MousePollerSettings,
        AxisArray.LinearAxis,
        AxisArray,
        MousePollerTransformer,
    ]
):
    """
    Unit for reading mouse position from Clock input.

    Receives LinearAxis from Clock and outputs current mouse position.
    """

    SETTINGS = MousePollerSettings


# =============================================================================
# Event-driven Mouse Listener Producer
# =============================================================================


class MouseListenerSettings(ez.Settings):
    """Settings for MouseListenerProducer."""

    pass


@processor_state
class MouseListenerState:
    """State for MouseListenerProducer."""

    listener: Listener | None = None
    event_queue: queue.Queue | None = None
    template: AxisArray | None = None


class MouseListenerProducer(BaseStatefulProducer[MouseListenerSettings, AxisArray, MouseListenerState]):
    """
    Produces mouse position events as they occur.

    Uses pynput.mouse.Listener to capture mouse move events with timestamps.
    Events are queued and emitted as AxisArray messages with irregular
    CoordinateAxis timestamps.

    Output: AxisArray with shape (n_events, 2) where n_events varies,
            time axis is CoordinateAxis with actual event timestamps.
    """

    def _reset_state(self) -> None:
        """Initialize listener and queue."""
        self._state.event_queue = queue.Queue()

        def on_move(x: int, y: int) -> None:
            """Callback for mouse movement events."""
            print(f"on_move called: ({x}, {y})")  # DEBUG
            self._state.event_queue.put((x, y, time.monotonic()))

        # def on_click(x, y, button, pressed):
        #     print(f"{'Pressed' if pressed else 'Released'} at {(x, y)}")
        #     if not pressed:
        #         # Stop listener
        #         return False

        self._state.listener = Listener(
            on_move=on_move,
            # on_click=on_click
        )
        self._state.listener.start()

        # Check if process is trusted for input monitoring (macOS)
        if hasattr(Listener, "IS_TRUSTED"):
            if not Listener.IS_TRUSTED:
                import warnings

                warnings.warn(
                    "Process is not trusted for input monitoring. "
                    "On macOS, add your terminal to Accessibility clients: "
                    "System Settings > Privacy & Security > Accessibility. "
                    "Then fully restart your terminal (Cmd+Q).",
                    RuntimeWarning,
                    stacklevel=2,
                )

        # Pre-construct template AxisArray
        self._state.template = AxisArray(
            data=np.zeros((0, 2), dtype=np.float64),
            dims=["time", "ch"],
            axes={
                "time": AxisArray.CoordinateAxis(
                    data=np.array([], dtype=np.float64),
                    dims=["time"],
                    unit="s",
                ),
                "ch": AxisArray.CoordinateAxis(
                    data=np.array(["x", "y"]),
                    dims=["ch"],
                ),
            },
            key="mouse",
        )

    def _hash_message(self) -> int:
        # Return constant - state persists across calls
        return 0

    def _drain_queue(self) -> tuple[list[float], list[float], list[float]]:
        """Drain all events from queue."""
        x_vals: list[float] = []
        y_vals: list[float] = []
        timestamps: list[float] = []

        while True:
            try:
                x, y, t = self._state.event_queue.get_nowait()
                x_vals.append(float(x))
                y_vals.append(float(y))
                timestamps.append(t)
            except queue.Empty:
                break

        return x_vals, y_vals, timestamps

    def _build_output(self, x_vals: list[float], y_vals: list[float], timestamps: list[float]) -> AxisArray | None:
        """Build output AxisArray from collected events."""
        if not timestamps:
            return None

        data = np.column_stack([x_vals, y_vals])
        time_axis = replace(
            self._state.template.axes["time"],
            data=np.array(timestamps, dtype=np.float64),
        )

        return replace(
            self._state.template,
            data=data,
            axes={"time": time_axis, "ch": self._state.template.axes["ch"]},
        )

    def __call__(self) -> AxisArray | None:
        """Synchronous production - drain queue and return events."""
        if self._hash == -1:
            self._reset_state()
            self._hash = 0

        x_vals, y_vals, timestamps = self._drain_queue()
        return self._build_output(x_vals, y_vals, timestamps)

    async def _produce(self) -> AxisArray | None:
        """Async production - drain queue and return events."""
        x_vals, y_vals, timestamps = self._drain_queue()
        return self._build_output(x_vals, y_vals, timestamps)

    def __del__(self) -> None:
        """Clean up listener on destruction."""
        if hasattr(self, "_state") and self._state.listener is not None:
            self._state.listener.stop()


class MouseListener(BaseProducerUnit[MouseListenerSettings, AxisArray, MouseListenerProducer]):
    """
    Unit for event-driven mouse position capture.

    Produces AxisArray messages with mouse positions and their timestamps
    as events occur. Time axis is an irregular CoordinateAxis.
    """

    SETTINGS = MouseListenerSettings
