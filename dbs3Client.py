#!/usr/bin/env python
"""

 DBS 3 Client
 Ports all the functionality from previously used
 dbsTest.py to use DBS3 directly.

"""


import urllib2,urllib, httplib, sys, re, os, json, datetime
from xml.dom.minidom import getDOMImplementation
from dbs.apis.dbsClient import DbsApi

#das_host='https://das.cern.ch'
das_host='https://cmsweb.cern.ch'
#das_host='https://cmsweb-testbed.cern.ch'
#das_host='https://das-dbs3.cern.ch'
#das_host='https://dastest.cern.ch'
dbs3_url = r'https://cmsweb.cern.ch/dbs/prod/global/DBSReader'


def duplicateRunLumi(dataset, verbose=False, skipInvalid=False):
    """
    checks if output dataset has duplicate lumis
    for every run.
    returns true if at least one duplicate lumi was found
    That is if there is the same lumi in the same run and
    two different files
    This can be used on datasets that have separate
    runs.
    Verbose: if true prints details
    skipInvalid: if true skips invalid files, by default is False because is faster
    """  
    dbsapi = DbsApi(url=dbs3_url)
    duplicated = False
    #check each run
    runs = getRunsDataset(dataset)
    #if only one run in the list
    if len(runs) == 1:
        if verbose:
            print "only one run:",runs
        return duplicateLumi(dataset, verbose, skipInvalid)
    #else manually
    for run in runs:
        #create a set
        lumisChecked={}
        # retrieve files for that run
        reply = dbsapi.listFiles(dataset=dataset, detail=skipInvalid)
        for f in reply:
            #skip invalid files
            if skipInvalid and f['is_file_valid'] != 1 :
                continue
            logical_file_name = f['logical_file_name']
            reply2 = dbsapi.listFileLumis(logical_file_name=logical_file_name, run_num=run)
            #retrieve lumis for each file
            if reply2:
                lumis = reply2[0]['lumi_section_num']
            else:
                continue
            #check that each lumi is only in one file
            for lumi in lumis:
                if lumi in lumisChecked:
                    #if verbose print results, if not end quickly
                    if verbose:
                        print 'Lumi',lumi,'in run',run,'is in these files'
                        print logical_file_name
                        print lumisChecked[lumi]
                        duplicated = True
                    else:
                        return True
                else:
                    lumisChecked[lumi] = logical_file_name

    return duplicated

def duplicateLumi(dataset, verbose=False, skipInvalid=False):
    """
    checks if output dataset has duplicate lumis
    returns true if at least one duplicate lumi was found
    Verbose: if true prints details
    skipInvalid: if true skips invalid files, by default is False because is faster
   """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)
    duplicated = False
    lumisChecked={}
    # retrieve files
    reply = dbsapi.listFiles(dataset=dataset, detail=skipInvalid)
    for f in reply:
        logical_file_name = f['logical_file_name']
        #skip invalid files
        if skipInvalid and f['is_file_valid'] != 1 :
            continue
        reply2 = dbsapi.listFileLumis(logical_file_name=logical_file_name)
        #retrieve lumis for each file
        lumis = reply2[0]['lumi_section_num']
        #check that each lumi is only in one file
        for lumi in lumis:
            if lumi in lumisChecked:
                #if verbose print results, if not end quickly
                if verbose:
                    print 'Lumi',lumi,'is in these files'
                    print logical_file_name
                    print lumisChecked[lumi]
                    duplicated = True
                else:
                    return True
            else:
                lumisChecked[lumi] = logical_file_name
    return duplicated


def getDatasetInfo(dataset):
    """
    Gets a summary of a dataset, returns a tuple with:
    ( Open for writing: 1 if at least one block is open for writing,
    creation date: the creation date of the first block,
    last modified: the latest modification date)
    """
    dbsapi = DbsApi(url=dbs3_url)
    reply = dbsapi.listBlocks(dataset=dataset, detail=True)
    if not reply:
        return (0,0,0)
    #first block
    max_last_modified = reply[0]['last_modification_date']
    min_creation_date = reply[0]['creation_date']
    open_for_writing = reply[0]['open_for_writing']
    #for all the blocks, get the details
    for block in reply:
        max_last_modified = max(max_last_modified, block['last_modification_date'])
        min_creation_date = min(min_creation_date, block['creation_date'])
        open_for_writing |= block['open_for_writing']
    return (open_for_writing, min_creation_date, max_last_modified)
    
def getMaxLumi(dataset):
    """
    Gets the number of the last lumi in a given dataset
    This is useful for appending new events to dataset
    without collision
    """
    dbsapi = DbsApi(url=dbs3_url)
    reply = dbsapi.listBlocks(dataset=dataset)
    maxl = 0
    for b in reply:
        reply2 = dbsapi.listFileLumis(block_name=b['block_name'])
        #retrieve lumis for each file
        for f in reply2:
            lumis = f['lumi_section_num']
            #check max of lumi
            lumi = max(lumis)
            if lumi > maxl:
                maxl = lumi
    return maxl   


def getRunsDataset(dataset):
    """
    returns a list with number of each run.
    """
    dbsapi = DbsApi(url=dbs3_url)
    # retrieve runs
    reply = dbsapi.listRuns(dataset=dataset)
    #a list with only the run numbersT3_US_Omaha
    runs = []
    #filter and clean
    for run in reply:
        if type(run['run_num']) is list:
            runs.extend(run['run_num'])
        else:
            runs.append(run['run_num'])
    return runs

