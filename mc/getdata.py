import sys,urllib,urllib2,re,time,os
try:
    import json
except ImportError:
    import simplejson as json
import optparse
import httplib
import datetime
import time
import shutil
import os.path
from xml.dom import minidom
import zlib
import re
import math

sys.path.append(os.path.abspath("git/WmAgentScripts"))

from WMCoreService.WMStatsClient import WMStatsClient
from WMCoreService.DataStruct.RequestInfoCollection import RequestInfoCollection, RequestInfo

cachedoverview = '/afs/cern.ch/user/c/cmst2/public/overview.cache'
d = open('/afs/cern.ch/user/c/cmst2/mc/config/blacklist.config').read()
blacklist = d.rstrip()
blacklist = blacklist.split('\n')

def getRequestsByTypeStatus(rtype,rstatus):
	global overview
	r = []
	for i in overview:
		if 'type' in i.keys():
			t = i['type']
		else:
			t = None
		if 'status' in i.keys():
			st = i['status']
		else:
			st = None
		if t in rtype and st in rstatus and t != '' and i['request_name'] not in r:
			#print "t = %s st = %s r = %s" % (t,st,i['request_name'])
			r.append(i['request_name'])
	return r
	
def getWorkflowInfo(workflow):
	global allacdc

	batch = workflow.split('_')[2]
	processingstring = workflow.split('_')[4]
	conn  =  httplib.HTTPSConnection('cmsweb.cern.ch', cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
	r1=conn.request('GET','/reqmgr/view/showWorkload?requestName=' + workflow)
	r2=conn.getresponse()
	data = r2.read()
	conn.close()
	list = data.split('\n')

	primaryds = ''
	cmssw = ''
	campaign = ''
	priority = -1
	timeev = 0
	timeev2 = 0
	sizeev = 0
	prepid = ''
	mergedLFNBase = ''
	globaltag = ''
	sites = []
	custodialsites = []
	blockswhitelist = []
	events_per_job = 0
	events_per_job2 = 0
	events_per_lumi = 0
	max_events_per_lumi = 0
	lumis_per_job = 0
	acquisitionEra = None
	processingVersion = None
	reqdate='' 
	totalevents = -1
	requestdays = 0
	acdc = []
	subrequesttype = ''

	for raw in list:
		if 'acquisitionEra' in raw:
                        a = raw.find("'")
                        if a >= 0:
                                b = raw.find("'",a+1)
                                acquisitionEra = raw[a+1:b]
                        else:
                                a = raw.find(" =")
                                b = raw.find('<br')
                                acquisitionEra = raw[a+3:b]
		elif 'SubRequestType' in raw:
			subrequesttype = raw[raw.find("'")+1:]
			subrequesttype = subrequesttype[0:subrequesttype.find("'")]
		elif 'primaryDataset' in raw:
			primaryds = raw[raw.find("'")+1:]
			primaryds = primaryds[0:primaryds.find("'")]
		elif '.schema.Campaign' in raw:
			campaign = raw[raw.find("'")+1:]
			campaign = campaign[0:campaign.find("'")]
		elif 'cmsswVersion' in raw:
			cmssw = raw[raw.find("'")+1:]
			cmssw = cmssw[0:cmssw.find("'")]
		elif 'properties.mergedLFNBase' in raw:
			mergedLFNBase = raw[raw.find("'")+1:]
			mergedLFNBase = mergedLFNBase[0:mergedLFNBase.find("'")]
		elif 'PrepID' in raw:
			prepid = raw[raw.find("'")+1:]
			prepid = prepid[0:prepid.find("'")]
		elif 'totalEvents' in raw:
			a = raw.find(" =")
			b = raw.find('<br')
			totalevents = int(raw[a+3:b])
		elif 'lumis_per_job' in raw:
			a = raw.find(" =")
			b = raw.find('<br')
			lumis_per_job = int(raw[a+3:b])
		elif '.events_per_job' in raw and not 'children' in raw:
			a = raw.find(" =")
			b = raw.find('<br')
			events_per_job = int(float(raw[a+3:b]))
		elif '.events_per_job' in raw and 'children' in raw:
			a = raw.find(" =")
			b = raw.find('<br')
			events_per_job2 = int(float(raw[a+3:b]))
		elif '.events_per_lumi' in raw:
			a = raw.find(" =")
			b = raw.find('<br')
			events_per_lumi = int(raw[a+3:b])
		elif '.max_events_per_lumi' in raw:
			a = raw.find(" =")
			b = raw.find('<br')
			max_events_per_lumi = int(raw[a+3:b])
		elif 'schema.SizePerEvent' in raw:
                        a = raw.find("'")
                        if a >= 0:
                                b = raw.find("'",a+1)
                                sizeev = int(float(raw[a+1:b]))
                        else:
                                a = raw.find(" =")
                                b = raw.find('<br')
                                sizeev = int(float(raw[a+3:b]))
		elif 'schema.TimePerEvent' in raw and 'children' in raw:
                        a = raw.find("'")
                        if a >= 0:
                                b = raw.find("'",a+1)
                                timeev2 = int(float(raw[a+1:b]))
                        else:
                                a = raw.find(" =")
                                b = raw.find('<br')
                                timeev2 = int(float(raw[a+3:b]))
		elif 'schema.TimePerEvent' in raw and not 'children' in raw:
                        a = raw.find("'")
                        if a >= 0:
                                b = raw.find("'",a+1)
                                timeev = int(float(raw[a+1:b]))
                        else:
                                a = raw.find(" =")
                                b = raw.find('<br')
                                timeev = int(float(raw[a+3:b]))
		elif 'request.priority' in raw:
			a = raw.find("'")
			if a >= 0:
				b = raw.find("'",a+1)
				priority = int(raw[a+1:b])
			else:
				a = raw.find(" =")
				b = raw.find('<br')
				priority = int(raw[a+3:b])
		elif 'RequestDate' in raw:
			reqdate = raw[raw.find("[")+1:raw.find("]")]	
			reqdate = reqdate.replace("'","")
			reqdate= "datetime.datetime(" + reqdate + ")"
			reqdate= eval(reqdate)
			requestdays = (datetime.datetime.now()-reqdate).days
		elif 'blocks.white' in raw and not '[]' in raw:
			blockswhitelist = '['+raw[raw.find("[")+1:raw.find("]")]+']'	
			blockswhitelist = eval(blockswhitelist)		
		elif '.custodialSites' in raw and not '[]' in raw:
			custodialsites = '['+raw[raw.find("[")+1:raw.find("]")]+']'	
			custodialsites = eval(custodialsites)		
		elif 'sites.white' in raw and not '[]' in raw:
			sites = '['+raw[raw.find("[")+1:raw.find("]")]+']'	
			sites = eval(sites)		
		elif 'processingVersion' in raw:
			processingVersion = raw[raw.find("'")+1:]
			processingVersion = processingVersion[0:processingVersion.find("'")]
                        a = raw.find("'")
                        if a >= 0:
                                b = raw.find("'",a+1)
                                processingVersion = raw[a+1:b]
                        else:
                                a = raw.find(" =")
                                b = raw.find('<br')
                                processingVersion = raw[a+3:b]
		elif 'request.schema.GlobalTag' in raw:
			globaltag = raw[raw.find("'")+1:]
			globaltag = globaltag[0:globaltag.find(":")]

	for a in allacdc:
		if prepid in a:
			acdc.append(a)

	custodialt1 = '?'
	for i in sites:
		if 'T1_' in i:
			custodialt1 = i
			break

	conn  =  httplib.HTTPSConnection('cmsweb.cern.ch', cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
	r1=conn.request('GET','/reqmgr/reqMgr/request?requestName=' + workflow)
	r2=conn.getresponse()
	data = r2.read()
	try:
		s = json.loads(data)
	except:
		print "cannot decode: %s" % data
		sys.exit(1)
	conn.close()
	try:
		filtereff = float(s['FilterEfficiency'])
	except:
		filtereff = 1
	try:
		team = s['Assignments']
		if len(team) > 0:
			team = team[0]
		else:
			team = ''
	except:
		team = ''
	try:
		typee = s['RequestType']
	except:
		typee = ''
	try:
		status = s['RequestStatus']
	except:
		status = ''
	try:
                reqevts = s['RequestSizeEvents']
        except:
                try:
                        reqevts = s['RequestNumEvents']
                except:
                        reqevts = 0
	inputdataset = {}
	try:
		inputdataset['name'] = s['InputDatasets'][0]
	except:
		pass
	
	if typee in ['MonteCarlo','LHEStepZero']:
	#if reqevts > 0:
		expectedevents = int(reqevts)
		if events_per_job > 0 and filtereff > 0:
			expectedjobs = int(math.ceil(expectedevents/(events_per_job*filtereff)))
			expectedjobcpuhours = int(timeev*(events_per_job*filtereff)/3600)
		else:
			expectedjobs = 0
			expectedjobcpuhours = 0
	elif typee in ['TaskChain']:
		expectedevents = totalevents * filtereff
		expectedjobs = -1
		expectedjobcpuhours = -1
	elif typee in ['MonteCarloFromGEN','ReReco','ReDigi']:
		[inputdataset['events'],inputdataset['status'],inputdataset['createts'],inputdataset['lastmodts']] = getdsdetail(inputdataset['name'],timestamps=0)
		if blockswhitelist != []:
			inputdataset['bwevents'] = getbdetail(blockswhitelist)
		else:
			[inputdataset['bwevents']] = [inputdataset['events']]


		if inputdataset['bwevents'] > 0 and filtereff > 0:
			expectedevents = int(filtereff*inputdataset['bwevents'])
		else:
			expectedevents = 0
		if events_per_job > 0 and filtereff > 0:
			expectedjobs = int(expectedevents / (events_per_job))
		else:
			expectedjobs = 0
		try:
			expectedjobcpuhours = int(lumis_per_job*timeev*inputdataset['bwevents']/inputdataset['bwlumicount']/3600)
		except:
			expectedjobcpuhours = 0

       		url='https://cmsweb.cern.ch/phedex/datasvc/json/prod/RequestList?dataset=' + inputdataset['name']
		try:
        		result = json.load(urllib.urlopen(url))
		except:
			print "Cannot get subscription status from PhEDEx"
		try:
			r = result['phedex']['request']
		except:
			r = None

		inputdataset['phreqinfo'] = []
		if r:
			for i in range(0,len(r)):
				phreqinfo = {}
 		    	   	requested_by = r[i]['requested_by']
				nodes = []
				for j in range(0,len(r[i]['node'])):
					nodes.append(r[i]['node'][j]['name'])
				id = r[i]['id']
				phreqinfo['nodes'] = nodes
				phreqinfo['id'] = id
				inputdataset['phreqinfo'].append(phreqinfo)
		
		url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/subscriptions?dataset=' + inputdataset['name']
		try:
			pass
	       	 	#result = json.load(urllib.urlopen(url))
		except:
			pass # print "Cannot get transfer status from PhEDEx"
		inputdataset['phtrinfo'] = []
		try:
			rlist = result['phedex']['dataset'][0]['subscription']
			for r in rlist:
				phtrinfo = {}
				node = r['node']
				custodial = r['custodial']
				phtrinfo['node'] = node
				try:
					phtrinfo['perc'] = int(float(r['percent_files']))
				except:
					phtrinfo['perc'] = 0
				inputdataset['phtrinfo'].append(phtrinfo)
		except:
			r = {}

	else:
		expectedevents = -1
		expectedjobs = -1
		expectedjobcpuhours = -1
	
	expectedtotalsize = sizeev * expectedevents / 1000000
	conn  =  httplib.HTTPSConnection('cmsweb.cern.ch', cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
	r1=conn.request('GET','/reqmgr/reqMgr/outputDatasetsByRequestName?requestName=' + workflow)
	r2=conn.getresponse()
	data = r2.read()
	s = json.loads(data)
	conn.close()
	ods = s
        if len(ods)==0:
                print "No Outpudatasets for this workflow: "+workflow
	outputdataset = []
	eventsdone = 0
	for o in ods:
		oel = {}
		oel['name'] = o
		if status in ['running','running-open','running-closed','completed','closed-out','announced','failed']:
			[oe,ost,ocreatets,olastmodts] = getdsdetail(o,timestamps=1)
			oel['events'] = oe
			oel['status'] = ost
                        oel['createts'] = ocreatets
                        oel['lastmodts'] = olastmodts
		
			phreqinfo = {}
       		 	url='https://cmsweb.cern.ch/phedex/datasvc/json/prod/RequestList?dataset=' + o
			try:
        			result = json.load(urllib.urlopen(url))
			except:
				print "Cannot get subscription status from PhEDEx"
			try:
				r = result['phedex']['request']
			except:
				r = None
			if r:
				for i in range(0,len(r)):
       			 		approval = r[i]['approval']
 			    	   	requested_by = r[i]['requested_by']
					custodialsite = r[i]['node'][0]['name']
					id = r[i]['id']
					if '_MSS' in custodialsite:
						phreqinfo['custodialsite'] = custodialsite
						phreqinfo['requested_by'] = requested_by
						phreqinfo['approval'] = approval
						phreqinfo['id'] = id
				oel['phreqinfo'] = phreqinfo
		
			phtrinfo = {}
			url = 'https://cmsweb.cern.ch/phedex/datasvc/json/prod/subscriptions?dataset=' + o
			try:
	       		 	result = json.load(urllib.urlopen(url))
			except:
				print "Cannot get transfer status from PhEDEx"
			try:
				rlist = result['phedex']['dataset'][0]['subscription']
			except:
				rlist = []
			
			phtrinfo = {}
			oel['phtrinfo'] = []
			for r in rlist:
				phtrinfo = {}
				node = r['node']
				custodial = r['custodial']
				if r['move'] == 'n':
					phtype = 'Replica'
				else:
					phtype = 'Move'
				phtrinfo['node'] = node
				phtrinfo['custodial'] = r['custodial']
				phtrinfo['time_create'] = datetime.datetime.fromtimestamp(int(r['time_create'])).ctime()
				phtrinfo['time_create_days'] = (datetime.datetime.now() - datetime.datetime.fromtimestamp(int(r['time_create']))).days
				try:
					phtrinfo['perc'] = int(float(r['percent_files']))
				except:
					phtrinfo['perc'] = 0
				phtrinfo['type'] = phtype

				oel['phtrinfo'].append(phtrinfo)
			eventsdone = eventsdone + oe
		else:
			eventsdone = 0
		outputdataset.append(oel)

	cpuhours = timeev*expectedevents/3600
	remainingcpuhours = max(0,timeev*(expectedevents-eventsdone)/3600)

	realremainingcpudays = 0
	totalslots = 0
	for (psite,pslots) in pledged.items():
		if psite in sites:
			totalslots = totalslots + pslots
	if totalslots == 0:
		realremainingcpudays = 0
	else:
		realremainingcpudays = float(remainingcpuhours) / 24 / totalslots 
	
	t2zone = {'T1_IT_CNAF':'CNAF','T1_DE_KIT':'KIT','T1_FR_CCIN2P3':'IN2P3','T1_ES_PIC':'PIC','T1_UK_RAL':'RAL','T1_US_FNAL':'FNAL'}
	try:
		zone = t2zone[custodialsites[0]]
	except:
		zone = '?'
	if workflow in jlist.keys():
		js = jlist[workflow]
	else:
		js = {}
	return {'subrequesttype':subrequesttype,'batch':batch,'processingstring':processingstring,'requestname':workflow,'filtereff':filtereff,'type':typee,'status':status,'expectedevents':expectedevents,'inputdatasetinfo':inputdataset,'primaryds':primaryds,'prepid':prepid,'globaltag':globaltag,'timeev':timeev,'timeev2':timeev2,'sizeev':sizeev,'priority':priority,'sites':sites,'zone':zone,'custodialsites':custodialsites,'blockswhitelist':blockswhitelist,'js':js,'outputdatasetinfo':outputdataset,'cpuhours':cpuhours,'realremainingcpudays':realremainingcpudays,'remainingcpuhours':remainingcpuhours,'team':team,'acquisitionEra':acquisitionEra,'requestdays':requestdays,'reqdate':'%s' % reqdate,'processingVersion':processingVersion,'events_per_job':events_per_job,'events_per_job2':events_per_job2,'lumis_per_job':lumis_per_job,'max_events_per_lumi':max_events_per_lumi,'events_per_lumi':events_per_lumi,'expectedjobs':expectedjobs,'expectedjobcpuhours':expectedjobcpuhours,'campaign':campaign,'cmssw':cmssw,'expectedtotalsize':expectedtotalsize,'mergedLFNBase':mergedLFNBase,'acdc':acdc}

def getpriorities(reqinfo):
	priorities = []
	for i in reqinfo.keys():
		if not reqinfo[i]['priority'] in priorities:
			priorities.append(reqinfo[i]['priority'])
	priorities.sort(reverse=True)
	return priorities

def getoverview():
	global cachedoverview
        if not os.path.exists(cachedoverview):
		print "Cannot get overview from %s" % cachedoverview
		sys.exit(1)
	d = open(cachedoverview).read()
        s = eval(d)
        return s

def getbdetail(blocklist):
        e = dbs3_get_block_data(blocklist)
        if e == -1:
                return 0
        else:
                return e

def getdsdetail(dataset,timestamps):
        [e,st,createts,lastmodts] = dbs3_get_data(dataset,timestamps)
	#print [e,st,createts,lastmodts]
        if e == -1:
                return [0,'',0,0]
        else:
                return [e,st,createts,lastmodts]

def dbs3_get_block_data(blocklist):
        q = "/afs/cern.ch/user/c/cmst2/mc/scripts/dbs3wrapper.sh /afs/cern.ch/user/c/cmst2/mc/scripts/datasetinfo.py --blocklist %s --json" % ",".join(blocklist)
        output=os.popen(q).read()
        s = json.loads(output)
	sum = 0
	for i in s:
        	if 'num_event' in i.keys():
                	sum = sum + i['num_event']
        return sum

def dbs3_get_data(dataset,timestamps=1):
        q = "/afs/cern.ch/user/c/cmst2/mc/scripts/dbs3wrapper.sh /afs/cern.ch/user/c/cmst2/mc/scripts/datasetinfo.py --dataset %s --json --ldate" % dataset
        output=os.popen(q).read()
        s = json.loads(output)
        if 'num_event' in s.keys():
                return [s['num_event'],s['dataset_access_type'],s['creation_date'],s['ldate']]
        else:
                return [0,'',0,0]

def das_get_data(dataset,timestamps=1):
	das_hosts = ['https://cmsweb.cern.ch']
	count = 20
        c = 0
        while c < count:
		das_host = das_hosts[c % 2]
		q = 'python26 /afs/cern.ch/user/c/cmst2/mc/external/das_cli.py --host="%s" --query "dataset dataset=%s system=dbs3|grep dataset.status,dataset.nevents" --format=json' % (das_host,dataset)
		print "q= %s" % q
        	output=os.popen(q).read()
        	output = output.rstrip()
		print output
        	#if (type(tmp) == dict and 'status' in output.keys() and tmp['status']=='fail'):
		if '{"status": "fail"' in output:
			c=c+1
			print "FAIL-%s: %s\n%s" %(c,q,output)
			time.sleep(10*c)
			continue
		else:
			break
	if c == count:
		print "ACCESS TO DAS FAILED"
		print "q= %s" % q
		return [0, '', 0, 0]
	if output == "[]":
                return [0, '',0,0] # dataset is not in DBS
        tmp = eval(output)
	if type(tmp) == list:
               	if 'dataset' in tmp[0].keys():
                       	for i in tmp[0]['dataset']:
                               	if i:
                                       	break
                       	events = i['nevents']
                       	status = i['status']
	else:
		return [0, '', 0, 0]
	createts = 0
	lastmodts = 0
	if timestamps:
        	while c < count:
			count = 20
  			c = 0
			q = 'python26 /afs/cern.ch/user/c/cmst2/mc/external/das_cli.py --host="%s" --query "block dataset=%s system=dbs | min(block.creation_time),max(block.modification_time)"|grep "(block"' % (das_host,dataset)
			print "q= %s" % q
        		output=os.popen(q).read()
       			output = output.rstrip()
			lines = output.split('\n')
			print output
        		#if (type(tmp) == dict and 'status' in output.keys() and tmp['status']=='fail'):
			if '{"status": "fail"' in output:
				c=c+1
				print "FAIL-%s: %s\n%s" %(c,q,output)
				time.sleep(10*c)
				continue
			else:
				break
		if c == count:
			print "ACCESS TO DAS FAILED"
			return [int(events),status, 0, 0]
			for line in lines:
				if 'min' in line:
					try:
						createts = int(line.split('=')[1])
					except:
						createts = 0
				elif 'max' in line:
					try:
						lastmodts = int(line.split('=')[1])
					except:
						lastmodts = 0

        ret = [int(events),status,int(createts),int(lastmodts)]
	return ret

def main():
	global overview,forceoverview,pledged,allacdc,jlist
	
	now = time.time()
	
	output=os.popen("ps aux | grep mc/cron/getdata.py | grep -v grep").read().split('\n')
	if len(output)>3:
		sys.stderr.write('WARNING: getdata already running\n')
		sys.exit(1)
		
	overview = getoverview()

	dp=open('/afs/cern.ch/user/c/cmst2/www/mc/pledged.json').read()
        pledged = json.loads(dp)


	rtypeb = ['MonteCarlo','MonteCarloFromGEN']
	#rtypeb = ['TaskChain','MonteCarlo','MonteCarloFromGEN']
	#rtypeb = ['TaskChain']

	rtype = rtypeb[:]
	rtype.append('Resubmission')
	rstatus = ['assignment-approved','assigned','acquired','running-open','running-closed','completed','closed-out','failed']
	#rstatus = ['running-closed','completed']
	allacdc = getRequestsByTypeStatus(['Resubmission'],rstatus)
	list = getRequestsByTypeStatus(rtype,rstatus)
	listb = getRequestsByTypeStatus(rtypeb,rstatus)

	jlist={}
	if 1:
		sys.stderr.write('Getting wmstats jobstats ')
		try:
			wMStats = WMStatsClient("https://cmsweb.cern.ch/couchdb/wmstats")
			jdata = wMStats.getRequestByNames(list, jobInfoFlag = True)
			requestCol = RequestInfoCollection(jdata)
			for wf, info in requestCol.getData().items():
				jlist[wf] = {}
				for t,n in  info.getJobSummary().getJSONStatus().items():
					jlist[wf][t]=n
		except:
			print "Cannot get job stats"
			pass
		#print jlist
		sys.stderr.write('Done.\n')
	
	reqinfo = {}
	struct = []
	
	sys.stderr.write("Number of requests in %s: %s\n" % (rstatus,len(listb)))
	count = 1
	for workflow in list:
		if workflow in allacdc or workflow in blacklist:
			#sys.stderr.write("[skipping %s]\n" % (workflow))
			continue
		sys.stderr.write("%s: %s\n" % (count,workflow))
		count = count + 1
		reqinfo[workflow] = getWorkflowInfo(workflow)
		for i in reqinfo[workflow].keys():
			sys.stderr.write("\t%s : %s\n" % (i,reqinfo[workflow][i]))
		if reqinfo[workflow]['type'] == 'TaskChain' and reqinfo[workflow]['subrequesttype'] != 'MC':
			sys.stderr.write('[Adding %s to blacklist]\n' % workflow)
			blacklist.append(workflow)
		else:
			struct.append(reqinfo[workflow])
	f=open('/afs/cern.ch/user/c/cmst2/www/mc/data.json','w')
	f.write(json.dumps(struct,indent=4,sort_keys=True))
	f.close()
	f=open('/afs/cern.ch/user/c/cmst2/mc/config/blacklist.config','w')
	for i in blacklist:
		f.write("%s\n" % i)
	f.close()
	sys.stderr.write("[END %s]\n" % (time.time() - now))

if __name__ == "__main__":
        main()

