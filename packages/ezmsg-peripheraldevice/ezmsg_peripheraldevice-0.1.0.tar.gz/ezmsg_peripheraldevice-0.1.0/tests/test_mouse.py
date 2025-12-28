"""Tests for mouse input module."""

import time as time_module
from unittest.mock import MagicMock, patch

import numpy as np
from ezmsg.util.messages.axisarray import AxisArray

from ezmsg.peripheraldevice.mouse import (
    MouseListenerProducer,
    MouseListenerSettings,
    MousePollerSettings,
    MousePollerTransformer,
)


class TestMousePollerTransformer:
    """Tests for MousePollerTransformer."""

    @patch("ezmsg.peripheraldevice.mouse.Controller")
    def test_basic_output(self, mock_controller_class):
        """Test that transformer produces valid output."""
        # Setup mock
        mock_controller = MagicMock()
        mock_controller.position = (100, 200)
        mock_controller_class.return_value = mock_controller

        transformer = MousePollerTransformer(MousePollerSettings())

        # Create a LinearAxis input (like what Clock produces)
        clock_tick = AxisArray.LinearAxis(gain=0.1, offset=0.0)

        result = transformer(clock_tick)

        # Check output shape
        assert result.data.shape == (1, 2), "Output should be (1, 2) for single sample with x, y"

        # Check dims
        assert result.dims == ["time", "ch"]

        # Check axes
        assert "time" in result.axes
        assert "ch" in result.axes

        # Check channel names
        ch_axis = result.axes["ch"]
        assert list(ch_axis.data) == ["x", "y"]

        # Check key
        assert result.key == "mouse"

        # Check data matches mock position
        np.testing.assert_array_equal(result.data[0], [100, 200])

    @patch("ezmsg.peripheraldevice.mouse.Controller")
    def test_output_values_are_numeric(self, mock_controller_class):
        """Test that output values are valid numbers (not NaN or Inf)."""
        mock_controller = MagicMock()
        mock_controller.position = (500, 300)
        mock_controller_class.return_value = mock_controller

        transformer = MousePollerTransformer(MousePollerSettings())

        clock_tick = AxisArray.LinearAxis(gain=0.1, offset=0.0)

        result = transformer(clock_tick)

        # Check that values are finite numbers
        assert np.all(np.isfinite(result.data)), "Output should contain finite numbers"

    @patch("ezmsg.peripheraldevice.mouse.Controller")
    def test_preserves_time_offset(self, mock_controller_class):
        """Test that time axis offset matches clock tick offset."""
        mock_controller = MagicMock()
        mock_controller.position = (0, 0)
        mock_controller_class.return_value = mock_controller

        transformer = MousePollerTransformer(MousePollerSettings())

        clock_tick = AxisArray.LinearAxis(gain=0.05, offset=1.5)

        result = transformer(clock_tick)

        # Check that time axis offset matches input
        time_axis = result.axes["time"]
        assert isinstance(time_axis, AxisArray.CoordinateAxis)
        assert time_axis.data[0] == 1.5

    @patch("ezmsg.peripheraldevice.mouse.Controller")
    def test_multiple_calls(self, mock_controller_class):
        """Test that transformer works correctly across multiple calls."""
        mock_controller = MagicMock()
        mock_controller_class.return_value = mock_controller

        transformer = MousePollerTransformer(MousePollerSettings())

        for i in range(5):
            # Update mock position each call
            mock_controller.position = (i * 10, i * 20)

            clock_tick = AxisArray.LinearAxis(gain=0.1, offset=i * 0.1)

            result = transformer(clock_tick)

            assert result.data.shape == (1, 2)
            assert np.all(np.isfinite(result.data))
            # Time axis should have offset matching clock tick
            assert result.axes["time"].data[0] == i * 0.1
            # Data should match mock position
            np.testing.assert_array_equal(result.data[0], [i * 10, i * 20])


