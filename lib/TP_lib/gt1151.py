import logging
from . import epdconfig as config


class TouchEvent:
    def __init__(self):
        self.Touch = 0
        self.TouchpointFlag = 0
        self.TouchCount = 0
        self.Touchkeytrackid = [0, 1, 2, 3, 4]
        self.X = [0, 1, 2, 3, 4]
        self.Y = [0, 1, 2, 3, 4]
        self.S = [0, 1, 2, 3, 4]

    def __eq__(self, __o):
        # NOTE: At the moment only looks at first touch point.
        # TODO: Should probably loop through the touch points and if hit am inequality
        # return false - on exit of loop return true
        return __o.X[0] == self.X[0] and __o.Y[0] == self.Y[0] and __o.S[0] == self.S[0]


class TouchPad:
    def __init__(self):
        # e-Paper
        self.ERST = config.EPD_RST_PIN
        self.DC = config.EPD_DC_PIN
        self.CS = config.EPD_CS_PIN
        self.BUSY = config.EPD_BUSY_PIN
        # TP
        self.TRST = config.TRST
        self.INT = config.INT

    # Private methods ---------------------------
    def _reset(self):
        config.digital_write(self.TRST, 1)
        config.delay_ms(100)
        config.digital_write(self.TRST, 0)
        config.delay_ms(100)
        config.digital_write(self.TRST, 1)
        config.delay_ms(100)

    def _write(self, register, data):
        config.i2c_writebyte(register, data)

    def _read(self, register, num_of_bytes):
        return config.i2c_readbyte(register, num_of_bytes)

    def _get_version(self):
        version = self._read(0x8140, 4)
        logging.debug(f"{version=}")

    # Public methods ----------------------------------------------
    def initialise(self):
        self._reset()
        self._get_version()

    def get_touch_events(self, current_event, event_memory=None):
        buf = []

        if current_event.Touch == 1:
            current_event.Touch = 0
            buf = self._read(0x814E, 1)
            mask = 0x00

            if buf[0] & 0x80 == 0x00:
                self._write(0x814E, mask)
                config.delay_ms(10)

            else:
                current_event.TouchpointFlag = buf[0] & 0x80
                current_event.TouchCount = buf[0] & 0x0F

                if current_event.TouchCount > 5 or current_event.TouchCount < 1:
                    self._write(0x814E, mask)
                    return

                buf = self._read(0x814F, current_event.TouchCount * 8)
                self._write(0x814E, mask)

                if event_memory:
                    event_memory.X[0] = current_event.X[0]
                    event_memory.Y[0] = current_event.Y[0]
                    event_memory.S[0] = current_event.S[0]

                for i in range(current_event.TouchCount):
                    current_event.Touchkeytrackid[i] = buf[0 + 8 * i]
                    current_event.X[i] = (buf[2 + 8 * i] << 8) + buf[1 + 8 * i]
                    current_event.Y[i] = (buf[4 + 8 * i] << 8) + buf[3 + 8 * i]
                    current_event.S[i] = (buf[6 + 8 * i] << 8) + buf[5 + 8 * i]

                logging.debug(
                    f"touch event= X: {current_event.X[0]} Y: {current_event.Y[0]} S: {current_event.S[0]}"
                )

    def digital_read(self, pin):
        return config.digital_read(pin)
