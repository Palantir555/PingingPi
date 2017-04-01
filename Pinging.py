import time
import led_colours
import binascii

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
    def __init__(self, array_led_num, spi_dev_path='/dev/spidev0.0'):
        self.spidev_path = spi_dev_path
        self.led_array_len = array_led_num
        #LPD6803 has 5 bit color, this seems to work but is not exact.
        self.spidev = file(self.spidev_path, "wb")
        self.gamma = bytearray(256)
        for i in range(256):
            self.gamma[i] = int(pow(float(i) / 255.0, 2.0) * 255.0 + 0.5)

    def write_stream(self, pixels):
        pixel_out_bytes = bytearray(2)
        self.spidev.write(bytearray(4))
        pixel_count = len(pixels) / PIXEL_SIZE
        print "pixel_count:\t{0}".format(pixel_count)
        for pixel_index in range(pixel_count):
            pixel_in = bytearray(pixels[(pixel_index * PIXEL_SIZE):((pixel_index * PIXEL_SIZE) + PIXEL_SIZE)])

            pixel_out = 0b1000000000000000  # bit 16 must be ON
            pixel_out |= (pixel_in[0] & 0x00F8) << 7  # RED is bits 11-15
            pixel_out |= (pixel_in[1] & 0x00F8) << 2  # GREEN is bits 6-10
            pixel_out |= (pixel_in[2] & 0x00F8) >> 3  # BLUE is bits 1-5

            pixel_out_bytes[0] = (pixel_out & 0xFF00) >> 8
            pixel_out_bytes[1] = (pixel_out & 0x00FF) >> 0
            self.spidev.write(pixel_out_bytes)
            print "pixel_index:     {0}".format(pixel_index)
            print "pixel_in:        {0}".format(binascii.hexlify(pixel_in))
            print "pixel_out:       {0}".format(pixel_out)
            print "pixel_out_bytes: {0}".format(binascii.hexlify(pixel_out_bytes))

        self.spidev.write(bytearray(len(pixels) / 8 + 1))

    # Apply Gamma Correction and RGB / GRB reordering
    # Optionally perform brightness adjustment
    def filter_pixel(self, input_pixel, brightness):
        output_pixel = bytearray(PIXEL_SIZE)
        input_pixel[0] = int(brightness * input_pixel[0])
        input_pixel[1] = int(brightness * input_pixel[1])
        input_pixel[2] = int(brightness * input_pixel[2])
        output_pixel[0] = self.gamma[input_pixel[0]]
        output_pixel[1] = self.gamma[input_pixel[1]]
        output_pixel[2] = self.gamma[input_pixel[2]]
        return output_pixel

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

    def routine_chase(self):
        pixel_output = bytearray(self.led_array_len + 3)
        current_color = bytearray(PIXEL_SIZE)
        pixel_index = 0
        while True:
            for current_color[:] in led_colours.RAINBOW:
                for pixel_index in range(self.led_array_len):
                    pixel_output[(pixel_index - 2):] = self.filter_pixel(current_color[:], 0.2)
                    pixel_output[(pixel_index - 1):] = self.filter_pixel(current_color[:], 0.4)
                    pixel_output[(pixel_index):] = self.filter_pixel(current_color[:], 1)
                    pixel_output += '\x00' * (self.led_array_len - 1 - pixel_index)
                    self.write_stream(pixel_output)
                    self.spidev.flush()
                    time.sleep((50) / 1000.0) #JC: 50 is args.refresh_rate from pixelpi.py
                    pixel_output[((pixel_index - 2) * PIXEL_SIZE):] = self.filter_pixel(current_color[:], 0)


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
    #driv.routine_chase()
    driv.routine_all_on()
    driv.routine_all_off()
    driv.routine_chase()