class TestMouseListenerProducer:
    """Tests for MouseListenerProducer."""

    @patch("ezmsg.peripheraldevice.mouse.Listener")
    def test_initialization(self, mock_listener_class):
        """Test that producer initializes without error."""
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener

        producer = MouseListenerProducer(MouseListenerSettings())

        # Force initialization by calling once
        result = producer()

        # Listener should have been started
        mock_listener.start.assert_called_once()

        # Result should be None since no events were added
        assert result is None

    @patch("ezmsg.peripheraldevice.mouse.Listener")
    def test_output_structure_when_events(self, mock_listener_class):
        """Test output structure is correct when events are present."""
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener

        producer = MouseListenerProducer(MouseListenerSettings())

        # Initialize
        producer()

        # Manually inject events into queue for testing
        t1 = time_module.monotonic()
        t2 = t1 + 0.001
        producer._state.event_queue.put((100.0, 200.0, t1))
        producer._state.event_queue.put((101.0, 201.0, t2))

        # Now call should return those events
        result = producer()

        assert result is not None
        assert isinstance(result, AxisArray)
        assert result.data.shape == (2, 2)  # 2 events, 2 channels (x, y)
        assert result.dims == ["time", "ch"]

        # Check time axis is CoordinateAxis (irregular timestamps)
        time_axis = result.axes["time"]
        assert isinstance(time_axis, AxisArray.CoordinateAxis)
        assert len(time_axis.data) == 2

        # Check channel axis
        ch_axis = result.axes["ch"]
        assert list(ch_axis.data) == ["x", "y"]

        # Check key
        assert result.key == "mouse"

        # Check data values
        np.testing.assert_array_equal(result.data[0], [100.0, 200.0])
        np.testing.assert_array_equal(result.data[1], [101.0, 201.0])

    @patch("ezmsg.peripheraldevice.mouse.Listener")
    def test_returns_none_when_no_events(self, mock_listener_class):
        """Test that producer returns None when no events in queue."""
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener

        producer = MouseListenerProducer(MouseListenerSettings())

        # Initialize
        producer()

        # Drain any existing events (shouldn't be any with mock)
        while not producer._state.event_queue.empty():
            producer._state.event_queue.get_nowait()

        # Now call should return None
        result = producer()
        assert result is None

    @patch("ezmsg.peripheraldevice.mouse.Listener")
    def test_timestamps_monotonically_increasing(self, mock_listener_class):
        """Test that timestamps in output are monotonically increasing."""
        mock_listener = MagicMock()
        mock_listener_class.return_value = mock_listener

        producer = MouseListenerProducer(MouseListenerSettings())

        # Initialize
        producer()

        # Inject events with known timestamps
        t1 = time_module.monotonic()
        t2 = t1 + 0.001
        t3 = t2 + 0.001

        producer._state.event_queue.put((100.0, 200.0, t1))
        producer._state.event_queue.put((101.0, 201.0, t2))
        producer._state.event_queue.put((102.0, 202.0, t3))

        result = producer()

        assert result is not None
        time_axis = result.axes["time"]
        timestamps = time_axis.data

        # Verify monotonically increasing
        for i in range(len(timestamps) - 1):
            assert timestamps[i] < timestamps[i + 1]

    @patch("ezmsg.peripheraldevice.mouse.Listener")
    def test_on_move_callback_populates_queue(self, mock_listener_class):
        """Test that the on_move callback correctly populates the event queue."""
        captured_callback = None

        def capture_callback(**kwargs):
            nonlocal captured_callback
            captured_callback = kwargs.get("on_move")
            return MagicMock()

        mock_listener_class.side_effect = capture_callback

        producer = MouseListenerProducer(MouseListenerSettings())

        # Initialize - this should set up the listener with callback
        producer()

        # Verify callback was captured
        assert captured_callback is not None

        # Simulate mouse movement by calling the callback
        captured_callback(150, 250)
        captured_callback(160, 260)

        # Check queue has the events
        assert producer._state.event_queue.qsize() == 2

        # Get events and verify structure
        event1 = producer._state.event_queue.get_nowait()
        event2 = producer._state.event_queue.get_nowait()

        assert event1[0] == 150
        assert event1[1] == 250
        assert isinstance(event1[2], float)  # timestamp

        assert event2[0] == 160
        assert event2[1] == 260
        assert isinstance(event2[2], float)  # timestamp
