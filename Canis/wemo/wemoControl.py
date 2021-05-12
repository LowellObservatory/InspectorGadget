# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 12 May 2021
#
#  @author: rhamilton

import argparse

from pywemo.ouimeaux_device import probe_wemo
from pywemo.discovery import discover_devices, device_from_description


if __name__ == "__main__":
    parser = argparse.ArgumentParser("WeMo Plug Controller")

    parser.add_argument("name", metavar="NAME",
                        help="Exact (case sensitive) name of the plug")
    parser.add_argument("state", default='toggle',
                        metavar="STATE", choices=['on', 'off', 'toggle'],
                        help="Control the state (on, off, toggle) of the plug")

    parser.add_argument("--direct", default=False, action='store_true',
                        help="Interpret NAME as the hostname/IP of the plug")

    args = parser.parse_args()

    if args.direct is False:
        print("Searching the network for WeMo devices...", end='')
        devices = []
        devices = discover_devices()
        print("%d found" % (len(devices)))

    else:
        print("Attempting direct connection...")
        port = probe_wemo(args.name)
        if port is not None:
            # This also matches https, but I'm pretty sure the current line
            #    of WeMo devices don't have enough onboard memory for https
            if args.name.startswith("http"):
                urlwport = "%s:%s/setup.xml" % (args.name, port)
            else:
                urlwport = "http://%s:%s/setup.xml" % (args.name, port)

            # print(urlwport)
            d = device_from_description(urlwport)
            # Hack to use the existing logic
            devices = [d]
        else:
            print("No WeMo devices found :(")
            print("Are you on the same network *and* subnet?")

    if devices != []:
        reqPlugs = {}
        allPlugs = []

        # We only need to do this if we didn't specify the direct connection
        if args.direct is False:
            print("Making sure plug with name %s was found..." % (args.name))
            for each in devices:
                # Only look at switches; could check each.model_name (Socket)
                #   but I feel like that one is less descriptive
                if each.device_type == "Switch":
                    # Store all the names
                    allPlugs.append(each.name)
                    if each.name == args.name:
                        reqPlugs.update({each.name: each})
        else:
            reqPlugs.update({args.name: d})

        if reqPlugs != {}:
            if len(reqPlugs.keys()) > 1:
                print("Too many matches for %s found!" % (args.name))
                print("Which one did you mean?")
                print(reqPlugs.keys())
            else:
                sender = reqPlugs[args.name]
                try:
                    oldState = int(sender.get_state())
                    if oldState == 0:
                        txtState = "Off"
                    else:
                        txtState = "On"
                    print("State is currently:", txtState)

                    # Do the requested action
                    print("Requested action was:", args.state)
                    if args.state.lower() == "on":
                        sender.set_state(1)
                    elif args.state.lower() == "off":
                        sender.set_state(0)
                    elif args.state.lower() == "toggle":
                        sender.set_state(not oldState)
                    newState = int(sender.get_state())
                    newState = int(sender.get_state())
                    if newState == 0:
                        txtState = "Off"
                    else:
                        txtState = "On"
                    print("State is now:", txtState)
                except Exception as err:
                    print(str(err))
                    print("Changing state failed!")
        else:
            print("%s plug not found!" % (args.name))
            print("Are you on the same network *and* subnet?")
    else:
        print("No WeMo devices found :(")
        print("Are you on the same network *and* subnet?")
