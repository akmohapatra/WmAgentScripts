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

# TODO see local_queue
#TODO: view for distribution of all the Summer12 VALID GEN-SIM not yet chained to any DR step
#TODO: assignment-approved 1week, input datasets slots ready
# TODO MC statistics (DBS)
# TODO sites/pledged
# TODO add cooloffs/failures (new page?)

def human(n):
	if n<1000:
		return "%s" % n
	elif n>=1000 and n<1000000:
		order = 1
	elif n>=1000000 and n<1000000000:
		order = 2
	else:
		order = 3

	norm = pow(10,3*order)

	value = float(n)/norm

	letter = {1:'k',2:'M',3:'G'}
	return ("%.1f%s" % (value,letter[order])).replace(".0", "")

def savelist(f,l):
        try:
                ff = open(f,'w')
        except:
                print "Cannot open %s for write" % ff
                sys.exit(1)
	for i in l:
		ff.write("%s\n" % i)
	ff.close()

def loadlist(f):
        try:
                d = open(f).read()
        except:
                print "Cannot load %s" % f
                sys.exit(1)
        try:
                s = d.split('\n')
		if '' in s:
			s.remove('')
        except:
                print "Cannot eval %s " % f
                sys.exit(1)
        print "%s loaded successfully" % f
        return s

def savejobstats(f,j):
	ff = open(f,'w')
	ff.write(json.dumps(j,indent=4,sort_keys=True))
	ff.close()

def loadjobstats(f):
	if not os.path.exists(f):
		return {}
        try:
                d = open(f).read()
        except:
                print "Cannot load jobstats from %s" % f
                sys.exit(1)
	return json.loads(d)
	
def loadcampaignconfig(f):
        try:
                d = open(f).read()
        except:
                print "Cannot load config file %s" % f
                sys.exit(1)
        try:
                s = eval(d.strip())
		if '' in s:
			print "XXXXXXXXX"
			s.remove('')
        except:
                print "Cannot eval config file %s " % f
                sys.exit(1)
        print "\nConfiguration loaded successfully from %s" % f
        #for c in s.keys():
        #       print "%s" % c
        #       for i in s[c]:
        #               print "\t%s\t%s" % (i,s[c][i])
        return s

def getpriorities(s,campaign,zone,status):
	p = []
	for r in s:
		if r['priority'] not in p:
			if (campaign == getcampaign(r) or not campaign) and (zone == r['zone'] or not zone ) and r['status'] in status:
				p.append(r['priority'])
	p.sort()
	p.reverse()
	#print p
	return p

def getcampaign(reqinfo):
	return reqinfo['campaign']

def main():
	mcdir = '/afs/cern.ch/user/c/cmst2/www/mc'

	campaignconfig = loadcampaignconfig('/afs/cern.ch/user/c/cmst2/mc/config/campaign.cfg')
	urgent_requests_prepid = loadlist('/afs/cern.ch/user/c/cmst2/www/mc/urgent.txt')
	autosetvalid = []

