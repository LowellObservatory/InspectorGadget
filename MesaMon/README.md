# Mesa Monitor

A Raspberry Pi based monitoring system for components out at Anderson Mesa.

## Setup

- Raspberry Pi 3b+ or greater (or equivalent)
    - influxdb (docker)
    - nginx (docker)
    - exim4 (docker)
        - NOTE: This is a super-duper terrible idea to keep this
          up and running.  This should be REMOVED ASAP!!!
    - Pi-compatible camera
        - Custom capture software (docker)
    - DS18x20 temperature sensors
        - Custom query software (docker)

### docker-compose

Change the ```dockEnvFile.sh``` script to what is needed for your setup,
and run it.



Change MOAR STUFF TO MAKE THIS WORK



Give the Raspberry Pi a static IP/hostname, and when you navigate to it 
in a browser you should see an animating HTML5 canvas of the most recent
set of pictures.  

# TODO

Need to port over the extra directory hack for dockEnvFile.sh since
I need to still make ${DCDATADIR}/snapper/anim by hand for things to work.
