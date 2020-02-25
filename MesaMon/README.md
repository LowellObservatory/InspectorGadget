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
    - Always-on image capture (__picam__ in docker)
    - __Uatu__ manages monitoring
        - Temperature logging
        - Emailing morning summaries
        - Send recent data to archival database

## Layout

- __picam__ captures images in a loop, autoscaling the exposure
- __temperamental__ captures temperatures from the attached sensors
  and publishes them in the database on the pi


### docker-compose

Change the ```dockEnvFile.sh``` script to what is needed for your setup,
and run it.

It's helpful to give the Raspberry Pi a static IP/hostname, since
you can navigate directly to it in a browser and see an animating HTML5
canvas of the most recent set of pictures.
