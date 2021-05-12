# wemoControl.py

```python wemoControl.py <WeMo name> <on, off, toggle>```

Takes an option argument, ```--direct```, that allows one to use an IP
address instead of the WeMo name.  If this is specified the initial whole
subnet scan is skipped and things are generally much faster.

:warning: ```--direct``` currently only works with IPs and not hostnames!

# wemoDiscover.py

```python wemoDiscover.py```

Takes no arguments, and it will scan the entire subnet for WeMo devices and
return their IP addresses, active ports, MAC address, and WeMo name.
