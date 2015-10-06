#!/bin/sh

export PART_SIZE=128m
export FILE_NAME=$1.zip
export TEMP_FOLDER=archive_$1

mkdir $TEMP_FOLDER
cp $FILE_NAME $TEMP_FOLDER
cd $TEMP_FOLDER

split -b $PART_SIZE $FILE_NAME $1Photos_

rm -f $FILE_NAME
