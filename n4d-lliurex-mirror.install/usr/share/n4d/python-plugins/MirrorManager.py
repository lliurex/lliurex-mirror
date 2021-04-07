from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
from jinja2 import Template

import tempfile

import os
import threading
import datetime
import pexpect
import signal
import re
import json

import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from multiprocessing import Process
import socket
from urllib2 import urlopen
import string
import subprocess

DEBUG = True

class MirrorManager:

	def __init__(self):
		#Default values
		self.app="domirror" # debmirror
		self.distro="llx19"
		self.llxpath = '/etc/lliurex-mirror/'
		self.applications={
			"domirror":{
				"command":"/usr/bin/domirror",
				"filename":"mirror.list",
				"configpath":"/etc/apt",
				"killsignal": signal.SIGUSR1,
				"needparams": True
			},
			"debmirror":{
				"command":"/usr/bin/debmirror",
				"filename":"debmirror.conf",
				"configpath":"/etc",
				"killsignal": signal.SIGKILL,
				"needparams": False
			}
		}
		self.llxappconfpath = os.path.join(self.llxpath,self.app)
		self.appcommand = self.applications[self.app]["command"]
		self.appneedparams = self.applications[self.app]["needparams"]
		self.appconfigfilename = self.applications[self.app]["filename"]
		self.appconfigfile = os.path.join(self.applications[self.app]["configpath"],self.applications[self.app]["filename"])
		self.appkillsignal = self.applications[self.app]["killsignal"]
		self.llxconfigspath = os.path.join(self.llxpath,'conf')
		self.llxappconfig = os.path.join(self.llxappconfpath,self.distro)
		self.httpd = {}
		self.debmirrorprocess = None

		self.tpl_env = Environment(loader=FileSystemLoader('/usr/share/n4d/templates/lliurex-mirror'))
		self.update_thread=threading.Thread()
		self.get_mirror_thread = threading.Thread()
		self.percentage=(0,None)
		self.exportpercentage = (None,None)
		self.mirrorworking = None
		self.webserverprocess = {}
		self.defaultmirrorinfo = {"status_mirror":"New","last_mirror_date":None,"mirror_size":0,"progress":0}
		self.valid_chars = "-_.%s%s" % (string.ascii_letters, string.digits)
		self.exitting = False
		self.default_path_configs = { 	'llx19':	'/usr/share/lliurex-mirror/conf/llx19.json',
		                                'llx16':	'/usr/share/lliurex-mirror/templates/llx16.json',
						'llx15':	'/usr/share/lliurex-mirror/templates/llx15.json',
						'llx14':	'/usr/share/lliurex-mirror/templates/llx14.json',
						'llx13':	'/usr/share/lliurex-mirror/templates/llx13.json',
					    }
		self.default_mirror_config = '''
{
	"NAME": "",
	"BANNER": "",
	"ORIGS" : {"1":"lliurex.net/bionic","2":"","3":""}, # 1 ORIGINAL ; 2 LOCALFILESYSTEM; 3 REMOTEURL
	"ARCHITECTURES": [ "amd64", "i386"],
	"SECTIONS": ["main", "main/debian-installer", "universe", "restricted", "multiverse", "preschool"],
	"MIRROR_PATH": "/net/mirror/llx19",
	"DISTROS": ["bionic","bionic-updates","bionic-security"],
	"IGN_GPG":1,
	"IGN_RELEASE":0,
	"CHK_MD5":0,
	"CURRENT_UPDATE_OPTION":"1"
}'''
		
	#def init
	
	def debug(self,*args,**kwargs):
		if not DEBUG:
			return None
		try:
			caller = sys._getframe().f_back.f_code.co_name
		except:
			caller = ""
		with open('/var/log/lliurex-mirror.log','a') as fp:
			for a in args:
				fp.write("{}:> {}\n".format(caller,a))
		for kw in kwargs:
			fp.write("{}:> {}={}\n".format(caller,kw,kwargs.get(kw)))
	
	def startup(self,options):
		self.n4d_vars=objects["VariablesManager"]
		self.variable=objects["VariablesManager"].get_variable("LLIUREXMIRROR")
		
		
		if self.variable==None:
			try:
				self.n4d_vars.add_variable("LLIUREXMIRROR",{},"","Lliurex Mirror info variable","n4d-lliurex-mirror")
			except Exception as e:
				pass
			
		if type(self.variable)!=type({}):
			self.variable={}
		
		try:
			for repo in self.get_available_mirrors()['msg']:
				if self.variable.has_key(repo) and self.variable[repo].has_key("status_mirror") and self.variable[repo]["status_mirror"] == "Working":
					if not self.update_thread.isAlive():
						self.variable[repo]["status_mirror"] = "Error"
						self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
				else:
					if not self.variable.has_key(repo):
						self.variable[repo] = self.defaultmirrorinfo
		except Exception as e:
			pass
	#def startup

	def apt(self):
		# executed after apt operations
		pass
		
	#def apt
	
	# service test and backup functions #
	
	def test(self):

		pass
		
	#def test
	
	def backup(self):

		pass
		
	#def backup

	def restore(self):
		pass
	#def restore
	
	def cancel_actions(self):
		try:
			self.exitting = True
			time.sleep(3)
			ret=self.debmirrorprocess.kill(self.appkillsignal)
			time.sleep(3)
			self.debmirrorprocess.close(force=True)
			return {'status':True,'msg':'Killed'}
		except Exception as e:
			return {'status':False,'msg':e}
	#def cancel_actions(self)
	
	def set_cname(self):
		#Get template
		template = self.tpl_env.get_template("cname")
		list_variables = {}
		
		list_variables = self.n4d_vars.get_variable_list(['INTERNAL_DOMAIN','HOSTNAME'])
		for x in list_variables.keys():
			if list_variables[x] == None:
				return {'status':False,'msg':'Variable ' + x + ' not defined'}
			
		#Encode vars to UTF-8
		string_template = template.render(list_variables).encode('UTF-8')
		#Open template file
		fd, tmpfilepath = tempfile.mkstemp()
		new_export_file = open(tmpfilepath,'w')
		new_export_file.write(string_template)
		new_export_file.close()
		os.close(fd)
		#Write template values
		n4d_mv(tmpfilepath,'/var/lib/dnsmasq/config/cname-mirror',True,'root','root','0644',False )
		
		return {'status':True,'msg':'Set mirror cname'}
	#def set_cname
	
	def update(self,ip,distro=None,callback_args=None,restore_info={}):

		if distro==None:
			distro=self.distro
	
		if self.update_thread.is_alive():
			return {'status':False,'msg':'Lliurex-mirror (n4d instance) is running'}
		
		self.percentage=(0,None)
		self.update_thread=threading.Thread(target=self._update,args=(ip,distro,callback_args,restore_info,))
		self.update_thread.daemon=True
		self.update_thread.start()
		
		return {'status':True,'msg':'running'}

	#def update
	
	def _update(self,ip,distro,callback_args,restore_info):
		if distro is None:
			distro = self.distro
		if not self.variable.has_key(distro):
			self.variable[distro]=self.defaultmirrorinfo 
		# link config debmirror to correct path with distro name
		self.variable[distro]['status_mirror'] = "Working"
		self.variable[distro]['progress'] = 0
		self.variable[distro]['exception_msg'] = ""
		self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
		self.build_debmirror_config(distro)
		if os.path.lexists(self.appconfigfile):
			os.remove(self.appconfigfile)
		os.symlink(os.path.join(self.llxappconfpath,distro),self.appconfigfile)
		self.mirrorworking = distro
		fd = open('/var/log/lliurex-mirror.log','a')
		import datetime
		fd.write("MIRROR START AT " + str(datetime.datetime.now())+ " \n")
		fd.flush()
		errors_found = False
		ret = None
		if self.appneedparams:
			ret = self.get_checksum_validation(distro)
			if isinstance(ret,dict) and 'status' in ret and ret['status'] and 'CHK_MD5' in ret and ret['CHK_MD5']:
				ret = ret['CHK_MD5']
		if ret is not None and (ret == 1 or ret == True):
			self.appcommand += " -v -rf"
		self.debmirrorprocess=pexpect.spawn(self.appcommand)
		download_packages = False
		emergency_counter = 0
		try:
			objects["ZCenterVariables"].add_pulsating_color("lliurexmirror")
		except:
			pass
		fd.write('Starting Loop, reading {} process {}\n'.format(self.app,self.debmirrorprocess.pid))
		fd.flush()
		while True and not self.exitting:
			try:
				emergency_counter += 1
				if emergency_counter > 100:
					download_packages = True
				self.debmirrorprocess.expect('\n',timeout=480)
				line =self.debmirrorprocess.before
				if line.find("Files to download") >= 0 or line.lower().find('starting apt-mirror'):
					download_packages = True
				line1=line.strip()
				if download_packages:
					if line1.startswith("[") and line1[5] == "]":
						self.percentage=(int(line1[1:4].strip()),self.debmirrorprocess.exitstatus)
						self.variable[distro]['progress'] = self.percentage[0]
						self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
					if line1.startswith("Everything OK") or line1.lower().startswith("end apt-mirror"):
						self.percentage=(100,self.debmirrorprocess.exitstatus)
						self.variable[distro]['progress'] = 100
						self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
				
				if errors_found:
					e=Exception(line1)
					raise e

				if line1.startswith("Errors"):
					errors_found = True
					# error is printed on next line iteration

			except pexpect.EOF:
					fd.write("Exception EOF line:'{}'\n".format(line1))
					fd.flush()
					line1 = self.debmirrorprocess.before
					if line1 != "" and line1.startswith("[") and line1[5] == "]":
						self.percentage=(int(line1[1:4].strip()),self.debmirrorprocess.exitstatus)
					self.debmirrorprocess.close()
					status = self.debmirrorprocess.exitstatus
					self.percentage=(self.percentage[0],status)
					self.variable[distro]['progress'] = self.percentage[0]
					self.variable[distro]['status_mirror'] = "Ok" if status == 0 else "Error"
					self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
					break
			except Exception as e:
				fd.write("Errors detected: '{}'\n".format(line1))
				fd.flush()
				#self.debmirrorprocess.kill(self.appkillsignal)
				#self.debmirrorprocess.close(force=True)
				self.cancel_actions()
				print(e)
				self.variable[distro]['status_mirror'] = "Error"
				self.variable[distro]["exception_msg"] = str(e)
				status = self.debmirrorprocess.exitstatus
				self.percentage=(self.percentage[0],str(e))
				self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
				break


		fd.write("EXITTING LOOP errors_found={}\n".format(errors_found))
		fd.flush()
		
		if restore_info and isinstance(restore_info,dict):
			if 'distro' in restore_info:
				self.debug(restore=restore_info)
				if 'mirrororig' in restore_info and 'optionorig' in restore_info:
					self.debug(msg='setting mirror orig')
					self.set_mirror_orig(restore_info['distro'],restore_info['mirrororig'],restore_info['optionused'])
				if 'optionorig' in restore_info:
					self.debug(msg='setting option orig')
					self.set_option_update(restore_info['distro'],restore_info['optionorig'])

		if self.exitting:
			fd.write("Forced exit from update process!!!\n")
			fd.flush()
			self.percentage=(self.percentage[0],1)
			self.variable[distro]['progress'] = self.percentage[0]
			self.variable[distro]['status_mirror'] = "Cancelled"
			self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
			fd.close()
			self.exitting = False
			return 0
		else:
			fd.close()

		if not errors_found and type(callback_args) == type({}):
			if callback_args.has_key('port'):
				import xmlrpclib as x
				c = x.ServerProxy('https://' + ip + ':9779')
				c.stop_webserver('','MirrorManager',callback_args['port'])

		self.download_time_file(distro)
		self.set_mirror_info(distro)
		self.mirrorworking = None
		try:
			objects["ZCenterVariables"].remove_pulsating_color("lliurexmirror")
		except:
			pass

	#def _update
	
	def is_alive(self):
		return {'status':self.update_thread.is_alive(),'msg':self.mirrorworking}
	#def is_alive

	def set_mirror_info(self,distro=None):
		if distro is None:
			distro=self.distro
		
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		config = json.load(open(configpath,'r'))

		mirrorpath = config["MIRROR_PATH"]
		#self.n4d_vars.set_variable("ZEROCENTERINTERNAL",self.internal_variable)
		
		MIRROR_DATE=datetime.date.today().strftime("%d/%m/%Y")
		MIRROR_SIZE=self.get_size(mirrorpath)
		
		self.variable[distro]["last_mirror_date"]=MIRROR_DATE
		self.variable[distro]["mirror_size"]=str(MIRROR_SIZE)
		self.variable[distro]["progress"]=self.percentage[0]
		
		self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
		
		#set_custom_text(self,app,text):
		txt="Updated on: " + str(MIRROR_DATE)
		txt+=" # Size: %.2fGB"%MIRROR_SIZE
		try:
			objects["ZCenterVariables"].set_custom_text("lliurexmirror",txt)
			abstract=open('/var/log/lliurex/lliurex-mirror.log','w')
			abstract.write(txt+"\n")
			abstract.close()
		except Exception as e:
			pass

	#def set_mirror_info(self):
	    
	def get_distro_options(self,distro):
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		try:
		    config = json.load(open(configpath,'r'))
		except Exception as e:
			return {'status':False,'msg': e }

		if "ORIGS" in config.keys():
			return {'status':True,'msg':config["ORIGS"].keys() }

		return {'status':False,'msg':' No options into configfile {}'.format(configpath)}

	#def get_distro_options(self,distro)
	
	def update_size_info(self,distro):
		if distro is None:
			distro=self.distro
		
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		config = json.load(open(configpath,'r'))

		mirrorpath = config["MIRROR_PATH"]
		MIRROR_SIZE=self.get_size(mirrorpath)
		self.variable[distro]["mirror_size"]=str(MIRROR_SIZE)
		self.n4d_vars.set_variable("LLIUREXMIRROR",self.variable)
		return {'status':True,'msg':MIRROR_SIZE}


	def get_size(self,start_path = '.'):
	
		total_size = 0
		try:
			for dirpath, dirnames, filenames in os.walk(start_path):
				for f in filenames:
					fp = os.path.join(dirpath, f)
					total_size += os.path.getsize(fp)
					
			total_size/=1024*1024*1024.0
			return total_size
		except:
			return 0
	
	#def get_size(start_path = '.'):
	
	def search_field(self,filepath,fieldname):
		try:
			f = open(filepath,'r')
			needle = None
			lines = f.readlines()
			for x in lines:
				if re.match('\s*'+fieldname,x):
					needle = x.strip()
			return needle
		except:
			return None
	# def search_field
	
	def get_mirror_architecture(self,distro):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		config = json.load(open(configpath,'r'))
		if not os.path.lexists(configpath):
			return {'status':False,'msg':'not exists {} to {}'.format(self.appconfigfilename,distro) }

		if "ARCHITECTURES" in config.keys():
			return {'status':True,'msg':config["ARCHITECTURES"] }

		return {'status':False,'msg':"{} hasn't architecture variable".format(self.appconfigfilename) }
	#def get_mirror_architecture
	
	def set_mirror_architecture(self,distro,archs):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		config = json.load(open(configpath,'r'))
		config['ARCHITECTURES'] = archs
		f=open(configpath,"w")
		data=unicode(json.dumps(config,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")
		f.write(data)
		f.close()
		self.build_debmirror_config(distro)
		return {'status':True,'msg':'set architecture'}
		
	#def set_mirror_architecture
	
	def get_mirror_orig(self,distro,option):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		config = json.load(open(configpath,'r'))
		if not os.path.lexists(configpath):
			return {'status':False,'msg':'not exists {} to {}'.format(self.appconfigfilename,distro) }

		if "ORIGS" in config.keys():
			if option:
				if option in config['ORIGS']:
					return {'status':True,'msg':config["ORIGS"][option] }
				else:
					return {'status':False,'msg':'No such option available'}
			else:
				ret=[]
				for opt in config['ORIGS']:
					ret.append({opt:config['ORIGS'][opt]})
				return {'status':True,'msg':ret}

		return {'status':False,'msg':"{} hasn't orig variable".format(self.appconfigfilename) }
	#def get_mirror_from

	def set_mirror_orig(self,distro,url,option):
		if distro is None:
			distro = self.distro
		if url is None:
			return {'status':False,'msg':'url is None'}
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		config = json.load(open(configpath,'r'))
		config['ORIGS'][str(option)] = url
		f=open(configpath,"w")
		data=unicode(json.dumps(config,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")
		f.write(data)
		f.close()
		self.build_debmirror_config(distro)
		return {'status':True,'msg':'set orig'}
	#def set_mirror_architecture

	def get_option_update(self,distro):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		config = json.load(open(configpath,'r'))
		if not os.path.lexists(configpath):
			return {'status':False,'msg':' no configfile {} available'.format(configpath) }

		if "CURRENT_UPDATE_OPTION" in config.keys():
			return {'status':True,'msg':config["CURRENT_UPDATE_OPTION"] }
			
		return {'status':False,'msg':' No current_update_option into configfile {}'.format(configpath)}
	#def get_option_update

	def set_option_update(self,distro,option):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		config = json.load(open(configpath,'r'))
		#Sanitize mirror url if it's a custom one
		customMirror=config['ORIGS']['3']
		if "http" in customMirror:
			customMirror=customMirror.split('//')[-1]
			config['ORIGS']['3']=customMirror
		config['CURRENT_UPDATE_OPTION'] = str(option)

		f=open(configpath,"w")
		data=unicode(json.dumps(config,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")
		f.write(data)
		f.close()
		self.build_debmirror_config(distro)
		return {'status':True,'msg':'set update option'}
	#def set_option_update

	def get_percentage(self,distro):
		if self.variable.has_key(distro):
			return {'status':True,'msg':self.variable[distro]['progress']}
		else:
			return {'status':False,'msg':'this repo nos has been configured'}
	#def get_percentage

	def build_debmirror_config(self,distro):
		if distro is None:
			distro = self.distro
		result = self.render_debmirror_config(distro)
		string_template = result['msg']
		f = open(os.path.join(self.llxappconfpath,distro),'w')
		f.write(string_template)
		f.close()
	#def build_debmirror_config

	def reset_debmirror_config(self,distro):
		if distro is None:
			distro = self.distro
		try:
			try:
				config=self.default_path_configs[distro]
				with open(config,'r') as fp_orig:
					with open(os.path.join(self.llxconfigspath,distro + ".json"),'w') as fp_dest:
						fp_dest.write(fp_orig.read())
			except:
				return {'status': False, 'msg': e}
			self.build_debmirror_config(distro)
			return {'status': True, 'msg': 'CONFIG RESET'}
		except Exception as e:
			return {'status': False, 'msg': e}
	#def reset_debmirror_config(self,distro)
	
	def render_debmirror_config(self,arg):
		if type(arg) == type(""):
			return self._render_debmirror_config_distro(arg)
		if type(arg) == type({}):
			return self._render_debmirror_config_values(arg)
	#def render_debmirror_config

	def _render_debmirror_config_distro(self,distro):
		template = self.tpl_env.get_template(self.appconfigfilename)
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		config = json.load(open(configpath,'r'))
		return {'status':True,'msg':template.render(config).encode('utf-8')}
	#def render_debmirror_config

	def _render_debmirror_config_values(self,config):
		template = self.tpl_env.get_template(self.appconfigfilename)
		return {'status':True,'msg':template.render(config).encode('utf-8')}
	#def _render_debmirror_config_values

	def enable_webserver_into_folder(self,path):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind(('localhost', 0))
		addr, port = s.getsockname()
		s.close()
		self.webserverprocess[str(port)] = Process(target=self._enable_webserver_into_folder,args=(port,path,))
		self.webserverprocess[str(port)].start()
		return {'status':True,'msg':port}
	#enable_webserver_into_folder

	def _enable_webserver_into_folder(self,port,path):
		try:
			iface = '127.0.0.1'
			sock = (iface,port)
			proto = "HTTP/1.0"
			os.chdir(path)
			handler = SimpleHTTPRequestHandler
			handler.protocol_version = proto
			self.httpd[str(port)] = BaseHTTPServer.HTTPServer(sock,handler)
			self.httpd[str(port)].serve_forever()
		except Exception as e:
			return None
	#_enable_webserver_into_folder

	def stop_webserver(self,port):
		if self.webserverprocess.has_key(port):
			self.webserverprocess[port].terminate()
			self.webserverprocess.pop(port)
			return {'status':True,'msg':'Server stopped'}
		return {'status':False,'msg':'Server not exists'}
	#stop_webserver
	
	def set_checksum_validation(self,distro,status):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		config = json.load(open(configpath,'r'))
		config['CHK_MD5'] = status

		f=open(configpath,"w")
		data=unicode(json.dumps(config,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")
		f.write(data)
		f.close()

		self.build_debmirror_config(distro)
		return {'status':True,'msg':'set checksum validation'}
	#set_checksum_validation
	
	def get_checksum_validation(self,distro):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		config = json.load(open(configpath,'r'))
		if not os.path.lexists(configpath):
			return {'status':False,'msg':'not exists {} to {}'.format(self.appconfigfilename,distro) }
		if "IGN_GPG" in config.keys():
			return {'status':True,'msg':config["CHK_MD5"] }

		return {'status':False,'msg':"{} hasn't orig variable".format(self.appconfigfilename) }
	#get_checksum_validation
	
	def get_available_mirrors(self):
		versions = os.listdir(self.llxconfigspath)
		versions = [ version.replace('.json','') for version in versions if version.endswith('.json')]
		return {'status':True,'msg':versions}

	def stopupdate(self):
		try:
			self.cancel_actions()
			self.debmirrorprocess.terminate()
			return {'status':True,'msg':'{} stopped'.format(self.app)}
		except Exception as e:
			return {'status':False,'msg':str(e)}

	def stopgetmirror(self):
		try:
			self.get_mirror_process.terminate()
			return {'status':True,'msg':'{} stopped'.format(self.app)}
		except Exception as e:
			return {'status':False,'msg':str(e)}

	def download_time_file(self,distro):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		config = json.load(open(configpath,'r'))
		path=config["MIRROR_PATH"]
		f="time-of-last-update"
		dest=os.path.join(path,f)

		orig_mirror=self.get_mirror_orig(distro,"1")
		url_mirror="http://"+os.path.join(orig_mirror['msg'],f)

		return self.get_time_file(url_mirror,dest)

	# # def download_time_file

	def get_time_file(self,url,dest):
		
		try:
			r=urlopen(url)
			f=open(dest,"wb")
			f.write(r.read())
			f.close()
			r.close()
			return {'status':True,'msg':dest + 'successfully downloaded.'}
		except Exception as e:
			return {'status':False,'msg':'Error downloading' + dest + ':' + str(e)}
	# def get_time_file

	def is_update_available(self,distro=None):

		if distro is None:
			return {'status':False,'msg':"No distro selected",'action':'nothing'}
		configpath = os.path.join(self.llxconfigspath,"%s.json"%distro)
		config = json.load(open(configpath,'r'))
		path = config["MIRROR_PATH"]
		file_time_name = "time-of-last-update"
		file_local_mirror = os.path.join(path,file_time_name)

		if os.path.isfile(file_local_mirror):
			url_pool = "http://"+os.path.join(config["ORIGS"]['1'],file_time_name)
			file_pool = os.path.join("/tmp",file_time_name)

			exist_file_pool = self.get_time_file(url_pool,file_pool)
			if exist_file_pool['status']:
				file_local_mirror_content=open(file_local_mirror,"r")
				file_local_miror_datetime=(file_local_mirror_content.readline().strip()).split("_")
				file_pool_content=open(file_pool,'r')
				file_pool_datetime=(file_pool_content.readline().strip()).split("_")
				file_local_mirror_content.close()
				file_pool_content.close()

				date_local_mirror=datetime.datetime.strptime(file_local_miror_datetime[0],"%Y/%m/%d")
				date_pool=datetime.datetime.strptime(file_pool_datetime[0],"%Y/%m/%d")

				if date_local_mirror==date_pool:
					time_local_mirror=datetime.datetime.strptime(file_local_miror_datetime[1],"%H:%M")	
					time_pool=datetime.datetime.strptime(file_pool_datetime[1],"%H:%M")

					if time_local_mirror<time_pool:
						return {'status':False,'msg':'Mirror not updated','action':'update'}
					else:
						return {'status':True,'msg':'Mirror is updated','action':'nothing'}

				elif date_local_mirror<date_pool:
					return {'status':False,'msg':'Mirror not updated','action':'update'}
				else:
					return {'status':True,'msg':'Mirror is updated','action':'nothing'}	
			else:
				return {'status':False,'msg':exist_file_pool['msg'],'action':'nothing'}	

		else:
			return {'status':False,'msg':file_local_mirror + ' does not exist.','action':'nothing'}

	# def is_update_available

	def new_mirror_config(self,config):
		name = config["NAME"].lower().strip()
		name = ''.join(c for c in name if c in self.valid_chars)

		# Checks
		if name == "":
			return {'status':False,'msg':"Name can't be empty"}
		while True:
			newconfigpath = os.path.join(self.llxconfigspath,name + '.json')
			if not os.path.lexists(newconfigpath):
				break
			name = name + "1"

		data=unicode(json.dumps(config,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")
		f = open(newconfigpath,'w')
		f.write(data)
		f.close()
		self.variable[name] = self.defaultmirrorinfo
		return {'status':True,'msg':name}
	#def new_mirror_config

	def get_all_configs(self):
		versions = os.listdir(self.llxconfigspath)
		allconfigs = {}
		for version in versions:
			configfile = os.path.join(self.llxconfigspath,version)
			f = open(configfile,'r')
			allconfigs[version.replace('.json','')] = json.load(f)
			f.close()
			#Sanitize mirror url if it's a custom one
			customMirror=allconfigs[version.replace('.json','')]['ORIGS']['3']
			if "http" in customMirror:
				customMirror=customMirror.split('//')[-1]
				allconfigs[version.replace('.json','')]['ORIGS']['3']=customMirror
		return {'status':True,'msg':allconfigs}
	#def get_all_configs

	def update_mirror_config(self,mirror,config):
		configpath = os.path.join(self.llxconfigspath,mirror + ".json")

		f=open(configpath,"w")

		data=unicode(json.dumps(config,indent=4,encoding="utf-8",ensure_ascii=False)).encode("utf-8")
		f.write(data)
		f.close()

		return {'status':True,'msg':'Updated config'}
	#def update_mirror_config

	def get_client_ip(self,ip):
		return {'status':True,'msg':ip}
	#def get_client_ip

	def is_alive_get_mirror(self):
		return {'status':self.get_mirror_thread.is_alive(),'msg':self.exportpercentage}
	#def is_alive_get_mirror

	def get_mirror(self,config_path,callback_args):
		self.get_mirror_thread = threading.Thread(target=self._get_mirror,args=(config_path,callback_args,))
		self.get_mirror_thread.daemon = True
		self.get_mirror_thread.start()
	#def get_mirror

	def _get_mirror(self,config_path,callback_args):
		ret = None
		if self.appneedparams:
			ret = self.get_checksum_validation(distro)
			if isinstance(ret,dict) and 'status' in ret and ret['status'] and 'CHK_MD5' in ret and ret['CHK_MD5']:
				ret = ret['CHK_MD5']
		if ret is not None and (ret == 1 or ret == True):
			self.appcommand += " -v -rf"
		self.get_mirror_process = pexpect.spawn("{} --config-file={}".format(self.appcommand,config_path))
		while True:
			try:
				self.get_mirror_process.expect('\n')
				line =self.get_mirror_process.before
				line1=line.strip("\n")
				if line1.startswith("[") and line1[5] == "]":
					self.exportpercentage = (int(line1[1:4].strip()),self.get_mirror_process.exitstatus)
			except pexpect.EOF:
				line1 = self.get_mirror_process.before
				if line1 != "" and line1.startswith("[") and line1[5] == "]":
					self.exportpercentage=(int(line1[1:4].strip()),self.get_mirror_process.exitstatus)
				self.get_mirror_process.close()
				status = self.get_mirror_process.exitstatus
				self.exportpercentage=(self.exportpercentage[0],status)
				break
			except Exception as e:
				break
		if callback_args.has_key('port') and callback_args.has_key('ip'):
			import xmlrpclib as x
			c = x.ServerProxy('https://' + callback_args['ip'] + ':9779')
			c.stop_webserver('','MirrorManager',callback_args['port'])
	#def _get

	def get_last_log(self):
		import base64
		p = subprocess.Popen('lliurex-mirror-get-last-log',stdout=subprocess.PIPE)
		path = p.communicate()[0].strip()
		f = open(path,'r')
		content = f.readlines()
		onelinecontent = ''.join(content)
		return {'status':True,'msg':base64.b64encode(onelinecontent)}
	#def get_last_log(self):
	
	def is_mirror_available(self):
		import fnmatch
		config=self.get_all_configs()
		path=str(config['msg'][self.distro]['MIRROR_PATH'])
		found=False
		for root,dirnames,filenames in os.walk(path+'/pool/main/l/lliurex-version-timestamp/'):
			for filename in fnmatch.filter(filenames,'lliurex-version-timestamp_*.deb'):
				found=True
		if found:
			return {'status':True,'msg':'Mirror available'}
		else:
			return {'status':False,'msg':'Mirror unavailable'}
	#def is_mirror_available(self):
