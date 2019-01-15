import xmlrpclib
import base64
import tempfile
import os

class LliurexMirrorN4d:
	def __init__(self,server,credentials):
		self.mode = None
		self.client = None
		self.serverip = server
		self.localclient = None
		self.connect(server)
		self.local_connect()
		self.credentials = credentials
		self.localcredentials = self.get_local_credentials()
		self.localport = None
		self.remoteport = None
		
		self.key_list=["NAME","ARCHITECTURES","CURRENT_UPDATE_OPTION","BANNER","DISTROS","SECTIONS","MIRROR_PATH","ORIGS","CHK_MD5","IGN_GPG","IGN_RELEASE"]
		
		
	#def __init__


	def connect(self,server):
		self.client = xmlrpclib.ServerProxy('https://' + server + ':9779',allow_none=True)
		self.serverip = server
		try:
			self.client.get_methods()
		except:
			self.client = None
			return False
		return True
	#def connect

	def local_connect(self):
		self.localclient = xmlrpclib.ServerProxy('https://localhost:9779',allow_none=True)
		try:
			self.localclient.get_methods()
		except:
			self.localclient = None
			return False
		return True
	#def connect

	def get_local_credentials(self):
		try:
			f = open('/etc/n4d/key','r')
			key = f.readline().strip()
			return key
		except:
			return None

	def mirror_list(self):
		try:
			if type(self.client) == type(None):
				return {}
			result = self.client.get_all_configs(self.credentials,'MirrorManager')
			if not result['status']:
				return {}
			return result['msg']
		except:
			return {}
			
	#def mirror_list

	def is_alive(self):
		try:
			return self.client.is_alive(self.credentials,'MirrorManager')
		except:
			return {'status':False,'msg':None}
			
	#def is_alive
	
	def save_config(self,mirror,config):
		
		try:
		
			parsed_mirror={}
			
			for key in self.key_list:
				parsed_mirror[key]=config[key]
			
			
			result = self.client.update_mirror_config(self.credentials,'MirrorManager',mirror,parsed_mirror)
			return result
			
		except Exception as e:
			print "[!] Error saving configuration: [!]"
			print e
			return None
		
	#def save_config

	def create_config(self,config):
		
		try:
		
			if type(self.client) == type(None):
				return {}
			result = self.client.new_mirror_config(self.credentials,'MirrorManager',config)
		
			if result['status']:
				return result['msg']
				
		except:
			
			return {}
		
		
		
	#def create_conf

	def update(self,mirror,mode,data=None):
		'''
		mode is option to update mirror. (Internet, local network, folder)
		data is extra info to update (local network ip, )
		'''
		
		try:
		
			self.mode = None
			self.localport = None
			callback_args = None
			if mode == '2':
				self.mode = 2 
				result = self.client.get_client_ip('','MirrorManager','')
				tempserver = result['msg']
				result = self.localclient.enable_webserver_into_folder(self.localcredentials,'MirrorManager',data)
				print result
				tempserver = tempserver + ":" + str(result['msg'])
				data = tempserver
				callback_args = {}
				callback_args['port'] = str(result['msg'])
				self.localport = str(result['msg'])
			if data != None:
				self.client.set_mirror_orig(self.credentials,'MirrorManager',mirror,data,mode)
			self.client.set_option_update(self.credentials,'MirrorManager',mirror,mode)
			result = self.client.update(self.credentials,'MirrorManager','',mirror,callback_args)
			return result['status']
			
		except Exception as e:
			print e
			
			return None
			
	#def update

	def export(self, mirror,folder):
		
		try:
			# Get config for this mirror
			result = self.client.get_all_configs(self.credentials,'MirrorManager')
			config = result['msg'][mirror]
			result = self.client.get_client_ip('','MirrorManager','')
			ip = result['msg']
			# Open webserver for mirror and get ip
			result = self.client.enable_webserver_into_folder(self.credentials,'MirrorManager',config['MIRROR_PATH'])
			port = str(result['msg'])
			self.remoteport = port
			# Modify Config and write
			
			config['MIRROR_PATH'] = folder
			config['CURRENT_UPDATE_OPTION'] = '3'
			config['ORIGS']['3'] = self.serverip + ":" + str(port)
			result = self.client.render_debmirror_config(self.credentials,'MirrorManager',config)
			temp_file = tempfile.mktemp()
			f = open(temp_file,'w')
			f.write(result['msg'])
			f.close()
			callback_args = {}
			callback_args['ip'] = ip
			callback_args['port'] = port
			# Execute mirror
			print self.localclient.get_mirror(self.localcredentials,'MirrorManager',temp_file,callback_args)
			return True
		except:
			
			return False
	#def export

	def get_percentage_export(self):
		try:
			result = self.localclient.is_alive_get_mirror(self.localcredentials,'MirrorManager')
			return result['msg'][0]
		except Exception as e:
			print e
			return None
			
	#def get_percentage_export

	def is_alive_export(self):
		try:
			result = self.localclient.is_alive_get_mirror(self.localcredentials,'MirrorManager')
			return result
		except Exception as e:
			print e
			return None
		


	def get_percentage(self,mirror):
		
		try:
		
			result = self.client.get_percentage(self.credentials,'MirrorManager',mirror)
			if result['status'] :
				return result['msg']
				
		except Exception as e:
			print e
			return None
			
	#def get_percentage

	
	def get_status(self,mirror):
		
		try:
			var=self.client.get_variable(self.credentials,"VariablesManager","LLIUREXMIRROR")
			if var[mirror]["status_mirror"]=="Ok":
				return {"status": True, "msg": None}
			else:
				return {"status": False, "msg": var[mirror]["exception_msg"]}
				
		except Exception as e:
			return {"status": False, "msg": str(e) }
			
	#def get_status

	
	def get_last_log(self):
		
		try:
		
			ret=self.client.get_last_log(self.credentials,"MirrorManager")
			txt=base64.b64decode(ret["msg"])
			tmp_file=tempfile.mkstemp(suffix=".lliurex-mirror.log")
			f=os.fdopen(tmp_file[0],"w")
			f.write(txt)
			f.close()
			return tmp_file[1]
			
		except Exception as e:
			print e
			return None

	#def get_last_log

	def is_update_available(self,mirror):
		try:
			result = self.client.is_update_available(self.credentials,'MirrorManager',mirror)
			return result['status']
		except Exception as e:
			print e
			return None
			
	#def is_update_available

	def stop_update(self):
		try:
			if self.mode == '2':
				self.localclient.stop_webserver(self.credentials,'MirrorManager',self.localport)
			result = self.client.stopupdate(self.credentials,'MirrorManager')
			return result['status']
		except Exception as e:
			print e
			return None
			
	#def stop_update

	def stop_export(self):
		
		try:
			self.client.stop_webserver(self.credentials,'MirrorManager',self.remoteport)
			result = self.localclient.stopgetmirror(self.credentials,'MirrorManager')
			return result['status']
		except Exception as e:
			print e
			return None
			
	#def stop_update


