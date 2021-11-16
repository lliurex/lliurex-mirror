#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

import cairo
import os
import threading
#import ConfigParser
import configparser
import platform
import json
import random
import xmlrpc.client as x
import ssl
#import xmlrpclib
import time
import math
import sys
import tempfile
from math import pi
import lliurex_mirror_connect

from gi.repository import Gtk, Gdk, GObject, GLib, PangoCairo, Pango,GdkPixbuf

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import glob

import gettext
gettext.textdomain('lliurex-mirror')
_ = gettext.gettext


BASE_DIR="/usr/share/lliurex-mirror/"
BANNERS_PATH=BASE_DIR+"./banners/"
UNKNOWN_BANNER=BANNERS_PATH+"mirror_banner.png"
SHADOW_BANNER=BASE_DIR+"rsrc/shadow.png"
MIRROR_CONF_DIR="/etc/lliurex-mirror/conf/"
GLADE_FILE=BASE_DIR+"rsrc/lliurex-mirror.ui"
ADD_IMAGE=BASE_DIR+"rsrc/a1.png"
ADD_IMAGE_OVER=BASE_DIR+"rsrc/a2.png"
TOKEN_FILE="/tmp/lliurex-mirror.pid"
ERROR=Gtk.MessageType.ERROR
INFO=Gtk.MessageType.INFO

class MirrorButton:
	
	def __init__(self,info):
		
		self.info=info # "pkg"
		self.info["updating"]=False
		self.info["exporting"]=False
		self.info["executing"]=False
		self.info["shadow_alpha"]=0.1
		self.info["animation_active"]=False
		self.info["shadow_start"]=0
		self.info["available"]=True
		self.info["degree_offset"]=0
		self.info["red_position"]=0
		self.info["red_right"]=True
		self.info["max_random_lights"]=30
		self.info["random_lights"]=[]
		self.info["cancelled"]=False
		
		if os.path.exists(BANNERS_PATH+self.info["BANNER"]+".png"):
			self.info["image"]=BANNERS_PATH+self.info["BANNER"]+".png"
		else:
			self.info["image"]=UNKNOWN_BANNER
		
	#def init
	
	
#class GridButton

class LightPoint:
	
	def __init__(self,x,y,radius=None):
		
		#self.degree=degree
		self.radius=radius
		
		self.x=x
		self.y=y
		self.opacity=1.0
		
	#def 

class CustomColor:
	
	def __init__(self,r,g,b):
		
		self.r=r/255.0
		self.g=g/255.0
		self.b=b/255.0

#class CustomColor		