# Last update
	now = datetime.datetime.now()
	(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat('%s/data.json' % mcdir)
	datajsonmtime = "%s" % time.ctime(mtime)
	d=open('%s/data.json' % mcdir).read()
	s = json.loads(d)

	(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat('%s/gen-sim-wr.json' % mcdir)
	wrjsonmtime = "%s" % time.ctime(mtime)
	d=open('%s/gen-sim-wr.json' % mcdir).read()
	wrjson = json.loads(d)

	(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat('%s/pledged.json' % mcdir)
	pledgedjsonmtime = "%s" % time.ctime(mtime)
	d=open('%s/pledged.json' % mcdir).read()
	pledged = json.loads(d)
	totalpledged = 0
	for i in pledged.keys():
		totalpledged = totalpledged + pledged[i]

#	d=open('%s/running-pending.json' % mcdir).read()
	#ssbrunpend = json.loads(d)
	#sitestatus = {}
	#for i in ssbrunpend['summaries']:
	#		sitestatus[i['name']] = {'running':int(i['running']),'pending':int(i['pending'])}

	#jsonstats = loadjobstats('%s/jobstats.json' % mcdir)
	#for site in sitestatus.keys():
	#	running = sitestatus[site]['running']
	#	if site not in jsonstats.keys():
			#jsonstats[site] = {'max_abs_running':running,'range_running':[{'ts':int(time.time()),'running':running}]}
	#	else:
#			jsonstats[site]['max_abs_running'] = max(running,jsonstats[site]['max_abs_running'])
#			newrange_running = [{'ts':int(time.time()),'running':running}] 
#			range_running = jsonstats[site]['range_running']
#			for p in range_running:
#				if int(time.time()) - p['ts'] < 60*60*24*30:
#					newrange_running.append(p)
#			jsonstats[site]['range_running'] = newrange_running

#	savejobstats('%s/jobstats.json' % mcdir,jsonstats)

	htmlfile = '%s/index.html' % mcdir
	htmlmonday = '%s/monday.txt' % mcdir
	requestspath='%s/requests' % mcdir

	bar = '<table><tr>\
<td><a href="http://cmst2.web.cern.ch/cmst2/mc/">Summary</a></td>\
<td><a href="http://cmst2.web.cern.ch/cmst2/mc/requests.html">Requests</a></td>\
<td><a href="http://cmst2.web.cern.ch/cmst2/mc/assignment.html">Assignment</a></td>\
<td><a href="http://cmst2.web.cern.ch/cmst2/mc/closed-out.html">Closed-out</a></td>\
<td><a href="http://cmst2.web.cern.ch/cmst2/mc/announce.html">Announce batches</a></td>\
<td><a href="http://cmst2.web.cern.ch/cmst2/mc/sites.html">Sites</a></td>\
<td><a href="http://cmst2.web.cern.ch/cmst2/mc/issues.html">Issues</a></td>\
<td><a target="_blank" href="https://cmst2.web.cern.ch/cmst2/ops.php">Ops</a></td>\
<td><a target="_blank" href="https://cmsweb.cern.ch/wmstats/index.html">WMStats</a></td>\
<td><a target="_blank" href="http://cmst2.web.cern.ch/cmst2/mc/announcements.log">Announcement logs</a></td>\
<td><a target="_blank" href="http://www.gridpp.rl.ac.uk/cms/reprocessingcampaigns_totals.html">Processing campaigns</a></td>\
<td><a target="_blank" href="https://hypernews.cern.ch/HyperNews/CMS/SECURED/edit-response.pl/datasets.html">New announcement HN</a></td>\
</tr></table><hr>'
	foot = "<hr>Last update: %s<hr><i>Acquired->Closed-out MonteCarlo* requests JSON file: <a target='_blank' href='http://cmst2.web.cern.ch/cmst2/mc/data.json'>data.json</a> (updated: %s)</i><br/><i>Pledged JSON file: <a target='_blank' href='http://cmst2.web.cern.ch/cmst2/mc/pledged.json'>pledged.json</a> (updated: %s)</i><br/><i>Assignment txt file: <a target='_blank' href='http://cmst2.web.cern.ch/cmst2/mc/assignment.txt'>assignment.txt</a></i><br/></html>" % (str(now),datajsonmtime,pledgedjsonmtime)

	# purge old requests
	oldrequests = os.listdir(requestspath)
	for r in oldrequests:
		if os.path.isfile("%s/%s" % (requestspath,r)):
			os.unlink("%s/%s" % (requestspath,r))

	urgent_requests = []
	#if urgent_requests_prepid:
	if 0:
                f = open('%s/urgent.txt' % mcdir,'w')
		for r in s:
			if r['status'] in ['acquired','running','running-open','running-closed'] and r['type'] in ['MonteCarlo','MonteCarloFromGEN','TaskChain']:
				for p in urgent_requests_prepid:
					if p in r['requestname']:
						urgent_requests.append(r['requestname'])
						f.write("%s\n" % r['requestname'])
                f.close()
	for r in s:
		f = open("%s/%s.html" % (requestspath,r['requestname']),'w')
		#print "%s/%s.html" % (requestspath,r['requestname'])
		f.write('<html><head><title>Request: %s</title>\n<meta http-equiv="Refresh" content="1800">\n</head>\n' % r['requestname'])
		f.write('<body>')
		f.write('<table>')
		for k in r.keys():
			f.write('<tr><td valign=top>%s</td><td valign=top>%s</td></tr>' % (k,r[k]))
		f.write('</table>')
		f.write('</body>')
		f.write(foot)
		f.close()

	fmonday = open(htmlmonday,'w')

	f = open('%s/assignment.html' % mcdir,'w')
	ftxt = open('%s/assignment.txt' % mcdir,'w')
	f.write('<html><head><title>MC Status - Assignment</title><style>td{padding:4px;}</style>\n<meta http-equiv="Refresh" content="1800">\n</head>\n')
	f.write('<body style=\'font-family:sans-serif;padding:0px\'>')
	f.write(bar)

	f.write('<h3>Summary of requests in assignment-approved</h3>')
	f.write('<table border=0 style=\'border-width:1px;border-spacing:0px;border-collapse:collapse;font-size:10px\'>')
	f.write('<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>'% ('Priority','TotalEvents','TotalCPUHours','TotalSizeBytes'))

	summary = {}
	batches = {}

	# purge old batches
	oldbatches = os.listdir("%s/batches/" % (mcdir))
	for b in oldbatches:
		if os.path.isfile("%s/%s" % ("%s/batches" % (mcdir),b)):
			os.unlink("%s/%s" % ("%s/batches" % (mcdir),b))
	for r in s:
		if r['type'] not in ['MonteCarlo','MonteCarloFromGEN','TaskChain']:
			continue
		if r['status'] in ['assignment-approved']:
			if r['priority'] not in summary.keys():
				summary[r['priority']] = {'events':0,'cpuhours':0,'size':0}
			summary[r['priority']]['events'] = summary[r['priority']]['events'] + r['expectedevents']
			summary[r['priority']]['cpuhours'] = summary[r['priority']]['cpuhours'] + r['cpuhours']
			summary[r['priority']]['size'] = summary[r['priority']]['size'] + r['sizeev']*r['expectedevents']

			if 'pdmvserv' in r['requestname']:
				if r['processingstring'] != '':
					batchname = "%s_%s_%s" % (r['campaign'],r['batch'],r['processingstring'])
				else:
					batchname = "%s_%s" % (r['campaign'],r['batch'])
				if batchname not in batches.keys():
					batches[batchname] = []
				batches[batchname].append(r['requestname'])

	for b in batches.keys():
		fb=open("%s/batches/%s.txt" % (mcdir,b),'w') # overwrites existing batch list
		fb.write("\n".join(x for x in batches[b]) + '\n')
		fb.close()
	
	priorities = summary.keys()
	priorities.sort(reverse=1)
	for priority in priorities:
		f.write('<tr>')
		f.write("<td valign=top align=center>%s</td>" % priority)
		f.write("<td valign=top align=center>%s</td>" % human(summary[priority]['events']))
		f.write("<td valign=top align=center>%s</td>" % human(float(summary[priority]['cpuhours'])))
		f.write("<td valign=top align=center>%s</td>" % human(summary[priority]['size']))
		f.write('</tr>')

	f.write('</table>')

	f.write('<h3>Regular batches waiting for assignment</h3>')
	for b in batches.keys():
		f.write("<p><a target=\"_blank\" href=\"%s\">%s</a>" % ("https://cmst2.web.cern.ch/cmst2/mc/batches/%s.txt" % (b),b))


	f.write('<h3>Requests in assignment-approved</h3>')
	f.write('<table border=0 style=\'border-width:1px;border-spacing:0px;border-collapse:collapse;font-size:10px;\'>')
	f.write('<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>'% ('OutputDataset','RequestName','Type','Priority','Events','CPUH','DaysInj','Hrs/J','FEff','TimeEv','Ev/Job','Ev/Lumi','Lum/Job','TotJobs','TotSize'))

	for priority in priorities:
		for r in s:
			if r['status'] in ['assignment-approved'] and r['priority'] == priority and r['type'] in ['MonteCarlo','MonteCarloFromGEN','TaskChain']:
				for ods in r['outputdatasetinfo']:
					events_lumi = -1
					events_job = -1
					lumis_job = 0
					if r['type'] == 'MonteCarloFromGEN':
						t2count=0
						try:
							h = float(r['timeev'])*r['inputdatasetinfo']['events']/r['inputdatasetinfo']['lumicount']/3600
						except:
							h = 0
						events_job = r['events_per_job']
						events_lumi = r['max_events_per_lumi']
						lumis_job = r['lumis_per_job']
						t1list = []
						slots = 0
						if 'status' in r['inputdatasetinfo'].keys():
							if r['inputdatasetinfo']['status'] == 'VALID':
								for i in r['inputdatasetinfo']['phtrinfo']:
									if 'T1_' in i['node'] and float(i['perc']==100):
										t1list.append(i['node'].split('_')[2])
									node = i['node'].replace('_MSS','')
									if node in pledged.keys() and i['perc'] == 100 and 'T2_' in node:
										slots = slots + pledged[node]
										t2count=t2count+1
						reqs = "<a href=\"https://cmsweb.cern.ch/phedex/prod/Data::Subscriptions#filter=%s\" target=\"_blank\">input</a>" % (r['inputdatasetinfo']['name'])
						t1list = ",".join(t1list)
						t1list="%s(%s)" % (t1list,reqs)
						#t1list="%s" % (t1list)
							
					elif r['type'] == 'MonteCarlo':
						h = float(r['timeev']) * r['events_per_job'] * r['filtereff'] / 3600
						events_job = r['events_per_job']
						events_lumi = r['events_per_lumi']
						lumis_job = r['lumis_per_job']
						t1list = '(any)'
						t2count = ''
						slots = totalpledged
					else:
						h = 0
						events_lumi = -1
						events_job = -1
						lumis_job = r['lumis_per_job']
						t1list = ''
						t2count = ''
						# TODO add default whitelist for MonteCarlo
						slots = totalpledged
					ftxt.write('%s events=%s priority=%s daysinj=%s\n' % (r['requestname'],r['expectedevents'],r['priority'],r['requestdays']))
					f.write('<tr onMouseOver="this.bgColor=\'#CCFFFF\'" onMouseOut="this.bgColor=\'#FFFFFF\'">')
					f.write("<td style='padding:8px 8px;' valign=top>%s</td>" % ods['name'])
					#f.write("<td style='padding:8px 8px;' valign=top><a href='https://cmst2.web.cern.ch/cmst2/mc/requests/%s.html' target='_blank'>%s</a></td>" % (r['requestname'],r['requestname']))
					f.write("<td style='padding:8px 8px;' valign=top>%s<br/><a href='https://cmst2.web.cern.ch/cmst2/mc/requests/%s.html' target='_blank'>req</a>,<a href='https://cmsweb.cern.ch/reqmgr/view/details/%s' target='_blank'>det</a>,<a href='https://cmsweb.cern.ch/reqmgr/view/showWorkload?requestName=%s' target='_blank'>wld</a></td>" % (r['requestname'],r['requestname'],r['requestname'],r['requestname']))
					f.write("<td style='padding:8px 8px;' valign=top>%s</td>" % r['type'])
					f.write("<td style='padding:8px 8px;' valign=top align=right>%s</td>" % human(r['priority']))
					f.write("<td style='padding:8px 8px;' valign=top align=right>%s</td>" % human(r['expectedevents']))
					f.write("<td style='padding:8px 8px;' valign=top align=right>%s</td>" % human(r['cpuhours']))
					f.write("<td style='padding:8px 8px;' valign=top align=center>%s</td>" % r['requestdays'])
					f.write("<td style='padding:8px 8px;' valign=top align=center>%.1f</td>" % h)
					f.write("<td style='padding:8px 8px;' valign=top align=left>%s</td>" % r['filtereff'])
					f.write("<td style='padding:8px 8px;' valign=top align=left>%s</td>" % r['timeev'])
					if events_job >= 0:
						f.write("<td style='padding:8px 8px;' valign=top align=center>%s</td>" % events_job)
					else:
						f.write("<td style='padding:8px 8px;' valign=top align=center>%s</td>" % "-")
					if events_lumi >= 0:
						f.write("<td style='padding:8px 8px;' valign=top align=center>%s</td>" % events_lumi)
					else:
						f.write("<td style='padding:8px 8px;' valign=top align=center>%s</td>" % "-")
					if lumis_job > 0:
						f.write("<td style='padding:8px 8px;' valign=top align=center>%s</td>" % lumis_job)
					else:
						f.write("<td style='padding:8px 8px;' valign=top align=center>%s</td>" % "-")
					f.write("<td style='padding:8px 8px;' valign=top align=center>%s</td>" % r['expectedjobs'])
					f.write("<td style='padding:8px 8px;' valign=top align=center>%sB</td>" % human(1000*r['sizeev']*r['expectedevents']))
					f.write('</tr>')
		f.write('<tr><td></td></tr>')
	f.write('</table>')
	f.write(foot)
	f.close()
	ftxt.close()

	f = open('%s/sites.html' % mcdir,'w')
	f.write('<html><head><title>MC Status - Sites</title><style>td{padding:4px;}</style>\n<meta http-equiv="Refresh" content="1800">\n</head>\n')
	f.write('<body style=\'font-family:sans-serif;\'>')
	f.write(bar)
	f.write('<h3>MC Production at Sites</h3>')
	#kys=sitestatus.keys()
	kys=[]
	#kys.sort()
	f.write('<table border=0 style=\'border-width:1px;border-spacing:0px;border-collapse:collapse;font-size:12px;\'>')
	#f.write('<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>'% ('Site','Running','Pending','RealSlots'))
	f.write('<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>'% ('Site','Running','RealSlots','MaxAbsRunning','ALARM'))
	for i in kys:
		if i in pledged.keys():
			color = '#FFFFFF'
			msg = ''
			if sitestatus[i]['pending'] > 100 and sitestatus[i]['running'] < pledged[i]/15 and ('T2_' in i or i in ['T1_RU_JINR']):
				color='#FFCCCC'
				msg = 'RUNNING_LOW'
			f.write("<tr bgcolor=%s><td valign=top>%s (<a target=\"_blank\" href=\"http://dashb-cms-job.cern.ch/dashboard/templates/web-job2/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=1&usr=&site=%s&submissiontool=&application=&activity=production&status=&check=submitted&tier=&sortby=task&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=\">dasbboard</a>,<a target=\"blank\" href=\"http://dashb-ssb.cern.ch/dashboard/templates/sitePendingRunningJobs.html?site=%s\">pendingrunning</a>)</td><td valign=top align=right>%s</td><td valign=top align=right>%s</td><td valign=top align=right>%s</td><td valign=top>%s</td></tr>" % (color,i,i,i,sitestatus[i]['running'],pledged[i],jsonstats[i]['max_abs_running'],msg))
	f.write('</table>')
	f.write(foot)
	f.close()

	f = open('%s/wmstats.html' % mcdir,'w')
	f.write('<html><head><title>MC Status - WMStats</title><style>td{padding:4px;}</style>\n<meta http-equiv="Refresh" content="1800">\n</head>\n')
	f.write('<body style=\'font-family:sans-serif;\'>')
	f.write(bar)
	f.write(' <iframe frameborder=0 width=100% height=100% src="https://cmsweb.cern.ch/wmstats/index.html"></iframe> ')
	f.write(foot)
	f.close()

	f = open('%s/ops.html' % mcdir,'w')
	f.write('<html><head><title>MC Status - Ops</title><style>td{padding:4px;}</style>\n<meta http-equiv="Refresh" content="1800">\n</head>\n')
	f.write('<body style=\'font-family:sans-serif;\'>')
	f.write(bar)
	f.write(' <iframe frameborder=0 width=100% height=100% src="https://cmst2.web.cern.ch/cmst2/ops.php"></iframe> ')
	f.write(foot)
	f.close()

	f = open('%s/requests.html' % mcdir,'w')
	f.write('<html><head><title>MC Status - Requests</title><style>td{padding:4px;}</style>\n<meta http-equiv="Refresh" content="1800">\n</head>\n')
	f.write('<body style=\'font-family:sans-serif;\'>')
	f.write(bar)

	stuck_days = 5
	old_days = 15
	oldest = {}

	issues = {}
	for i in ['highprio','dsstuck','mostlydone','veryold','subscribe','wronglfnbase','trstuck','acdc']:
		issues[i] = []

	highest_prio = max(getpriorities(s,'','',['assigned','acquired','running-open','running-closed','completed']))
	for status in ['failed','assigned','acquired','running-open','running-closed','completed']:
		f.write('<h3>Status: %s</h3>' % (status))
		f.write('<table border=0 style=\'border-width:1px;border-spacing:0px;border-collapse:collapse;font-size:10px;\'>')
		f.write('<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>'% ('Prio','OutputDataset','RequestName','Team','Subscr','Jobs%','Creat','Qud','Pnd','Run','Cff','Succ','Fail','ExpEv','DBSEvts','Days','ACDC'))
		for priority in getpriorities(s,'','',[status]):
			for r in s:
				if r['type'] not in ['MonteCarlo','MonteCarloFromGEN','TaskChain']:
					continue
				if r['type'] == 'MonteCarlo':
					split = r['events_per_job']
				elif r['type'] == 'MonteCarloFromGEN':
					split = r['lumis_per_job']
				else:
					split = 0
				jlist=r['js']
				js = {}
				for j in jlist.keys():
					if j == 'sucess':
						k = 'success'
					else:
						k = j
					js[k] = jlist[j]
				if status == r['status'] and priority == r['priority']:
					for ods in r['outputdatasetinfo']:
						if len(r['custodialsites']) > 0:
							custodialt1 = r['custodialsites'][0]
						etas = ''
						eta = 0
						eperc = 0
						if 'events' in ods.keys():
							try:
								eperc = float(ods['events']) / r['expectedevents'] * 100
							except:
								eperc = 0
							if eperc > 5 and r['status'] in ['running','running-open','running-closed']:
								a=(datetime.datetime.now() - datetime.datetime.fromtimestamp(ods['createts']))
								elapsedtime = (a.days*24*3600+a.seconds)/3600
								if elapsedtime > 0:
									if 'created' in js.keys() and js['created'] > 0 and js['success'] > 0 and js['running'] > 0 and js['running']/js['created'] > .1 and 0:
										eta=(js['success']/elapsedtime)*(js['created']-js['success'])/js['running']
									else:
										speed = ods['events'] / elapsedtime
										remainingevents = r['expectedevents'] - ods['events']
										if speed>0:
											eta = remainingevents / speed
										else:
											eta = 0
									
									if eta < 0:
										eta = 0
									#print "elapsedtime = %s ods['events'] = %s ods['createts'] = %s speed = %s remainingevents = %s eta = %s" % (elapsedtime,ods['events'],ods['createts'],speed,remainingevents,eta)
								else:
									eta = 0
								if eta == 0:
									etas = ''
								elif eta > 24*30:
									etas = '&#8734;'
								else:
									etas = '%sd' % (eta/24+1)
						phperc = ''
						transferred_events = 0
						if 'phtrinfo' in ods.keys():
							for p in ods['phtrinfo']:
								if p['custodial'] == 'y':
									if 'perc' in p.keys():
										phperc = "%s" % p['perc']
										transferred_events = int(float(ods['events']) * float(phperc) / 100)
									break
						subscr = 0
						if 'phreqinfo' in ods.keys():
							if 'id' in ods['phreqinfo'].keys():
								subscr = ods['phreqinfo']['id']

						if 'created' in js.keys() and js['created'] > 0:
							jobperc = min(100,100*float(js['success']+js['failure'])/js['created'])
						else:
							jobperc = 0
						if eperc > 20 and 'phreqinfo' in ods.keys() and ods['phreqinfo'] == {}:
							issues['subscribe'].append(r['requestname'])

						if ('HIN' in r['requestname'] and r['mergedLFNBase'] != '/store/himc' ) or (r['outputdatasetinfo'][0]['name'][-3:] == 'GEN' and r['mergedLFNBase'] != '/store/generator') or (r['outputdatasetinfo'][0]['name'][-3:] in ['GEN-SIM','AODSIM'] and r['mergedLFNBase'] != '/store/mc'):
							issues['wronglfnbase'].append(r['requestname'])
							#alarmlink='https://cmsweb.cern.ch/reqmgr/view/showWorkload?requestName=%s' % r['requestname']
						if len(r['acdc'])>1:
							issues['acdc'].append(r['requestname'])
							#alarm = 'ACDC(%s)' % len(r['acdc'])
							alarmlink='https://cmst2.web.cern.ch/cmst2/mc/requests/%s.html' % r['requestname']
						if status in ['completed','closed-out'] and 'phtrinfo' in ods.keys():
							j = {}
							for i in ods['phtrinfo']:
								if 'custodial' in i.keys():
									if i['custodial'] == 'y':
										j = i
										break
							if 'perc' in j.keys():
								if j['perc'] < 100:
									issues['trstuck'].append(r['requestname'])
									#alarmlink = 'https://cmsweb.cern.ch/phedex/prod/Activity::ErrorInfo?tofilter=%s*&fromfilter=.*&report_code=.*&xfer_code=.*&to_pfn=.*%%2Fstore%%2Fmc%%2F%s%%2F%s%%2F.*&from_pfn=.*%%2Fstore%%2Fmc%%2F%s%%2F%s%%2F.*&log_detail=.*&log_validate=.*&.submit=Update#' % (custodialt1,r['acquisitionEra'],r['primaryds'],r['acquisitionEra'],r['primaryds'])
						elif status in ['acquired','running','running-open','running-closed'] and 'cooloff' in js.keys() and js['cooloff'] > 100:
							pass
							#issues['cooloff'].append(r['requestname'])
							#alarmlink='' % ()
						elif status in ['running','running-open','running-closed'] and eperc >0 and (time.time() - ods['lastmodts']) > stuck_days*24*3600:
							issues['dsstuck'].append(r['requestname'])
							#alarmlink='https://cmsweb.cern.ch/das/request?view=list&limit=10&instance=cms_dbs_prod_global&input=dataset+dataset=%s*+' % ods['name']
						if eperc >=95 and not 'SMS' in r['outputdatasetinfo'][0]['name'] and 'CMSSM' not in r['outputdatasetinfo'][0]['name'] and r['status'] in ['acquired','running-open','running-closed']:
							issues['mostlydone'].append(r['requestname'])
								
						if r['priority'] == highest_prio:
							issues['highprio'].append(r['requestname'])

						if r['requestdays'] > old_days+int(r['expectedevents']/10000000):
							issues['veryold'].append(r['requestname'])
							if r['requestdays'] not in oldest.keys():
								oldest[r['requestdays']] = []
							oldest[r['requestdays']].append(r['requestname'])
							#alarmlink = ''
						if len(r['acdc']):
							sacdc='Yes'
						else:
							sacdc=''

						if r['requestname'] in urgent_requests:
							color = '#CCCCFF'
							##issues['urgent'].append(r['requestname'])
						else:
							color = '#FFFFFF'
						f.write('<tr bgcolor=%s onMouseOver="this.bgColor=\'#DDDDDD\'" onMouseOut="this.bgColor=\'%s\'">' % (color,color))
						f.write("<td valign=top>%s</td>" % human(r['priority']))
						f.write("<td valign=top>%s<br/><a href='https://cmsweb.cern.ch/das/request?view=list&limit=100&instance=prod/global&input=dataset+dataset%%3D%s' target='_blank'>das</a></td>" % (ods['name'],ods['name']))
						if r['status'] in ['completed']:
							temp_wsum = ",<a href='https://cmsweb.cern.ch/couchdb/workloadsummary/_design/WorkloadSummary/_show/histogramByWorkflow/%s' target='_blank'>sum</a>" % r['requestname']
						else:
							temp_wsum = ''
						f.write("<td valign=top>%s<br/><a href='http://dashb-cms-job.cern.ch/dashboard/templates/web-job2/#user=&refresh=0&table=Jobs&p=1&records=25&activemenu=1&usr=&site=&submissiontool=&application=&activity=production&status=&check=submitted&tier=&date1=&date2=&sortby=jobtype&scale=linear&bars=20&ce=&rb=&grid=&jobtype=&submissionui=&dataset=&submissiontype=&task=wmagent_%s&subtoolver=&genactivity=&outputse=&appexitcode=&accesstype=' target='_blank'>dsh</a>,<a href='https://cmst2.web.cern.ch/cmst2/mc/requests/%s.html' target='_blank'>req</a>,<a href='https://cmsweb.cern.ch/reqmgr/view/details/%s' target='_blank'>det</a>,<a href='https://cmsweb.cern.ch/reqmgr/view/showWorkload?requestName=%s' target='_blank'>wld</a>%s</td>" % (r['requestname'],r['requestname'],r['requestname'],r['requestname'],r['requestname'],temp_wsum))
						f.write("<td valign=top>%s</td>" % r['team'])
						if subscr:
							f.write("<td valign=top align='left'><a href=\"https://cmsweb.cern.ch/phedex/prod/Request::View?request=%s\" target=\"_blank\">%s</a></td>" % (ods['phreqinfo']['id'],ods['phreqinfo']['custodialsite']))
						else:
							f.write("<td valign=top align='right'>&nbsp;</td>")
						f.write("<td valign=top>%.1f%%</td>" % jobperc)
						if 'created' in js.keys():
							f.write("<td valign=top align=right>%s</td>" % (js['created']))
							f.write("<td valign=top align=right>%s</td>" % (js['queued']))
							f.write("<td valign=top align=right>%s</td>" % (js['pending']))
							f.write("<td valign=top align=right><b>%s</b></td>" % (js['running']))
							f.write("<td valign=top align=right>%s</td>" % (js['cooloff']))
							f.write("<td valign=top align=right>%s</td>" % (js['success']))
							f.write("<td valign=top align=right>%s</td>" % (js['failure']))
						else:
							for ct in range(1,8):
								f.write("<td valign=top align=right>0</td>")
						f.write("<td valign=top align='right'>%s</td>" % human(r['expectedevents']))
						if 'events' in ods.keys():
							if ods['events'] > 0:
								f.write("<td valign=top align='right'>%s</td>" % (human(ods['events'])))
							else:
								f.write("<td valign=top align='right'>0</td>")
						else:
							f.write("<td valign=top align='right'>0</td>")
						f.write("<td valign=top align=right>%s</td>" % r['requestdays'])
						f.write("<td valign=top align=center>%s</td>" % len(r['acdc']))
						f.write('</tr>')
		f.write('</table>')

	f.write(foot)
	f.close()
	announce_batches = {}
	f = open('%s/closed-out.html' % mcdir,'w')
	f.write('<html><head><title>MC Status - Closed-out</title><style>td{padding:4px;}</style>\n<meta http-equiv="Refresh" content="1800">\n</head>\n')
	f.write('<body style=\'font-family:sans-serif;\'>')
	f.write(bar)

	for status in ['closed-out']:
		f.write('<h3>Requests in Closed-out</h3>')
		f.write('<table border=0 style=\'border-width:1px;border-spacing:0px;border-collapse:collapse;font-size:12px;\'>')
		f.write('<tr><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td><td><strong>%s</strong></td></tr>'% ('Prio','OutputDataset','Status','Campaign','Type','RequestName','Subscr','ExpEvts','DBSEvts','Evts%','Alarm'))
		for priority in getpriorities(s,'','',[status]):
			for r in s:
				if r['type'] not in ['MonteCarlo','MonteCarloFromGEN','TaskChain']:
					continue
				#for kk in r.keys():
				#	print "%s:\t%s" % (kk,r[kk])
				if r['type'] == 'MonteCarlo':
					split = r['events_per_job']
				elif r['type'] == 'MonteCarloFromGEN':
					split = r['lumis_per_job']
				elif r['type'] == 'TaskChain':
					split = ''
				else:
					continue
				if status == r['status'] and priority == r['priority']:
					for ods in r['outputdatasetinfo']:
						if len(r['custodialsites']) > 0:
							custodialt1 = r['custodialsites'][0]
						eperc = 0
						if 'events' in ods.keys():
							eperc = float(ods['events']) / r['expectedevents'] * 100
						phperc = ''
						transferred_events = 0
						if 'phtrinfo' in ods.keys():
							for p in ods['phtrinfo']:
								if p['custodial'] == 'y':
									if 'perc' in p.keys():
										phperc = "%s" % p['perc']
										transferred_events = int(float(ods['events']) * float(phperc) / 100)
									break
						#if js['created'] > 0:
						if 0:
							jobperc = min(100,100*float(js['success']+js['failure'])/js['created'])
						else:
							jobperc = 0
						alarmlink = ''
						alarm = ''
						subscr = 0
						if 'phreqinfo' in ods.keys():
							if 'id' in ods['phreqinfo'].keys():
								subscr = ods['phreqinfo']['id']
						if eperc > 20 and 'phreqinfo' in ods.keys() and ods['phreqinfo'] == {}:
							alarm = 'SUBSCRIBE'
							alarmlink = 'https://cmsweb.cern.ch/phedex/prod/Request::Create?type=xfer'
						elif ('HIN' in r['requestname'] and r['mergedLFNBase'] != '/store/himc') or (r['outputdatasetinfo'][0]['name'][-3:] == 'GEN' and r['mergedLFNBase'] != '/store/generator') or ('HIN' not in r['requestname'] and r['outputdatasetinfo'][0]['name'][-7:] == 'GEN-SIM' and r['mergedLFNBase'] != '/store/mc'):
							alarm = 'WRONG_LFNBASE'
							alarmlink='https://cmsweb.cern.ch/reqmgr/view/showWorkload?requestName=%s' % r['requestname']
						elif len(r['acdc'])>1 and 0:
							alarm = 'ACDC(%s)' % len(r['acdc'])
							alarmlink='https://cmst2.web.cern.ch/cmst2/mc/requests/%s.html' % r['requestname']
						elif eperc < 90 and status in ['closed-out']:
							alarm = 'MISSING_EVENTS'
							alarmlink='' % ()
						elif eperc < 99 and status in ['closed-out'] and '/SMS' in ods['name']:
							alarm = 'MISSING_EVENTS_SMS'
                                                        alarmlink='' % ()
						elif status in ['running','running-open','running-closed'] and eperc >0 and (time.time() - ods['lastmodts']) > 10*24*3600:
							alarm = 'DS_STUCK'
							alarmlink='https://cmsweb.cern.ch/das/request?view=table&limit=10&instance=cms_dbs_prod_global&input=block+dataset=%s*+' % ods['name']
						elif eta > 100:
							alarm = 'HIGH_ETA'
							alarmlink = ''
						else:
							alarm = ''
							alarmlink = ''

						if alarm != '' and r['outputdatasetinfo'][0]['status'] != 'VALID':
							color = '#FFCCCC'
						else:
							if r['campaign'] not in announce_batches.keys():
								announce_batches[r['campaign']] = []
							announce_batches[r['campaign']].append(r['outputdatasetinfo'][0]['name'])
							for ds in r['outputdatasetinfo']:
								if ds['name'] not in autosetvalid:
									if r['campaign'] in campaignconfig.keys():
										if 'announce' not in campaignconfig[r['campaign']].keys() or campaignconfig[r['campaign']]['announce'] == 'none':
											autosetvalid.append(ds['name'])
							color = '#FFFFFF'

						f.write('<tr bgcolor=%s onMouseOver="this.bgColor=\'#DDDDDD\'" onMouseOut="this.bgColor=\'%s\'">' % (color,color))
						f.write("<td valign=top>%s</td>" % human(r['priority']))
						f.write("<td valign=top>%s</td>" % ods['name'])
						f.write("<td valign=top>%s</td>" % ods['status'])
						f.write("<td valign=top>%s</td>" % r['campaign'])
						f.write("<td valign=top>%s</td>" % r['type'])
						f.write("<td style='padding:8px 8px;' valign=top>%s<br/><a href='https://cmst2.web.cern.ch/cmst2/mc/requests/%s.html' target='_blank'>req</a>,<a href='https://cmsweb.cern.ch/reqmgr/view/details/%s' target='_blank'>det</a>,<a href='https://cmsweb.cern.ch/reqmgr/view/showWorkload?requestName=%s' target='_blank'>wld</a>,<a href='https://cmsweb.cern.ch/couchdb/workloadsummary/_design/WorkloadSummary/_show/histogramByWorkflow/%s' target='_blank'>sum</a></td>" % (r['requestname'],r['requestname'],r['requestname'],r['requestname'],r['requestname']))
						if subscr:
							f.write("<td valign=top align='left'><a href=\"https://cmsweb.cern.ch/phedex/prod/Request::View?request=%s\" target=\"_blank\">%s</a></td>" % (ods['phreqinfo']['id'],ods['phreqinfo']['custodialsite']))
						else:
							f.write("<td valign=top align='right'>&nbsp;</td>")
						f.write("<td valign=top align='right'>%s</td>" % human(r['expectedevents']))
						if 'events' in ods.keys():
							if ods['events'] > 0:
								f.write("<td valign=top align='right'><a href='https://cmsweb.cern.ch/das/request?view=list&limit=100&instance=cms_dbs_prod_global&input=block+dataset%%3D%s' target='_blank'>%s</a></td>" % (ods['name'],human(ods['events'])))
							else:
								f.write("<td valign=top align='right'>0</td>")
						else:
							f.write("<td valign=top align='right'>0</td>")
						f.write("<td valign=top align='right'>%s</td>" % int(100*ods['events']/r['expectedevents']))
						if alarmlink == '':
							f.write("<td valign=top align='center'>%s</td>" % (alarm))
						else:
							f.write("<td valign=top align='center'><a href='%s' target='_blank'>%s</a></td>" % (alarmlink,alarm))
						f.write('</tr>')
		f.write('</table>')
	savelist('%s/autosetvalid.txt' % mcdir,autosetvalid)

	f.write(foot)
	f.close()

	oldbatches = os.listdir("%s/announcebatches/" % (mcdir))
	for b in oldbatches:
		if os.path.isfile("%s/%s" % ("%s/announcebatches" % (mcdir),b)):
			os.unlink("%s/%s" % ("%s/announcebatches" % (mcdir),b))
	for c in announce_batches.keys():
		f = open('%s/announcebatches/%s' % (mcdir,c),'w')
		f.write("\n".join(x for x in announce_batches[c])+'\n')
		f.close()

	f = open('%s/announce.html' % mcdir,'w')
	f.write('<html><head><title>MC Status - Announce batches</title><style>td{padding:4px;}</style>\n<meta http-equiv="Refresh" content="1800">\n</head>\n')
	f.write('<body style=\'font-family:sans-serif;\'>')
	f.write(bar)

	f.write('<h3>Datasets to be announced</h3>')
	for c in announce_batches.keys():
		f.write('<p><a href="http://cmst2.web.cern.ch/cmst2/mc/announcebatches/%s" target="_blank">%s</a>' % (c,c))
	f.close()

	f = open('%s/issues.html' % mcdir,'w')
	f.write('<html><head><title>MC Status - Issues</title><style>td{padding:4px;}</style>\n<meta http-equiv="Refresh" content="1800">\n</head>\n')
	f.write('<body style=\'font-family:sans-serif;\'>')
	f.write(bar)

	irlist = []
	for i in issues.keys():
		for r in issues[i]:
			if not r in irlist:
				irlist.append(r)
	irlist.sort()

	f.write('<h3>Force-complete (very old that are mostly done)</h3>')
	f.write('<pre>')
	for i in irlist:
		if i in issues['veryold'] and i in issues['mostlydone'] and '_EXT_' not in i:
			f.write('%s\n' % i)
	f.write('</pre>')

	if oldest.keys():
		k = max(oldest.keys())
		f.write('<h3>Oldest requests in the system (%s days)</h3>' % k)
		f.write('<pre>')
		for i in oldest[k]:
			f.write('%s\n' % i)
		f.write('</pre>')

	f.write('<h3>Highest priority</h3>')
	f.write('<pre>')
	for i in irlist:
		if i in issues['highprio'] and '_EXT_' not in i:
			f.write('%s\n' % i)
	f.write('</pre>')

	f.write('<h3>Check needed</h3>')
	f.write('<pre>')
	for i in irlist:
		if i in issues['wronglfnbase']:
			f.write('%s\n' % i)
	f.write('</pre>')

	f.write('<h3>Dataset stuck</h3>')
	f.write('<pre>')
	for i in irlist:
		if i in issues['dsstuck']:
			f.write('%s\n' % i)
	f.write('</pre>')

	f.write('<h3>Summary</h3>')

	h = ['request','priority','reqnumevts']
	for i in issues.keys():
		h.append(i)

	f.write("<table border=1>")
	f.write("<tr>")
	for i in h:
		f.write('<td align=center><strong>%s</strong></td>' % i)
	f.write("</tr>")
	for r in irlist:
		for req in s:
			if req['requestname'] == r:
				break
		f.write("<tr onMouseOver=\"this.bgColor='#DDDDDD'\" onMouseOut=\"this.bgColor='#FFFFFF'\">")
		for i in h:
			if i == 'request':
				f.write('<td>%s (<a target="_blank" href="https://cmst2.web.cern.ch/cmst2/mc/requests/%s.html">req</a>)</td>' % (r,r))
			elif i == 'priority':
				f.write('<td align=right>%s</td>' % (human(req['priority'])))
			elif i == 'reqnumevts':
				f.write('<td align=right>%s</td>' % (human(req['expectedevents'])))
			else:
				if r in issues[i]:
					color='#FF0000'
					stri='<strong>X</strong>'
				else:
					color='#00FF00'
					stri='&nbsp;'
				#f.write('<td align=center bgcolor=%s>&nbsp;</td>' % color)
				f.write('<td align=center>%s</td>' % stri)
		f.write("</tr>")
	f.write("</table>")

	f.write(foot)
	f.close()
	
	if len(issues['veryold']):
		fmonday.write('---+++++Old requests (injected >%s days ago)\n\n' % old_days)
		for r in issues['veryold']:
			for i in s:
				if r == i['requestname']:
					fmonday.write("   * %s (priority = %s)\n" % (r,i['priority']))
					break
		fmonday.write('\n')
	if len(issues['dsstuck']):
		fmonday.write('---+++++Stuck requests (no new events in DBS for >%s days)\n\n' % stuck_days)
		for r in issues['dsstuck']:
			for i in s:
				if r == i['requestname']:
					fmonday.write("   * %s (priority = %s)\n" % (r,i['priority']))
					break
		fmonday.write('\n')
	fmonday.write('[[http://cmst2.web.cern.ch/cmst2/mc/issues.html][Link to the issues summary page for details]]\n\n')

	timesummary = {}
	eventsummary = {}
	for zone in ['CNAF','KIT','IN2P3','PIC','RAL','FNAL']:
		#TODO get campaigns
		for campaign in campaignconfig.keys():
			for status in ['acquired','running','running-open','running-closed']:
				for priority in getpriorities(s,campaign,zone,status):
					remainingcpudays = 0
					remainingevents = 0
					for r in s:
						if r['type'] not in ['MonteCarlo','MonteCarloFromGEN','TaskChain']:
							continue
						if campaign == getcampaign(r) and zone == r['zone'] and status == r['status'] and priority == r['priority']:
							remainingcpudays = remainingcpudays + float(r['realremainingcpudays'])
							for o in r['outputdatasetinfo']:
								if 'events' in o.keys():
									if o['events'] < r['expectedevents']:
										remainingevents = remainingevents + r['expectedevents'] - o['events'] 
					if remainingevents < 0:
						remainingevents = 0
					if zone not in timesummary.keys():
						timesummary[zone] = {}
						eventsummary[zone] = {}
					if campaign not in timesummary[zone].keys():
						timesummary[zone][campaign] = {}
						eventsummary[zone][campaign] = {}
					if status not in timesummary[zone][campaign].keys():
						timesummary[zone][campaign][status] = {}
						eventsummary[zone][campaign][status] = {}
					if priority not in timesummary[zone][campaign][status].keys():
						timesummary[zone][campaign][status][priority] = {}
						eventsummary[zone][campaign][status][priority] = {}
					timesummary[zone][campaign][status][priority] = remainingcpudays
					eventsummary[zone][campaign][status][priority] = remainingevents

	wrsummary = {}
	for i in wrjson:
		if i['campaign'] not in wrsummary.keys():
			wrsummary[i['campaign']] = {}
		site = i['sites'][0]
		if site not in wrsummary[i['campaign']].keys():
			wrsummary[i['campaign']][site] = i['events']
		else:
			wrsummary[i['campaign']][site] = wrsummary[i['campaign']][site] + i['events']

	f = open(htmlfile,'w')

	f.write('<html><head><title>MC Status</title>\n<meta http-equiv="Refresh" content="1800">\n</head>\n<body style=\'font-family:sans-serif;\'>')
	f.write(bar)
	f.write("<table><tr><td><h3>MC+Repro@T1s</h3></td><td><h3>MC+Repro@WMA</h3></td></tr><tr><td><img height=400 src='http://dashb-cms-jobsmry.cern.ch/dashboard/request.py/resourceutilization_individual?sites=T1_CH_CERN&sites=T1_RU_JINR&sites=T1_IT_CNAF&sites=T1_US_FNAL&sites=T1_FR_CCIN2P3&sites=T1_DE_KIT&sites=T1_ES_PIC&sites=T1_UK_RAL&activities=production&activities=reprocessing&sitesSort=1&start=null&end=null&timeRange=last24&granularity=Hourly&generic=0&sortBy=0&diag1=0&diag2=0&diag3=0&diag4=0&diag5=0&diag6=0&diag7=0&diagT=0&type=a'></td><td><img height=400 src='http://dashb-cms-prod.cern.ch/dashboard/request.py/condorjobnumbers_individual?sites=All%20Servers&sitesSort=11&jobTypes=&start=null&end=null&timeRange=last48&granularity=Hourly&sortBy=4&series=All&type=r'></td></tr><tr><td><img height=400 src='http://dashb-cms-jobsmry.cern.ch/dashboard/request.py/jobnumbers_individual?sites=T0_CH_CERN&sites=T1_CH_CERN&sites=T2_CH_CERN&sites=T1_RU_JINR&sites=T1_IT_CNAF&sites=T1_US_FNAL&sites=T1_FR_CCIN2P3&sites=T1_DE_KIT&sites=T1_ES_PIC&sites=T1_UK_RAL&sites=T2_AT_Vienna&sites=T2_BE_IIHE&sites=T2_BE_UCL&sites=T2_BR_SPRACE&sites=T2_BR_UERJ&sites=T2_CH_CAF&sites=T2_CH_CERN&sites=T2_CH_CSCS&sites=T2_CN_Beijing&sites=T2_DE_DESY&sites=T2_DE_RWTH&sites=T2_EE_Estonia&sites=T2_ES_CIEMAT&sites=T2_ES_IFCA&sites=T2_FI_HIP&sites=T2_FR_CCIN2P3&sites=T2_FR_GRIF_IRFU&sites=T2_FR_GRIF_LLR&sites=T2_FR_IPHC&sites=T2_HU_Budapest&sites=T2_IN_TIFR&sites=T2_IT_Bari&sites=T2_IT_Legnaro&sites=T2_IT_Pisa&sites=T2_IT_Rome&sites=T2_KR_KNU&sites=T2_PK_NCP&sites=T2_PL_Warsaw&sites=T2_PT_LIP_Lisbon&sites=T2_PT_NCG_Lisbon&sites=T2_RU_IHEP&sites=T2_RU_INR&sites=T2_RU_ITEP&sites=T2_RU_JINR&sites=T2_RU_PNPI&sites=T2_RU_RRC_KI&sites=T2_RU_SINP&sites=T2_TR_METU&sites=T2_TW_Taiwan&sites=T2_UA_KIPT&sites=T2_UK_London_Brunel&sites=T2_UK_London_IC&sites=T2_UK_SGrid_Bristol&sites=T2_UK_SGrid_RALPP&sites=T2_US_Caltech&sites=T2_US_Florida&sites=T2_US_MIT&sites=T2_US_Nebraska&sites=T2_US_Purdue&sites=T2_US_UCSD&sites=T2_US_Wisconsin&sites=T3_US_Omaha&sites=T3_US_Colorado&sites=T2_US_Vanderbilt&activities=production&sitesSort=2&start=null&end=null&timeRange=last24&granularity=Hourly&generic=0&sortBy=0&type=r'></td><td><img height=400 src='http://dashb-cms-jobsmry.cern.ch/dashboard/request.py/jobnumbers_individual?sites=T0_CH_CERN&sites=T1_CH_CERN&sites=T2_CH_CERN&sites=T1_RU_JINR&sites=T1_IT_CNAF&sites=T1_US_FNAL&sites=T1_FR_CCIN2P3&sites=T1_DE_KIT&sites=T1_ES_PIC&sites=T1_UK_RAL&sites=T2_AT_Vienna&sites=T2_BE_IIHE&sites=T2_BE_UCL&sites=T2_BR_SPRACE&sites=T2_BR_UERJ&sites=T2_CH_CAF&sites=T2_CH_CERN&sites=T2_CH_CSCS&sites=T2_CN_Beijing&sites=T2_DE_DESY&sites=T2_DE_RWTH&sites=T2_EE_Estonia&sites=T2_ES_CIEMAT&sites=T2_ES_IFCA&sites=T2_FI_HIP&sites=T2_FR_CCIN2P3&sites=T2_FR_GRIF_IRFU&sites=T2_FR_GRIF_LLR&sites=T2_FR_IPHC&sites=T2_HU_Budapest&sites=T2_IN_TIFR&sites=T2_IT_Bari&sites=T2_IT_Legnaro&sites=T2_IT_Pisa&sites=T2_IT_Rome&sites=T2_KR_KNU&sites=T2_PK_NCP&sites=T2_PL_Warsaw&sites=T2_PT_LIP_Lisbon&sites=T2_PT_NCG_Lisbon&sites=T2_RU_IHEP&sites=T2_RU_INR&sites=T2_RU_ITEP&sites=T2_RU_JINR&sites=T2_RU_PNPI&sites=T2_RU_RRC_KI&sites=T2_RU_SINP&sites=T2_TR_METU&sites=T2_TW_Taiwan&sites=T2_UA_KIPT&sites=T2_UK_London_Brunel&sites=T2_UK_London_IC&sites=T2_UK_SGrid_Bristol&sites=T2_UK_SGrid_RALPP&sites=T2_US_Caltech&sites=T2_US_Florida&sites=T2_US_MIT&sites=T2_US_Nebraska&sites=T2_US_Purdue&sites=T2_US_UCSD&sites=T2_US_Wisconsin&sites=T3_US_Omaha&sites=T3_US_Colorado&sites=T2_US_Vanderbilt&activities=production&sitesSort=2&start=null&end=null&timeRange=last24&granularity=Hourly&generic=0&sortBy=0&type=p'></td></tr></table>")

	fmonday.write('\n\n')
	
	statuscount = {'assignment-approved':0,'assigned':0,'acquired':0,'running':0,'running-open':0,'running-closed':0,'completed':0,'closed-out':0,'failed':0}
	for r in s:
		if r['status'] in ['assignment-approved','assigned','acquired','running','running-open','running-closed','completed','closed-out','failed'] and r['type'] in ['MonteCarlo','MonteCarloFromGEN','TaskChain']:
			statuscount[r['status']] = statuscount[r['status']] + 1
			
	f.write('<h3>Requests by status</h3>')
	f.write('<table border=0 style=\'border-width:2px;border-spacing:3px;border-collapse:collapse;font-size:16px;\'>')
	fmonday.write('---+++++Requests by status\n')
	for status in ['assignment-approved','assigned','acquired','running-open','running-closed','completed','closed-out','failed']:
		f.write('<tr><td valign=top style=\'padding:5px;\'>%s</td><td align=right valign=top style=\'padding:5px;\'>%s</td></tr>' % (status,statuscount[status]))
		fmonday.write('|%s|%s|\n' % (status,statuscount[status]))
	f.write('</table>')
	fmonday.write('\n')

	summary = {}
	teams = []
	for r in s:
		if r['status'] in ['acquired','running','running-open','running-closed']:
			if r['priority'] not in summary.keys():
				summary[r['priority']] = {}
			if r['team'] not in teams:
				teams.append(r['team'])
			for priority in summary.keys():
				for team in teams:
					if team not in summary[priority]:
						summary[priority][team] = 0
			summary[r['priority']][r['team']] = summary[r['priority']][r['team']] + r['realremainingcpudays']
	#print summary

	f.write('<h3>CPUDays in acquired/running per Priority/Team for MonteCarlo/MonteCarloFromGEN/TaskChainMC</h3>')
	fmonday.write('---+++++ CPUDays in acquired/running per Priority/Team\n')
	f.write('<table border=1 style=\'border-width:1px;border-spacing:0px;border-collapse:collapse;font-size:16px;\'>')
	f.write("<tr><td bgcolor=#DDFFDD valign=top style='padding:5px;'><strong><i>PRIORITY/TEAM</i></strong></td>\n")
	fmonday.write('|*PRIORITY/TEAM*|')
	for team in teams:
		f.write('<td bgcolor=#DDFFDD valign=top style=\'padding:5px;\' align=center><strong>%s</strong></td>' % team)
		fmonday.write('*%s*|' % team)
	f.write("</tr>\n")
	fmonday.write("\n")

	keylist = summary.keys()
	keylist.sort(reverse=True)
	for priority in keylist:
		f.write("<tr><td bgcolor=#DDFFDD valign=top style='padding:5px;' align=center><strong>%s</strong></td>" % priority)
		fmonday.write('|*%s*|' % priority)
		for team in teams:
			if summary[priority][team] > 0:
				summary_string = "<strong>%.1f</strong>" % summary[priority][team]
				summary_string_monday = "*%.1f*" % summary[priority][team]
			else:
				summary_string = "%.1f" % summary[priority][team]
				summary_string_monday = summary_string
			f.write("<td valign=top style='padding:5px;' align=center>%s</td>" % summary_string)
			fmonday.write('%s|' % summary_string_monday)
		f.write("</tr>")
		fmonday.write('\n')
	f.write("</table>")

	f.write(foot)
	f.close()
	fmonday.close()

# manage acquired/running,completed,closed-out requests;purge them at every cycle
        sys.exit(0)

if __name__ == "__main__":
        main()
