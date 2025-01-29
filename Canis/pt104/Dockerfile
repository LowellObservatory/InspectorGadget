FROM yourDockerHubThing:8042/lig/ligbase_reborn:latest

USER root

#RUN apt-get update && \
#    apt-get install -y udev && \
#    rm -rf /var/lib/apt/lists/*
#RUN udevadm control --reload-rules || echo "done"
#RUN udevadm trigger

RUN bash -c 'wget -O- https://labs.picotech.com/Release.gpg.key | gpg --dearmor > /usr/share/keyrings/picotech-archive-keyring.gpg' && \
    bash -c 'echo "deb [signed-by=/usr/share/keyrings/picotech-archive-keyring.gpg] https://labs.picotech.com/picoscope7/debian/ picoscope main" >/etc/apt/sources.list.d/picoscope7.list'

RUN apt-get update && \
    ln -s /bin/true /bin/udevadm && \
    mkdir -pv /etc/udev/rules.d && \
    apt-get install -qqy libcap2-bin libusb-1.0-0 libusbpt104 && \
    rm -rf /var/lib/apt/lists/* && \
    rm /bin/udevadm

RUN ln -s /opt/picoscope/lib/* /usr/local/lib && ln -s /usr/local/lib/libusbpt104.so /usr/local/lib/libusbPt104.so
RUN setcap 'CAP_NET_BIND_SERVICE=ep' /opt/conda/envs/ligbase/bin/python3.12

USER lig

RUN git clone https://github.com/picotech/picosdk-python-wrappers
RUN cd picosdk-python-wrappers && conda run -n ligbase pip install -e . && cd
COPY pt104Example.py .
