FROM ubuntu:latest

RUN apt-get update &&\
    apt-get install -y git-core sudo subversion build-essential gcc-multilib  libssl-dev unzip\
                       libncurses5-dev zlib1g-dev gawk flex gettext wget unzip python &&\
    apt-get clean
RUN useradd -m openwrt &&\
    echo 'openwrt ALL=NOPASSWD: ALL' > /etc/sudoers.d/openwrt
#RUN sudo -iu openwrt bash -c "pwd; git clone git@github.com:jonpry/openwrt_mt7688.git openwrt"
RUN sudo -iu openwrt bash -c "cp ./SGD-def.config .config; ./scripts/feeds update; cd openwrt; make defconfig; make download"
RUN sudo -iu openwrt bash -c "make V=s"

