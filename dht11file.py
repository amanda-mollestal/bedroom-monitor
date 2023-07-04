import utime
import array
from machine import Pin
import micropython
from micropython import const


class InvalidChecksumError(Exception):
    pass


class IncorrectPulseCountError(Exception):
    pass


MAX_CONSTANT = const(100)
MINIMUM_INTERVAL_US = const(200000)
HIGH_VALUE = const(50)
REQUIRED_PULSES = const(84)


class DHT11Sensor:
    _temp: float
    _humidity: float

    def __init__(self, pin):
        self._pin = pin
        self._prev_measure = utime.ticks_us()
        self._temp = -1
        self._humidity = -1

    def take_measure(self):
        current_ticks = utime.ticks_us()
        if utime.ticks_diff(current_ticks, self._prev_measure) < MINIMUM_INTERVAL_US and (
            self._temp > -1 or self._humidity > -1
        ):
            return

        self._start_signal()
        pulses = self._get_pulses()
        buffer = self._pulses_to_buffer(pulses)
        self._validate_checksum(buffer)

        self._humidity = buffer[0] + buffer[1] / 10
        self._temp = buffer[2] + buffer[3] / 10
        self._prev_measure = utime.ticks_us()

    @property
    def humidity(self):
        self.take_measure()
        return self._humidity

    @property
    def temperature(self):
        self.take_measure()
        return self._temp

    def _start_signal(self):
        self._pin.init(Pin.OUT, Pin.PULL_DOWN)
        self._pin.value(1)
        utime.sleep_ms(50)
        self._pin.value(0)
        utime.sleep_ms(18)

    @micropython.native 
    def _get_pulses(self):
        pin = self._pin
        pin.init(Pin.IN, Pin.PULL_UP)

        val = 1
        idx = 0
        shifts = bytearray(REQUIRED_PULSES)
        stable = 0
        time_stamp = utime.ticks_us()

        while stable < MAX_CONSTANT:
            if val != pin.value():
                if idx >= REQUIRED_PULSES:
                    raise IncorrectPulseCountError(
                        "Got more than {} pulses".format(REQUIRED_PULSES)
                    )
                now = utime.ticks_us()
                shifts[idx] = now - time_stamp
                time_stamp = now
                idx += 1

                val = 1 - val
                stable = 0
            else:
                stable += 1
        pin.init(Pin.OUT, Pin.PULL_DOWN)
        if idx != REQUIRED_PULSES:
            raise IncorrectPulseCountError(
                "Expected {} but got {} pulses".format(REQUIRED_PULSES, idx)
            )
        return shifts[4:]

    def _pulses_to_buffer(self, pulses):
        binary = 0
        for idx in range(0, len(pulses), 2):
            binary = binary << 1 | int(pulses[idx] > HIGH_VALUE)

        buffer = array.array("B")
        for shift in range(4, -1, -1):
            buffer.append(binary >> shift * 8 & 0xFF)
        return buffer

    def _validate_checksum(self, buffer):
        checksum = 0
        for buf in buffer[0:4]:
            checksum += buf
        if checksum & 0xFF != buffer[4]:
            raise InvalidChecksumError()
