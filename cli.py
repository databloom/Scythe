#!/usr/local/bin/python

import magic
import json
from json import JSONDecoder
import os
import elasticsearch
# import bz2
import gzip
import shutil
from threading import Thread
import multiprocessing
import psutil
import decimal

es = elasticsearch.Elasticsearch()  # use default of localhost, port 9200

es.indices.delete(index='testfsobj', ignore=[400, 404])

meta = {}
mymetapieces = []



def indexcompress(i, base, name):
    gzipcompressedsize = 0
    # print("files:", os.path.join(base, name))
    fullfilepath = os.path.join(base, name)
    mymagicstring = magic.from_buffer(open(fullfilepath).read(1024))
    filesize = os.path.getsize(os.path.join(base, name))
    meta['path'] = os.path.join(base, name)
    mymetapieces = {'path': fullfilepath, 'magicident': mymagicstring, 'filesize': filesize,
                    'gzipcompressedsize': gzipcompressedsize}
    # print ("Found thread", i, fullfilepath,json.dumps(mymetapieces))
    gzipcompressname = os.path.join(base, name + ".compressiontest.gzip")
    with open(fullfilepath, 'rb') as f_in, gzip.open(gzipcompressname, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    gzipcompressedsize = os.path.getsize(gzipcompressname)
    spacesavingsgzip = filesize - gzipcompressedsize
    if gzipcompressedsize > 0:
        compressionratio_gzip = filesize / gzipcompressedsize
    filenamesuffix = ""
    filenamesuffix = os.path.splitext(name)[1]
    mymetapieces = {'path': fullfilepath, 'magicident': mymagicstring, 'filesize': filesize,
                    'gzipcompressedsize': gzipcompressedsize, 'compressionratio_gzip': compressionratio_gzip,
                    'spacesavingsgzip': spacesavingsgzip, 'filenamesuffix': filenamesuffix}
    # print("Compressing thread ", i, gzipcompressname, mymetapieces)
    es.index(index='testfsobj', doc_type='message', id=meta['path'], body=mymetapieces)
    # print("Indexing files and uploading compression numbers for: thread ",i,  gzipcompressname, mymetapieces)
    os.remove(gzipcompressname)
    # print("Removed temp file thread ",i,gzipcompressname)


def cleanupmygzip(i, base, name):
    gzipcompressname = os.path.join(base, name + ".compressiontest.gzip")
    os.remove(gzipcompressname)
    # print ("Deleted ", gzipcompressname)


filecount = 0
if 1:
    for base, subdirs, files in os.walk('testdata'):
        for name in files:
            if name.endswith('.compressiontest.gzip'):
                print("ignore")
            else:
                filecount = filecount + 1

#print("filecount", filecount)

processcount = 0
# find contenders for compression and queue up for threaded compression
if 1:
    # for base, subdirs, files in os.walk('/dlink/action'):
    for base, subdirs, files in os.walk('testdata'):
        for name in files:
            if name.endswith('.compressiontest.gzip'):
                for i in range(psutil.cpu_count()):
                    t = Thread(target=cleanupmygzip, args=(i, base, name))
                    t.start()
            else:
                # print("Cores available", psutil.cpu_count())
                processcount = processcount + 1
            #procdec = decimal.Decimal(processcount)
            #totaldec = decimal.Decimal(filecount)
            #float.getcontext().prec = 3
            procdec = float(processcount)
            totaldec = float(filecount)

            progress = (procdec / totaldec * 100)
            if progress:
                print progress, "% Complete"
                #print("filecount ", filecount);
            for i in range(1):
                t = Thread(target=indexcompress, args=(i, base, name))
                t.start()  # find compressed files from previous runs and delete

if 0:

    #       for base, subdirs, files in os.walk('/dlink/action'):
    for base, subdirs, files in os.walk('testdata/'):
        for name in files:
            if name.endswith('.compressiontest.gzip'):
                # print("Cores available", psutil.cpu_count())
                for i in range(1):
                    t = Thread(target=cleanupmygzip, args=(i, base, name))
                    t.start()
