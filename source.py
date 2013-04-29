#!/usr/bin/python

import cgi 
from  urlparse import urlparse
import json 
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import libvirt
import os
import sys

vmidlt = {}
vmidcounter = 0 
vmlt = {}
machines = []
imglt = []
diccpu = {}
dicpmid = {}
vmnameck = {}

def parse(req):
	dic = cgi.parse_qs(urlparse(req).query)
	if 'create' in req :
		imgtyp = int(dic['image_type'][0])
		vmname = dic['name'][0]
		vmtyp = int(dic['vm_type'][0])
		print imgtyp , vmname , vmtyp
		tmp = createvm(imgtyp , vmname , vmtyp )
		dic = {}
		dic['vmid'] = tmp
		print json.dumps(dic, indent = 4 )
		return dic
	elif 'query' in req :
		print 'query'
		tmp = int(dic['vmid'][0])
		return query(tmp)
	elif 'destroy' in req : 
		tmp = int(dic['vmid'][0])
		print "vmid to destroy is ", tmp
		tmp1 = vmdestroy(tmp)
		dic = {}
		dic['status'] = tmp1
		return dic
	elif 'types' in req :
		f = open('Vm_types', 'r')
		a = json.load(f)
		print type(a)
		print a
		return a
	elif 'listvms' in req :
		retdic = {}
		tmp = []
		tmpimid = req.split('/listvms')[0]
		tmpimid = int(tmpimid.split('/pm/')[-1])
		print tmpimid
		tmpimname = ""
		for i in dicpmid :
			if dicpmid[i] == tmpimid :
				tmpimname = i 
				break 
		print 'name is ' + tmpimname 
		for num , i in enumerate(vmidlt) :
			if vmidlt[i][-1] == 1 and vmidlt[i][1] == tmpimname :
				tmp.append(num)
		print tmp 
		retdic['vmids'] = tmp
		return retdic
	elif 'pm/list' in req  :
		retdic = {}
		tmp = []
		for i in dicpmid :
			tmp.append(dicpmid[i]) 
		retdic['pmids'] = tmp
		return retdic
			
	elif 'image' in req :
		tmp = []
		finaldic = {}
		for num  , i in enumerate(imglt) :
			dic = {}
			dic['id'] = num
			dic['name'] = i[0]
			tmp.append(dic)
		finaldic['images'] = tmp
		return finaldic
	elif 'pm' in req :
		tmpimid = int(req.split('/pm/')[-1])
		tmpimname = ""
		for i in dicpmid :
			if dicpmid[i] == tmpimid :
				tmpimname = i 
				break
		print tmpimname
		os.system("./infoextract.sh %s"  % i )
		tmp = []
		f = open('folder_info/mem' ,'r')
		a = f.readlines()
		dicmemtmp  = {}
		dicmemtmp['ram'] = int(str(a[0]).split()[1]) / 1024
		tmp.append(dicmemtmp)
		dicdisktmp = {}
		dicdisktmp['cpu'] = len(open('folder_info/cpu' , 'r').readlines())
		tmp.append(dicdisktmp)
		retdic = {}
		retdic['pmid'] = tmpimid 
		retdic['free'] =  tmp 
		return retdic
			

def query(number):
	dic ={}
	dic['vmid'] = number
	dic['name'] = vmidlt[number][3]
	dic['instance_type'] = vmidlt[number][4]
	dic['pmid'] = dicpmid[vmidlt[number][1]]
	return dic

##	vmidlt[vmidcounter] = [dom , host , imgtyp , vmname , vmtyp , 1]

def createvm( imgtyp , vmname , vmtyp) :
	if vmname in vmnameck :
		return 
	global vmidcounter
	dicmem = {}
	for i in machines :
		print "this is i::",i,"::"
		if i == "" :
			continue
		os.system("./infoextract.sh %s"  % i )
		if i not in diccpu :
			diccpu[i] = len(open('folder_info/cpu' , 'r').readlines())
		f = open('folder_info/mem' ,'r')
		a = f.readlines()
		tmp = int(str(a[0]).split()[1]) / 1024
		dicmem[i] = tmp 
	print dicmem
#	return 
	ind = -1
	print vmlt[vmtyp][0] , vmlt[vmtyp][1]
	for num  ,i in enumerate(dicmem) :
		if diccpu[i] >= vmlt[vmtyp][0] :
			if dicmem[i] >= vmlt[vmtyp][1] :
				if ind == -1 :
					ind  = i
					mini = dicmem[i] - vmlt[vmtyp][1]
				elif mini > dicmem[i] - vmlt[vmtyp][1]  :
					mini = dicmem[i] - vmlt[vmtyp][1]
					ind = i
	print "ind is " , ind
	if ind == -1 :
		return
	else :
		host = ind
