#!/usr/bin/env python
import urllib2,urllib, httplib, sys, re, os
import time
import datetime
import math

try:
    import json
except ImportError:
    import simplejson as json

minsites = 45
siteblacklist = ['T2_TH_CUNSTDA']
custodial = {'CERN':'T0_CH_CERN','FNAL':'T1_US_FNAL','CNAF':'T1_IT_CNAF','IN2P3':'T1_FR_CCIN2P3','RAL':'T1_UK_RAL','PIC':'T1_ES_PIC','KIT':'T1_DE_KIT'}


def get_linkedsites(custodial):
	global siteblacklist
	list = []
	if custodial == '':
		return []

	if custodial == 'T0_CH_CERN':
		ext = 'Export'
	else:
		ext= 'Buffer'

	#T2
	url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/links?status=ok&to=%s*%s&from=T2_*" % (custodial,ext)
	try:
		response = urllib2.urlopen(url)
	except:
		print "Cannot get list of linked T2s for %s" % custodial
		print "url = %s" % url
        	print 'Status:',response.status,'Reason:',response.reason
        	print sys.exc_info()
		sys.exit(1)

	j = json.load(response)["phedex"]
	for dict in j['link']:
		if dict['from'] not in siteblacklist:
			list.append(dict['from'])

	#T1
	url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/links?status=ok&to=%s*%s&from=T1_*_Disk" % (custodial,ext)
	try:
		response = urllib2.urlopen(url)
	except:
		print "Cannot get list of linked T1s for %s" % custodial
		print "url = %s" % url
        	print 'Status:',response.status,'Reason:',response.reason
        	print sys.exc_info()
		sys.exit(1)

	j = json.load(response)["phedex"]
	for dict in j['link']:
		t1 = dict['from'].replace('_Disk','')
		if t1 not in siteblacklist:
			list.append(t1)

	#T3
	url = "https://cmsweb.cern.ch/phedex/datasvc/json/prod/links?status=ok&to=%s*%s&from=T3_*" % (custodial,ext)
	try:
		response = urllib2.urlopen(url)
	except	Exception:
        	print 'Status:',response.status,'Reason:',response.reason
        	print sys.exc_info()
		sys.exit(1)
	j = json.load(response)["phedex"]
	for dict in j['link']:
		if dict['from'] in ['T3_US_Omaha','T3_US_Colorado'] and dict['from'] not in siteblacklist:
			list.append(dict['from'])

	list.sort()
	return list

def getwhitelist():
	sites={}
	reversesites={}
	for zone in custodial.keys():
		sites[zone] = get_linkedsites(custodial[zone])
		#print zone,sites[zone]
		time.sleep(.1)
		for s in sites[zone]:
			if s not in reversesites.keys():
				reversesites[s] = []
			if zone not in reversesites[s]:
				reversesites[s].append(zone)
	#print json.dumps(reversesites,indent=4)
	goodsites=[]
	for k in reversesites.keys():
		#print k,len(reversesites[k])
		if len(reversesites[k]) == 7:
			goodsites.append(k)
	goodsites.sort()
	return goodsites

def main():
	global siteblacklist,custodial
	
	count = 0
	while count < 20:
		goodsites = getwhitelist()
		if len(goodsites)<=minsites:
			print "Retry (%s)" % count
			print goodsites,len(goodsites)
			time.sleep(10)
			count = count + 1
			continue
		else:
			print "OK"
			break

	print goodsites,len(goodsites)
	if len(goodsites)>minsites:
		f=open('/afs/cern.ch/user/c/cmst2/www/mc/whitelist.json','w')
		f.write(json.dumps(goodsites,indent=4))
		f.close()
	
	sys.exit(0)

if __name__ == "__main__":
	main()
