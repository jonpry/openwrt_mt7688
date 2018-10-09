#!/bin/bash
./scripts/feeds update
cp package/feeds/stel/helloworld/openocd_makefile.txt
package/feeds/packages/openocd/Makefile
./scripts/feeds install -a
cp ./SGD-def.config .config
cat .config | grep cares
cp -R package/feeds/stel/helloworld/files .
cd feeds/stel/netresolve/src
./autogen.sh
cd ../../../..
make -j16
