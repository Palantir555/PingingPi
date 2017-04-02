import time
import led_colours
import binascii
import sys
from Queue import Queue

PIXEL_SIZE=3 #imported from pixelpi.py
LED_STRIP_LEN=47
PING_SERVER="google.com"
PING_DELAY=10
GREEN_MAX=80
YELLOW_MAX=120
TIMEOUT_COLOUR=led_colours.RED

class CliLogger:
    def __init__(self):
        pass

class lpd6803_driver:
    default_colour = led_colours.BLACK
    def __init__(self, array_led_num, spi_dev_path='/dev/spidev0.0'):
        self.output_colour_queue = Queue(maxsize=array_led_num)
        self.spidev_path = spi_dev_path
        self.led_array_len = array_led_num
        self.spidev = file(self.spidev_path, "wb")

    def write_stream(self, pixels):
        pixel_out_bytes = bytearray(2)
        self.spidev.write(bytearray(4))
        pixel_count = len(pixels) / PIXEL_SIZE
        for pixel_index in range(pixel_count):
            pixel_in = bytearray(pixels[(pixel_index * PIXEL_SIZE):((pixel_index * PIXEL_SIZE) + PIXEL_SIZE)])

            pixel_out = 0b1000000000000000  # bit 16 must be ON
            pixel_out |= (pixel_in[0] & 0x00F8) << 7  # RED is bits 11-15
            pixel_out |= (pixel_in[1] & 0x00F8) << 2  # GREEN is bits 6-10
            pixel_out |= (pixel_in[2] & 0x00F8) >> 3  # BLUE is bits 1-5

            pixel_out_bytes[0] = (pixel_out & 0xFF00) >> 8
            pixel_out_bytes[1] = (pixel_out & 0x00FF) >> 0
            self.spidev.write(pixel_out_bytes)

        self.spidev.write(bytearray(len(pixels) / 8 + 1))

    def queue_put_colour(self, colour):
        if self.output_colour_queue.full():
            self.output_colour_queue.get()
        self.output_colour_queue.put(colour)

    def queue_display(self):
        lis = list(self.output_colour_queue.queue)
        ordered_list = list(reversed(lis))
        while len(ordered_list) < self.led_array_len:
            ordered_list.append(self.default_colour)
        self.routine_set_colours_list(ordered_list)

    @staticmethod
    def pixel_adjust_brightness(input_pixel, brightness):
        input_pixel[0] = int(brightness * input_pixel[0])
        input_pixel[1] = int(brightness * input_pixel[1])
        input_pixel[2] = int(brightness * input_pixel[2])
        return input_pixel

    @staticmethod
    def pixel_rgb_to_brg(input_pixel):
        output_pixel = bytearray(PIXEL_SIZE)
        output_pixel[0] = input_pixel[2]
        output_pixel[1] = input_pixel[0]
        output_pixel[2] = input_pixel[1]
        return output_pixel

    def filter_pixel(self, input_pixel, brightness):
        input_pixel = self.pixel_adjust_brightness(input_pixel, brightness)
        input_pixel = self.pixel_rgb_to_brg(input_pixel)
        return input_pixel

    def routine_all_on(self):
        print("Turning all LEDs On")
        pixel_output = bytearray(self.led_array_len * PIXEL_SIZE + 3)
        for led in range(self.led_array_len):
            pixel_output[led * PIXEL_SIZE:] = self.filter_pixel(led_colours.WHITE, 1)
        self.write_stream(pixel_output)
        self.spidev.flush()

    def routine_all_off(self):
        print("Turning all LEDs Off")
        pixel_output = bytearray(self.led_array_len * PIXEL_SIZE + 3)
        for led in range(self.led_array_len):
            pixel_output[led * PIXEL_SIZE:] = self.filter_pixel(led_colours.BLACK, 1)
        self.write_stream(pixel_output)
        self.spidev.flush()

    #receives a list of pixels and combines them into a string
    #brightness = [0, 0.1, ... 1]
    def routine_set_colours_list(self, pixels_list, brightness=1):
        spi_output = bytearray(self.led_array_len * PIXEL_SIZE + 3)
        spi_ready_pixel = bytearray(PIXEL_SIZE)
        for idx in range(len(pixels_list)):
            #adjust brightness and convert rgb to brg
            spi_ready_pixel = self.filter_pixel(pixels_list[idx], brightness)
            #set the pixel to the bytearray we wanna send via SPI
            spi_output[idx*PIXEL_SIZE :] = self.filter_pixel(pixels_list[idx], brightness)
        for idx in range(len(pixels_list), self.led_array_len):
            #fill the rest of the string with a user-defined default colour
            spi_output[idx*PIXEL_SIZE :] = self.filter_pixel(self.default_colour, 1)
        self.write_stream(spi_output)
        self.spidev.flush()


class LedController:
    def __init__(self):
        pass

    def init_leds(self, default_colour=led_colours.WHITE):
        pass

class Pinger:
    def __init__(self, target_servers=["google.com"], pings_delay=60):
        pass

if __name__ == '__main__':
    driv = lpd6803_driver(LED_STRIP_LEN)
    driv.routine_all_off()

    output_colours_list = [led_colours.GREEN, led_colours.YELLOW, led_colours.RED]
    #output_colours_list = led_colours.RAINBOW

    col_idx = 0
    while True:
        print "Starting new loop iteration"
        for i in range(LED_STRIP_LEN):
            driv.queue_put_colour(output_colours_list[col_idx])
            driv.queue_display()

        #change colours in the next round
        col_idx += 1
        if col_idx >= len(output_colours_list):
            col_idx = 0