def getNumberofFilesPerRun(das_url, dataset, run):
    """
    Count number of files
    """
     # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)

    # retrieve file list
    reply = dbsapi.listFiles(dataset=dataset)
    return len(reply)


def getFileCountDataset(dataset):
    """
    Returns the number of files registered in DBS3
    """
     # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)

    # retrieve file list
    reply = dbsapi.listFiles(dataset=dataset)
    return len(reply)



def getEventCountDataSet(dataset):
    """
    Returns the number of events in a dataset using DBS3

    """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)
    # retrieve dataset summary
    reply = dbsapi.listBlockSummaries(dataset=dataset)
    if not reply:
        return 0
    return reply[0]['num_event']


def getLumiCountDataSet(dataset):
    """
    Get the number of unique lumis in a dataset
    """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)
    # retrieve dataset summary
    reply = dbsapi.listFileSummaries(dataset=dataset)
    if not reply:
        return 0
    return reply[0]['num_lumi']


def getLumiCountDataSetBlockList(dataset, blockList):
    """
    Counts and adds all the lumis for a given lists
    blocks inside a dataset
    """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)
    #transform from strin to list
    if type(blockList) in (str, unicode):
        blockList = eval(blockList)
    total = 0
    #get one by one block and add it so uri wont be too large
    for block in blockList:
        reply = dbsapi.listFileSummaries(block_name=block)
        total += reply[0]['num_lumi']
    return total
    


def hasAllBlocksClosed(dataset):
    """
    checks if a given dataset has all blocks closed
    """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)
    # retrieve dataset summary
    reply = dbsapi.listBlocks(dataset=dataset, detail=True)
    for block in reply:
        #print block['block_name']
        #print block['open_for_writing']
        if block['open_for_writing']:
            return False
    return True


def getEventCountDataSetBlockList(dataset,blockList):
    """
    Counts and adds all the events for a given lists
    blocks inside a dataset
    """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)    
    #transform from strin to list
    if type(blockList) in (str, unicode):
        blockList = eval(blockList)
    total = 0
    #get one by one block and add it so uri wont be too large
    for block in blockList:
        reply = dbsapi.listBlockSummaries(block_name=block)
        total += reply[0]['num_event']
    return total

def getEventCountDataSetFileList(dataset,fileList):
    """
    Counts and adds all the events for a given lists
    blocks inside a dataset
    """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)    
    #transform from strin to list
    if type(fileList) in (str, unicode):
        fileList = eval(fileList)
    total = 0
    #get one by one block and add it so uri wont be too large
    for f in fileList:
        reply = dbsapi.listFiles(logical_file_name=f, detail=True)
        total += reply[0]['event_count']
    return total


def getEventCountDataSetRunList(dataset,runList):
    """
    Counts and adds all the events for a given lists
    of runs inside a dataset
    """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)
    # retrieve file aggregation only by the runs
    #transform from strin to list
    if type(runList) in (str, unicode):
        runList = eval(runList)
    total = 0
    #get one by one run, so URI wont be too large
    for run in runList:
        reply = dbsapi.listFileSummaries(dataset=dataset,run_num=run)
        if reply:
            total += reply[0]['num_event']
    return total

def getLumiCountDataSetRunList(dataset,runList):
    """
    Counts and adds all the lumis for a given lists
    of runs inside a dataset
    """
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)
    # retrieve file aggregation only by the runs
    #transform from strin to list
    if type(runList) in (str, unicode):
        runList = eval(runList)
    total = 0
    #get one by one run, so URI wont be too large
    for run in runList:
        reply = dbsapi.listFileSummaries(dataset=dataset,run_num=run)
        if reply:
            total += reply[0]['num_lumi']
    return total

def getDatasetSize(dataset):
    # initialize API to DBS3
    dbsapi = DbsApi(url=dbs3_url)
    # retrieve file aggregation only by the runs
    #transform from strin to list
    reply = dbsapi.listBlockSummaries(dataset=dataset)
    return reply[0]['file_size']

def main():
    args=sys.argv[1:]
    if len(args) < 1:
        print "usage:dbs3Client dataset dataset2 ..."
        sys.exit(0)
    workflow=args[0]
    url='cmsweb.cern.ch'
    datasets = args
    for dataset in datasets:
        print dataset
        print " Events:", getEventCountDataSet(dataset)
        print " Lumis:", getLumiCountDataSet(dataset)
        info = getDatasetInfo(dataset)
        print " Open Blocks: ", info[0]
        print " Creation:", datetime.datetime.fromtimestamp(info[1]).strftime('%Y-%m-%d %H:%M:%S')
        print " Last update:", datetime.datetime.fromtimestamp(info[2]).strftime('%Y-%m-%d %H:%M:%S')
        #print " Duplicated Lumis:", duplicateRunLumi(dataset)
        #print " Duplicated Lumis:", duplicateLumi(dataset)
        #print " Runs", getRunsDataset(dataset))
        #print " Blocks", hasAllBlocksClosed(dataset)
        #print " blockEvents", getEventCountDataSetBlockList(dataset,blocklist)
        
    sys.exit(0);

if __name__ == "__main__":
    main()
    sys.exit(0);
