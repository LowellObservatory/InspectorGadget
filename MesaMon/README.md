# Mesa Monitor

A Raspberry Pi based monitoring system for components out at Anderson Mesa.

## Components

- Hardware
    - Raspberry Pi 3b+ or greater (or equivalent)
    - Pi-compatible camera
    - DS18x20 temperature sensors
- Software
    - influxdb (docker)
    - nginx (docker)
    - [PiCamAnimator](https://github.com/LowellObservatory/PiCamAnimator)
    - __Uatu__ manages monitoring
        - Temperature logging
        - Emailing morning summaries
        - Send recent data to archival database

## Layout

This isn't set up as a proper python package, since it's mutated rather
than planned out.  A lot of cross-pollination has occured from things like
[Ultimonitor](https://github.com/LowellObservatory/Ultimonitor) so it's
more of a collection of independent modules that will eventually be
consolidated under the umbrella of the main watcher, Uatu.

### docker-compose

Change the ```dockEnvFile.sh``` script to what is needed for your setup,
and run it.

It's helpful to give the Raspberry Pi a static IP/hostname, since
you can navigate directly to it in a browser and see an animating HTML5
canvas of the most recent set of pictures.
