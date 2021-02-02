#import xmlrpclib
#import xmlrpc.client as x
#import ssl
import base64
import tempfile
import os
from n4d.client import Client,Key,Credential

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
		self.client = Client(address="https://{}:9779".format(server))
		self.serverip = server
		try:
			self.client.get_methods()
		except:
			self.client = None
			return False
		return True
	#def connect

	def local_connect(self):
		self.localclient = Client()
		try:
			self.localclient.get_methods()
		except:
			self.localclient = None
			return False
		return True
	#def connect

	def get_local_credentials(self):
		k = Key.master_key()
		if k.valid():
			return k
		else:
			return None

	def mirror_list(self):
		try:
			if type(self.client) == type(None):
				return {}
			try:
				result = self.client.MirrorManager.get_all_configs()
			except Exception as e:
				print("Unable to get mirror configurations, {}".format(e))
				return {}
			return result
		except:
			return {}
			
	#def mirror_list

	def is_alive(self):
		try:
			self.client.credential = Credential(*self.credentials)
			return self.client.MirrorManager.is_alive()
		except:
			return {'status':False,'msg':None}
			
	#def is_alive
	
	def save_config(self,mirror,config):
		try:
			parsed_mirror={}
			for key in self.key_list:
				parsed_mirror[key]=config[key]
			self.client.credential = Credential(*self.credentials)
			try:
				result = self.client.MirrorManager.update_mirror_config(mirror,parsed_mirror)
			except Exception as e:
				print("Fail to update mirror config, {}".format(e))
				return None
			return result
		except Exception as e:
			print ("[!] Error saving configuration: [!]")
			print (e)
			return None
	#def save_config

	def create_config(self,config):
		try:
			if type(self.client) == type(None):
				return {}
			try:
				self.client.credential = Credential(*self.credentials)
				result = self.client.MirrorManager.new_mirror_config(config)
			except Exception as e:
				print('Error creating new mirror configuration, {}'.format(e))
				return {}
			return result
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
			callback_args = {}
			if mode == '2':
				self.mode = 2 
				try:
					tempserver = self.client.MirrorManager.get_client_ip('','')
				except Exception as e:
					print('Error getting client ip,{}'.format(e))
					return None
				try:
					self.localclient.credential = Credential(*self.localcredentials)
					result = self.localclient.MirrorManager.enable_webserver_into_folder(data)
				except Exception as e:
					print('Error enabling local webserver, {}'.format(e))
					return None
				tempserver = "{}:{}".format(tempserver,result)
				data = tempserver
				callback_args['port'] = str(result)
				self.localport = str(result)
			if data != None:
				try:
					self.client.credential = Credential(*self.credentials)
					self.client.MirrorManager.set_mirror_orig(mirror,data,mode)
				except Exception as e:
					print('Error setting mirrir origin,{}'.format(e))
			try:
				self.client.credential = Credential(*self.credentials)
				self.client.MirrorManager.set_option_update(mirror,mode)
				result = self.client.MirrorManager.update('','',mirror,callback_args)
			except Exception as e:
				print('Error updating mirror,{}'.format(e))
				return None
			return result
		except Exception as e:
			print(e)
			return None
	#def update

	def export(self, mirror,folder):
		try:
			# Get config for this mirror
			self.client.credential = Credential(*self.credentials)
			result = self.client.MirrorManager.get_all_configs()
			config = result[mirror]
			ip = self.client.MirrorManager.get_client_ip('','')

			# Open webserver for mirror and get ip
			port = self.client.MirrorManager.enable_webserver_into_folder(config['MIRROR_PATH'])
			self.remoteport = str(port)
			# Modify Config and write
			
			config['MIRROR_PATH'] = folder
			config['CURRENT_UPDATE_OPTION'] = '3'
			config['ORIGS']['3'] = self.serverip + ":" + str(port)
			result = self.client.MirrorManager.render_debmirror_config(config)
			temp_file = tempfile.mktemp()
			f = open(temp_file,'w')
			f.write(result)
			f.close()
			callback_args = {}
			callback_args['ip'] = ip
			callback_args['port'] = port
			# Execute mirror
			self.localclient.credential = Credential(*self.localcredentials)
			print(self.localclient.MirrorManager.get_mirror(temp_file,callback_args))
			return True
		except:
			return False
	#def export

	def get_percentage_export(self):
		try:
			self.localclient.credential = Credential(*self.localcredentials)
			result = self.localclient.is_alive_get_mirror()
			return result
			# if isinstance(result,dict):
			#     msg=result.get('msg')
			# elif isinstance(result,(int,str)):
			#     msg=result
			# if isinstance(msg,(int,str)):
			#     return msg
			# elif isinstance(msg,(tuple,list)) and len(msg) > 0:
			#     return msg[0]
		except Exception as e:
			print (e)
			return None
	#def get_percentage_export

	def is_alive_export(self):
		try:
			self.localclient.credential = Credential(*self.localcredentials)
			result = self.localclient.MirrorManager.is_alive_get_mirror()
			return result
		except Exception as e:
			print (e)
			return None

	def get_percentage(self,mirror):
		try:
			self.client.credential = Credential(*self.credentials)
			result = self.client.MirrorManager.get_percentage(mirror)
			return result
		except Exception as e:
			print (e)
			return None
	#def get_percentage

	
	def get_status(self,mirror):
		try:
			self.client.credential = Credential(*self.credentials)
			var=self.client.get_variable("LLIUREXMIRROR")
			if var[mirror]["status_mirror"]=="Ok":
				return {"status": True, "msg": None}
			else:
				return {"status": False, "msg": var[mirror]["exception_msg"]}
		except Exception as e:
			return {"status": False, "msg": str(e) }
	#def get_status

	
	def get_last_log(self):
		try:
			self.client.credential = Credential(*self.credentials)
			ret=self.client.MirrorManager.get_last_log()
			txt=base64.b64decode(ret)
			if (isinstance(txt,bytes)):
				txt=txt.decode()
			tmp_file=tempfile.mkstemp(suffix=".lliurex-mirror.log")
			f=os.fdopen(tmp_file[0],"w")
			f.write(txt)
			f.close()
			return tmp_file[1]
		except Exception as e:
			print (e)
			return None
	#def get_last_log

	def is_update_available(self,mirror):
		try:
			self.client.credential = Credential(*self.credentials)
			result = self.client.MirrorManager.is_update_available(mirror)
			return result
		except Exception as e:
			print (e)
			return None
	#def is_update_available

	def stop_update(self):
		try:
			if self.mode == '2':
				self.localclient.credential = Credential(*self.localcredentials)
				self.localclient.MirrorManager.stop_webserver(self.localport)
			self.client.credential = Credential(*self.credentials)
			result = self.client.MirrorManager.stopupdate()
			return True
			#return result['status']
		except Exception as e:
			print("{}".format(e))
			return None
	#def stop_update

	def stop_export(self):
		try:
			self.client.credential = Credential(*self.credentials)
			self.client.MirrorManager.stop_webserver(self.remoteport)
			self.localclient.credential = Credential(*self.localcredentials)
			try:
				result = self.localclient.MirrorManager.stopgetmirror()
			except Exception as e:
				print("Error stopping localmirror, {}".format(e))
				return None
			return True
			# result['status']
		except Exception as e:
			print (e)
			return None
	#def stop_update


