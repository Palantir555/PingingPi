#! /bin/bash

curl -SLs https://apt.adafruit.com/add-pin | sudo bash
sudo apt-get -y install raspberrypi-bootloader
sudo apt-get -y install adafruit-pitft-helper
