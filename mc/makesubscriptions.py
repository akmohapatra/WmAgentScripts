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
from xml.dom.minidom import getDOMImplementation

#TODO set printlog
#TODO modify getdata: no closeout if no subscription
#TODO recycle tape families

minfreemss = 500
testmode=0
autoapprovelist = ['T2_CH_CERN','T2_IT_Bari' ,'T2_IT_Legnaro' ,'T2_IT_Pisa' ,'T2_IT_Rome' ,'T1_IT_CNAF','T2_ES_CIEMAT','T2_ES_IFCA','T2_EE_Estonia','T2_US_Wisconsin','T1_UK_RAL','T3_US_Colorado']

def createXML(datasets):
        # Create the minidom document
        impl=getDOMImplementation()
        doc=impl.createDocument(None, "data", None)
        result = doc.createElement("data")
        result.setAttribute('version', '2')
        # Create the <dbs> base element
        dbs = doc.createElement("dbs")
        #dbs.setAttribute("name", "https://cmsdbsprod.cern.ch:8443/cms_dbs_prod_global_writer/servlet/DBSServlet")
        dbs.setAttribute("name", "https://cmsweb.cern.ch/dbs/prod/global/DBSReader")
        result.appendChild(dbs)
        #Create each of the <dataset> element
        for datasetname in datasets:
                dataset=doc.createElement("dataset")
                dataset.setAttribute("is-open","y")
                dataset.setAttribute("is-transient","y")
                dataset.setAttribute("name",datasetname)
                dbs.appendChild(dataset)
        #print result.toprettyxml(indent="  ")
        return result.toprettyxml(indent="  ")

