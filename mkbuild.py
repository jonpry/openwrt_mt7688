#!/usr/bin/python
import subprocess
from datetime import date
import requests

subprocess.call("objcopy -I ihex /home/jon/zephyr.hex -O binary zephyr.bin", shell=True)
zhash = subprocess.check_output("strings zephyr.bin | grep zephyr", shell=True).split("\n")[0].split("-g")[1].split(" ")[0]

print "Zephyr hash: " + zhash
subprocess.call("cd feeds/stel && git pull", shell=True)
hhash = subprocess.check_output("cd feeds/stel && git rev-parse HEAD", shell=True)[:7]

print "Helloworld hash: " + hhash

sw_ver = subprocess.check_output("grep HELLOWORLD_VERSION feeds/stel/helloworld/src/Makefile | head -n 1", shell=True).split("=")[1].split("\"")[1]

print "Helloworld version: " + sw_ver

subprocess.call("make package/helloworld/compile -j16", shell=True)
subprocess.call("./signit.sh bin/packages/mipsel_24kc/stel/helloworld_1_mipsel_24kc.ipk", shell=True)

subprocess.call("cp /home/jon/zephyr.hex /mnt2/builds/deploy/", shell=True)
subprocess.call("cp /home/jon/zephyr.hex /mnt2/builds/deploy/auto_update", shell=True)

subprocess.call("cp signed.ipk /mnt2/builds/deploy/", shell=True)
subprocess.call("cp signed.ipk /mnt2/builds/deploy/auto_update", shell=True)

subprocess.call("cd /mnt2/builds/deploy && tar cz auto_update > auto_update.tgz", shell=True)

prefix = date.today().strftime("%Y%m%d") + "-v" + sw_ver
print "Prefix: " + prefix

subprocess.call("mkdir /mnt2/builds/" + prefix, shell=True)
subprocess.call("cp /mnt2/builds/deploy/* /mnt2/builds/" + prefix + "/ -R", shell=True)

url = 'https://10.9.8.1/api/create_ver'
files = {'file': open('/mnt2/builds/deploy/auto_update.tgz', 'rb')}
values = {'nrf': zhash, 'helloworld' : hhash, 'version': sw_ver}
r = requests.request('POST', url, files=files, data=values, verify=False)
print r
print r.text
