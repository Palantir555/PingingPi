Really simple script to ping a server every n seconds and print a nicely formatted formatted to stdout. In order to have a useful output without having to read the response times, it is coloured depending on the value:

    - Green:  Response time under the threshold - 80ms by default
    - Yellow: Response time over the threshold
    - Red:    Dropped packet - The complete error is printed

I'm currently using a 2.8" TFT screen from Adafruit to keep it always in sight.

![Working PingingPi](http://i.imgur.com/XdKprKY.jpg)

TODO:
    - Add arguments to set time between pings and server to hit
