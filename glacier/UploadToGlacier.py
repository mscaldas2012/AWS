#!/bin/bash
import boto3
import sys
import os
import shutil

def split_file(file, prefix, max_size, buffer=1024):
    """
    file: the input file
    prefix: prefix of the output files that will be created
    max_size: maximum size of each created file in bytes
    buffer: buffer size in bytes

    Returns the number of parts created.
    """
    with open(file, 'r+b') as src:
        suffix = 0
        while True:
            with open(prefix + '.%s' % suffix, 'w+b') as tgt:
                written = 0
                while written < max_size:
                    data = src.read(buffer)
                    if data:
                        tgt.write(data)
                        written += buffer
                    else:
                        return suffix
                suffix += 1


def cat_files(infiles, outfile, buffer=1024):
    """
    infiles: a list of files
    outfile: the file that will be created
    buffer: buffer size in bytes
    """
    with open(outfile, 'w+b') as tgt:
        for infile in sorted(infiles):
            with open(infile, 'r+b') as src:
                while True:
                    data = src.read(buffer)
                    if data:
                        tgt.write(data)
                    else:
                        break


def prepareFiles(fileName, TEMP_FOLDER, PART_SIZE):
  # craete directory:
  dir = os.path.dirname(TEMP_FOLDER);
  if not os.path.exists(dir):
    os.mkdir(TEMP_FOLDER);

  #copy the zip file into new directory for splitting:
  #shutil.copy(fileName +".zip", TEMP_FOLDER)
  split_file(fileName + ".zip", TEMP_FOLDER + "/archive_" + fileName, PART_SIZE)


def uploadToGlacier():
  # Variables:
  fileName = sys.argv[1];

  TEMP_FOLDER = "archive_" + fileName
  VAULT = "photos"
  PART_SIZE = 134217728

  # main method:
  #prepareFiles(fileName, TEMP_FOLDER, PART_SIZE)
  glacier = boto3.client('glacier')

  startMultipart = glacier.initiate_multipart_upload(
    vaultName = VAULT,
    archiveDescription = "Backup photos for " + fileName,
    partSize = str(PART_SIZE)
  )
  uploadId = startMultipart.get("uploadId")
  print(uploadId)
  start = 0
  end = 0
  total = 0
  fullChecksum = "";
  splitfiles = [ f for f in os.listdir(TEMP_FOLDER) if os.path.isfile(os.path.join(TEMP_FOLDER,f)) ]
  for file in splitfiles:
    in_file = open(TEMP_FOLDER + "/" + file, "rb")
    #last file might be smaller:
    if (os.path.getsize(TEMP_FOLDER + "/" +file) < PART_SIZE):
      end = start + os.path.getsize(TEMP_FOLDER + "/" +file)
    else:
      end = start + PART_SIZE
    
    response = glacier.upload_multipart_part(
      vaultName = VAULT,
      uploadId = uploadId,
      range="bytes " + str(start) +"-" + str(end-1) + "/*",
      body=in_file.read()
    )
    fullChecksum += str(response.get("checksum"))
    in_file.close()
    print ("uploaded " + file + "[" + str(start) + "-" + str(end) + "]")
    start = end

  endMultipart = glacier.complete_multipart_upload(
     vaultName = VAULT,
     uploadId = uploadId,
     archiveSize= str(end),
     checksum = fullChecksum
  )
  print(endMultipart)
  print("ArchiveId: " + endMultipart.get("archiveId"))


  #glacier.abort_multipart_upload(
  #   vaultName = VAULT,
  #   uploadId = response.get("uploadId")
  #)


uploadToGlacier()