from _thread import start_new_thread
from time import sleep

import machine
import network
import socket
from machine import Pin

import rotary
from rotary import volume_knobs

from secret import SSID, PASSWORD

# Declare LED objects, onboard LED, and red status LED
led = Pin("LED", Pin.OUT)
red = Pin(2, Pin.OUT)
green = Pin(17, Pin.OUT)


# Function to obtain the HTML file, makes it easier to refresh the server
def get_html(html_name):
    with open(html_name, 'r') as file:
        html = file.read()
    return html

# Turn off all LED's incase they weren't off before soft reboot
led.off()
red.off()
green.off()

# Red light on to show it isn't connected yet
red.on()

# Onboard LED flashes, this is to show the script has loaded and the pico is powered
for i in range(0, 5):
    led.on()
    sleep(0.15)
    led.off()
    sleep(0.15)

# Create network object
wlan = network.WLAN(network.STA_IF)
# This prevents an error where after a soft reset the pico thinks it is still connected to the network
# just hard resets the pico if it thinks it is connected at this point
if wlan.active():
    machine.reset()

# Turn wlan on and connect via the credentials in the secret.py file
wlan.active(True)
wlan.connect(SSID, PASSWORD)

# Declare max number of tries to connect before resetting and trying again
max_wait = 50
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    sleep(1)
# When the max wait is reached if it is not connected then it will hard reset
if wlan.status() != 3:
    machine.reset()
# If it connected then turn on the onboard LED and turn off the red LED (This will be updated in future versions)
else:
    print('connected')
    green.on()
    red.off()
    status = wlan.ifconfig()
    print('ip = ' + status[0])

# Declare the address of the server on the local network
# (might do something here where it will message you if it receives no connections?)
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

# Start the pico listening for connections on its IP
s = socket.socket()
s.bind(addr)
s.listen(100)
print('listening on', addr)

# Start the volume control function on a different thread (See rotary.py)
newThread1 = start_new_thread(volume_knobs, ())

# Loop to listen for connections
while True:
    # Try to send info to client, if failure, then go around the loop again
    try:
        # Accept connections, and commented out serial prints for debugging
        cl, addr = s.accept()
        # print('client connected from', addr)
        request = cl.recv(1024)
        # print(request)
        request = str(request)

        # Get the html file, and replace the variables in the html file with the volume variables
        response = get_html("./index.html")
        response = response.replace("{a}", str(rotary.MASTER))
        response = response.replace("{b}", str(rotary.FIREFOX))
        response = response.replace("{c}", str(rotary.SPOTIFY))
        response = response.replace("{d}", str(rotary.GAMES))
        response = response.replace("{e}", str(rotary.DISCORD))
        response = response.replace("{user}", rotary.user)

        # Send the html file to the client and close the client
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()

    # Error handling
    except OSError as e:
        print('connection closed')
