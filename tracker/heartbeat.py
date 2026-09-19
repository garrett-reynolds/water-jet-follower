"""Hardware heartbeat for the normally-off 24 V watchdog contactor."""


class Heartbeat:
    """Toggle one requested GPIO line without importing Pi packages on a laptop."""

    def __init__(self, request, line, active, inactive):
        self._request = request
        self._line = line
        self._active = active
        self._inactive = inactive
        self._next = active
        self._closed = False

    def beat(self):
        if self._closed:
            raise RuntimeError("watchdog heartbeat is closed")
        self._request.set_value(self._line, self._next)
        self._next = (self._inactive if self._next == self._active
                      else self._active)

    def close(self):
        if self._closed:
            return
        try:
            self._request.set_value(self._line, self._inactive)
        finally:
            self._request.release()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _traceback):
        self.close()


def open_gpio(line, chip="/dev/gpiochip0"):
    """Request a Pi GPIO output and return it inactive."""
    import gpiod

    inactive = gpiod.line.Value.INACTIVE
    active = gpiod.line.Value.ACTIVE
    request = gpiod.request_lines(
        chip,
        consumer="water-jet-watchdog",
        config={line: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=inactive,
        )},
    )
    return Heartbeat(request, line, active, inactive)
