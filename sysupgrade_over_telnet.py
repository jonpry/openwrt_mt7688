#!/usr/bin/python3
from telnetlib import Telnet
import sys
from subprocess import call
import io
import time

def print_help():
    print('Usage : install2board <target pi IP>')
### Constants

SYSIMAGE="bin/targets/ramips/mt76x8/openwrt-ramips-mt76x8-wrtnode2r-squashfs-sysupgrade.bin"
PACKAGE_HELLOWORLD="bin/packages/mipsel_24kc/stel/helloworld_1_mipsel_24kc.ipk"

PORT = 7000


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_help()
    dev_ip = sys.argv[1]
    scp_target = "root@{}:/tmp".format(dev_ip)
    
    print("Telnet Connect from rapberryPi  {}, port {}".format(dev_ip, PORT))
    state = "start"
    telnet_con = Telnet(dev_ip, str(PORT))
    socket = telnet_con.get_socket()
    tfile = socket.makefile('rwb', buffering=0)
    bufferr = io.BufferedReader(tfile)
    bufferw = io.BufferedWriter(tfile)
    i2c_read_ok = False
    ril_ok = False
    rdb_ok = False
    start_time = None
    strip_ln_telnet = False
    str_ = ''
    try:
        so = io.TextIOWrapper(bufferw, encoding='ascii')
        si = io.TextIOWrapper(bufferr, encoding='ascii', errors='replace')
    except Exception as e:
        print(e.msg)
    try:
        while True:
            if strip_ln_telnet:
                str_ = si.readline().rstrip("\n")
                
                if len(str_) == 0:
                    continue

            print("[{}] : {}".format(state, str_))

            if state == "start":
                print("copy sending IMAGE file over ssh to {}".format(scp_target))
                call(["scp", "-P", "2022", SYSIMAGE, scp_target])
                sysimage_file = SYSIMAGE.split("/")[-1]
                command_ = "sysupgrade /tmp/{}\n".format(sysimage_file)
                print(command_)
                so.write(command_)
                so.flush()
                state = "upgrading"
                strip_ln_telnet = True

            elif state == "upgrading":

                if ("Starting kernel ..." in str_):
                    print("\n\nUpgrade is done!!")
                    print("\n\nInstalling application in 15 seconds!!")
                    state = "install_app"
                    strip_ln_telnet = False
                    time.sleep(15)
            elif state == "install_app":
                print("copy sending APPLICATION file over ssh to {}".format(scp_target))
                call(["scp", "-P", "2022", PACKAGE_HELLOWORLD, scp_target])
                package_file = PACKAGE_HELLOWORLD.split("/")[-1]
                so.write("opkg install /tmp/{}".format(PACKAGE_HELLOWORLD))
                so.flush()
                strip_ln_telnet = True
                state = "installing"
            elif state == "installing":
                if "Configuring" in str_:
                    time.sleep(2)
                    state = "checking_install"
                    start_time = time.time()
                
            elif state == "checking_install":
                if time.time() - start_time > 30:
                    print("We waited for too long, there is a problem")
                    print("RIL: {}".format(ril_ok))
                    print("RDB: {}".format(rdb_ok))
                    print("I2C: {}".format(i2c_read_ok))
                    exit(1)
                if "[RDB] [info] Advertising" in str_:
                    print("RDB advertising ok")
                    rdb_ok = True
                if "[RIL] [info] Deadline in" in str_:
                    print("RIL runing!")
                    ril_ok = True
                if "[I2C] [info] WT Read" in str_:
                    print("I2C read ok!")
                    i2c_read_ok = True
                if rdb_ok and ril_ok and i2c_read_ok:
                    print("All ok!")
                    state="stop_app"
                

            elif state == "stop_app":
                
                print("sending CTRL-C to application")
                so.write('\x03')
                so.flush()
                state = "quit_app"
                start_time = time.time()

            elif state == "quit_app":
                if time.time() - start_time > 10:
                    print("We waited for too long, the app did not quit")
                    exit(1)
                
                
                if "[RIL] [error] Event loop terminated" in str_:
                    print("application quit ok")
                    state="done"

            elif state == "done":
                exit(0)
    except Exception as e:
        print(e.msg)
