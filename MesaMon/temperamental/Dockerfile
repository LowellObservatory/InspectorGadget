FROM balenalib/raspberrypi3-python:3.7

USER root

ARG userid="31415"
ARG groupid="31415"
ARG vidid="31415"
ARG i2cid="31415"
ARG spiid="31415"
ARG gpioid="31415"

RUN addgroup --gid ${groupid} lig && \
    adduser lig --uid ${userid} --gid ${groupid} \
    --gecos '' --disabled-password 

#RUN addgroup --gid ${vidid} video && \
#RUN addgroup --gid ${i2cid} i2c && \
RUN addgroup --gid ${spiid} spi && \
    addgroup --gid ${gpioid} gpio

RUN usermod -a -G video lig && \
    usermod -a -G i2c lig && \
    usermod -a -G spi lig && \
    usermod -a -G gpio lig 

# This updates to the raspberry pi python repo to make sure that we 
#   download binaries whenever possible vs. building from source
COPY pip.conf /etc/pip.conf

RUN pip3 install w1thermsensor

USER lig
RUN mkdir /home/lig/

WORKDIR /home/lig/

COPY --chown=lig:lig database.py . 
COPY --chown=lig:lig packetizer.py .

COPY --chown=lig:lig temperamental.py .

CMD ["python", "temperamental.py"]
