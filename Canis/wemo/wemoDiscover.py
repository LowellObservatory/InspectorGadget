# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 12 May 2021
#
#  @author: rhamilton

import pywemo


if __name__ == "__main__":
    print("Searching the network for WeMo devices...", end='')
    devices = []
    devices = pywemo.discover_devices()
    print("%d found" % (len(devices)))

    if devices != []:
        print()
        print("Host/IP\t\tPort\tMAC\t\tWeMoName\tState (0==Off)")
        for plug in devices:
            print("%s\t%d\t%s\t%s\t%s" % (plug.host, plug.port,
                                          plug.mac, plug.name,
                                          plug.get_state()))

    else:
        print("No WeMo devices found :(")
        print("Are you on the same network *and* subnet?")