class LliurexMirror:
	
	def __init__(self):
		
		self.t_counter=0
		self.last_time=time.time()
		self.frame_size=116
		self.percentage=0
		self.circle={}
		self.circle["x"]=58
		self.circle["y"]=58
		self.circle["radius"]=46
		self.degree_offset=0
		self.y_offset=5
		
		self.wave_xoffset=0
		self.wave_yoffset=0
		self.wave_lenght=80
		self.wave_amplitude=3
		self.wave_amplitude2=2
		self.wave_amplitude3=2
		self.wave_xoffset2=50
		self.wave_xoffset3=80
		
		self.add_flag=False
		
		self.current_grid_width=0
		self.current_grid_height=0
		self.max_grid_width=2
	
		self.dark_gray=CustomColor(130.0,151.0,161.0)
		self.light_gray=CustomColor(185.0,195.0,195.0)
		
		self.green=CustomColor(74.0,166.,69.0)
		self.light_green=CustomColor(88.0,208.0,86.0)
		
		
		self.conf_light=CustomColor(49.0,55.0,66.0)
		self.conf_dark=CustomColor(30.0,36.0,42.0)
		
		self.conf_light_shadow=CustomColor(107.0,116.0,137.0)
		self.conf_dark_shadow=CustomColor(0,0,0)
		self.red=CustomColor(255,0,0)
		
		self.update_water_colors=[]
		
		self.update_water_colors.append(CustomColor(12,54,64))
		self.update_water_colors.append(CustomColor(17,92,108))
		self.update_water_colors.append(CustomColor(0.2*255,0.93*255,0.97*255))
		self.update_water_colors.append(CustomColor(82, 176, 225))
		self.update_water_colors.append(CustomColor(68, 159, 255))
		
		
		self.export_water_colors=[]
		
		
		
		self.export_water_colors.append(CustomColor(29,12,64))
		self.export_water_colors.append(CustomColor(47,17,108))
		self.export_water_colors.append(CustomColor(93,51,247))
		self.export_water_colors.append(CustomColor(153,82,225))
		self.export_water_colors.append(CustomColor(182,68,225))
		
		#self.update_water_colors=self.export_water_colors
		
		self.login_animation_x=236 + 127/2
		self.login_animation_y=131 + 128/2
		self.login_animation_r=60
		
		self.login_enabled=True
		
		self.current_mirror=None
		self.updating_mirror=None
		
		self.update_percentage_time=10000
		self.update_y_time=1000/15
		self.update_degree_time=1000/15
		self.update_mirror_button_time=1000/15
		
		
	#def init
	
	def check_root(self):
		
		try:
		
			f=open(TOKEN_FILE,"w")
			f.write(str(os.getpid()))
			f.close()
			
			return True
			
		except:
			
			dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Lliurex Mirror")
			dialog.format_secondary_text("You need administration privileges to run this application.")
			dialog.run()
			sys.exit(1)
		
	#def check_root
	
	def start_gui(self):
		
		ui_path=GLADE_FILE
		builder=Gtk.Builder()
		builder.set_translation_domain('lliurex-mirror')
		builder.add_from_file(ui_path)
		
		
		
		
		self.stack = Gtk.Stack()
		self.stack.set_transition_duration(500)
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		
		self.label_image=builder.get_object("label_da")
		self.label_image1=builder.get_object("label_da1")
		self.label_image.connect("draw",self.draw_label)
		self.label_image1.connect("draw",self.draw_label)
		
		
		self.window=builder.get_object("main_window")
		self.mirror_header_box=builder.get_object("mirror_header_box")
		self.mirror_name_label=builder.get_object("mirror_name_label")
		self.conf_mirror_name_label=builder.get_object("conf_mirror_name_label")
		self.llx_mirror_label=builder.get_object("llx_mirror_label")
		self.arch_label=builder.get_object("arch_label")
		self.progress_da=builder.get_object("progress_drawingarea")
		self.shadow_box=builder.get_object("shadow_box")
		self.shadow_box1=builder.get_object("shadow_box1")
		self.shadow_box2=builder.get_object("shadow_box2")
		self.content_box=builder.get_object("mirror_box")
		#self.main_content_box=builder.get_object("main_content_box")
		self.progress_label=builder.get_object("progress_label")
		self.list_box=builder.get_object("list_box")
		self.arrow_eb=builder.get_object("arrow_eventbox")
		self.main_header_box=builder.get_object("main_header_box")
		self.update_label_box=builder.get_object("update_label_box")
		self.export_label_box=builder.get_object("export_label_box")
		self.configuration_label_box=builder.get_object("configuration_label_box")
		self.folder_fcb=builder.get_object("folder_fcb")
		self.folder_fcb.connect("file-set",self.folder_fcb_changed)
		self.local_folder_label=builder.get_object("local_folder_label")
		self.destination_fcb=builder.get_object("destination_fcb")
		self.destination_fcb.connect("file-set",self.destination_fcb_changed)
		self.destination_label=builder.get_object("destination_label")
		self.scrolledwindow=builder.get_object("scrolledwindow1")
		
		self.internet_rb=builder.get_object("internet_rb")
		self.local_folder_rb=builder.get_object("local_folder_rb")
		self.url_rb=builder.get_object("url_rb")
		self.url_entry=builder.get_object("url_entry")
		
		self.configuration_infobar=builder.get_object("configuration_infobar")
		self.configuration_panel_label=builder.get_object("configuration_panel_label")
		self.configuration_infobar.connect("response",self.ib_response)
		
		
		self.arrow_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK )
		self.arrow_eb.connect("button-release-event",self.arrow_clicked)
		
		self.update_eb=builder.get_object("update_eventbox")
		self.update_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK )
		self.update_eb.connect("motion-notify-event",self.mouse_over_update)
		self.update_eb.connect("leave_notify_event",self.mouse_exit_update)
		self.update_eb.connect("button-release-event",self.update_clicked)
		
		self.export_eb=builder.get_object("export_eventbox")
		self.export_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK )
		self.export_eb.connect("motion-notify-event",self.mouse_over_export)
		self.export_eb.connect("leave_notify_event",self.mouse_exit_export)
		self.export_eb.connect("button-release-event",self.export_clicked)
		
		self.configuration_eb=builder.get_object("configuration_eventbox")
		self.configuration_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK )
		self.configuration_eb.connect("motion-notify-event",self.mouse_over_conf)
		self.configuration_eb.connect("leave_notify_event",self.mouse_exit_conf)
		self.configuration_eb.connect("button-release-event",self.conf_clicked)
		
		
		self.configuration_box=builder.get_object("configuration_box")
		self.configuration_header_box=builder.get_object("configuration_header_box")
		self.configuration_arrow_eb=builder.get_object("configuration_arrow_eventbox")
		self.configuration_arrow_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK )
		self.configuration_arrow_eb.connect("button-release-event",self.configuration_arrow_clicked)
		
		self.name_label=builder.get_object("name_label")
		self.banner_label=builder.get_object("banner_label")
		self.origin_label=builder.get_object("origin_label")
		self.distributions_label=builder.get_object("distributions_label")
		self.sections_label=builder.get_object("sections_label")
		self.architectures_label=builder.get_object("architectures_label")
		self.local_path_label=builder.get_object("local_path_label")
		self.check_md5_label=builder.get_object("check_md5_label")
		self.ign_gpg_label=builder.get_object("ign_gpg_label")
		self.ign_release_label=builder.get_object("ign_release_label")
		
		self.name_entry=builder.get_object("name_entry")
		self.banner_combobox=builder.get_object("banner_combobox")
		self.origin_entry=builder.get_object("origin_entry")
		self.distributions_entry=builder.get_object("distributions_entry")
		self.sections_entry=builder.get_object("sections_entry")
		self.i386_cb=builder.get_object("i386_checkbutton")
		self.amd64_cb=builder.get_object("amd64_checkbutton")
		self.mirror_path_entry=builder.get_object("mirror_path_entry")
		self.check_md5_cb=builder.get_object("check_md5_checkbutton")
		self.ign_gpg_cb=builder.get_object("ign_gpg_checkbutton")
		self.ign_release_cb=builder.get_object("ign_release_checkbutton")
		
		
		self.save_button_box=builder.get_object("save_button_box")
		self.save_eb=builder.get_object("save_eventbox")
		self.save_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK  )
		self.save_eb.connect("button-release-event",self.save_button_clicked)
		self.save_eb.connect("motion-notify-event",self.mouse_over_save)
		self.save_eb.connect("leave_notify_event",self.mouse_exit_save)
		
		self.export_label=builder.get_object("export_label")
		self.update_label=builder.get_object("update_label")
		self.save_label=builder.get_object("save_label")
		self.conf_label=builder.get_object("conf_label")
		self.i386_label=builder.get_object("i386_label")
		self.amd64_label=builder.get_object("amd64_label")
		
		self.update_header_label=builder.get_object("update_header_label")
		self.export_header_label=builder.get_object("export_header_label")
		self.internet_rb_label=builder.get_object("internet_rb_label")
		self.internet_rb_label=builder.get_object("internet_rb_label")
		self.local_folder_rb_label=builder.get_object("local_folder_rb_label")
		self.url_rb_label=builder.get_object("url_rb_label")
		self.destination_opt_label=builder.get_object("destination_opt_label")
				
		self.ib=builder.get_object("infobar1")
		self.ib.connect("response",self.ib_response)
		self.info_label=builder.get_object("info_label")
		
		self.info_button=builder.get_object("info_button")
		self.info_button.connect("clicked",self.info_button_clicked)
		
		self.main_content_box=Gtk.Grid()
		self.main_content_box.set_column_homogeneous(True)
		self.main_content_box.set_row_spacing(10)
		self.main_content_box.set_margin_top(15)
		self.main_content_box.set_margin_left(40)
		
		self.viewport=builder.get_object("viewport1")
		self.viewport.add(self.main_content_box)
		
	
		self.overlay=Gtk.Overlay()
		self.overlay.add(self.list_box)
		self.overlay.show_all()
		
		eb=Gtk.EventBox()
		eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK  )
		b=Gtk.Image()
		
		eb.connect("button-release-event",self.add_clicked)
		eb.connect("motion-notify-event",self.add_mouse_over,b)
		eb.connect("leave_notify_event",self.add_mouse_left,b)
		b.set_from_file(ADD_IMAGE)
		b.show()
		
		eb.add(b)
		
		eb.set_valign(Gtk.Align.END)
		eb.set_halign(Gtk.Align.END)
		eb.set_margin_bottom(5)
		eb.set_margin_right(20)
		self.overlay.add_overlay(eb)
		
		
		self.login_da_box=builder.get_object("login_da_box")
		self.login_da=builder.get_object("login_drawingarea")
		self.login_da.connect("draw",self.draw_login)
		
		self.login_overlay=Gtk.Overlay()
		self.login_overlay.add(self.login_da_box)
		
		'''
		self.login_box=Gtk.VBox()
		
		self.login_button=Gtk.Button("Login")
		self.login_button.connect("clicked",self.login_clicked)
		
		self.login_box.pack_end(self.login_button,False,True,5)
		self.login_box.pack_end(Gtk.Entry(),False,True,5)
		self.login_box.pack_end(Gtk.Entry(),False,True,5)
		self.tmp_label=Gtk.Label("hola")
		self.login_box.pack_start(self.tmp_label,False,True,100)
		'''
		
		self.login_box=builder.get_object("login_box")
		self.login_eb=builder.get_object("login_eventbox")
		self.login_eb.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK  )
		self.login_eb.connect("button-press-event",self.login_clicked)
		self.login_eb.connect("motion-notify-event",self.mouse_over_login)
		self.login_eb.connect("leave_notify_event",self.mouse_exit_login)
		self.user_entry=builder.get_object("user_entry")
		self.user_entry.connect("activate",self.entries_press_event)
		self.password_entry=builder.get_object("password_entry")
		self.password_entry.connect("activate",self.entries_press_event)
		self.login_eb_box=builder.get_object("login_eb_box")
		self.login_msg_label=builder.get_object("login_msg_label")
		
		self.server_ip_entry=builder.get_object("server_ip_entry")
		self.server_ip_entry.connect("activate",self.entries_press_event)
		
		self.button1=builder.get_object("button1")
		self.button1.grab_focus()
		
		
		self.login_overlay.add_overlay(self.login_box)
		self.login_overlay.show_all()
		
		
		self.stack.add_titled(self.login_overlay,"login","Login")
		self.stack.add_titled(self.overlay, "main", "Main")
		self.stack.add_titled(self.content_box, "mirror", "Mirror")
		self.stack.add_titled(self.configuration_box,"configuration","Configuration")
		
		
		self.banner_combo=builder.get_object("banner_combobox")
		self.banner_store=Gtk.ListStore(GdkPixbuf.Pixbuf,str)
		
		for x in glob.glob(BANNERS_PATH+"*.png"):
			f_name=x.replace(BANNERS_PATH,"").split(".png")[0]
			image=Gtk.Image()
			image.set_from_file(x)
			pixbuf=image.get_pixbuf()
			pixbuf=pixbuf.scale_simple(64,64,GdkPixbuf.InterpType.BILINEAR)
			self.banner_store.append([pixbuf,f_name])
			
			
		self.banner_combobox.set_model(self.banner_store)
		txt_renderer=Gtk.CellRendererText()
		pixbuf_renderer=Gtk.CellRendererPixbuf()
		
		self.banner_combobox.pack_start(pixbuf_renderer,True)
		self.banner_combobox.add_attribute(pixbuf_renderer,"pixbuf",0)
		self.banner_combobox.pack_start(txt_renderer,True)
		self.banner_combobox.add_attribute(txt_renderer,"text",1)
		
		
		self.window.add(self.stack)
		
		self.check_root()
		
		self.set_css_info()
		
		self.window.show_all()
		self.ib.hide()
		self.button1.hide()
		self.configuration_infobar.hide()
		
		self.progress_da.connect("draw",self.draw_progress)
		self.window.connect("destroy",self.quit)
		
		
		#self.set_previous_values()
		
		
		GObject.threads_init()
		Gtk.main()
		
	#def start_gui
	
	
	def set_css_info(self):
		
		css = b"""
		
		#BLUE_HEADER {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#455A64),  to (#455A64));;
			
		}
		
		#LIGHT_BLUE_BACKGROUND {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#338fef),  to (#338fef));;
			
		}
		
		#HEADER_SHADOW {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#7b7b7b),  to (#ffffff));;
		
		}
		
		
		#WHITE_BACKGROUND {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#ffffff),  to (#ffffff));;
		
		}
		
		#RED_BACKGROUND {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#cc0000),  to (#cc0000));;
		
		}
		
		#ORANGE_BACKGROUND {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#ff6600),  to (#ff6600));;
		}
		
		#LIGHT_RED_BACKGROUND {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#ff2d2d),  to (#ff2d2d));;
		
		}
		
		#BUTTON_COLOR {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#448AFF),  to (#448AFF));;
			
		
		}
		
		#DISABLED_BUTTON_OVER{
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#888888),  to (#888888));;
		}
		
		#DISABLED_BUTTON{
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#666666),  to (#666666));;
		}
		
		#CANCEL_BUTTON{
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#D32F2F),  to (#D32F2F));;
		}
		
		#CANCEL_BUTTON_OVER{
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#F44336),  to (#F44336));;
		}
		
		#SECTION_LABEL {
			font: 16px Roboto;
		}
		
		
		#BUTTON_OVER_COLOR {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#449fff),  to (#449fff));;
			
		
		}
		
		#BUTTON_LABEL{
			color:white;
			font: 10px Roboto;
		}
		
		
		#WHITE_MIRROR_NAME {
			color: white;
			font: 20px Roboto Medium;
		
		}
		
		#WHITE_EXTRA_INFO {
			color: white;
			font: 12px Roboto Light;
		
		}
		
		#BLUE_FONT {
			color: #3366cc;
			font: 10px Roboto;
			
		}

		#LABEL_OPTION{
		
			color: #808080;
			font: 11px Roboto;
		}
		
		#LOGIN_BUTTON {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#448AFF),  to (#448AFF));;
			color: #FFFFFF;
			font: 12px Roboto; 
		}
		
		#LOGIN_BUTTON_OVER {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#449fff),  to (#449fff));;
			color: #FFFFFF;
			font: 12px Roboto; 
		}
		
		#LOGIN_BUTTON_DISABLED {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#666666),  to (#666666));;
			color: #FFFFFF;
			font: 12px Roboto; 
		}
		
		#LOGIN_BUTTON_DISABLED_OVER {
			background-image:-gtk-gradient (linear,	left top, left bottom, from (#888888),  to (#888888));;
			color: #FFFFFF;
			font: 12px Roboto; 
		}
		
		#ERROR_FONT {
			color: #CC0000;
			font: 10px Roboto; 
		}
		

		"""
		
		self.style_provider=Gtk.CssProvider()
		self.style_provider.load_from_data(css)
		Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),self.style_provider,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		
		self.mirror_header_box.set_name("BLUE_HEADER")
		self.main_header_box.set_name("BLUE_HEADER")
		self.update_label_box.set_name("BUTTON_COLOR")
		self.export_label_box.set_name("BUTTON_COLOR")
		self.save_button_box.set_name("BUTTON_COLOR")
		self.configuration_header_box.set_name("BLUE_HEADER")
		self.configuration_label_box.set_name("BUTTON_COLOR")
		
		self.mirror_name_label.set_name("WHITE_MIRROR_NAME")
		self.llx_mirror_label.set_name("WHITE_MIRROR_NAME")
		self.conf_mirror_name_label.set_name("WHITE_MIRROR_NAME")
		self.arch_label.set_name("WHITE_EXTRA_INFO")
		self.shadow_box.set_name("HEADER_SHADOW")
		self.shadow_box1.set_name("HEADER_SHADOW")
		self.shadow_box2.set_name("HEADER_SHADOW")
		self.content_box.set_name("WHITE_BACKGROUND")
		self.list_box.set_name("WHITE_BACKGROUND")
		self.configuration_box.set_name("WHITE_BACKGROUND")
		
		self.name_label.set_name("LABEL_OPTION")
		self.banner_label.set_name("LABEL_OPTION")
		self.origin_label.set_name("LABEL_OPTION")
		self.distributions_label.set_name("LABEL_OPTION")
		self.sections_label.set_name("LABEL_OPTION")
		self.architectures_label.set_name("LABEL_OPTION")
		self.local_path_label.set_name("LABEL_OPTION")
		self.check_md5_label.set_name("LABEL_OPTION")
		self.ign_gpg_label.set_name("LABEL_OPTION")
		self.ign_release_label.set_name("LABEL_OPTION")
	
		self.update_label.set_name("BUTTON_LABEL")
		self.export_label.set_name("BUTTON_LABEL")
		self.save_label.set_name("BUTTON_LABEL")
		self.conf_label.set_name("BUTTON_LABEL")
		
		self.url_entry.set_name("BLUE_FONT")
		self.name_entry.set_name("BLUE_FONT")
		self.origin_entry.set_name("BLUE_FONT")
		self.distributions_entry.set_name("BLUE_FONT")
		self.sections_entry.set_name("BLUE_FONT")
		self.mirror_path_entry.set_name("BLUE_FONT")
		self.i386_label.set_name("BLUE_FONT")
		self.amd64_label.set_name("BLUE_FONT")
		
		self.user_entry.set_name("BLUE_FONT")
		self.password_entry.set_name("BLUE_FONT")
		self.server_ip_entry.set_name("BLUE_FONT")
		
		self.update_header_label.set_name("SECTION_LABEL")
		self.export_header_label.set_name("SECTION_LABEL")
		
		self.internet_rb_label.set_name("LABEL_OPTION")
		self.local_folder_rb_label.set_name("LABEL_OPTION")
		self.url_rb_label.set_name("LABEL_OPTION")
		self.destination_opt_label.set_name("LABEL_OPTION")
		
		self.local_folder_label.set_name("BLUE_FONT")
		self.destination_label.set_name("BLUE_FONT")
		self.login_eb.set_name("LOGIN_BUTTON")
		#self.login_eb_box.set_name("HEADER_SHADOW")
		self.login_msg_label.set_name("ERROR_FONT")
		
		
	#def set_css
	
	def set_mirror_info(self,mirror_button):


		'''
		"NAME": "",
		"BANNER": "",
		"ORIGS" : {"1":"lliruex.net/xenial","2":"","3":""},
		"ARCHITECTURES": [ "amd64", "i386"],
		"SECTIONS": ["main", "main/debian-installer", "universe", "restricted", "multiverse", "preschool"],
		"MIRROR_PATH": "/net/mirror/llx16",
		"DISTROS": ["xenial","xenial-updates","xenial-security"],
		"IGN_GPG":1,
		"IGN_RELEASE":0,
		"CHK_MD5":0,
		"CURRENT_UPDATE_OPTION":"1"
		'''

		self.url_entry.set_text(mirror_button.info["ORIGS"]["3"])
		if len(mirror_button.info["NAME"]) < 22 :
			self.mirror_name_label.set_text(mirror_button.info["NAME"])
			self.conf_mirror_name_label.set_text(mirror_button.info["NAME"])
			self.mirror_name_label.set_tooltip_text("")
			self.conf_mirror_name_label.set_tooltip_text("")
		else:
			self.mirror_name_label.set_text(mirror_button.info["NAME"][0:19]+"...")
			self.mirror_name_label.set_tooltip_text(mirror_button.info["NAME"])
			self.conf_mirror_name_label.set_tooltip_text(mirror_button.info["NAME"])	
			self.conf_mirror_name_label.set_text(mirror_button.info["NAME"][0:19]+"...")
		
		
		
		
		self.arch_label.set_text(", ".join(mirror_button.info["ARCHITECTURES"]))
		
		self.internet_rb.set_active(True)
		
		#if mirror_button.info["CURRENT_UPDATE_OPTION"]=="2":
		#	self.local_folder_rb.set_active(True)
			
		if mirror_button.info["CURRENT_UPDATE_OPTION"]=="3":
			self.url_rb.set_active(True)
		
		self.name_entry.set_text(mirror_button.info["NAME"])
		
		c=0
		
		for i in self.banner_store:
			if i[1]==mirror_button.info["BANNER"]:
				break
			c+=1
			
		self.banner_combobox.set_active(c)
			
			
		
		self.origin_entry.set_text(mirror_button.info["ORIGS"]["1"])
		self.distributions_entry.set_text(", ".join(mirror_button.info["DISTROS"]))
		self.sections_entry.set_text(", ".join(mirror_button.info["SECTIONS"]))
		self.i386_cb.set_active("i386" in mirror_button.info["ARCHITECTURES"])
		self.amd64_cb.set_active("amd64" in mirror_button.info["ARCHITECTURES"])
		self.mirror_path_entry.set_text(mirror_button.info["MIRROR_PATH"])
		
		self.check_md5_cb.set_active(mirror_button.info["CHK_MD5"]==1)
		self.ign_gpg_cb.set_active(mirror_button.info["IGN_GPG"]==1)
		self.ign_release_cb.set_active(mirror_button.info["IGN_RELEASE"]==1)
		
		self.progress_label.set_text("")
		
		self.current_mirror=mirror_button

		
		
		
		if self.updating_mirror!=None:
			if self.current_mirror!=self.updating_mirror and self.updating_mirror.info["updating"]:
				self.update_label_box.set_name("DISABLED_BUTTON")
				self.update_label.set_text(_("Update"))
				
			if self.current_mirror!=self.updating_mirror and self.updating_mirror.info["exporting"]:
				self.export_label_box.set_name("DISABLED_BUTTON")
				self.export_label.set_text(_("Export"))
				
			if self.current_mirror==self.updating_mirror:
				
				if self.updating_mirror.info["updating"]:
					self.update_label.set_text(_("Cancel"))
					self.update_label_box.set_name("CANCEL_BUTTON")
					
				if self.updating_mirror.info["exporting"]:
					self.export_label.set_text(_("Cancel"))
					self.export_label_box.set_name("CANCEL_BUTTON")
					
		
		'''
		if "2.5" in self.current_mirror.info["ORIGS"]:
		
			if self.current_mirror.info["ORIGS"]["2.5"]!="":
				self.folder_fcb.set_filename(self.current_mirror.info["ORIGS"]["2.5"])
				self.local_folder_label.set_text(self.current_mirror.info["ORIGS"]["2.5"])
			else:
				self.folder_fcb.set_filename(os.environ["HOME"])
				self.local_folder_label.set_text(os.environ["HOME"])
		'''		
				
		path="/home/%s"%os.environ["USER"]
		self.destination_fcb.set_filename(path)
		self.destination_label.set_text(path)
		
		
		
		return True
		
	#def set_mirror_info


	def parse_mirrors(self):
		'''
		self.mirrors={}
		
		once=True
		
		for t in range(0,1):
		
			for m_file in glob.glob(MIRROR_CONF_DIR+"*"):
				
				f=open(m_file,"r")
				data=json.load(f)
				f.close()
				m=MirrorButton(data)

				if once:
					
					if m.info["updating"]:
						if once:
							GLib.timeout_add(5,self.update_mirror_button_animation,m)
							once=False
								
				else:
						
					m.info["updating"]=False
					
				if t == 0:
					self.mirrors[m_file.split("/")[-1]]=m
				else:
					self.mirrors[m_file.split("/")[-1]+"%s"%t]=m
				self.add_mirror_button(m)
		
		return True
		'''
		
		self.mirrors=self.llx_conn.mirror_list()
		
		#print self.mirrors["mippa"]
		
		mirror_key=self.llx_conn.is_alive()
		
		for key in self.mirrors:
		
			m=MirrorButton(self.mirrors[key])
			m.info["KEY"]=key
			if key==mirror_key["msg"] and mirror_key["status"]:
				m.info["executing"]=True
				m.info["updating"]=True
				self.updating_mirror=m
				
				GLib.timeout_add(self.update_y_time,self.update_ys)
				GLib.timeout_add(self.update_percentage_time,self.update_percentage)
				GLib.timeout_add(self.update_degree_time,self.update_degree)
				
				GLib.timeout_add(self.update_mirror_button_time,self.update_mirror_button_animation,self.updating_mirror)
				self.export_label_box.set_name("DISABLED_BUTTON")
				
				
				
			self.add_mirror_button(m)
		
		return True
		
		
	#def parse_mirrors
	

	def set_previous_values(self):
		
		#self.folder_fcb.set_filename("/home/cless")
		#self.local_folder_label.set_text("/home/cless")
		
		#self.destination_fcb.set_filename("/home/cless")
		#self.destination_label.set_text("/home/cless")
		
		pass
		
	#def set_previous_values
	
	def set_info_text(self,txt,message_type=Gtk.MessageType.INFO):
		
		self.ib.set_message_type(message_type)
		self.info_label.set_markup(txt)
		self.ib.show()
		
	#def set_info_text
	
	def set_conf_text(self,txt,message_type=Gtk.MessageType.INFO):
		
		self.configuration_infobar.set_message_type(message_type)
		self.configuration_panel_label.set_markup(txt)
		self.configuration_infobar.show()
		
	#def set_info_text
	
	def show_content(self,widget):
		
		self.ib.hide()
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		self.stack.set_visible_child_name("mirror")
		
		
	#show_content
	
	def add_mirror_button(self,mirror_button):
		
		#print mirror_button.info
		
		da=Gtk.DrawingArea()
		da.set_size_request(140,148)
		da.add_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK | Gdk.EventMask.BUTTON_PRESS_MASK )
		
		da.connect("draw",self.draw_button,mirror_button)
		da.connect("motion-notify-event",self.mouse_over,mirror_button)
		da.connect("leave_notify_event",self.mouse_left,mirror_button)
		da.connect("button-press-event",self.mirror_button_clicked,mirror_button)
		
		da.size_request()
		
		da.show()
		
		mirror_button.info["da"]=da
		
		self.main_content_box.attach(da,self.current_grid_width,self.current_grid_height,1,1)
		
		self.current_grid_width+=1
		
		if self.current_grid_width > self.max_grid_width:
			self.current_grid_width=0
			self.current_grid_height+=1
			
	#def add_mirror_button
	

	def add_clicked(self,widget,event):
		
