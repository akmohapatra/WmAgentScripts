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

#TODO for each request, get list of linked MSS
#TODO for each request, order by expected events, subscribe to the most free ones in round robin
#TODO set printlog

blacklist = 'T1_CH_CERN_Buffer'

def phedex_call(call,params):
	conn  =  httplib.HTTPSConnection('cmsweb.cern.ch', cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
	conn.connect()
      	conn.request("POST", "/phedex/datasvc/json/prod/%s" % call, params)
        response = conn.getresponse()
        #print response.status, response.reason
        #print response.msg
        a = response.read()
        if response.status != 200:
                print a
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
	global blacklist
	mcdir = '/afs/cern.ch/user/c/cmst2/www/mc'
	cmsweb='cmsweb.cern.ch'

        d=open('%s/disktape.json' % mcdir).read()
	disktape=json.loads(d)

	d=open('%s/data.json' % mcdir).read()
	s = json.loads(d)

	print

	sites = []
	for r in s:
		for i in r['sites']:
			if i not in sites:
				sites.append(i)
	sites.sort()

	uplinks = {}
	#params = urllib.urlencode({"status":"ok","kind":"WAN"})
	params = urllib.urlencode({"status":"ok"})
	links = phedex_call('links',params)
	for site in sites:
		for p in links['phedex']['link']:
			if site == p['from'] and ('Buffer' in p['to'] or p['to'] == 'T0_CH_CERN_Export') and p['to'] not in blacklist:
				if site not in uplinks.keys():
					uplinks[site] = []
				uplinks[site].append(p['to'])
	print json.dumps(uplinks,indent=4)
	f=open('/afs/cern.ch/user/c/cmst2/www/mc/uplinks.json','w')
	f.write(json.dumps(uplinks,indent=4))
	f.close()

        sys.exit(0)

if __name__ == "__main__":
        main()
