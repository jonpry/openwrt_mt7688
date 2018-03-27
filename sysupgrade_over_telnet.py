"""sysupgrade_over_telnet
   Returns the Virtual IP of a device in STDERR 
   to chain with bash use `python3 get_ip_ssh.py 2> my_script`
Usage:
    sysupgrade_over_telnet.py [--verbose | --quiet] [--logfile FILE] <ip> [--skip-sysup] [--bin FILE] [--ipk FILE]
    sysupgrade_over_telnet.py (-h | --help)
    sysupgrade_over_telnet.py --version

Options:
    -h --help         Show this screen.
    --version         Show version.
    --logfile FILE    specify output file [default: ./log.txt]
    --skip-sysup      To only apply helloworld update
    --bin             Specify BIN file to use (ignored if --skip-sysup)
    --ipk             Specify IPK file
    --verbose         Verbose (logger level is debug, instead of info)
    --quiet           Verbose (logger level is warning, instead of info)
"""
#!/usr/bin/python3
from telnetlib import Telnet
import sys
from subprocess import call
import io
import time
from docopt import docopt
import logging

logger = logging.getLogger(__name__)

def print_help():
    print("""Usage : sysupgrade_over_telnet <target pi IP> [--skip-sysup]
    --skip-sysup to skip susupgrade and only run package install""")
### Constants
GLIBC = False
if GLIBC:
    SYSIMAGE="bin/targets/ramips/mt76x8-glibc/openwrt-ramips-mt76x8-wrtnode2r-squashfs-sysupgrade.bin"
    PACKAGE_HELLOWORLD="bin/packages/mipsel_24kc/stel/helloworld_1_mipsel_24kc.ipk"
else:
    SYSIMAGE="bin/targets/ramips/mt76x8/openwrt-ramips-mt76x8-wrtnode2r-squashfs-sysupgrade.bin"
    PACKAGE_HELLOWORLD="bin/packages/mipsel_24kc/stel/helloworld_1_mipsel_24kc.ipk"
    
PORT = 7000

def send_command_on_telnet_stream(stream, command_):
    print("sending command over telnet: {}".format(command_))
    stream.write("\n{}\n".format(command_))
    stream.flush()
                

def wait_for_ssh(ip):

    script = """#!/usr/bin/bash
echo "Wait for SSH on {target}"
while ! nc -z {ip} {port}; do   
    sleep 0.5 # wait for 1/10 of the second before check again
    echo "waiting for SSH on {target}"
done
echo "SSH available on {target}"
""".format(ip=ip, port="2022", target="{}:{}".format(ip, "2022"))
    sf = open("/tmp/wait_ssh.sh", 'w')
    # print("Executing script\n{}\n\n".format(script))
    sf.write(script)
    sf.flush()
    sf.close()
    call(["sh", "/tmp/wait_ssh.sh"])




logger = logging.getLogger(__name__)

if __name__ == '__main__':
    arguments = docopt(__doc__, version='STEL get connection info V0.^')

    print(arguments)
    dev_ip = arguments['<ip>']
    logfile = arguments['--logfile']
    skip_sysupgrade = arguments['--skip-sysup']
    appipk = arguments['--ipk']
    imagebin = arguments['--bin']
    if appipk is None:
        appipk = PACKAGE_HELLOWORLD
    if imagebin is None:
        imagebin = SYSIMAGE
    lv = logging.INFO
    if arguments['--verbose']:
        lv = logging.DEBUG
    elif arguments['--quiet']:
        lv = logging.WARNING
    logging.basicConfig(level=lv,
                        format='%(name)s [%(levelname)s] - %(message)s')


    scp_target = "root@{}:/tmp".format(dev_ip)
    wait_for_ssh(dev_ip)
    
    print("Telnet Connect from rapberryPi  {}, port {}".format(dev_ip, PORT))
    state = "start"
    telnet_con = Telnet(dev_ip, str(PORT))
    socket = telnet_con.get_socket()
    tfile = socket.makefile('rwb', buffering=0)
    bufferr = io.BufferedReader(tfile)
    bufferw = io.BufferedWriter(tfile)
    i2c_read_ok = False
    ril_ok = False
    # rdb_ok = False
    start_time = None
    app_ckeck_ok = False
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

            if "Port already in use" in str_:
                print("Close other telnet access to {} before running this script".format(dev_ip))
                exit(1)
            if state == "start":
                wait_for_ssh(dev_ip)
                if skip_sysupgrade:
                    print("Skipping System upgrade because of {}".format(sys.argv[2]))
                    state = "waiting_before_install"
                    start_time = time.time()
                    continue
                print("copy sending IMAGE file over ssh to {}".format(scp_target))

                call(["scp", "-P", "2022", imagebin, scp_target])
                sysimage_file = imagebin.split("/")[-1]
                command_ = "sysupgrade /tmp/{}".format(sysimage_file)
                send_command_on_telnet_stream(so, command_)
                state = "upgrading"
                strip_ln_telnet = True

            elif state == "upgrading":

                if ("Starting kernel ..." in str_):
                    print("\nUpgrade is done!!")
                    print("\n\nWaiting to install application!!")
                    state = "waiting_before_install"
                    start_time = time.time()
            elif state == "waiting_before_install":
                wait_for_ssh(dev_ip)
                if time.time()-start_time > 120:
                    print("ERROR: SSH never detecting, quiting install, sysupgrade done, install app failed")
                    exit(1) 
                state = "install_app"
                strip_ln_telnet = False
            elif state == "install_app":
                print("copy sending APPLICATION file over ssh to {}".format(scp_target))
                call(["scp", "-P", "2022", appipk, scp_target])
                package_file = appipk.split("/")[-1]
                command_ = "opkg remove helloworld"
                send_command_on_telnet_stream(so, command_)
                command_ = "opkg install /tmp/{}".format(package_file)
                send_command_on_telnet_stream(so,command_)
                strip_ln_telnet = True
                state = "installing"
            elif state == "installing":
                if "is up to date" in str_ or "Configuring" in str_:
                    time.sleep(2)
                    state = "checking_install"
                    start_time = time.time()
                    command_ = "helloworld"
                    send_command_on_telnet_stream(so, command_)
                
            elif state == "checking_install":
                if time.time() - start_time > 60:
                    print("We waited for too long, there is a problem")
                    print("RIL: {}".format(ril_ok))
                    # print("RDB: {}".format(rdb_ok))
                    print("I2C: {}".format(i2c_read_ok))
                    state = "stop_app"
                # if "[RDB] [info] Advertising" in str_:
                #     print("RDB advertising ok")
                #     rdb_ok = True
                if "[RIL] [info] Deadline in" in str_:
                    print("RIL runing!")
                    ril_ok = True
                if "[I2C] [info] WT Read" in str_:
                    print("I2C read ok!")
                    i2c_read_ok = True
                if ril_ok and i2c_read_ok:
                    print("All ok!")
                    app_ckeck_ok = True
                    state = "stop_app"
                
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
                    state = "done"

            elif state == "done":
                if app_ckeck_ok:
                    print("the app check RIL ({}), I2C ({})".format(ril_ok, i2c_read_ok))
                exit(0)
    except Exception as e:
        print(e.msg)
