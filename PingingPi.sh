#! /bin/bash

light_green='\033[1;32m'
light_red='\033[1;31m'
yellow='\033[1;33m'
green='\033[0;32m'
red='\033[0;31m'
end='\033[0m' #Stop coloring

ping_threshold=90

while [ 1 ]
do
    date=`date +"%e/%m/%y@%R:%S"`
    out=`ping -W 2 -c 1 bbc.co.uk 2>&1`
    if [ $? = 0 ]
    then
        log=`echo ${out} | sed -e 's/ ms.*$//' -e 's/^.*time=//'`
        ping_ms=`echo ${log} | sed -e 's/^.* //'`
        if (( $(echo "$ping_ms < $ping_threshold" | bc -l) ))
        then
            color=${light_green}
        else
            color=${yellow}
        fi
        echo -e "${color}[${date}] ${log}${end}"
    else
        echo -e "${red}[${date}] ERROR:${end}"
        echo -e "${light_red}${out}${end}"
    fi
    sleep 5
done
