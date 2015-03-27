#!/usr/bin/env python
import urllib2,urllib, httplib, sys, re, os,json
from xml.dom.minidom import getDOMImplementation

def getdata():
        d=open('/afs/cern.ch/user/c/cmst2/www/mc/data.json').read()
        return json.loads(d)

def changePriorityWorkflow(url, workflow, priority):
	conn  =  httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
	params = {workflow+":status":"",workflow+":priority" : str(priority)}
    	headers={"Content-type": "application/x-www-form-urlencoded",
             "Accept": "text/plain"}
    	encodedParams = urllib.urlencode(params)
    	conn.request("PUT", "/reqmgr/view/doAdmin", encodedParams, headers)
    	response = conn.getresponse()	
    	print response.status, response.reason
    	data = response.read()
    	print data
    	conn.close()


def main():
	url='cmsweb.cern.ch'
	s = getdata()
	for i in s:
		if 'test' in i['requestname'].lower() or i['status'] not in ['assignment-approved']:
			continue
		newpriority = 0
		if 'STEP0ATCERN' in i['requestname'] and  i['priority'] < 150000:
			newpriority = 100000
		elif i['priority'] >= 63000:
			newpriority = i['priority']-50000
			if i['primaryds'].startswith('MinBias'):
				newpriority = newpriority + 1000

		if newpriority > 0:
			print "Remapping priority of %s from %s to %s" % (i['requestname'],i['priority'],newpriority)
			changePriorityWorkflow(url, i['requestname'], newpriority)
	sys.exit(0)

if __name__ == "__main__":
	main()
