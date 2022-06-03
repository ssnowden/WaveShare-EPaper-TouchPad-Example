# *****************************************************************************
# * | File        :	  epd2in13_V2.py
# * | Author      :   Simon Snowden based on Waveshare team excellent work
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * | This version:   V4.1
# * | Date        :   2022-06-03
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


from itertools import product
import logging
from . import epdconfig

# Display resolution
EPD_WIDTH = 122
EPD_HEIGHT = 250


class EPaperDisplay:
    _lut_full_update = [
        0x80,
        0x60,
        0x40,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT0: BB:     VS 0 ~7
        0x10,
        0x60,
        0x20,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT1: BW:     VS 0 ~7
        0x80,
        0x60,
        0x40,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT2: WB:     VS 0 ~7
        0x10,
        0x60,
        0x20,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT3: WW:     VS 0 ~7
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT4: VCOM:   VS 0 ~7
        0x03,
        0x03,
        0x00,
        0x00,
        0x02,  # TP0 A~D RP0
        0x09,
        0x09,
        0x00,
        0x00,
        0x02,  # TP1 A~D RP1
        0x03,
        0x03,
        0x00,
        0x00,
        0x02,  # TP2 A~D RP2
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP3 A~D RP3
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP4 A~D RP4
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP5 A~D RP5
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP6 A~D RP6
        0x15,
        0x41,
        0xA8,
        0x32,
        0x30,
        0x0A,
    ]

    _lut_partial_update = [  # 20 bytes
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT0: BB:     VS 0 ~7
        0x80,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT1: BW:     VS 0 ~7
        0x40,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT2: WB:     VS 0 ~7
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT3: WW:     VS 0 ~7
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # LUT4: VCOM:   VS 0 ~7
        0x0A,
        0x00,
        0x00,
        0x00,
        0x00,  # TP0 A~D RP0
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP1 A~D RP1
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP2 A~D RP2
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP3 A~D RP3
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP4 A~D RP4
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP5 A~D RP5
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,  # TP6 A~D RP6
        0x15,
        0x41,
        0xA8,
        0x32,
        0x30,
        0x0A,
    ]
    refresh = False
    touch_count_since_refresh = full_update_refresh_count = loop_count_since_refresh = 0

    # magic methods -------------------------------------------------------------
    def __init__(self):
        self.reset_pin = epdconfig.EPD_RST_PIN
        self.dc_pin = epdconfig.EPD_DC_PIN
        self.busy_pin = epdconfig.EPD_BUSY_PIN
        self.cs_pin = epdconfig.EPD_CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT
        epdconfig.address = 0x14

    # Private methods -------------------------------------------------------
    def _reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(5)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)

    def _send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)

    def _send_data_as_list(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)

    def _send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte(data)
        epdconfig.digital_write(self.cs_pin, 1)

    def _read_busy(self):
        while epdconfig.digital_read(self.busy_pin) == 1:  # 0: idle, 1: busy
            epdconfig.delay_ms(10)

    def _turn_on_display(self):
        self._send_command(0x22)
        self._send_data_as_list(0xC7)
        self._send_command(0x20)
        self._read_busy()

    def _turn_on_display_part(self):
        self._send_command(0x22)
        self._send_data_as_list(0x0C)
        self._send_command(0x20)
        # self.ReadBusy()

    def _turn_on_display_part_wait(self):
        self._send_command(0x22)
        self._send_data_as_list(0x0C)
        self._send_command(0x20)
        self._read_busy()

    def _display(self, image):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self._send_command(0x24)
        # for j in range(0, self.height):
        # for i in range(0, linewidth):
        # self.send_data(image[i + j * linewidth])
        self._send_data(image)
        self._turn_on_display()

    # Public Methods --------------------------------------------------------------
    def update(self, partial_update=False):
        if epdconfig.module_init() != 0:
            return -1
        # EPD hardware init start
        self._reset()
        if partial_update == False:
            self._read_busy()
            self._send_command(0x12)  # soft reset
            self._read_busy()

            self._send_command(0x74)  # set analog block control
            self._send_data_as_list(0x54)
            self._send_command(0x7E)  # set digital block control
            self._send_data_as_list(0x3B)

            self._send_command(0x01)  # Driver output control
            self._send_data_as_list(0xF9)
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x00)

            self._send_command(0x11)  # data entry mode
            self._send_data_as_list(0x01)

            self._send_command(0x44)  # set Ram-X address start/end position
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x0F)  # 0x0C-->(15+1)*8=128

            self._send_command(0x45)  # set Ram-Y address start/end position
            self._send_data_as_list(0xF9)  # 0xF9-->(249+1)=250
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x00)

            self._send_command(0x3C)  # BorderWavefrom
            self._send_data_as_list(0x03)

            self._send_command(0x2C)  # VCOM Voltage
            self._send_data_as_list(0x55)  #

            self._send_command(0x03)
            self._send_data_as_list(self._lut_full_update[70])

            self._send_command(0x04)  #
            self._send_data_as_list(self._lut_full_update[71])
            self._send_data_as_list(self._lut_full_update[72])
            self._send_data_as_list(self._lut_full_update[73])

            self._send_command(0x3A)  # Dummy Line
            self._send_data_as_list(self._lut_full_update[74])
            self._send_command(0x3B)  # Gate time
            self._send_data_as_list(self._lut_full_update[75])

            self._send_command(0x32)
            for count in range(70):
                self._send_data_as_list(self._lut_full_update[count])

            self._send_command(0x4E)  # set RAM x address count to 0
            self._send_data_as_list(0x00)
            self._send_command(0x4F)  # set RAM y address count to 0X127
            self._send_data_as_list(0xF9)
            self._send_data_as_list(0x00)
            self._read_busy()
        else:
            self._send_command(0x2C)  # VCOM Voltage
            self._send_data_as_list(0x26)

            self._read_busy()

            self._send_command(0x32)
            for count in range(70):
                self._send_data_as_list(self._lut_partial_update[count])

            self._send_command(0x37)
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x40)
            self._send_data_as_list(0x00)
            self._send_data_as_list(0x00)

            self._send_command(0x22)
            self._send_data_as_list(0xC0)
            self._send_command(0x20)
            self._read_busy()

            self._send_command(0x3C)  # BorderWavefrom
            self._send_data_as_list(0x01)
        return 0

    def get_buffer(self, image):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        buf = [0xFF] * (linewidth * self.height)
        image_monocolor = image.convert("1")
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()

        if imwidth == self.width and imheight == self.height:
            # logging.debug("Vertical")
            for y, x in product(range(imheight), range(imwidth)):
                if pixels[x, y] == 0:
                    x = imwidth - x
                    buf[int(x / 8) + y * linewidth] &= ~(0x80 >> (x % 8))
        elif imwidth == self.height and imheight == self.width:
            # logging.debug("Horizontal")
            for y in range(imheight):
                newx = y
                for x in range(imwidth):
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        newy = imwidth - newy - 1
                        buf[int(newx / 8) + newy * linewidth] &= ~(0x80 >> (y % 8))
        return buf

    def sleep(self):
        # self.send_command(0x22) #POWER OFF
        # self.send_data(0xC3)
        # self.send_command(0x20)

        self._send_command(0x10)  # enter deep sleep
        self._send_data_as_list(0x03)
        epdconfig.delay_ms(100)

    def exit(self):
        epdconfig.module_exit()

    def clear(self, color):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self._send_command(0x24)
        for _ in range(self.height):
            for _ in range(linewidth):
                self._send_data_as_list(color)

        self._turn_on_display()

    def display_full_page_image(self, image):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self._send_command(0x24)
        for j in range(self.height):
            for i in range(linewidth):
                self._send_data_as_list(image[i + j * linewidth])

        self._send_command(0x26)
        for j in range(self.height):
            for i in range(linewidth):
                self._send_data_as_list(image[i + j * linewidth])
        self._turn_on_display()

    def display_partial_image_wait(self, image):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self._send_command(0x24)
        for j in range(self.height):
            for i in range(linewidth):
                self._send_data_as_list(image[i + j * linewidth])

        self._turn_on_display_part_wait()

    def display_partial_image(self, image):
        if self.width % 8 == 0:
            linewidth = int(self.width / 8)
        else:
            linewidth = int(self.width / 8) + 1

        self._send_command(0x24)
        # for j in range(0, self.height):
        # for i in range(0, linewidth):
        # self.send_data(image[i + j * linewidth])
        self._send_data(image)
        self._turn_on_display_part()
