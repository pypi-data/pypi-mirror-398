"""
Example: Polling mouse position using Clock -> MousePoller.

This example demonstrates how to read mouse position at a fixed rate
using the MousePoller transformer. The Clock produces timing ticks,
and MousePoller reads the current mouse position on each tick.

Run this script and move your mouse to see position updates printed
at the specified poll rate.

Press Ctrl+C to stop.
"""

import ezmsg.core as ez
from ezmsg.baseproc import Clock, ClockSettings
from ezmsg.util.debuglog import DebugLog

from ezmsg.peripheraldevice import MousePoller, MousePollerSettings


class MousePollSettings(ez.Settings):
    """Settings for MousePoll system."""

    poll_rate: float = 60.0
    """Rate (Hz) to poll mouse position."""


class MousePollSystem(ez.Collection):
    """
    System that polls mouse position at a fixed rate.

    Flow: Clock -> MousePoller -> DebugLog
    """

    SETTINGS = MousePollSettings

    CLOCK = Clock()
    MOUSE = MousePoller()
    LOG = DebugLog()

    def configure(self) -> None:
        self.CLOCK.apply_settings(ClockSettings(dispatch_rate=self.SETTINGS.poll_rate))
        self.MOUSE.apply_settings(MousePollerSettings())

    def network(self) -> ez.NetworkDefinition:
        return (
            (self.CLOCK.OUTPUT_SIGNAL, self.MOUSE.INPUT_SIGNAL),
            (self.MOUSE.OUTPUT_SIGNAL, self.LOG.INPUT),
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Poll mouse position at a fixed rate")
    parser.add_argument(
        "--rate",
        type=float,
        default=10.0,
        help="Poll rate in Hz (default: 60.0)",
    )
    args = parser.parse_args()

    print(f"Polling mouse position at {args.rate} Hz")
    print("Move your mouse to see position updates. Press Ctrl+C to stop.\n")

    settings = MousePollSettings(poll_rate=args.rate)
    system = MousePollSystem(settings)
    ez.run(SYSTEM=system)