#		diccpu[ind] -= vmlt[vmtyp][0]	
	print "diccpu AFTER is " , diccpu[ind]
	
#	return 
#	host = 'root@192.168.56.101'
	print imglt[imgtyp]  , imgtyp  , host , imgtyp
	os.system("scp folder_images/%s %s:/var/lib/libvirt/images/%s" %  (imglt[imgtyp][0] , host , imglt[imgtyp][0]))
	conn=libvirt.open('remote+ssh://' + host )
	
	xmlOut = conn.getCapabilities()
	print "print getInfo()"  ,conn.getInfo ()

	emulatorLoc = xmlOut.split("emulator>");
	emulatorLoc = emulatorLoc[1].split("<")[0];

	emulatorDom = xmlOut.split("<domain type='")
	emulatorDom = emulatorDom[1].split("'")[0]

	compbits = xmlOut.split("<arch>")[1]
	compbits = compbits.split("</")[0]
	print "compbits is", compbits , "done"


	domXML="<domain type='"+ emulatorDom + "'><name>" + vmname + "</name><memory>" + str(vmlt[vmtyp][1] * 1024) + "</memory><vcpu>" + str(vmlt[vmtyp][0]) + "</vcpu><os><type arch='"+compbits+"' machine='pc'>hvm</type>	<boot dev='hd'/></os><features>	<acpi/><apic/><pae/></features><on_poweroff>destroy</on_poweroff><on_reboot>restart</on_reboot><on_crash>restart</on_crash><devices><emulator>"+ emulatorLoc + "</emulator><disk type='file' device='disk'><driver name='"+ emulatorDom + "' type='raw'/><source file='/var/lib/libvirt/images/" + imglt[imgtyp][0] +"'/><target dev='hda' bus='ide'/><address type='drive' controller='0' bus='0' unit='0'/></disk></devices></domain>"


	dom=conn.defineXML(domXML)
	dom.create()
	vmidlt[vmidcounter] = [dom , host , imgtyp , vmname , vmtyp , 1]
	vmnameck[vmname] = 1
	vmidcounter += 1
	return vmidcounter - 1

def vmdestroy(number):
	if number not in vmidlt :
		return 0 
	elif vmidlt[number][-1] == 0 :
		return 0
	else :
		vmidlt[number][0].destroy()
		vmidlt[number][0].undefine()
		vmidlt[number][-1] = 0
#	        diccpu[vmidlt[number][1]] += vmidlt[[number][-2][0]]
		print "domain test-linux has been destroy"
		return 1


class myHandler(BaseHTTPRequestHandler):
	#Handler for the GET requests
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','application/json')
		self.end_headers()
		if self.path :
			print self.path
			dic = parse(self.path)
			print type(dic) ,  " IS THE TYPE OF RETURNED"
			self.wfile.write(json.dumps(dic,indent=4))
		# Send the html message
		return
def server():
	try:
		#Create a web server and define the handler to manage the
		#incoming request
		server = HTTPServer(('', 8080), myHandler)

		#Wait forever for incoming htto requests
		server.serve_forever()
		print server

	except KeyboardInterrupt:
		print '^C received, shutting down the web server'
		server.socket.close()
		
def main():
	f = open('Vm_types' , 'r') 
	vmjson = json.load(f)
	vmjson = vmjson['types']
	for i in vmjson :
		tmp = []
		for num , j in enumerate(i) :
			if num != 0 :
				tmp.append(i[j])
			else :
				tmp1 = i[j]
#		print i
		vmlt[tmp1] = tmp
	print vmlt
#	exit(0)


	f = open(sys.argv[1], 'r') 
	a = f.readlines()
	for num , i in enumerate(a) :
		machines.append(i.split('\n')[0])
		dicpmid[i.split('\n')[0]] = num
	print machines
	print dicpmid
	print 'reached here'

	f = open(sys.argv[2] , 'r')
	a = f.readlines()
	for num , i in enumerate(a) :
		tmp = i.split('/')
		tmp = tmp[-1]
		tmp = tmp.split('\n')
		img = tmp[0]

		imglt.append([img, i.split('\n')[0]])
		os.system("scp %s ./folder_images/" % i.split('\n')[0] )
	print imglt
	print "done with checking input files"

	server()

if __name__ == "__main__" :
	main()