#		print ("add clicked")
		
		self.add_flag=True
	
		info={}
		
		info["NAME"]=""
		info["ARCHITECTURES"]=""
		info["CURRENT_UPDATE_OPTION"]=""
		info["BANNER"]=""
		info["DISTROS"]=""
		info["SECTIONS"]=""
		info["MIRROR_PATH"]=""
		info["ORIGS"]={}
		info["ORIGS"]["1"]=""
		info["ORIGS"]["2"]=""
		info["ORIGS"]["3"]=""
		info["CHK_MD5"]=""
		info["IGN_GPG"]=""
		info["IGN_RELEASE"]=""
		
		
		mirror=MirrorButton(info)
		mirror.info["updating"]=False
		
		self.set_mirror_info(mirror)
		self.banner_combobox.set_active(0)
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		self.stack.set_visible_child_name("configuration")
		
		
		
	#def add_clicked
	
	def add_mouse_over(self,widget,event,i):
		
		i.set_from_file(ADD_IMAGE_OVER)
		
	#def add_mouse_over
	
	
	def add_mouse_left(self,widget,event,i):
		
		i.set_from_file(ADD_IMAGE)
		
	#def add_mouse_over
	
	def entries_press_event(self,widget):
		
		
		
		self.login_clicked(None,None)

	def ib_response(self,widget,response):

		widget.hide()
		
	#
	
	def folder_fcb_changed(self,widget):
		
		
		self.local_folder_label.set_text(self.folder_fcb.get_filename())
		
	#def
	
	def destination_fcb_changed(self,widget):
		
		
		self.destination_label.set_text(self.destination_fcb.get_filename())
		
	#def
	
	
	def configuration_arrow_clicked(self,widget,event):
		
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
		if self.add_flag:
			self.stack.set_visible_child_name("main")
			self.add_flag=False
			return True
		
		self.ib.hide()			
		self.stack.set_visible_child_name("mirror")
		
		
	#def arrow_clicked
	
	
	def arrow_clicked(self,widget,event):
		
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
		self.stack.set_visible_child_name("main")
		
		
		
	#def arrow_clicked

	
	def mouse_over_update(self,widget,event):
		
		
		if self.updating_mirror!=None and self.updating_mirror.info["updating"]:
			
			if self.updating_mirror==self.current_mirror:
				self.update_label_box.set_name("CANCEL_BUTTON_OVER")
				return True
				
			self.update_label_box.set_name("DISABLED_BUTTON_OVER")
			return True
			
		
		if self.updating_mirror!=None and self.updating_mirror.info["exporting"]:
			
			self.update_label_box.set_name("DISABLED_BUTTON_OVER")
			return True
		
			
		self.update_label_box.set_name("BUTTON_OVER_COLOR")
		
	#def mouse_over_event
	
	def mouse_exit_update(self,widget,event):
		
		
		if self.updating_mirror!=None and self.updating_mirror.info["updating"]:
			
			if self.updating_mirror==self.current_mirror:
				self.update_label_box.set_name("CANCEL_BUTTON")
				return True
				
			self.update_label_box.set_name("DISABLED_BUTTON")
			return True
			
		
		if self.updating_mirror!=None and self.updating_mirror.info["exporting"]:
			
			self.update_label_box.set_name("DISABLED_BUTTON")
			return True
		
			
		self.update_label_box.set_name("BUTTON_COLOR")
		
		
	#def mouse left_update
	
	def update_clicked(self,widget,event):
		
		mode="1"
		data=None
	
		self.current_mirror.info["cancelled"]=False
		
		if self.updating_mirror!=None and self.updating_mirror!=self.current_mirror:
			if self.updating_mirror.info["executing"]:
				self.set_info_text(_("'%(mirror-name)s' is currently %(updating-or-exporting)s.")%{"mirror-name": self.updating_mirror.info["NAME"], "updating-or-exporting":  _('updating') if self.updating_mirror.info["updating"] else _('exporting')},Gtk.MessageType.ERROR)
				return False
		
		if self.current_mirror.info["exporting"]:
			self.set_info_text(_("'%(mirror-name)s' is currently exporting.")%{"mirror-name":self.updating_mirror.info["NAME"]},Gtk.MessageType.ERROR)
			return False
		
		if self.internet_rb.get_active():
			pass
			#print "INTERNET"
		
		if self.local_folder_rb.get_active():
