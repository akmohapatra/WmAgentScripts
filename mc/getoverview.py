#!/usr/bin/env python -w
import sys,time,os,urllib,urllib2,re
try:
    import json
except ImportError:
    import simplejson as json
import httplib
import shutil
import time
import datetime
import zlib

# To use the cached overview:
#               d = open(cachedoverview).read()
#               s = eval(d)

overview = ''
cachedoverview = '/afs/cern.ch/user/c/cmst2/public/overview.cache'
cachedoverviewzipped = '/afs/cern.ch/user/c/cmst2/public/overview.cache.zipped'
	
def downloadoverview():
	global cachedoverview
	c = 1
	time.sleep(1)
	st = 30
	while c < 15:
		print "Connecting(%s)" % c
		try:
			conn  =  httplib.HTTPSConnection('cmsweb.cern.ch', cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'),timeout=30)
			# Broken after cmsweb upgrade on March 2, 2015.
                        #r1=conn.request("GET",'/wmstats/_design/WMStats/_view/requestByStatusAndType?stale=update_after')
                        # Use New Api
                        r1=conn.request("GET",'/couchdb/reqmgr_workload_cache/_design/ReqMgr/_view/bystatusandtype?stale=update_after')
		except:
			print "Cannot connect"
		try:
			r2=conn.getresponse()
		except:
			print "Cannot get response"
			c=c+1
			time.sleep(st)
			continue
		#r2=conn.getresponse()
		print r2.status, r2.reason
		if r2.status != 200:
			c=c+1
			time.sleep(5*c)
			continue
		print "Loading JSON"
		s = json.loads(r2.read())
		conn.close()
		if type(s) is list:
			if 'error_url' in s[0].keys():
				print "ERROR: %s\n" % s
				c=c+1
				time.sleep(st)
				continue
		break
	if s:
		print "Creating data" 
		now = time.time()
		reqs = []
		statuses = []
		for r in s['rows']:
			ret = {}
			ret['request_name'],ret['status'],ret['type'] = r['key']

			if ret['status'] == 'aborted-archived':
				ret['status'] = 'aborted'
			elif ret['status'] == 'normal-archived':
				ret['status'] = 'announced'
			elif ret['status'] == 'rejected-archived':
				ret['status'] = 'rejected'
			elif ret['status'] == 'testing-failed':
				continue
			elif ret['status'] == 'testing-approved':
				continue

			#print ret

			if not ret in reqs and ret['status'] not in ['aborted','rejected','announced','testing-failed','testing-approved']:
				reqs.append(ret)

		print " > %s" % (time.time()-now)
			
		print "Writing"
		now = time.time()
                output = open(cachedoverview, 'w')
                output.write("%s" % reqs)
                output.close()
		print "Uncompressed > %s" % (time.time()-now)
		now = time.time()
		comp = zlib.compress("%s" % reqs)
                output = open(cachedoverviewzipped, 'w')
                output.write("%s" % comp)
                output.close()
		print "Compressed > %s" % (time.time()-now)
		return reqs
	else:
		print "Cannot read json"
		sys.exit(2)

def main():
	global overview
	
	print datetime.datetime.utcnow()
	overview = downloadoverview()
	print datetime.datetime.utcnow()

if __name__ == "__main__":
        main()
