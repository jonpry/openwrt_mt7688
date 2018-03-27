#!/usr/bin/python3
from telnetlib import Telnet
import sys
from subprocess import call
import io
import os
import time

def print_help():
    print("""Usage : launch_valgrind.py <target pi IP>""")

### Constants
HELLOWORLD_PATH = "./package/feeds/stel/helloworld/src/"

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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
    dev_ip = sys.argv[1]
    ssh_target = "root@{}".format(dev_ip)
    scp_target = "{}:/tmp".format(ssh_target)
    wait_for_ssh(dev_ip)
    
    print("Telnet Connect from rapberryPi  {}, port {}".format(dev_ip, PORT))
    telnet_con = Telnet(dev_ip, str(PORT))
    socket = telnet_con.get_socket()
    tfile = socket.makefile('rwb', buffering=0)
    bufferr = io.BufferedReader(tfile)
    bufferw = io.BufferedWriter(tfile)
    state = "start"

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

            if "Port already in use" in str_:
                print("Close other telnet access to {} before running this script".format(dev_ip))
                exit(1)
            if state == "start":
                root_path = os.getcwd()
                if not os.path.isdir(HELLOWORLD_PATH):
                    print("""The path {} is not an existing directory,
                    you should run this script from the root folder of the project,
                    you are currently here: {}""".format(HELLOWORLD_PATH, root_path))
                    exit(1)
                wait_for_ssh(dev_ip)
                state = "compile"

            elif state == "compile":
                bin_path = HELLOWORLD_PATH+"helloworld"
                
                print("deleting previous binaries")
                call(["ls", HELLOWORLD_PATH])
                
                os.chdir(HELLOWORLD_PATH)
                call(["ls", HELLOWORLD_PATH])
                
                print("building")
                call(["sh", "./cross.sh"])
                os.chdir(root_path)
                if not os.path.isfile(bin_path):
                    print("""the file {} was not created, there was an error""")
                    exit(1)
                state = "copy"

            elif state == "copy":
                call(["scp", "-P", "2022", bin_path, scp_target])
                call(["ssh", "-p", "2022", ssh_target, "rm /mnt/debian/mnt/helloworld"])
                call(["ssh" ,"-p", "2022", ssh_target, "cp /tmp/helloworld /mnt/debian/mnt/; ls /mnt/debian/mnt/"])
                call(["ssh", "-p", "2022", ssh_target, "rm /mnt/debian/mnt/valgrind.log"])
                call(["ssh", "-p", "2022", ssh_target, "swapon /mnt/myswap"])
                state = "debian_launch"
 
            elif state == "debian_launch":
                strip_ln_telnet = True
                send_command_on_telnet_stream(so, "cd /mnt")
                send_command_on_telnet_stream(so, "sh ./launch.sh")
                send_command_on_telnet_stream(so, "ls ./mnt/")
                state = "valgrind"
            elif state == "valgrind":
                try:
                    send_command_on_telnet_stream(so, "valgrind --tool=memcheck --leak-check=full --time-stamp=yes --track-origins=yes --log-file=./mnt/valgrind.log -v ./mnt/helloworld")
                    
                    while True:
                        if strip_ln_telnet:
                            str_ = si.readline().rstrip("\n")
                            
                            if len(str_) == 0:
                                continue
                        print("[{}]: {}".format(state, str_))
                except KeyboardInterrupt as e:
                    print("Programm aborted by user, quiting valgrind")
                        
                    print("sending CTRL-C to application")
                    so.write('\x03')
                    so.flush()
                    send_command_on_telnet_stream(so, "exit")
                    state = "retrievelog"
            elif state == "retrievelog":
                strip_ln_telnet = False
                print("retrieving log")
                call(["rm", "./valgrind.log"])
                call(["scp", "-P", "2022", ssh_target+":/mnt/debian/mnt/valgrind.log", "./"])
                state = "done"
            elif state == "done":
                print("We are done with this run")
                exit(0)
    except Exception as e:
        print(e.msg)