#			print ("LOCAL_FOLDER: %s"%self.folder_fcb.get_filename())
			mode="2"
			data=self.folder_fcb.get_filename()
			self.current_mirror.info["ORIGS"]["2"]=data
			
			
		if self.url_rb.get_active():
#			print ("URL: %s"%self.url_entry.get_text())
			mode="3"
			data=self.url_entry.get_text()
			self.current_mirror.info["ORIGS"]["3"]=data
		
		self.current_mirror.info["CURRENT_UPDATE_OPTION"]=mode
		
		if not self.current_mirror.info["executing"]:
			
			self.percentage=0
			self.progress_label.set_text("")
			GLib.idle_add(self.ib.hide)
			self.updating_mirror=self.current_mirror
			self.current_mirror.info["updating"]=True
			self.current_mirror.info["executing"]=True
			self.current_mirror.info["cancelled"]=False
			GLib.timeout_add(self.update_y_time,self.update_ys)
			GLib.timeout_add(self.update_percentage_time,self.update_percentage)
			GLib.timeout_add(self.update_degree_time,self.update_degree)
			
			self.llx_conn.update(self.current_mirror.info["KEY"],mode,data)
			
			GLib.timeout_add(self.update_mirror_button_time,self.update_mirror_button_animation,self.updating_mirror)
			self.update_label.set_text(_("Cancel"))
			self.update_label_box.set_name("CANCEL_BUTTON_OVER")
			self.export_label_box.set_name("DISABLED_BUTTON")
			
		else:
			
			self.llx_conn.stop_update()
			
			self.updating_mirror.info["updating"]=False
			self.updating_mirror.info["executing"]=False
			self.updating_mirror.info["cancelled"]=True
			self.update_label.set_text(_("Update"))
			self.update_label_box.set_name("BUTTON_COLOR")
			self.export_label_box.set_name("BUTTON_COLOR")

	#def update_clicked

	
	def mouse_over_export(self,widget,event):
		
		
		if self.updating_mirror!=None and self.updating_mirror.info["exporting"]:
			
			if self.updating_mirror==self.current_mirror:
				self.export_label_box.set_name("CANCEL_BUTTON_OVER")
				return True
				
			self.export_label_box.set_name("DISABLED_BUTTON_OVER")
			return True
			
		
		if self.updating_mirror!=None and self.updating_mirror.info["updating"]:
			
			self.export_label_box.set_name("DISABLED_BUTTON_OVER")
			return True
		
		self.export_label_box.set_name("BUTTON_OVER_COLOR")
		
	#def mouse_over_event
	
	def mouse_exit_export(self,widget,event):
		
		if self.updating_mirror!=None and self.updating_mirror.info["exporting"]:
			
			if self.updating_mirror==self.current_mirror:
				self.export_label_box.set_name("CANCEL_BUTTON")
				return True
				
			self.export_label_box.set_name("DISABLED_BUTTON")
			return True
			
		
		if self.updating_mirror!=None and self.updating_mirror.info["updating"]:
			
			self.export_label_box.set_name("DISABLED_BUTTON")
			return True
		
		self.export_label_box.set_name("BUTTON_COLOR")
		
	#def mouse left_update
	
	def export_clicked(self,widget,event):
		
