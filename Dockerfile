FROM ubuntu:latest

RUN apt-get update &&\
    apt-get install -y git-core sudo subversion build-essential gcc-multilib  libssl-dev unzip\
                       libncurses5-dev zlib1g-dev gawk flex gettext wget unzip python &&\
    apt-get clean && useradd -m openwrt &&\
    echo 'openwrt ALL=NOPASSWD: ALL' > /etc/sudoers.d/openwrt



RUN cp ./SGD-def.config .config && ./scripts/feeds update && ./scripts/feeds install -a &&\
    make download
COPY --chown=openwrt:openwrt . /home/openwrt/openwrt/

RUN sudo -iu openwrt bash -c "cd openwrt; make -j16 V=s"

