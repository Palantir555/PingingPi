import signal
import time
import led_colours
import binascii
import sys
from Queue import Queue
from subprocess import Popen, PIPE, CalledProcessError

#Config
LED_STRIP_LEN = 47
PING_SERVER = "bbc.co.uk"
DELAY_BETWEEN_PINGS = 0.5 #seconds

MAXPING_NETWORK_OK   = 80 #milliseconds
MAXPING_NETWORK_SLOW = 120 #milliseconds

#Green/Yellow/Red colour scheme - Default to Black
#LEDCOLOUR_DEFAULT = led_colours.BLACK
#LEDCOLOUR_NETWORK_OK = led_colours.GREEN
#LEDCOLOUR_NETWORK_SLOW = led_colours.YELLOW
#LEDCOLOUR_NETWORK_ERROR = led_colours.RED

#White/Yellow/Red colour scheme - Default to White
LEDCOLOUR_DEFAULT = led_colours.WHITE
LEDCOLOUR_NETWORK_OK = led_colours.WHITE
LEDCOLOUR_NETWORK_SLOW = led_colours.YELLOW
LEDCOLOUR_NETWORK_ERROR = led_colours.RED

#Macros
PIXEL_SIZE = 3 #imported from pixelpi.py

class lpd6803_driver:
    default_colour = LEDCOLOUR_DEFAULT
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

def ping_server(server="google.com"):
    '''Ping $server, return a float with the ping response time or None in case
    of timeout or error'''
    try:
        print "Pinging {0}".format(server)
        process = Popen(['ping', '-w', str(MAXPING_NETWORK_SLOW/1000), '-c1', server],
                        stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
    except CalledProcessError as error:
        print "Ping returned with error code [{0}]".format(error.returncode)
        return None

    if stdout.find("time=") >= 0:
        time_str_idx = stdout.find("time=") + len("time=")
        ms_str_idx = stdout[time_str_idx:].find("ms") + time_str_idx
        time = float(stdout[time_str_idx : ms_str_idx].strip())
        return time
    else:
        #TODO: Check what was the error, maybe review stderr, etc.
        return None

def sigint_handler(signal, frame):
    print "You pressed Ctrl+C - Initiating shutdown routine"
    try:
        driv.routine_all_off()
    except NameError:
        pass #driv has not been created yet
    sys.exit(0)

if __name__ == '__main__':
    driv = lpd6803_driver(LED_STRIP_LEN)
    driv.routine_all_off()
    signal.signal(signal.SIGINT, sigint_handler)

    while True:
        response_time = ping_server("bbc.co.uk")
        if response_time:
            print "Response time: [{0}]".format(response_time)
        else:
            print "Got no response"

        if response_time is None:
            driv.queue_put_colour(LEDCOLOUR_NETWORK_ERROR)
        elif response_time <= MAXPING_NETWORK_OK:
            driv.queue_put_colour(LEDCOLOUR_NETWORK_OK)
        elif response_time <= MAXPING_NETWORK_SLOW:
            driv.queue_put_colour(LEDCOLOUR_NETWORK_SLOW)
        else:
            driv.queue_put_colour(LEDCOLOUR_NETWORK_ERROR)
        driv.queue_display()
        time.sleep(DELAY_BETWEEN_PINGS)