#		print ("Export clicked: %s"%self.destination_fcb.get_filename())
		
		
		if self.updating_mirror!=None and self.updating_mirror!=self.current_mirror:
			if self.updating_mirror.info["executing"]:
				self.set_info_text(_("'%(mirror-name)s' is currently %(updating-or-exporting)s.")%{"mirror-name": self.updating_mirror.info["NAME"], "updating-or-exporting": _('updating') if self.updating_mirror.info["updating"] else _('exporting')},Gtk.MessageType.ERROR)
				return False
		

		if self.current_mirror.info["updating"]:
			self.set_info_text(_("'%(mirror-name)s' is currently updating.")%{"mirror-name":self.updating_mirror.info["NAME"]},Gtk.MessageType.ERROR)
			return False

		if not self.current_mirror.info["exporting"]:
			
			self.percentage=0
			self.updating_mirror=self.current_mirror
			self.updating_mirror.info["exporting"]=True
			self.updating_mirror.info["executing"]=True
			self.updating_mirror.info["cancelled"]=False
			GLib.timeout_add(self.update_y_time,self.update_ys)
			GLib.timeout_add(self.update_percentage_time,self.update_percentage)
			GLib.timeout_add(self.update_degree_time,self.update_degree)
			
			self.llx_conn.export(self.updating_mirror.info["KEY"],self.destination_fcb.get_filename())
			
			GLib.timeout_add(self.update_mirror_button_time,self.update_mirror_button_animation,self.updating_mirror)
			
			

			self.export_label.set_text(_("Cancel"))
			self.export_label_box.set_name("CANCEL_BUTTON_OVER")
			
			self.update_label_box.set_name("DISABLED_BUTTON")

			
		else:
			self.llx_conn.stop_export()
			self.updating_mirror.info["exporting"]=False
			self.updating_mirror.info["executing"]=False
			self.updating_mirror.info["cancelled"]=True
			self.export_label.set_text(_("Export"))
			self.update_label_box.set_name("BUTTON_COLOR")
			self.export_label_box.set_name("BUTTON_COLOR")
		
		
		
		
		
		
	#def update_clicked
		

	def mouse_over_conf(self,widget,event):
		
		self.configuration_label_box.set_name("BUTTON_OVER_COLOR")
		
	#def mouse_over_event
	
	def mouse_exit_conf(self,widget,event):
		
		self.configuration_label_box.set_name("BUTTON_COLOR")
		
	#def mouse left_update
	
	def conf_clicked(self,widget,event):
		
