"""
Example: Event-driven mouse position using MouseListener.

This example demonstrates how to capture mouse movement events as they
occur using the MouseListener producer. Unlike polling, this captures
every mouse movement with its exact timestamp.

The MouseListener uses pynput's event-driven callback to capture mouse
movements, which are then output as AxisArray messages with irregular
(CoordinateAxis) timestamps.

Run this script and move your mouse to see movement events printed.

Press Ctrl+C to stop.
"""

import ezmsg.core as ez
from ezmsg.util.debuglog import DebugLog

from ezmsg.peripheraldevice import MouseListener, MouseListenerSettings


class MouseListenSystem(ez.Collection):
    """
    System that captures mouse movement events.

    Flow: MouseListener -> DebugLog
    """

    LISTENER = MouseListener()
    LOG = DebugLog()

    def configure(self) -> None:
        self.LISTENER.apply_settings(MouseListenerSettings())

    def network(self) -> ez.NetworkDefinition:
        return ((self.LISTENER.OUTPUT_SIGNAL, self.LOG.INPUT),)


if __name__ == "__main__":
    print("Listening for mouse events")
    print("Move your mouse to see events. Press Ctrl+C to stop.\n")

    system = MouseListenSystem()
    ez.run(SYSTEM=system)
