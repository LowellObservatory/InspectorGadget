import sys
import urequests


def postToInfluxDB(dbconfig, pkt):
    """
    Just using the HTTP endpoint and the simple line protocol.

    Also letting the database time tag it for us.
    """
    host = dbconfig['dbhost']
    port = dbconfig['dbport']
    dbname = dbconfig['dbname']
    metric = dbconfig['dbtabl']

    dbuser = None
    dbpass = None
    try:
        dbuser = dbconfig['dbuser']
    except KeyError:
        # print("No database user found")
        pass

    if dbuser is not None:
        try:
            dbpass = dbconfig['dbpass']
        except KeyError:
            pass
            # print("DB user defined, but no password given!")

    success = False

    if dbuser is not None and dbpass is not None:
        url = "http://%s:%s/write?u=%s&p=%s&db=%s" % (host, port,
                                                      dbuser, dbpass, dbname)
    else:
        url = "http://%s:%s/write?db=%s" % (host, port, dbname)

    print("Using HTTP URL:")
    print(url)

    print(pkt)

    # Manually format the line protocol message for influxdb
    metric = pkt['measurement']
    line = "%s" % (metric)

    # Handle tags first
    allTags = pkt['tags']
    if len(allTags) != 0:
        line += ","
        for n, tagn in enumerate(pkt['tags']):
            line += "%s=%s" % (tagn, pkt['tags'][tagn])
            if n < len(pkt['tags'])-1:
                line += ","

    # Line protocol Whitespace I
    line += " "

    # Now dump in the fields
    for n, f in enumerate(pkt['fields']):
        value = pkt['fields'][f]

        if isinstance(value, float):
            line += '%s=%f' % (f, value)
        elif isinstance(value, int):
            line += '%s=%d' % (f, value)
        else:
            # This is where strings end up
            line += '%s="%s"' % (f, value)

        if n < len(pkt['fields'])-1:
            line += ","

    print(line)

    # There are few rails here so this could go ... poorly.
    try:
        print("Posting to %s:%s %s.%s" % (host, port,
                                          dbname, metric))
        # print("%s=%s, %s=%s" % (tagN, tagV, keyname, value))
        print(url)
        print(line)
        response = urequests.post(url, data=line)
        print("HTTPResponse:", response.status_code, response.text)
        # Informational responses (100–199)
        # Successful responses (200–299)
        # Redirects (300–399)
        # Client errors (400–499)
        # Server errors (500–599)
        if response.status_code < 300:
            success = True
        else:
            success = False
    except OSError as e:
        print(str(e))
    except Exception as e:
        print(str(e))
        success = True
    except OSError as e:
        print(str(e))
    except Exception as e:
        print(str(e))

    return success


def makeInfluxPacket(meas='', ts=None, tags=None, fields=None, debug=False):
    """
    Makes an InfluxDB styled packet given the measurement name, metadata tags,
    and actual fields/values to put into the database
    """
    packet = {}
    if tags is None:
        tags = {}
    if fields is None:
        fields = {}

    packet.update({'measurement': meas})
    if tags is not None:
        if not isinstance(tags, dict):
            print("ERROR! tags must be of type dict.")
            sys.exit(-1)
        else:
            packet.update({'tags': tags})

    # InfluxDB wants timestamps in nanoseconds from Epoch (1970/01/01)
    #   but Grafana defaults to ms precision from Epoch.
    if isinstance(ts, float):
        print("ERROR! Timestamp can not be a float because dumb.")
        sys.exit(-1)
    elif ts is None:
        # If we don't specify a timestamp, don't even put it in the packet
        pass
    else:
        # Also assume that it's right. But this is probably the
        #   weakest link of all of these
        packet.update({'time': ts})

    if not isinstance(fields, dict):
        print("ERROR! fields must be of type dict.")
        sys.exit(-1)

    packet.update({'fields': fields})

    if debug is True:
        print(packet)

    return packet