#		print ("Configuration clicked")
		self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
		self.stack.set_visible_child_name("configuration")
		
	#def update_clicked

	def mirror_button_clicked(self,widget,event,mirror_button):
		
		self.set_mirror_info(mirror_button)
		self.show_content(None)
		
	#def button_clicked
	
	def mouse_over_save(self,widget,event):
		
		self.save_button_box.set_name("BUTTON_OVER_COLOR")
		
	#def mouse_over_event
	
	def mouse_exit_save(self,widget,event):
		
		self.save_button_box.set_name("BUTTON_COLOR")
		
	#def mouse left_update
	
	
	def save_button_clicked(self,widget,event):
		
		self.current_mirror.info["NAME"]=self.name_entry.get_text()
		
		self.current_mirror.info["BANNER"]=self.banner_store[self.banner_combobox.get_active()][1]
		
		# internal info based on banner name
		if os.path.exists(BANNERS_PATH+self.current_mirror.info["BANNER"]+".png"):
			self.current_mirror.info["image"]=BANNERS_PATH+self.current_mirror.info["BANNER"]+".png"
		else:
			self.current_mirror.info["image"]=UNKNOWN_BANNER
			
		if "img" in self.current_mirror.info:
			self.current_mirror.info.pop("img")
		
		# 
		
		
		
		self.label_image.queue_draw()
		self.label_image1.queue_draw()
		
		
		self.current_mirror.info["ORIGS"]["1"]=self.origin_entry.get_text()
		
		self.current_mirror.info["DISTROS"]=[]
		for item in self.distributions_entry.get_text().split(","):
			
			item=item.lstrip(" ").rstrip(" ")
			self.current_mirror.info["DISTROS"].append(item)
		
		self.current_mirror.info["SECTIONS"]=[]
		for item in self.sections_entry.get_text().split(","):
			
			item=item.lstrip(" ").rstrip(" ")
			self.current_mirror.info["SECTIONS"].append(item)
			
		self.current_mirror.info["ARCHITECTURES"]=[]
		if self.i386_cb.get_active():
			self.current_mirror.info["ARCHITECTURES"].append("i386")
		if self.amd64_cb.get_active():
			self.current_mirror.info["ARCHITECTURES"].append("amd64")
		
		self.current_mirror.info["MIRROR_PATH"]=self.mirror_path_entry.get_text()
		
		self.current_mirror.info["IGN_GPG"]=0
		if self.ign_gpg_cb.get_active():
			self.current_mirror.info["IGN_GPG"]=1
		
		self.current_mirror.info["IGN_RELEASE"]=0
		if self.ign_release_cb.get_active():
			self.current_mirror.info["IGN_RELEASE"]=1
		
		self.current_mirror.info["CHK_MD5"]=0
		if self.check_md5_cb.get_active():
			self.current_mirror.info["CHK_MD5"]=1

		self.set_mirror_info(self.current_mirror)
		
		if self.add_flag:
			
			self.mirrors[str(random.random())]=self.current_mirror
			self.add_mirror_button(self.current_mirror)
			self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
			self.ib.hide()
			self.stack.set_visible_child_name("mirror")
			
			self.add_flag=False
			
			try:
				key=self.llx_conn.create_config(self.current_mirror.info)
				self.current_mirror.info["KEY"]=key
				self.set_conf_text(_("Configuration Saved"),INFO)
			except Exception as e:
				self.set_conf_text(_("Could not save configuration")+" [%s]"%e,ERROR)
		
		else:
			try:
				self.llx_conn.save_config(self.current_mirror.info["KEY"],self.current_mirror.info)
				self.configuration_infobar.hide()
				self.set_conf_text(_("Configuration Saved"),INFO)
			except Exception as e:
				self.set_conf_text(_("Could not save configuration") +" [%s]"%e,ERROR)
		
	#def save_button_clicked

	
	def mouse_over_login(self,widget,event):
		
		if self.login_enabled:
		
			self.login_eb.set_name("LOGIN_BUTTON_OVER")
			
		else:
			
			self.login_eb.set_name("LOGIN_BUTTON_DISABLED")
		
	#def mouse_over_login
	
	def mouse_exit_login(self,widget,event):
		
		if self.login_enabled:
		
			self.login_eb.set_name("LOGIN_BUTTON")
		else:
			
			self.login_eb.set_name("LOGIN_BUTTON_DISABLED")
		
	#def mouse_over_login

	def validate_user(self):
		
		GLib.idle_add(self.validate_thread)
		
	#validate_user
	
	def validate_thread(self):
		
		
