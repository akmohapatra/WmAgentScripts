#!/usr/bin/env python
import sys,urllib,urllib2,re,time,os
try:
    import json
except ImportError:
    import simplejson as json
import optparse
import httplib
import datetime
import time
import zlib 
import re

datasets = {}
actions = {}
requests = {}
mcdir = '/afs/cern.ch/user/c/cmst2/www/mc'

def printlog(msg):
	global mcdir
	ff=open('%s/lastweekannouncements.log' % mcdir,'a')
	ff.write("[%s] %s\n" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),msg))
	ff.close()
	ff=open('%s/announcements.log' % mcdir,'a')
	ff.write("[%s] %s\n" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),msg))
	ff.close()

def loadcampaignconfig(f):
        try:
                d = open(f).read()
        except:
                print "Cannot load config file %s" % f
                sys.exit(1)
        try:
                s = eval(d)
        except:
                print "Cannot eval config file %s " % f
                sys.exit(1)
        print "\nConfiguration loaded successfully from %s" % f
	#for c in s.keys():
	#	print "%s" % c
	#	for i in s[c]:
	#		print "\t%s\t%s" % (i,s[c][i])
        return s

def loadcheckedrequests(f):
        try:
                d = open(f).read()
        except:
                print "Cannot load checked requests file %s" % f
                sys.exit(1)
        try:
                s = d.split('\n')
                if '' in s:
                        s.remove('')
        except:
                print "Cannot eval checked requests file %s " % f
                sys.exit(1)
        print "\nchecked requests loaded successfully from %s" % f
        return s

def setReqStatus(workflowname,newstatus):
	printlog("SETREQUESTSTATUS %s %s RUN" % (workflowname,newstatus))
	conn  =  httplib.HTTPSConnection('cmsweb.cern.ch', cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
	headers={"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
	params = {"requestName" : workflowname,"status" : newstatus}
	encodedParams = urllib.urlencode(params)
	conn.request("PUT", "/reqmgr/reqMgr/request", encodedParams, headers)
	response = conn.getresponse()
	data = response.read()
	conn.close()
	printlog("SETREQUESTSTATUS %s %s DONE %s %s" % (workflowname,newstatus,response.status,response.reason))

def main():
	campaignconfig = loadcampaignconfig('/afs/cern.ch/user/c/cmst2/public/MCCONFIG/campaign.cfg')

	d=open('%s/data.json' % mcdir).read()
	s = json.loads(d)

	for r in s:
		if r['type'] in ['MonteCarloFromGEN','MonteCarlo','TaskChain'] and r['status'] == 'closed-out':
			print r['requestname']
			dataset = r['outputdatasetinfo'][0]['name']
			dataset_status = r['outputdatasetinfo'][0]['status']
			if dataset_status == 'VALID':
				setReqStatus(r['requestname'],'announced')

if __name__ == "__main__":
        main()
