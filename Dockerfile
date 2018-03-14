FROM ubuntu:latest

RUN apt-get update &&\
    apt-get install -y git-core sudo subversion build-essential gcc-multilib  libssl-dev unzip\
                       libncurses5-dev zlib1g-dev gawk flex gettext wget unzip python &&\
    apt-get clean && useradd -m openwrt &&\
    echo 'openwrt ALL=NOPASSWD: ALL' > /etc/sudoers.d/openwrt



COPY --chown=openwrt:openwrt . /home/openwrt/openwrt/
COPY --chown=openwrt:openwrt ./temp_ssh /home/openwrt/.ssh

RUN sudo -iu openwrt bash -c "pwd; ls; ls .ssh/; cd openwrt; cp ./SGD-def.config .config; ./scripts/feeds update; ./scripts/feeds install -a; make download"
RUN sudo -iu openwrt bash -c "cd openwrt; cp -R package/feeds/stel/helloworld/files .; make -j1 V=s"