#		c=xmlrpclib.ServerProxy("https://"+self.server_ip+":9779")
		context=ssl._create_unverified_context()
		c = x.ServerProxy("https://%s:9779"%self.server_ip,context=context,allow_none=True)
		self.ret=None

		try:
			self.ret=c.validate_user(self.user,self.password)
		except Exception as e:
			self.ret=[False,str(e)]
			GLib.idle_add(self.set_login_msg,str(e))
			GLib.idle_add(self.login_form_sensitive)
			return

		
		if self.ret[0]:
			GLib.timeout_add(10,self.update_login_animation)
			GLib.idle_add(self.set_login_msg,"")
		else:
			GLib.idle_add(self.set_login_msg,"Wrong user and/or password")
			GLib.idle_add(self.login_form_sensitive)
			
		
	#def validate_thread

	def set_login_msg(self,msg):
		
		self.login_msg_label.set_text(msg)
		
	#def set_login_msg
	
	
	def login_form_sensitive(self,state=None):
		
		if state==None:
			state=not self.login_enabled
		
		self.login_enabled=state
		
		self.user_entry.set_sensitive(state)
		self.password_entry.set_sensitive(state)
		self.server_ip_entry.set_sensitive(state)
		
		if state:
			self.login_eb.set_name("LOGIN_BUTTON")
		else:
			self.login_eb.set_name("LOGIN_BUTTON_DISABLED")
		
		
	#def login_form_sensible
	

	def login_clicked(self,widget,event):
		
		
		if self.login_enabled:
		
			
			self.user=self.user_entry.get_text()
			self.password=self.password_entry.get_text()
			self.server_ip=self.server_ip_entry.get_text()
			
			if self.server_ip=="":
				#self.server_ip="server"
				self.server_ip="localhost"
			
			'''
			if self.user=="":	
				self.user="lliurex"
			if self.password=="":
				self.password="lliurex"
			'''
			
			self.login_animation_r=60
			self.login_form_sensitive()
			
			
			
			self.t=threading.Thread(target=self.validate_thread)
			self.t.daemon=True
			self.t.start()
			
			
			
		
		
	#def login_clicked
	
	def update_login_animation(self):
		
		#print "update_login_animation"
		
		self.login_animation_r+=10
		
		if self.login_animation_r<650:
			self.login_da.queue_draw()
			return True
		else:
			#return False
			self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
			self.stack.set_visible_child_name("main")
			self.llx_conn=lliurex_mirror_connect.LliurexMirrorN4d(self.server_ip,(self.user,self.password))
			self.parse_mirrors()
			
	def update_mirror_button_animation(self,mirror_button):
		
		#print "update_button_animation"
		
		if self.stack.get_visible_child_name()!="main":
			return True
		
		mirror_button.info["degree_offset"]+=4
		
		if self.updating_mirror.info["executing"]:
			if self.stack.get_visible_child_name()=="main":
				mirror_button.info["da"].queue_draw()
			return True
		
	#def update_mirror_animation
	
			
		


	def update_ys(self):
		

		# fps counter logic
		'''

		t1=time.time()
		t=t1-self.last_time
		self.t_counter+=1
		
		if self.t_counter >= 30:
			self.t_counter=0
		
		self.last_time=t1
		
		'''
		
		self.wave_xoffset-=1
		self.wave_xoffset2+=2
		self.wave_xoffset3+=1
		
		if self.stack.get_visible_child_name()=="mirror":
			self.progress_da.queue_draw()

		if self.updating_mirror.info["executing"]:
		
			return True
			

		
		
		
	#def update_ys

		
	def update_percentage(self):
		

		
		ret={}
		ret["status"]=False
		
		if self.updating_mirror.info["updating"]:
			ret=self.llx_conn.is_alive()
			self.percentage=self.llx_conn.get_percentage(self.updating_mirror.info["KEY"])
		if self.updating_mirror.info["exporting"]:
			ret=self.llx_conn.is_alive_export()
			self.percentage=self.llx_conn.get_percentage_export()
		
		self.progress_label.set_text(str(self.percentage) + "%")
		
		
		'''
		
		if self.percentage>=100:
					
			self.updating_mirror.info["executing"]=False
			self.updating_mirror.info["updating"]=False
			self.updating_mirror.info["exporting"]=False
			self.export_label_box.set_name("BUTTON_COLOR")
			self.update_label_box.set_name("BUTTON_COLOR")
					
			self.update_label.set_text("Update")
			self.export_label.set_text("Export")

		'''

		if ret["status"]:
			return True
		else:
			
			self.updating_mirror.info["executing"]=False
			self.updating_mirror.info["updating"]=False
			self.updating_mirror.info["exporting"]=False
			self.export_label_box.set_name("BUTTON_COLOR")
			self.update_label_box.set_name("BUTTON_COLOR")
						
			self.update_label.set_text(_("Update"))
			self.export_label.set_text(_("Export"))


			if not self.updating_mirror.info["cancelled"]:
				ret=self.llx_conn.get_status(self.updating_mirror.info["KEY"])
				if ret["status"]:
					pass
				else:
					error="Error:\n"

					error+=ret["msg"].lstrip().rstrip()
					self.set_info_text(error,Gtk.MessageType.ERROR)
						
					self.updating_mirror.info["executing"]=False
					self.updating_mirror.info["updating"]=False
					self.updating_mirror.info["exporting"]=False
					self.updating_mirror.info["cancelled"]=True
					self.export_label_box.set_name("BUTTON_COLOR")
					self.update_label_box.set_name("BUTTON_COLOR")
					self.update_label.set_text(_("Update"))
					self.export_label.set_text(_("Export"))

		
	#def update_percentage

		
	def update_degree(self):
		
		#print "update degree"
		
		self.degree_offset+=3
		
		if self.degree_offset>=360:
			self.dregree_offset=0
		
		if self.updating_mirror.info["executing"]:
			if self.stack.get_visible_child_name()=="mirror":
				self.updating_mirror.info["da"].queue_draw()
			
			return True
		
	#def update_degree
	

	def draw_label(self,widget,ctx):
		
		if self.stack.get_visible_child_name()=="main" :
			return
		
		ctx.move_to(0,0)
		if "img" not in self.current_mirror.info:
			self.current_mirror.info["img"]=cairo.ImageSurface.create_from_png(self.current_mirror.info["image"])
		ctx.set_source_surface(self.current_mirror.info["img"],(140-116)/-2,(140-116)/-2)
		ctx.paint()
		
		ctx.set_source_rgba(69/255.0,90/255.0,100/255.0,1)
		ctx.rectangle(0,0,116,116)
		ctx.arc_negative(self.circle["x"],self.circle["y"],self.circle["radius"]*0.9,self.to_rad(360),self.to_rad(0))
		ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
		ctx.fill()
		
		ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
		ctx.set_source_rgba(1,1,1,1)
		ctx.set_line_width(1)
		ctx.arc(self.circle["x"],self.circle["y"],self.circle["radius"]*0.9,self.to_rad(0),self.to_rad(360))
		ctx.stroke()
		
	#def draw

	
	def draw_progress(self,widget,ctx):

		if self.stack.get_visible_child_name()!="mirror":
			return

		if self.current_mirror==self.updating_mirror and self.updating_mirror.info["executing"]:
			percentage=self.percentage
		else:
			percentage=110

		if not percentage:
			percentage=0

		ctx.set_source_rgba(1,1,1,1)
		ctx.rectangle(0,0,self.frame_size,self.frame_size)
		ctx.fill()
		
		ctx.move_to(0,self.frame_size)

		
		
		ctx.set_source_rgba(self.update_water_colors[0].r,self.update_water_colors[0].g,self.update_water_colors[0].b,1)
		self.wave_yoffset=self.frame_size-(self.frame_size - (self.circle["radius"]*2))/2 - 7  - self.circle["radius"]*2*percentage/100
		
		
		first=True
		for x in range(0,self.frame_size + 1):
			
			y=self.get_wave_y(x,2)
			if y>self.frame_size:
				y=self.frame_size
			if first:
				fy=y
				first=False
			ctx.line_to(x,y)
		
		ctx.line_to(x,self.frame_size)
		ctx.line_to(0,self.frame_size)
		ctx.fill()
		
				
		ctx.set_source_rgba(self.update_water_colors[1].r,self.update_water_colors[1].g,self.update_water_colors[1].b,1)
		self.wave_yoffset=self.frame_size-(self.frame_size - (self.circle["radius"]*2))/2 - 5  - self.circle["radius"]*2*percentage/100
		
		first=True
		for x in range(0,self.frame_size + 1):
			
			y=self.get_wave_y(x,1)
			if y>self.frame_size:
				y=self.frame_size
			if first:
				fy=y
				first=False
			ctx.line_to(x,y)
		
		ctx.line_to(x,self.frame_size)
		ctx.line_to(0,self.frame_size)
		ctx.fill()
		
				
		ctx.set_source_rgba(self.update_water_colors[2].r,self.update_water_colors[2].g,self.update_water_colors[2].b,1)
		self.wave_yoffset=self.frame_size- (self.frame_size - (self.circle["radius"]*2))/2  - 2  - self.circle["radius"]*2*percentage/100
		
		first=True
		
		ys=[]		
		for x in range(0,self.frame_size + 1):
			
			y=self.get_wave_y(x)
			ys.append(y)
			if y>self.frame_size:
				y=self.frame_size
			
			if first:
				fy=y
				first=False
				
			
			ctx.line_to(x,y)
		
		ctx.line_to(x,self.frame_size)
		ctx.line_to(0,self.frame_size)
		ctx.fill()
		
		
		
		r2 = cairo.RadialGradient(0, 40, 1,0, 50, 100)
		r2.add_color_stop_rgb(0,self.update_water_colors[3].r,self.update_water_colors[3].g,self.update_water_colors[3].b)
		r2.add_color_stop_rgb(1, self.update_water_colors[4].r,self.update_water_colors[4].g,self.update_water_colors[4].b)
		ctx.set_source(r2)
		self.wave_yoffset=self.frame_size -  (self.frame_size - (self.circle["radius"]*2))/2   - self.circle["radius"]*2*percentage/100
		
		first=True
		
		for x in range(0,self.frame_size + 1):
			
			y=ys[x]+3
			
			if y>self.frame_size:
				y=self.frame_size
			
			if first:
				fy=y
				first=False
				
			
			ctx.line_to(x,y)
		
		ctx.line_to(x,self.frame_size)
		ctx.line_to(0,self.frame_size)
		ctx.fill()
		
		ctx.set_source_rgba(69/255.0,90/255.0,100/255.0,1)
		ctx.rectangle(0,0,self.frame_size,self.frame_size)
		ctx.arc_negative(self.circle["x"],self.circle["y"],self.circle["radius"],self.to_rad(360),self.to_rad(0))
		ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
		ctx.fill()
		
		ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
		ctx.set_source_rgba(52/255.0,52/255.0,52/255.0,1)
		ctx.set_line_width(2)
		ctx.arc(self.circle["x"],self.circle["y"],self.circle["radius"],self.to_rad(0),self.to_rad(360))
		ctx.stroke()
		
		ctx.set_line_width(2)
		ctx.set_source_rgba(1,1,1,1)
		if self.current_mirror.info["cancelled"]:
			ctx.set_source_rgba(1,0,0,1)
		ctx.arc(self.circle["x"],self.circle["y"],self.circle["radius"]+1,self.to_rad(0+self.degree_offset),self.to_rad(percentage*360/100+self.degree_offset))
		ctx.stroke()
		
	#

	def draw_login(self,widget,ctx):
		
		
		
		
		ctx.move_to(0,0)
		ctx.set_source_rgba(1,1,1,1)
		ctx.rectangle(0,0,600,1000)
		ctx.fill()
		
		
		'''
		ctx.set_source_rgba(0.4,0.4,1,1)
		ctx.arc(300,150,50,self.to_rad(0),self.to_rad(360))
		ctx.fill()
		'''
		
		
		
		#ctx.set_source_rgba(0,0,0,0.1)
		
	
		
		ctx.set_source_rgba(69/255.0,90/255.0,100/255.0,1)
		
		
		ctx.arc(self.login_animation_x,self.login_animation_y,self.login_animation_r,self.to_rad(0),self.to_rad(360))
		ctx.fill()
		
				
		'''
		ctx.arc(self.login_animation_x,self.login_animation_y,self.login_animation_r,self.to_rad(0),self.to_rad(360))
		x,y=ctx.get_current_point()

		r2 = cairo.RadialGradient(x, y, self.login_animation_r/2,x, y, self.login_animation_r)
		r2.add_color_stop_rgba(0, 1,1,0,1)
		r2.add_color_stop_rgba(1, 0, 0, ,1)
		ctx.set_line_width(8)
		ctx.set_source(r2)
			
		ctx.stroke()
		'''
		
		
	#def draw_login


	def draw_button(self,widget,ctx,mirror_button):
		
		if self.stack.get_visible_child_name()!="main":
			return 
		
		ctx.move_to(0,0)
		img=cairo.ImageSurface.create_from_png(SHADOW_BANNER)
		ctx.set_source_surface(img,0,mirror_button.info["shadow_start"])
		ctx.paint_with_alpha(mirror_button.info["shadow_alpha"])
		
		ctx.move_to(0,0)
		img=cairo.ImageSurface.create_from_png(mirror_button.info["image"])
		ctx.set_source_surface(img,0,0)
		ctx.paint()
		
		ctx.move_to(0,0)
		ctx.set_source_rgba(1,1,1,1)
		ctx.rectangle(0,110,140,30)
		ctx.fill()
		
		ctx.set_source_rgba(self.dark_gray.r,self.dark_gray.g,self.dark_gray.b,1)
		
		pctx = PangoCairo.create_layout(ctx)
		
		desc = Pango.font_description_from_string ("Roboto 9")
		pctx.set_font_description(desc)
		pctx.set_markup(mirror_button.info["NAME"])
		width=pctx.get_pixel_size()[0]
		
		if width > 130:
			pctx.set_markup(mirror_button.info["NAME"][0:22]+"...")
			
			
		
		ctx.move_to(5,118)
		PangoCairo.show_layout(ctx, pctx)
		
		
		
		
		if mirror_button.info["executing"]:
			
			ctx.move_to(0,0)
			ctx.set_source_rgba(0,0,0,0.5)
			ctx.rectangle(0,0,140,110)
			ctx.fill()
			
			ctx.arc(70,70-15,40,self.to_rad(0+mirror_button.info["degree_offset"]),self.to_rad(180+mirror_button.info["degree_offset"]))
			x,y=ctx.get_current_point()

			r2 = cairo.RadialGradient(x, y, 10,x, y, 60)
			r2.add_color_stop_rgba(0, 1,1,1,1)
			r2.add_color_stop_rgba(1, 68/255.0, 159/255.0, 255/255.0,0)
			ctx.set_line_width(8)
			ctx.set_source(r2)
			
			ctx.stroke()
			
			ctx.set_line_width(1)
			
			ctx.set_source_rgba(1,1,1,1)
			ctx.arc(x,y,4,self.to_rad(0),self.to_rad(360))
			ctx.fill()
			
			if int(random.random()*100) > 45:
	
				if len(mirror_button.info["random_lights"]) < mirror_button.info["max_random_lights"]:
					
					offset=int(random.random()*12)
					
					if offset > 6:
						
						offset=offset/-2
					
					mirror_button.info["random_lights"].append(LightPoint(x+offset,y,random.random()*2))

				
			for i in range(len(mirror_button.info["random_lights"])-1,-1,-1):
				
				mirror_button.info["random_lights"][i].opacity-=0.02
				if mirror_button.info["random_lights"][i].opacity <=0.0:
					mirror_button.info["random_lights"].pop(i)
					continue
				
				#ctx.set_source_rgba(1,1,1,mirror_button.info["random_lights"][i].opacity)
				ctx.set_source_rgba(random.random(),1,1,mirror_button.info["random_lights"][i].opacity)
				ctx.arc(mirror_button.info["random_lights"][i].x,mirror_button.info["random_lights"][i].y,mirror_button.info["random_lights"][i].radius,self.to_rad(0),self.to_rad(360))
				#ctx.arc(mirror_button.info["random_lights"][i].x,mirror_button.info["random_lights"][i].y,random.random()*3,self.to_rad(0),self.to_rad(360))
				ctx.fill()
	
	#def draw_button

	
	def mouse_over(self,widget,event,mirror_button):
		
		#print mirror_button.info
		mirror_button.info["animation_active"]=False
		if mirror_button.info["shadow_alpha"] <0.3 :
			mirror_button.info["shadow_alpha"]+=0.1
			widget.queue_draw()
			return True
			
		return False
		
	#def mouse_over

	
	def mouse_left(self,widget,event,mirror_button):
		
		if not mirror_button.info["animation_active"]:
			
			mirror_button.info["animation_active"]=True
			GLib.timeout_add(10,self.restore_shadow_alpha,mirror_button,widget)
			
	#def mouse_left

	def info_button_clicked(self,button):
		
		ret=self.llx_conn.get_last_log()
		if ret!=None:
			os.system("scite %s &"%ret)
		
	#def info_button_clicked

	def hide_window(self,widget,event):
		
		widget.hide()
		return True
		
	#def 

	
	def restore_shadow_alpha(self,mirror_button,widget):

		if mirror_button.info["shadow_alpha"] >=0.2 :
			mirror_button.info["shadow_alpha"]-=0.1
			widget.queue_draw()
			return True
			
		mirror_button.info["animation_active"]=False
		return False
		
	#def  restore_shadow_alpha
	

	def to_rad(self,degree):
		
		return degree * (pi/180)
		
	#def to_rad
	
	
	def get_wave_y(self,x,wtype=0):
		
		
		#return 1
		
		x_offset=self.wave_xoffset
		amplitude=self.wave_amplitude
		
		if wtype==1:
			x_offset=self.wave_xoffset2
			amplitude=self.wave_amplitude2
			
		if wtype==2:
			x_offset=self.wave_xoffset3
			amplitude=self.wave_amplitude3
		
		return amplitude * math.sin((2*pi / self.wave_lenght)*(x - x_offset)) + self.wave_yoffset
		
		
	#def get_wave_y


	def quit(self,widget):
		
		Gtk.main_quit()
	
	#def quit

	
#class LliurexMirror

lm=LliurexMirror()
lm.start_gui()
