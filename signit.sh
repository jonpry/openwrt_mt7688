#!/bin/sh
mkdir -p work/contents
rm work/* -f -R
mkdir -p work/contents/control
mkdir -p work/contents/data
rm signed.ipk

filename=$(basename -- "$1")
cp $1 ./work/$filename.gz
gzip -d ./work/$filename.gz
tar xf ./work/$filename -C ./work/contents
tar zxf ./work/contents/control.tar.gz -C ./work/contents/control
tar zxfp ./work/contents/data.tar.gz -C ./work/contents/data
mkdir -p work/contents/data/etc
cd work/contents/data
hash=$(find -type f | xargs sha256sum)
cd ../../..
echo "$hash" > foo.sums
sha256sum ./foo.sums | cut -d' ' -f1 >> foo.sums 
cp foo.sums ./work/contents/data/etc/helloworld.sig
find ./work/contents/data -exec touch {} \;

tar zcfv ./work/contents/data.tar.gz -C ./work/contents/data .
#tar zcfv --atime-preserve ./work/contents/data.tar.gz -C ./work/contents/data .


rm ./work/contents/data -R -f
rm ./work/contents/control -R -f
tar zcf ./signed.ipk -C ./work/contents/ .
rm -R -f work
rm foo.sums
