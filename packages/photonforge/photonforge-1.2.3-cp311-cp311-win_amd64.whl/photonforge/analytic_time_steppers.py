import numpy

from .extension import TimeStepper, register_time_stepper_class
from .typing import TimeDelay


class _DelayBuffer:
    def __init__(self, delays, default_delay, time_step):
        self.delays = {k: int(v / time_step) for k, v in delays.items()}
        self.default_delay = int(default_delay / time_step)
        self.buffers = {}

    def reset(self):
        self.buffers = {}

    def put(self, buffer_index, values):
        for key in values:
            if key not in self.buffers:
                buffer_size = 1 + self.delays.get(key, self.default_delay)
                self.buffers[key] = numpy.zeros(buffer_size, dtype=complex)
        for key, buffer in self.buffers.items():
            buffer[buffer_index % buffer.size] = values.get(key, 0)

    def get(self, buffer_index, fallback):
        offset = buffer_index + 1
        return {
            key: buffer[offset % buffer.size] if buffer.size > 1 else fallback.get(key, 0)
            for key, buffer in self.buffers.items()
        }


class DelayedTimeStepper(TimeStepper):
    """Time stepper that adds time delays to other time steppers.

    Args:
        time_stepper: The time stepper to wrap with delays.
        input_delay: Default delay applied to the inputs.
        output_delay: Default delay applied to the outputs.
    """

    def __init__(
        self,
        time_stepper: TimeStepper | None = None,
        input_delay: TimeDelay = 0,
        output_delay: TimeDelay = 0,
    ):
        super().__init__(
            time_stepper=time_stepper, input_delay=input_delay, output_delay=output_delay
        )

    def setup_state(
        self,
        *,
        time_step: float,
        input_delays: dict[str, TimeDelay] = {},
        output_delays: dict[str, TimeDelay] = {},
        **kwargs,
    ):
        """Initialize internal buffers and set port-specific delays.

        Args:
            time_step: The interval between time steps (in seconds).
            input_delays: Mapping of port names to delays to override the
              default input delay.
            output_delays: Mapping of port names to delays to override the
              default output delay.
            kwargs: Unused.
        """
        self.buffer_index = 0
        self.input_buffer = _DelayBuffer(
            input_delays, self.parametric_kwargs["input_delay"], time_step
        )
        self.output_buffer = _DelayBuffer(
            output_delays, self.parametric_kwargs["output_delay"], time_step
        )
        self.time_stepper = self.parametric_kwargs["time_stepper"]
        return self.time_stepper.setup_state(time_step=time_step, **kwargs)

    def reset(self):
        self.buffer_index = 0
        self.input_buffer.reset()
        self.output_buffer.reset()
        self.time_stepper.reset()

    def step_single(
        self, inputs: dict[str, complex], time_index: int, update_state: bool, shutdown: bool
    ) -> dict[str, complex]:
        """Take a single time step on the given inputs.

        Args:
            inputs: Dictionary containing inputs at the current time step,
              mapping port names to complex values.
            time_index: Time series index for the current input.
            update_state: Whether to update the internal stepper state.
            shutdown: Whether this is the last call to the single stepping
              function for the provided :class:`TimeSeries`.

        Returns:
            Outputs at the current time step.
        """
        buffer_index = self.buffer_index
        if update_state:
            self.buffer_index += 1
            self.input_buffer.put(buffer_index, inputs)
        inputs_buffered = self.input_buffer.get(buffer_index, inputs)
        outputs = self.time_stepper.step_single(inputs_buffered, time_index, update_state, shutdown)
        if update_state:
            self.output_buffer.put(buffer_index, outputs)
        outputs_buffered = self.output_buffer.get(buffer_index, outputs)
        return outputs_buffered


register_time_stepper_class(DelayedTimeStepper)