def phedex_call(call,params):
	global testmode
	if testmode:
		print "phedex_call -> call: %s params: %s" % (call,params)
		return 0
	conn  =  httplib.HTTPSConnection('cmsweb.cern.ch', cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
	conn.connect()
      	conn.request("POST", "/phedex/datasvc/json/prod/%s" % call, params)
        response = conn.getresponse()
        a = response.read()
        if response.status != 200:
                print a
		print response.status, response.reason
		print response.msg
		sys.exit(1)
        b = json.loads(a)
	#print json.dumps(b,indent=4)
	return b

def human(n):
	if n<1000:
		return "%s" % n
	elif n>=1000 and n<1000000:
		order = 1
	elif n>=1000000 and n<1000000000:
		order = 2
	elif n>=1000000000 and n<1000000000000:
		order = 3
	else:
		order = 4

	norm = pow(10,3*order)

	value = float(n)/norm

	letter = {1:'k',2:'M',3:'G',4:'T'}
	return ("%.1f%s" % (value,letter[order])).replace(".0", "")

# Main
def main():
	global minfreemss,testmode
	mcdir = '/afs/cern.ch/user/c/cmst2/www/mc'
	cmsweb='cmsweb.cern.ch'

        d=open('%s/uplinks.json' % mcdir).read()
	uplinks=json.loads(d)

        d=open('%s/whitelist.json' % mcdir).read()
	whitelist=json.loads(d)
	for i in range(0,len(whitelist)):
		if 'T1_' in whitelist[i]:
			whitelist[i]="%s_Disk"%whitelist[i]

        d=open('%s/disktape.json' % mcdir).read()
	disktape=json.loads(d)

	d=open('%s/data.json' % mcdir).read()
	s = json.loads(d)

	print
	if testmode:
		print "*** TESTMODE ***"
	print "Whitelist: %s" % (whitelist)
	print "Autoapprove: %s" % (autoapprovelist)

        nodelist = []
        autonodelist = []
        for i in whitelist:
                if i in autoapprovelist:
                        autonodelist.append(i)
                else:
                        nodelist.append(i)

	ocust = {}
	for site in disktape.keys():
		if 'freemss' not in disktape[site].keys():
			continue
		if disktape[site]['freemss'] < minfreemss:
			print "Skipping %s having %sTB < %sTB" % (site, disktape[site]['freemss'], minfreemss)
			continue
		ocust[site] = disktape[site]['freemss']
	print "Available MSS resources: %s" % ocust
	ocust = sorted(ocust.items(), key=lambda x: x[1],reverse=True)
	print "Ordering MSS resources: %s (number: %s)" % (ocust,len(ocust))
	while len(ocust) > 5:
		print "Reducing to TOP5: removing %s" % (ocust[-1][0])
		ocust.pop()
	ocust = map(list,zip(*ocust))[0]
	print "Using MSS resources: %s (number: %s)" % (ocust,len(ocust))
	print
	
	newsubscr = {}
	for i in ocust:
		newsubscr[disktape[i]['mss']] = []
	for r in s:
		if r['requestname'] == 'pdmvserv_TOP-Summer12pLHE-00096_00146_v0_STEP0ATCERN_150201_201447_7174':
			print json.dumps(r,indent=4)
		if r['status'] in ['acquired','running-open','running-closed','completed','closed-out'] and r['custodialsites'] == [] and 'events' in r['outputdatasetinfo'][0]:
			print "%s -> %s" % (r['requestname'],r['outputdatasetinfo'][0]['name'])
			if r['expectedevents'] > 0:
				eperc = 100*r['outputdatasetinfo'][0]['events'] / r['expectedevents']
				if eperc > 10 and 'backfill' not in r['outputdatasetinfo'][0]['name'].lower() and 'test' not in r['outputdatasetinfo'][0]['name'].lower():
					params = urllib.urlencode({ "dataset" : r['outputdatasetinfo'][0]['name']})
					rr = phedex_call('requestlist',params)
					if (rr != 0 and rr['phedex']['request'] == []) or testmode:
						if not testmode:
							print "No PhEDEx subscription"
						else:
							print "Pretending that no subscription is in place"
						msslist = ocust[:]
						for site in r['sites']:
							if 'T1' in site or 'T0' in site:
								continue
							if 'T2_CH_CERN' in site:
								realsite = 'T2_CH_CERN'
							else:
								realsite = site
							if realsite not in uplinks.keys():
								print "No uplinks found for %s" % realsite
								continue
							for u in ocust:
								if disktape[u]['mss'] not in uplinks[realsite] and site in msslist:
									print "%s has no uplink to %s, removed" % (u,realsite)
									msslist.remove(u)
						minlen = 1000000
						posminlen = 0
						best = ''
						for i in msslist:
							if len(newsubscr[disktape[i]['mss']]) < minlen:
								minlen = len(newsubscr[disktape[i]['mss']])
								best = disktape[i]['mss']
						if 'HIN' in r['prepid']:
							print "HIN request -> forced to IN2P3" 
							if disktape['IN2P3']['mss'] not in newsubscr.keys():
								newsubscr[disktape['IN2P3']['mss']] = []
							newsubscr[disktape['IN2P3']['mss']].append(r['outputdatasetinfo'][0]['name'])
						elif best != '':
							print "Best MSS is %s" % best
							newsubscr[best].append(r['outputdatasetinfo'][0]['name'])
						else:
							print "Cannot match MSS!!"
							sys.exit(1)
					else:
						if not testmode:
							for rrr in rr['phedex']['request']:
								print "Subscription: https://cmsweb.cern.ch/phedex/prod/Request::View?request=%s" % rrr['id']
					
			print

	print "----------------------------------\n"
	gendatasets = []
	for i in newsubscr.keys():
		if len(newsubscr[i])==0:
			continue
		print "\n Custodial subscription to %s:" % i
		for d in newsubscr[i]:
			print "%s" % d
			if re.search('/GEN$',d):
				gendatasets.append(d)
		datasetXML = createXML(newsubscr[i])
		params = urllib.urlencode({"node" : i, "data" : datasetXML, "group": "DataOps", "priority":'low', "custodial":"y","request_only":"y" ,"move":"y","no_mail":"n", "comments":'Custodial subscription for MC datasets'})
		s = phedex_call('subscribe',params)
		if not testmode:
	        	print "https://cmsweb.cern.ch/phedex/prod/Request::View?request=%s" % s['phedex']['request_created'][0]['id']
	if gendatasets:
		print "\n Replicas for :"
		for i in gendatasets:
			print "%s" % i
		datasetXML = createXML(gendatasets)
		params = urllib.urlencode({"node" : nodelist, "data" : datasetXML, "group": "DataOps", "priority":'low', "custodial":"n","request_only":"y" ,"move":"n","no_mail":"n", "comments":'Custodial replica for MC datasets'},doseq=True)
		s = phedex_call('subscribe',params)
		if not testmode:
			print "https://cmsweb.cern.ch/phedex/prod/Request::View?request=%s" % s['phedex']['request_created'][0]['id']

		params = urllib.urlencode({"node" : autonodelist, "data" : datasetXML, "group": "DataOps", "priority":'low', "custodial":"n","request_only":"n" ,"move":"n","no_mail":"n", "comments":'Custodial replica for MC datasets'},doseq=True)
		s = phedex_call('subscribe',params)
		if not testmode:
			print "https://cmsweb.cern.ch/phedex/prod/Request::View?request=%s" % s['phedex']['request_created'][0]['id']

	print
        sys.exit(0)

if __name__ == "__main__":
        main()
