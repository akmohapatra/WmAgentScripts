#!/usr/bin/env python
import sys,urllib,urllib2,re,time,os
import httplib
try:
    import json
except ImportError:
    import simplejson as json

# Main
def main():
	url='cmsweb.cern.ch'
        d=open('/afs/cern.ch/user/c/cmst2/mc/config/disktape.cfg').read()
	s=json.loads(d)
	#print json.dumps(s,indent=4)
	#tconst=1024**4
	tconst=1000000000000
	sites=s.keys()
	for site in sites:
		if 'blacklisted' in s[site].keys():
			if s[site]['blacklisted']:
				print "Blacklisted: %s" % site
				del(s[site])
				continue
		print "Processing: %s" % site
		for typ in ['mss','disk']:
			if typ in s[site].keys():
				params = urllib.urlencode({ "node" : s[site][typ]})
				conn  =  httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
			        conn.connect()
		        	conn.request("POST", "/phedex/datasvc/json/prod/nodeusage", params)
			        response = conn.getresponse()
			        #print response.status, response.reason
			        #print response.msg
			        a = response.read()
			        if response.status != 200:
			                print a
					sys.exit(1)
			        b = json.loads(a)
				#print json.dumps(b,indent=4)
				#print b
				if typ == 'mss':
					if type(b['phedex']['node']=='list'):
			        		s[site]['usedmss'] = b['phedex']['node'][0]['cust_dest_bytes']/tconst
					else:
			        		s[site]['usedmss'] = b['phedex']['node']['cust_dest_bytes']/tconst
					s[site]['freemss'] = s[site]['totalmss']-s[site]['usedmss']	
				else:
			        	s[site]['useddisk'] = b['phedex']['node'][0]['noncust_dest_bytes']/tconst
					s[site]['freedisk'] = s[site]['totaldisk']-s[site]['useddisk']	
	f=open('/afs/cern.ch/user/c/cmst2/www/mc/disktape.json','w')
	f.write(json.dumps(s,indent=4))
	f.close()
	for site in s.keys():
		if 'usedmss' in s[site]:
			print "%s MSS Total: %sTB Used: %s Available: %s" % (site,s[site]['totalmss'],s[site]['usedmss'],s[site]['freemss'])
		if 'useddisk' in s[site]:
			print "%s Disk Total: %sTB Used: %s Available: %s" % (site,s[site]['totaldisk'],s[site]['useddisk'],s[site]['freedisk'])
		print

if __name__ == "__main__":
        main()
