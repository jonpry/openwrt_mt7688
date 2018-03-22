FROM ubuntu:latest

RUN apt-get update &&\
    apt-get install -y git-core sudo subversion build-essential gcc-multilib  libssl-dev unzip\
                       libncurses5-dev zlib1g-dev gawk flex gettext wget unzip python &&\
    apt-get clean && useradd -m openwrt &&\
    echo 'openwrt ALL=NOPASSWD: ALL' > /etc/sudoers.d/openwrt



COPY --chown=openwrt:openwrt . /home/openwrt/openwrt/
COPY --chown=openwrt:openwrt ./temp_ssh /home/openwrt/.ssh

RUN sudo -iu openwrt bash -c "pwd; ls; ls .ssh/; cd openwrt; ./scripts/feeds update; cp package/feeds/stel/helloworld/openocd_makefile.txt package/feeds/packages/openocd/Makefile; ./scripts/feeds install -a; cp ./SGD-def.config .config; cat .config | grep cares"
RUN sudo -iu openwrt bash -c "cd openwrt; cp -R package/feeds/stel/helloworld/files .; make -j16"

