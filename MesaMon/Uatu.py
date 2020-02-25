# -*- coding: utf-8 -*-
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
#  Created on 25 Feb 2020
#
#  @author: rhamilton

"""Uatu (/ˈwɑːtuː/)ː Often simply known as The Watcher.

Uatu is a fictional character appearing in Marvel Comics.
He is a member of the Watchers, an extraterrestrial species who
in the distant past stationed themselves across space to monitor
the activities of other species. Uatu is the Watcher assigned to
observe Earth and its solar system.
"""

from __future__ import division, print_function, absolute_import

from ligmos.utils import databse

from . import temperamental


def run():
    """
    """
    pass


if __name__ == "__main__":
    dbhost = 'localhost'
    dbport = 8086
    dbname = 'mesa42'

    idb = database.influxobj(tablename=dbname,
                             host=dbhost, port=dbport,
                             connect=True)

    while True:
        pkt = readAllSensors()
        idb.singleCommit(pkt, table=dbname)

        print("Sleeping ...")
        time.sleep(10)
