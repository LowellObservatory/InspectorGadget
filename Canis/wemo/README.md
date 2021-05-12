# Requirements

- Python > 3.6
- [pywemo](https://github.com/pywemo/pywemo) >= 0.64

# General Notes

Default timeouts for connections are 10 seconds and not easily changed
since they're hardcoded in pywemo, so there will be at least a 10 second
wait if the name or IP is wrong in some cases.

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
