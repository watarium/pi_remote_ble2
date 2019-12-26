#!/usr/bin/python
import blescan
import sys
import os
import math
import bluetooth._bluetooth as bluez
import argparse

# Arguments parser
parser = argparse.ArgumentParser(description='Reliable Bluetooth LE (iBeacon) scanner')
parser.add_argument('-i', type=int, default=0, help='Bluetooth adapter ID')
parser.add_argument('-t', type=int, default=10,
                    help='Seconds between two survey. A small value can cause some beacon to be missed')
parser.add_argument('-n', type=float, default=1.0, help='Path loss exponent')
parser.add_argument('-pdz', type=int, default=1, help='TxPower at taring position')
parser.add_argument('-dz', type=int, default=1, help='Distance of taring position (m) ')

args = parser.parse_args()

# Console colors
W = '\033[0m'  # white (normal)
R = '\033[31m'  # red
G = '\033[32m'  # green
O = '\033[33m'  # orange
B = '\033[34m'  # blue
P = '\033[35m'  # purple
C = '\033[36m'  # cyan
GR = '\033[37m'  # gray


def printInfo(str):
    print
    G + "[INFO]" + str


def printError(str):
    print
    R + "[ERROR]" + str


def gracefulExit():
    print
    print
    R + "Quitting... ByeBye!"
    print
    W
    sys.exit(0)


def badExit():
    print
    print
    R + "Somethings went wrong...! Quitting!"
    print
    W
    sys.exit(1)


def getDistance(rssi,txP):
    ratio = round(rssi * 1.0 / (txP+1e-10),5)
    if abs(ratio) > 1e+3:
        distance = 99999999
    elif ratio < 1.0:
        distance = math.pow(ratio, 10.0)
    else:
        distance = (0.89976) * math.pow(ratio, 7.7095) + 0.111

    return distance


printInfo("Starting BLE thread on device ID: " + str(args.i) + "...")
try:
    sock = bluez.hci_open_dev(int(args.i))

except:
    printError("Error accessing bluetooth device!")
    badExit()

printInfo("Setting up BLE device ...")
try:
    blescan.hci_le_set_scan_parameters(sock)

except:
    printError("Error setting up bluetooth device!")
    badExit()

printInfo("Start scanning...")
try:
    blescan.hci_enable_le_scan(sock)
except:
    printError("Error scanning! Maybe not root?")
    badExit()

rssi_list = {}
for n in range(10):
    returnedList = blescan.parse_events(sock, args.t)

    seen = set()
    purgedList = []
    # We search and delete all the beacon from the same device
    # Looping througth the returnedList, every time we found a MAC adr
    # that is not present in 'seen', we add it to 'seen' and 'purgedList'
    for d in returnedList:
        t = d['MAC']
        if t not in seen:
            seen.add(t)
            purgedList.append(d)

    os.system('clear')

    # Formated output for result
    print G + "{0:<20s}{1:<10s}{2:<10s}{3:<10s}{4:<10s}{5:<13s}{6:<10s}".format("MAC", "MAJOR", "MINOR", "RSSI",
                                                                          "TxPOWER", "DISTANCE(m)", "UUDI")
    for beacon in purgedList:
        distance = getDistance(beacon['RSSI'][0],beacon['TxPOWER'][0])

        print("{0:<20s}{1:<10}{2:<10}{3:<10d}{4:<10d}{5:<13.2f}{6:<10}".format(beacon['MAC'], beacon['MAJOR'],
                                                                               beacon['MINOR'], beacon['RSSI'][0],
                                                                               beacon['TxPOWER'][0],
                                                                               distance,
                                                                               beacon['UUID']))
        rssi_list.setdefault(beacon['MAC'], []).append(distance)

print('')
print('Average distance')
for mac in rssi_list.keys():
    average_distance = sum(rssi_list[mac]) / len(rssi_list[mac])
    if len(rssi_list[mac]) > 3:
        if average_distance < 1000:
            print(mac + ': ' + str(average_distance) + ' (m)')


