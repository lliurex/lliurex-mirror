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
import sys
import time
import fnmatch
import datetime

from http.server import HTTPServer,SimpleHTTPRequestHandler
from multiprocessing import Process
import socket
from urllib.request import urlopen
import string
import subprocess
from n4d.server.core import Core
import n4d.responses
from n4d.utils import n4d_mv
from n4d.client import Client
import base64
import ssl
from n4d.client import Client

DEBUG = True

class MirrorManager:
	def __init__(self):
		try:
			self.n4d = Core.get_core()
		except Exception as e:
			print('Exception: {}'.format(e))
			sys.exit(1)
		#Default values
		self.app="domirror" # debmirror
		self.distro="llx21"
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
		self.default_path_configs = { 
						'llx21':	'/usr/share/lliurex-mirror/conf/llx21.json',
						'llx19':	'/usr/share/lliurex-mirror/conf/llx19.json',
					    }
		self.default_mirror_config = '''
{
	"NAME": "",
	"BANNER": "",
	"ORIGS" : {"1":"lliurex.net/focal","2":"","3":""}, # 1 ORIGINAL ; 2 LOCALFILESYSTEM; 3 REMOTEURL
	"ARCHITECTURES": [ "amd64" ],
	"SECTIONS": ["main", "main/debian-installer", "universe", "multiverse"],
	"MIRROR_PATH": "/net/mirror/llx21",
	"DISTROS": ["focal","focal-updates","focal-security"],
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
		self.variable=self.n4d.get_variable("LLIUREXMIRROR").get('return',None)
		
		if self.variable is None:
			try:
				self.n4d.set_variable("LLIUREXMIRROR",{})
			except Exception as e:
				pass
			
		if not isinstance(self.variable,dict):
			self.variable={}
		
		try:
			mirrors = self.get_available_mirrors().get('return',None)
			if mirrors:
				for repo in mirrors:
					if repo in self.variable and isinstance(self.variable[repo],dict) and "status_mirror" in self.variable[repo] and self.variable[repo]["status_mirror"] == "Working":
						if not self.update_thread.isAlive():
							self.variable[repo]["status_mirror"] = "Error"
					else:
						if repo not in self.variable:
							self.variable[repo] = self.defaultmirrorinfo
				for other in [ key for key in self.variable.keys() if key not in mirrors ]:
					del self.variable[other]
				self.n4d.set_variable("LLIUREXMIRROR",self.variable)
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
			return n4d.responses.build_successful_call_response('Killed')
			# return {'status':True,'msg':'Killed'}
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg=e)
			# return {'status':False,'msg':e}
	#def cancel_actions(self)
	
	def set_cname(self):
		#Get template
		template = self.tpl_env.get_template("cname")
		list_variables = {}
		try:
			list_variables = self.n4d.get_variable_list(['INTERNAL_DOMAIN','HOSTNAME']).get('return',{})
		except Exception as e:
			return n4d.responses.build_invalid_arguments_response(-1)
		for x in list_variables.keys():
			if list_variables.get(x,None) in [ '', None ]:
				return n4d.responses.build_failed_call_response(ret_msg='Variable {} not defined or empty'.format(x))
				# return {'status':False,'msg':'Variable ' + x + ' not defined'}
			
		#Encode vars to UTF-8
		string_template = template.render(list_variables)
		#Open template file
		fd, tmpfilepath = tempfile.mkstemp()
		new_export_file = open(tmpfilepath,'w')
		new_export_file.write(string_template)
		new_export_file.close()
		os.close(fd)
		#Write template values
		n4d_mv(tmpfilepath,'/var/lib/dnsmasq/config/cname-mirror',True,'root','root','0644',False )
		return n4d.responses.build_successful_call_response('Set mirror cname')
		#return {'status':True,'msg':'Set mirror cname'}
	#def set_cname

	def update(self,user=None,ip=None,distro=None,callback_args=None,restore_info={}):
		if distro==None:
			distro=self.distro
	
		if self.update_thread.is_alive():
			return n4d.responses.build_failed_call_response(ret_msg='Lliurex-mirror (n4d instance) is running')
			# return {'status':False,'msg':'Lliurex-mirror (n4d instance) is running'}
		
		self.percentage=(0,None)
		self.update_thread=threading.Thread(target=self._update,args=(ip,distro,callback_args,restore_info,))
		self.update_thread.daemon=True
		self.update_thread.start()
		
		return n4d.responses.build_successful_call_response('running')
		# return {'status':True,'msg':'running'}

	#def update
	
	def _update(self,ip,distro,callback_args,restore_info):
		if distro is None:
			distro = self.distro
		if isinstance(self.variable,dict) and distro not in self.variable:
			self.variable[distro]=self.defaultmirrorinfo 
		# link config debmirror to correct path with distro name
		self.variable[distro]['status_mirror'] = "Working"
		self.variable[distro]['progress'] = 0
		self.variable[distro]['exception_msg'] = ""
		self.n4d.set_variable("LLIUREXMIRROR",self.variable)
		self.build_debmirror_config(distro)
		if os.path.lexists(self.appconfigfile):
			os.remove(self.appconfigfile)
		os.symlink(os.path.join(self.llxappconfpath,distro),self.appconfigfile)
		self.mirrorworking = distro
		fd = open('/var/log/lliurex-mirror.log','a')
		fd.write("MIRROR START AT " + str(datetime.datetime.now())+ " \n")
		fd.flush()
		errors_found = False
		ret = None
		if self.appneedparams:
			try:
				ret = self.get_checksum_validation(distro)
			except Exception as e:
				return n4d.responses.build_unhandled_error_response()
		if ret is not None and ret.get('status') == 0 and ret.get('return') in [1,True]:
			tokens = self.appcommand.split()
			for x in '-v -rf'.split():
				if x not in tokens:
					self.appcommand += " {}".format(x)
		self.debmirrorprocess=pexpect.spawn(self.appcommand)
		download_packages = False
		emergency_counter = 0
		try:
			zc = self.n4d.get_plugin('ZCenterVariables')
			zc.add_pulsating_color("lliurexmirror")
		except:
			pass
		fd.write('Starting Loop, reading {} process {}\n'.format(self.app,self.debmirrorprocess.pid))
		fd.flush()
		self.exitting = False
		while True and not self.exitting:
			try:
				emergency_counter += 1
				if emergency_counter > 100:
					download_packages = True
				self.debmirrorprocess.expect('\n',timeout=480)
				line =self.debmirrorprocess.before.decode('utf8').strip()
				if line.find("Files to download") >= 0 or 'starting apt-mirror' in line.lower():
					download_packages = True
				if download_packages:
					if line.startswith("[") and line[5] == "]":
						self.percentage=(int(line[1:4].strip()),self.debmirrorprocess.exitstatus)
						self.variable[distro]['progress'] = self.percentage[0]
						self.n4d.set_variable("LLIUREXMIRROR",self.variable)
					if line.startswith("Everything OK") or line.lower().startswith("end apt-mirror"):
						self.percentage=(100,self.debmirrorprocess.exitstatus)
						self.variable[distro]['progress'] = 100
						self.n4d.set_variable("LLIUREXMIRROR",self.variable)
				
				if errors_found:
					e=Exception(line)
					raise e

				if line.startswith("Errors"):
					errors_found = True
					# error is printed on next line iteration

			except pexpect.exceptions.EOF:
					fd.write("Exception EOF line:'{}'\n".format(line))
					fd.flush()
					line = self.debmirrorprocess.before.decode('utf8').strip()
					if line != "" and line.startswith("[") and line[5] == "]":
						self.percentage=(int(line[1:4].strip()),self.debmirrorprocess.exitstatus)
					self.debmirrorprocess.close()
					status = self.debmirrorprocess.exitstatus
					self.percentage=(self.percentage[0],status)
					self.variable[distro]['progress'] = self.percentage[0]
					self.variable[distro]['status_mirror'] = "Ok" if status == 0 else "Error"
					self.n4d.set_variable("LLIUREXMIRROR",self.variable)
					break
			except Exception as e:
				fd.write("Errors detected: '{}'\n".format(line))
				fd.flush()
				#self.debmirrorprocess.kill(self.appkillsignal)
				#self.debmirrorprocess.close(force=True)
				self.cancel_actions()
				print(e)
				self.variable[distro]['status_mirror'] = "Error"
				self.variable[distro]["exception_msg"] = str(e)
				status = self.debmirrorprocess.exitstatus
				self.percentage=(self.percentage[0],str(e))
				self.n4d.set_variable("LLIUREXMIRROR",self.variable)
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
			self.n4d.set_variable("LLIUREXMIRROR",self.variable)
			fd.close()
			self.exitting = False
			return 0
		else:
			fd.close()

		if not errors_found and isinstance(callback_args,dict):
			if 'port' in callback_args:
				n4d_cli = Client(address='https://' + ip + ':9779')
				n4d_cli.MirrorManager.stop_webserver(callback_args['port'])

		self.download_time_file(distro)
		self.set_mirror_info(distro)
		self.mirrorworking = None
		try:
			zc = self.n4d.get_plugin("ZCenterVariables")
			zc.remove_pulsating_color("lliurexmirror")
		except:
			pass

	#def _update
	
	def is_alive(self):
		ret = {'status':self.update_thread.is_alive(),'msg':'{}'.format(self.mirrorworking)}
		return n4d.responses.build_successful_call_response(ret)
		# return {'status':self.update_thread.is_alive(),'msg':self.mirrorworking}
	#def is_alive

	def set_mirror_info(self,distro=None):
		if distro is None:
			distro=self.distro
		
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg="Fail when parsing json file {}".format(configpath))
		mirrorpath = config["MIRROR_PATH"]
		#self.n4d_vars.set_variable("ZEROCENTERINTERNAL",self.internal_variable)
		
		MIRROR_DATE=datetime.date.today().strftime("%d/%m/%Y")
		MIRROR_SIZE=self.get_size(mirrorpath)
		
		self.variable[distro]["last_mirror_date"]=MIRROR_DATE
		self.variable[distro]["mirror_size"]=str(MIRROR_SIZE)
		self.variable[distro]["progress"]=self.percentage[0]
		
		self.n4d.set_variable("LLIUREXMIRROR",self.variable)
		
		#set_custom_text(self,app,text):
		txt="Updated on: " + str(MIRROR_DATE)
		txt+=" # Size: %.2fGB"%MIRROR_SIZE
		try:
			zc = self.n4d.get_plugin("ZCenterVariables")
			zc.set_custom_text("lliurexmirror",txt)
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
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
			# return {'status':False,'msg': e }

		if "ORIGS" in config.keys():
			return n4d.responses.build_successful_call_response(list(config["ORIGS"].keys()))
			# return {'status':True,'msg':config["ORIGS"].keys() }

		return n4d.responses.build_failed_call_response(ret_msg='No options into configfile {}'.format(configpath))
		# return {'status':False,'msg':' No options into configfile {}'.format(configpath)}

	#def get_distro_options(self,distro)
	
	def update_size_info(self,distro):
		if distro is None:
			distro=self.distro
		
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
		mirrorpath = config["MIRROR_PATH"]
		MIRROR_SIZE=self.get_size(mirrorpath)
		self.variable[distro]["mirror_size"]=str(MIRROR_SIZE)
		self.n4d.set_variable("LLIUREXMIRROR",self.variable)
		return n4d.responses.build_successful_call_response(MIRROR_SIZE)
		# return {'status':True,'msg':MIRROR_SIZE}


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
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
		if not os.path.lexists(configpath):
			return n4d.responses.build_failed_call_response(ret_msg='not exists {} to {}'.format(self.appconfigfilename,distro))
			# return {'status':False,'msg':'not exists {} to {}'.format(self.appconfigfilename,distro) }

		if "ARCHITECTURES" in config.keys():
			return n4d.responses.build_successful_call_response(config["ARCHITECTURES"])
			# return {'status':True,'msg':config["ARCHITECTURES"] }

		return n4d.responses.build_failed_call_response(ret_msg="{} hasn't architecture variable".format(self.appconfigfilename))
		# return {'status':False,'msg':"{} hasn't architecture variable".format(self.appconfigfilename) }
	#def get_mirror_architecture
	
	def set_mirror_architecture(self,distro,archs):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
		config['ARCHITECTURES'] = archs
		f=open(configpath,"w")
		data=json.dumps(config,indent=4,ensure_ascii=False)
		f.write(data)
		f.close()
		self.build_debmirror_config(distro)
		return n4d.responses.build_successful_call_response('set architecture')
		# return {'status':True,'msg':'set architecture'}
		
	#def set_mirror_architecture
	
	def get_mirror_orig(self,distro,option):
		if distro is None or not isinstance(distro,str):
			distro = self.distro
		if isinstance(option,int):
			option = str(option)
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		try:
			if not os.path.lexists(configpath):
				return n4d.responses.build_failed_call_response(ret_msg='not exists {} to {}'.format(self.appconfigfilename,distro))
				# return {'status':False,'msg':'not exists {} to {}'.format(self.appconfigfilename,distro) }
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
		

		if "ORIGS" in config.keys():
			if option:
				if option in config['ORIGS']:
					return n4d.responses.build_successful_call_response(config["ORIGS"][option])
					# return {'status':True,'msg':config["ORIGS"][option] }
				else:
					return n4d.responses.build_failed_call_response(ret_msg='No such option available')
					# return {'status':False,'msg':'No such option available'}
			else:
				ret=[]
				for opt in config['ORIGS']:
					ret.append({opt:config['ORIGS'][opt]})
				return n4d.responses.build_successful_call_response(ret)
				# return {'status':True,'msg':ret}
		return n4d.responses.build_failed_call_response(ret_msg="{} hasn't orig variable".format(self.appconfigfilename))
		# return {'status':False,'msg':"{} hasn't orig variable".format(self.appconfigfilename) }
	#def get_mirror_from

	def set_mirror_orig(self,distro,url,option):
		if distro is None:
			distro = self.distro
		if url is None:
			return n4d.responses.build_failed_call_response(ret_msg='url is None')
			# return {'status':False,'msg':'url is None'}
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
		config['ORIGS'][str(option)] = url
		f=open(configpath,"w")
		data=json.dumps(config,indent=4,ensure_ascii=False)
		f.write(data)
		f.close()
		self.build_debmirror_config(distro)
		return n4d.responses.build_successful_call_response('set orig')
		# return {'status':True,'msg':'set orig'}
	#def set_mirror_architecture

	def get_option_update(self,distro):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		if not os.path.lexists(configpath):
			return n4d.responses.build_failed_call_response(ret_msg='no configfile {} available'.format(configpath))
			# return {'status':False,'msg':' no configfile {} available'.format(configpath) }
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
		if "CURRENT_UPDATE_OPTION" in config.keys():
			return n4d.responses.build_successful_call_response(config["CURRENT_UPDATE_OPTION"])
			# return {'status':True,'msg':config["CURRENT_UPDATE_OPTION"] }

		return n4d.responses.build_failed_call_response(ret_msg='No current_update_option into configfile {}'.format(configpath))	
		# return {'status':False,'msg':' No current_update_option into configfile {}'.format(configpath)}
	#def get_option_update

	def set_option_update(self,distro,option):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
		#Sanitize mirror url if it's a custom one
		customMirror=config['ORIGS']['3']
		if "http" in customMirror:
			customMirror=customMirror.split('//')[-1]
			config['ORIGS']['3']=customMirror
		config['CURRENT_UPDATE_OPTION'] = str(option)

		f=open(configpath,"w")
		data=json.dumps(config,indent=4,ensure_ascii=False)
		f.write(data)
		f.close()
		self.build_debmirror_config(distro)
		return n4d.responses.build_successful_call_response('set update option')
		# return {'status':True,'msg':'set update option'}
	#def set_option_update

	def get_percentage(self,distro):
		if isinstance(self.variable,dict) and distro in self.variable:
			return n4d.responses.build_successful_call_response(self.variable[distro]['progress'])
			# return {'status':True,'msg':self.variable[distro]['progress']}
		else:
			return n4d.responses.build_failed_call_response(ret_msg='this repo not has been configured')
			# return {'status':False,'msg':'this repo nos has been configured'}
	#def get_percentage

	def build_debmirror_config(self,distro):
		if distro in [None,""]:
			distro = self.distro
		result = self.render_debmirror_config(distro)
		string_template = result['return']
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
				return n4d.responses.build_failed_call_response(ret_msg=e)
				# return {'status': False, 'msg': e}
			self.build_debmirror_config(distro)
			return n4d.responses.build_successful_call_response('CONFIG RESET')
			# return {'status': True, 'msg': 'CONFIG RESET'}
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg=e)
			# return {'status': False, 'msg': e}
	#def reset_debmirror_config(self,distro)
	
	def render_debmirror_config(self,arg):
		if isinstance(arg,str):
			return self._render_debmirror_config_distro(arg)
		if isinstance(arg,dict):
			return self._render_debmirror_config_values(arg)
	#def render_debmirror_config

	def _render_debmirror_config_distro(self,distro):
		template = self.tpl_env.get_template(self.appconfigfilename)
		try:
			configpath = os.path.join(self.llxconfigspath,distro + ".json")
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg="Error importing json file, {}".format(configpath))
		return n4d.responses.build_successful_call_response(template.render(config))
		# return {'status':True,'msg':template.render(config).encode('utf-8')}
	#def render_debmirror_config

	def _render_debmirror_config_values(self,config):
		template = self.tpl_env.get_template(self.appconfigfilename)
		return n4d.responses.build_successful_call_response(template.render(config))
		# return {'status':True,'msg':template.render(config).encode('utf-8')}
	#def _render_debmirror_config_values

	def enable_webserver_into_folder(self,path):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.bind(('localhost', 0))
			addr, port = s.getsockname()
			s.close()
			self.webserverprocess[str(port)] = Process(target=self._enable_webserver_into_folder,args=(port,path,))
			self.webserverprocess[str(port)].start()
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='{}'.format(e))
		return n4d.responses.build_successful_call_response(port)
		# return {'status':True,'msg':port}
	#enable_webserver_into_folder

	def _enable_webserver_into_folder(self,port,path):
		try:
			iface = '127.0.0.1'
			sock = (iface,port)
			proto = "HTTP/1.0"
			os.chdir(path)
			handler = SimpleHTTPRequestHandler
			handler.protocol_version = proto
			self.httpd[str(port)] = HTTPServer(sock,handler)
			self.httpd[str(port)].serve_forever()
		except Exception as e:
			return None
	#_enable_webserver_into_folder

	def stop_webserver(self,port):
		port = str(port)
		if isinstance(self.webserverprocess,dict) and port in self.webserverprocess:
			self.webserverprocess[port].terminate()
			self.webserverprocess.pop(port)
			return n4d.responses.build_successful_call_response('Server stopped')
			# return {'status':True,'msg':'Server stopped'}
		return n4d.responses.build_failed_call_response(ret_msg='Server not exists')
		# return {'status':False,'msg':'Server not exists'}
	#stop_webserver
	
	def set_checksum_validation(self,distro,status):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath, distro + ".json")
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg="Error importing json file, {}".format(configpath))
		config['CHK_MD5'] = status

		f=open(configpath,"w")
		data=json.dumps(config,indent=4,ensure_ascii=False)
		f.write(data)
		f.close()

		self.build_debmirror_config(distro)
		return n4d.responses.build_successful_call_response('set checksum validation')
		# return {'status':True,'msg':'set checksum validation'}
	#set_checksum_validation
	
	def get_checksum_validation(self,distro):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		try:
			if not os.path.lexists(configpath):
				return n4d.responses.build_failed_call_response(ret_msg='not exists {} to {}'.format(self.appconfigfilename,distro))
			# return {'status':False,'msg':'not exists {} to {}'.format(self.appconfigfilename,distro) }
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Error importing json distro file {},{}'.format(configpath,e))
		if "IGN_GPG" in config.keys():
			return n4d.responses.build_successful_call_response(config["CHK_MD5"])
			# return {'status':True,'msg':config["CHK_MD5"] }
		return n4d.responses.build_failed_call_response(ret_msg="{} hasn't orig variable".format(self.appconfigfilename))
		# return {'status':False,'msg':"{} hasn't orig variable".format(self.appconfigfilename) }
	#get_checksum_validation
	
	def get_available_mirrors(self):
		try:
			versions = os.listdir(self.llxconfigspath)
			versions = [ version.replace('.json','') for version in versions if version.endswith('.json')]
			return n4d.responses.build_successful_call_response(versions)
			#return {'status':True,'msg':versions}
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg=str(e))

	def stopupdate(self):
		try:
			self.cancel_actions()
			self.debmirrorprocess.terminate()
			return n4d.responses.build_successful_call_response('{} stopped'.format(self.app))
			# return {'status':True,'msg':'{} stopped'.format(self.app)}
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg=str(e))
			# return {'status':False,'msg':str(e)}

	def stopgetmirror(self):
		try:
			self.get_mirror_process.terminate()
			return n4d.responses.build_successful_call_response('{} stopped'.format(self.app))
			# return {'status':True,'msg':'{} stopped'.format(self.app)}
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg=str(e))
			#return {'status':False,'msg':str(e)}

	def download_time_file(self,distro):
		if distro is None:
			distro = self.distro
		configpath = os.path.join(self.llxconfigspath,distro + ".json")
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg="Error importing json file, {}".format(configpath))
		path=config["MIRROR_PATH"]
		f="time-of-last-update"
		dest=os.path.join(path,f)

		orig_mirror=self.get_mirror_orig(distro,"1").get('return')
		if not orig_mirror:
			return n4d.responses.build_unhandled_error_response(ret_msg='Error gettting mirror orig')
		url_mirror="http://"+os.path.join(orig_mirror,f)

		return self.get_time_file(url_mirror,dest)
	# def download_time_file

	def get_time_file(self,url,dest):
		try:
			r=urlopen(url)
			f=open(dest,"wb")
			f.write(r.read())
			f.close()
			r.close()
			return n4d.responses.build_successful_call_response('{} successfully downloaded.'.format(dest))
			# return {'status':True,'msg':dest + 'successfully downloaded.'}
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Error downloading {}:{}'.format(dest,e))
			# return {'status':False,'msg':'Error downloading' + dest + ':' + str(e)}
	# def get_time_file

	def is_update_available(self,distro=None):
		if distro is None:
			return n4d.responses.build_failed_call_response(ret_msg="No distro selected")
			# return {'status':False,'msg':"No distro selected",'action':'nothing'}
		configpath = os.path.join(self.llxconfigspath,"%s.json"%distro)
		try:
			config = json.load(open(configpath,'r'))
		except Exception as e:
			return n4d.responses.build_failed_call_response(ret_msg='Fail when parsing json file {}'.format(configpath))
		path = config["MIRROR_PATH"]
		file_time_name = "time-of-last-update"
		file_local_mirror = os.path.join(path,file_time_name)

		if os.path.isfile(file_local_mirror):
			url_pool = "http://"+os.path.join(config["ORIGS"]['1'],file_time_name)
			file_pool = os.path.join("/tmp",file_time_name)

			exist_file_pool = self.get_time_file(url_pool,file_pool)
			if exist_file_pool.get('status') == 0:
				file_local_mirror_content=open(file_local_mirror,"r")
				file_local_miror_datetime=(file_local_mirror_content.readline().strip()).split("_")
				file_pool_content=open(file_pool,'r')
				file_pool_datetime=(file_pool_content.readline().strip()).split("_")
				file_local_mirror_content.close()
				file_pool_content.close()

				try:
					date_local_mirror=datetime.datetime.strptime(file_local_miror_datetime[0],"%Y/%m/%d")
				except Exception as e:
					return n4d.responses.build_failed_call_response(ret_msg="Invalid format from local mirror time-of-last-update")
				try:
					date_pool=datetime.datetime.strptime(file_pool_datetime[0],"%Y/%m/%d")
				except Exception as e:
					return n4d.responses.build_failed_call_response(ret_msg="Invalid format from remote mirror time-of-last-update")
				if date_local_mirror==date_pool:
					time_local_mirror=datetime.datetime.strptime(file_local_miror_datetime[1],"%H:%M")	
					time_pool=datetime.datetime.strptime(file_pool_datetime[1],"%H:%M")

					if time_local_mirror<time_pool:
						return n4d.responses.build_successful_call_response({'msg':'Mirror not updated','action':'update'})
						# return {'status':False,'msg':'Mirror not updated','action':'update'}
					else:
						return n4d.responses.build_successful_call_response({'msg':'Mirror is updated','action':'nothing'})
						# return {'status':True,'msg':'Mirror is updated','action':'nothing'}

				elif date_local_mirror<date_pool:
					return n4d.responses.build_successful_call_response({'msg':'Mirror not updated','action':'update'})
					# return {'status':False,'msg':'Mirror not updated','action':'update'}
				else:
					return n4d.responses.build_successful_call_response({'msg':'Mirror is updated','action':'nothing'})
					# return {'status':True,'msg':'Mirror is updated','action':'nothing'}	
			else:
				return n4d.responses.build_successful_call_response({'msg':'{}'.format(exist_file_pool.get('return')),'action':'nothing'})
				# return {'status':False,'msg':exist_file_pool['msg'],'action':'nothing'}
		else:
			return n4d.responses.build_successful_call_response({'msg':'{}  does not exist.'.format(file_local_mirror),'action':'nothing'})
			# return {'status':False,'msg':file_local_mirror + ' does not exist.','action':'nothing'}

	# def is_update_available

	def new_mirror_config(self,config):
		name = config["NAME"].lower().strip()
		name = ''.join(c for c in name if c in self.valid_chars)

		# Checks
		if name == "":
			return n4d.responses.build_failed_call_response(ret_msg="Name can't be empty")
			# return {'status':False,'msg':"Name can't be empty"}
		while True:
			newconfigpath = os.path.join(self.llxconfigspath,name + '.json')
			if not os.path.lexists(newconfigpath):
				break
			name = name + "1"

		data=json.dumps(config,indent=4,ensure_ascii=False)
		f = open(newconfigpath,'w')
		f.write(data)
		f.close()
		self.variable[name] = self.defaultmirrorinfo
		return n4d.responses.build_successful_call_response(name)
		# return {'status':True,'msg':name}
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
		return n4d.responses.build_successful_call_response(allconfigs)
		# return {'status':True,'msg':allconfigs}
	#def get_all_configs

	def update_mirror_config(self,mirror,config):
		configpath = os.path.join(self.llxconfigspath,mirror + ".json")

		f=open(configpath,"w")

		data=json.dumps(config,indent=4,ensure_ascii=False)
		f.write(data)
		f.close()
		return n4d.responses.build_successful_call_response('Updated config')
		# return {'status':True,'msg':'Updated config'}
	#def update_mirror_config

	def get_client_ip(self,user,ip):
		return n4d.responses.build_successful_call_response(ip)
		# return {'status':True,'msg':ip}
	#def get_client_ip

	def is_alive_get_mirror(self):
		return n4d.responses.build_successful_call_response((self.get_mirror_thread.is_alive(),self.exportpercentage[0]))
		# return {'status':self.get_mirror_thread.is_alive(),'msg':self.exportpercentage}
	#def is_alive_get_mirror

	def get_mirror(self,config_path,callback_args):
		self.get_mirror_thread = threading.Thread(target=self._get_mirror,args=(config_path,callback_args,))
		self.get_mirror_thread.daemon = True
		self.get_mirror_thread.start()
		return n4d.responses.build_successful_call_response()
	#def get_mirror

	def _get_mirror(self,config_path,callback_args):
		ret = None
		if self.appneedparams:
			try:
				ret = self.get_checksum_validation(self.distro)
				ret = ret.get('return')
			except Exception as e:
				print("Error getting checksum validation")
				return -1
		if ret is not None and (ret == 1 or ret == True):
			tokens = self.appcommand.split()
			for x in '-v -rf'.split():
				if x not in tokens:
					self.appcommand += " {}".format(x)
		self.get_mirror_process = pexpect.spawn("{} --config-file={}".format(self.appcommand,config_path))
		started = False
		while True:
			try:
				self.get_mirror_process.expect('\n',timeout=480)
				line =self.get_mirror_process.before.decode('utf8').strip()
				if line.startswith("[") and line[5] == "]":
					self.exportpercentage = (int(line[1:4].strip()),self.get_mirror_process.exitstatus)
				if line.lower().startswith("starting apt-mirror"):
					started = True
				if line.lower().startswith("end apt-mirror"):
					self.exportpercentage = (100,self.get_mirror_process.exitstatus)
			except pexpect.exceptions.EOF:
				if not started:
					raise Exception()
				line = self.get_mirror_process.before.decode('utf8').strip()
				if line != "" and line.startswith("[") and line[5] == "]":
					self.exportpercentage=(int(line[1:4].strip()),self.get_mirror_process.exitstatus)
				if line.lower().startswith("end apt-mirror"):
					self.exportpercentage = (100,self.get_mirror_process.exitstatus)
				self.get_mirror_process.close()
				status = self.get_mirror_process.exitstatus
				self.exportpercentage=(self.exportpercentage[0],status)
				break
			except Exception as e:
				break
		if isinstance(callback_args,dict) and 'port' in callback_args and 'ip' in callback_args:
			n4d_cli = Client(address='https://' + callback_args['ip'] + ':9779')
			n4d_cli.MirrorManager.stop_webserver(callback_args['port'])
	#def _get

	def get_last_log(self):
		p = subprocess.Popen('lliurex-mirror-get-last-log',stdout=subprocess.PIPE)
		path = p.communicate()[0].strip()
		f = open(path,'r')
		content = f.readlines()
		onelinecontent = ''.join(content)
		if isinstance(onlinecontent,str):
			onlinecontent = onlinecontent.encode('utf8')
		return n4d.responses.build_successful_call_response('{}'.format(base64.b64encode(onelinecontent)))
		# return {'status':True,'msg':base64.b64encode(onelinecontent)}
	#def get_last_log(self):
	
	def is_mirror_available(self):
		# Used by admin-center-netinstall
		config=self.get_all_configs()
		if not isinstance(config,dict) or 'return' not in config or not isinstance(config['return'],dict) or self.distro not in config['return'] or not isinstance(config['return'][self.distro],dict):
			return n4d.responses.build_failed_call_response(ret_msg='Unknown data from mirror')
		else:
			mirror_data = config.get('return').get(self.distro)

		path=str(mirror_data.get('MIRROR_PATH'))
		if not path:
			return n4d.responses.build_failed_call_response(ret_msg='MIRROR_PATH not available into mirror data')
		found=False
		for root,dirnames,filenames in os.walk(os.path.realpath(os.path.join(path,'pool/main/l/lliurex-version-timestamp/'))):
			for filename in fnmatch.filter(filenames,'lliurex-version-timestamp_*.deb'):
				found=True
		if found:
			return n4d.responses.build_successful_call_response('Mirror available')
			# return {'status':True,'msg':'Mirror available'}
		else:
			return n4d.responses.build_failed_call_response(ret_msg='Mirror unavailable')
			# return {'status':False,'msg':'Mirror unavailable'}
	#def is_mirror_available(self):