if __name__ == '__main__':
	#c = LliurexMirrorN4d('localhost',['lliurex','lliurex'])
	#config = {'IGN_GPG': 1, 'NAME': 'Mi ppa', 'ORIGS': {'1': 'ppa.launchpad.net/llxdev/xenial/ubuntu', '3': '172.20.8.6/mirror/ppa-xenial/', '2': '/home/kbut/miMirrorPortatil'}, 'SECTIONS': ['main', 'universe', 'restricted', 'multiverse'], 'MIRROR_PATH': '/home/mirror-ppa', 'ARCHITECTURES': ['amd64', 'i386'], 'CHK_MD5': 0, 'IGN_RELEASE': 0, 'BANNER': '', 'CURRENT_UPDATE_OPTION': '1', 'DISTROS': ['xenial']}
	#print c.save_config('mippa',config)
	#print c.create_conf(config)
	#print c.update('mippa','3','172.20.8.6/mirror/ppa-xenial')
	#print c.update('mippa','2','/home/mirror-ppa-otracarpeta')
	#print c.update('mippa','1')
	#print c.mirror_list()
	#print c.export('mippa','/home/mirror16')
	#print c.is_alive_export()
	#print(c.get_percentage_export())
	#print c.get_percentage('mippa')
	#print c.is_alive()
	#print c.stop_export()
	pass
