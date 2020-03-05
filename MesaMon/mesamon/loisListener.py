# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 4 Mar 2020
#
#  @author: rhamilton

"""One line description of module.

Further description.
"""

from __future__ import division, print_function, absolute_import

from collections import OrderedDict

from stomp.listener import ConnectionListener

from ligmos import utils

from . import loisParser as parsers


class loisConsumer(ConnectionListener):
    def __init__(self, db=None):
        """
        This is just to route the messages to the right parsers
        """
        # This assumes that the database object was set up elsewhere
        self.db = db

    def on_message(self, headers, body):
        """
        Basically subclassing stomp.listener.ConnectionListener
        """
        badMsg = False
        tname = headers['destination'].split('/')[-1].strip()
        # Manually turn the bytestring into a string
        try:
            body = body.decode("utf-8")
            badMsg = False
        except UnicodeDecodeError as err:
            print(str(err))
            print("Badness 10000")
            print(body)
            badMsg = True

        if badMsg is False:
            # Since this is a single-purpose listener, and I know it's not
            #   XML, I am cutting to the chase
            res = {tname: [headers, body]}

            if tname.endswith("loisLog"):
                tfields = parsers.parseLOISTemps(headers, body)

                # Only store the packet if we actually have fields that
                #   were successfully parsed
                if tfields != {}:
                    pkt = utils.packetizer.makeInfluxPacket(measname,
                                                            ts=None,
                                                            tags=tags,
                                                            fields=tfields,
                                                            debug=debug)

    if self.db is not None and pkt is not None:
        self.db.singleCommit(pkt, table=table, close=True)
