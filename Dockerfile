FROM ubuntu:latest

RUN apt-get update &&\
    apt-get install -y git-core sudo subversion build-essential gcc-multilib  libssl-dev unzip\
                       libncurses5-dev zlib1g-dev gawk flex gettext wget unzip python &&\
    apt-get clean
RUN useradd -m openwrt &&\
    echo 'openwrt ALL=NOPASSWD: ALL' > /etc/sudoers.d/openwrt



#RUN sudo -iu openwrt bash -c "pwd; git clone git@github.com:jonpry/openwrt_mt7688.git openwrt"
COPY --chown=openwrt:openwrt . /home/openwrt/openwrt/

RUN sudo -iu openwrt bash -c "pwd; ls; cd openwrt; cp ./SGD-def.config .config; ./scripts/feeds update; ./scripts/feeds install -a; make download"
RUN sudo -iu openwrt bash -c "cd openwrt; make -j1 V=s"