if __name__ == '__main__':
	#c = LliurexMirrorN4d('localhost',['kbut','lliurex'])
	#config = {'IGN_GPG': 1, 'NAME': 'Mi ppa', 'ORIGS': {'1': 'ppa.launchpad.net/llxdev/xenial/ubuntu', '3': '172.20.8.6/mirror/ppa-xenial/', '2': '/home/kbut/miMirrorPortatil'}, 'SECTIONS': ['main', 'universe', 'restricted', 'multiverse'], 'MIRROR_PATH': '/home/mirror-ppa', 'ARCHITECTURES': ['amd64', 'i386'], 'CHK_MD5': 0, 'IGN_RELEASE': 0, 'BANNER': '', 'CURRENT_UPDATE_OPTION': '1', 'DISTROS': ['xenial']}
	#print c.save_config('mippa',config)
	#print c.create_conf(config)
	#print c.update('mippa','3','172.20.8.6/mirror/ppa-xenial')
	#print c.update('mippa','2','/home/mirror-ppa-otracarpeta')
	#print c.update('mippa','1')
	#print c.mirror_list()
	#print c.export('mippa','/home/mirror16')
	#print c.is_alive_export()
	#print c.get_percentage_export()
	#print c.get_percentage('mippa')
	#print c.is_alive()
	#print c.stop_export()
	pass