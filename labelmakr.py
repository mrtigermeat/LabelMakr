from pathlib import Path
import sys, os

root_dir = Path(__file__).parent.parent.resolve()
os.environ['PYTHONPATH'] = str(root_dir)
sys.path.insert(0, str(root_dir))

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'

import warnings
warnings.simplefilter("ignore", UserWarning)

import re
from glob import glob
import logging

# GUI stuff
import customtkinter as ctk
import tkinter as tk
from ftfy import fix_text as fxy # unicode text all around fix
import threading
from PIL import Image, ImageTk
from CTkListbox import *
from CTkToolTip import *
from ezlocalizr import ezlocalizr

# function stuff
import yaml

# LabelMakr specific functions
#import modules.utils.sofa_func # basically just a script with sofa inference
import modules.utils.whisper_func as whisper_func # transcriber class is here
from modules.utils.labbu_func import labbu_func as labbu_func # for label editing, coming in future update.
from modules.utils import (
	get_logger,
	load_config,
	get_os,
	FontManager
)
from modules.utils.constants import (
	ASSETS,
	STRINGS,
	CORPUS,
	MODELS
)
from modules.utils.audio import mixer_wrapper

OS = get_os()

ctk.set_default_color_theme(Path(ASSETS / 'ctk_tgm_theme.json'))
ctk.deactivate_automatic_dpi_awareness()

def dummy():
	print('teehee :3c')

class LabelMakr(ctk.CTk):
	def __init__(self, debug: bool):
		super().__init__()

		self.debug = debug

		global logger
		if debug:
			logger = get_logger(level="DEBUG")
		else:
			logger = get_logger()

		os_ok = OS in ['linux', 'osx', 'win32']
		assert OS in ['linux', 'osx', 'win32']
		if debug:
			logger.success(f'{OS} is supported by LabelMakr2.')

		
		# init global config, default if error
		cfg_path = Path(ASSETS / 'cfg.yaml')
		if cfg_path.exists():
			self.cfg = load_config(cfg_path)
			logger.debug(f'loaded config {str(cfg_path)}')
		if self.cfg == {}:
			self.cfg = {
				'disp_lang': 'en_US',
				'matmul': True,
				'whisper_model': 'medium',
				'dark_mode': True,
				'force_cpu': False
			}
			logger.warning(f"Unable to open config {str(cfg_path)}, using default dictionary: \n {self.config}")

		if Path(ASSETS / 'cfg.yaml').exists():
			with open(Path(ASSETS / 'cfg.yaml'), 'r', encoding='utf-8') as c:
				try:
					self.cfg.update(yaml.safe_load(c))
					c.close()
				except yaml.YAMLError as exc:
					logger.warning(f'Cannot load config file, using default dictionary.')

		# init variables from config
		self.clang = ctk.StringVar(value=self.cfg['disp_lang'])
		self.inf_wh_model = ctk.StringVar(value=self.cfg['whisper_model'])
		self.matmul_var = ctk.BooleanVar(value=self.cfg['matmul'])
		self.dark_mode = ctk.BooleanVar(value=self.cfg['dark_mode'])	
		self.force_cpu = ctk.BooleanVar(value=self.cfg['force_cpu'])

		# init SOFA models
		self.sofa_models = {'models':{}}
		for model in glob(str(MODELS / '*')):
			model = model[7:]
			# ignore the g2p model file
			if model in ['g2p_model.py', '__pycache__']:
				continue
			g2p_bool = False
			g2p_model = None
			g2p_cfg = None

			if Path(MODELS / model / 'g2p').exists():
				g2p_bool = True
				g2p_model = Path(MODELS / model / 'g2p/model.ptsd')
				g2p_cfg = Path(MODELS / model / 'g2p/cfg.yaml')

			self.sofa_models['models'][model] = {
				'ckpt_path': Path(MODELS / model / 'model.ckpt'),
				'dict_path': Path(MODELS / model / 'dict.txt'),
				'g2p': g2p_bool,
				'g2p_model': g2p_model,
				'g2p_cfg': g2p_cfg
			}

		# init languages w/ezlocalizr
		self.L = ezlocalizr(language=self.clang.get(),
							string_path=STRINGS,
							default_lang='en_US')

		self.FontManager = FontManager()

		# init labbu for label fixes
		self.labu = labbu_func(lang='default')

		self.wh_models = ['tiny', 'base', 'small', 'medium', 'large']
		self.transcribe_lang_op = ['EN', 'JP', 'ZH', 'FR', 'KO']
		self.transcribe_lang_op.sort()

		self.font, self.font_sm = self.FontManager.load_font()

		if self.dark_mode.get():
			ctk.set_appearance_mode("dark")
		else:
			ctk.set_appearance_mode("light")

		logger.info('Successfully initialized LabelMakr.')

		self.tr_editor = None
		self.main_window()
		
	def main_window(self):

		# window config
		self.title(self.L('app_ttl'))
		#self.wm_class('labelmakr', self.L('app_ttl'))
		self.geometry(f"{1150}x{600}")
		self.resizable(height=True, width=True)
		self.minsize(width=1150, height=600)
		self.tt_delay = 1			

		#
		#	GUI Image Initialization
		#

		if Path(ASSETS / 'labelmakr.png').exists():
			self.labelmakr_logo = ctk.CTkImage(light_image=Image.open(ASSETS / 'labelmakr.png'), size=(300,30))
		if Path(ASSETS / 'folder.png').exists():
			self.folder_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'folder.png'))
		if Path(ASSETS / 'trns.png').exists():
			self.trns_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'trns.png'))
		if Path(ASSETS / 'trns_edit.png').exists():
			self.trns_edit_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'trns_edit.png'))
		if Path(ASSETS / 'align.png').exists():
			self.align_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'align.png'))
		if Path(ASSETS / 'fix.png').exists():	
			self.fix_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'fix.png'))
		if Path(ASSETS / 'play.png').exists():
			self.play_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'play.png'))
		if Path(ASSETS / 'pause.png').exists():
			self.pause_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'pause.png'))
		if Path(ASSETS / 'stop.png').exists():
			self.stop_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'stop.png'))
		if Path(ASSETS / 'save.png').exists():
			self.save_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'save.png'))
		if Path(ASSETS / 'fastfw.png').exists():
			self.next_ico = ctk.CTkImage(light_image=Image.open(ASSETS / 'fastfw.png'))

		# ICON SETUP - still need to test on osx
		if Path(ASSETS / 'tgm.ico').exists():
			if OS == 'win32':
				self.wm_iconbitmap(ASSETS / 'tgm.ico')
			elif OS == 'linux':
				if Path(ASSETS / 'tgm_logo.png').exists():
					self.icontk = ImageTk.PhotoImage(Image.open(ASSETS / 'tgm_logo.png'))
					self.iconphoto(True, self.icontk)

		# Variables
		self.corpus_path = ctk.StringVar(value="./corpus")
		self.trans_lang_choice = ctk.StringVar(value='EN')

		#
		#	TITLE LABEL
		#

		self.grid_columnconfigure(0, weight=1)
		self.grid_columnconfigure(1, weight=1)
		self.grid_rowconfigure(0, weight=1)
		self.grid_rowconfigure(1, weight=5)

		# logo at the top
		self.title_lbl = ctk.CTkLabel(self, image=self.labelmakr_logo, text='')
		self.title_lbl.grid(row=0, column=0, padx=10, pady=(10, 5), sticky=tk.NW, columnspan=2)

		# CORPUS BAR AT DA TOP
		self.corpus_label = ctk.CTkLabel(self,
										 text='Corpus Path' + ":", #NEEDSSTRING
										 font=self.font)
		self.corpus_label.grid(row=0, column=1, padx=5, pady=(15, 0), sticky=tk.NE)
		self.corpus_label_tt = CTkToolTip(self.corpus_label, delay=self.tt_delay, message='Path to the corpus you wish to process.', font=self.font) #NEEDSSTRING

		self.corpus_entry = ctk.CTkEntry(self,
										 corner_radius=5,
										 font=self.font,
										 state='normal',
										 textvariable=self.corpus_path,
										 width=350)
		self.corpus_entry.grid(row=0, column=2, padx=(5, 0), pady=(15, 0), sticky=tk.NE)

		def browse_corpus():
			folder_path = tk.filedialog.askdirectory()
			if folder_path:
				self.corpus_path.set(folder_path)

		self.corpus_browse = ctk.CTkButton(self,
										   text='Browse', #NEEDSSTRING
										   command=lambda: browse_corpus(),
										   compound=tk.LEFT,
										   font=self.font,
										   width=20)
		self.corpus_browse.grid(row=0, column=3, padx=(0, 15), pady=(15, 0), sticky=tk.NE)

		#
		#	Unnecessarily long tab configuration
		#

		self.tabs = ctk.CTkTabview(self)
		self.tabs.grid(row=1, column=0, padx=10, pady=(0, 5), sticky=tk.NSEW, columnspan=4)

		self.tab_ttl_1 = self.L('tab_ttl_1')
		self.tab_ttl_2 = self.L('tab_ttl_2')
		self.tab_ttl_3 = self.L('tab_ttl_3')
		self.tab_ttl_4 = self.L('tab_ttl_4')

		self.tabs.add(self.tab_ttl_1)
		self.tabs.add(self.tab_ttl_2)
		self.tabs.add(self.tab_ttl_3)
		self.tabs.add(self.tab_ttl_4)
		self.tabs.set(self.tab_ttl_1)

		self.tabs._segmented_button.configure(font=self.font)

		# copyright label at the bottom of the screen
		self.credits = ctk.CTkLabel(self, 
									text=fxy('© tigermeat 2023-2026 | v2.0.0.dev'), 
									text_color="gray50",
									font=self.font_sm)
		self.credits.grid(padx=5, pady=(0, 5), sticky=tk.EW, columnspan=4)

		#
		#	Transcription Tab
		#

		self.tabs.tab(self.tab_ttl_1).grid_columnconfigure((0, 2), weight=0)
		self.tabs.tab(self.tab_ttl_1).grid_columnconfigure(1, weight=1)
		self.tabs.tab(self.tab_ttl_1).grid_rowconfigure(0, weight=1)
		self.tabs.tab(self.tab_ttl_1).grid_rowconfigure(1, weight=0)

		# folder box
		self.trans_file_select = CTkListbox(self.tabs.tab(self.tab_ttl_1),
								   			multiple_selection=False,
								   			font=self.font)
		self.trans_file_select.bind("<<ListboxSelect>>", lambda: dummy())

		# placing all label files into the thingymajig.
		'''
		self.file_list_index = {}
		for i, file in enumerate(self.file_list):
			self.file_sel.insert(i, file)
			self.file_list_index[file] = i
		'''

		if self.debug:
			for i, file in enumerate(["strawberry.wav", "blueberry.wav", "which_is_it.wav"]):
				self.trans_file_select.insert(i, file)
			logger.debug("Displaying text audio files.")
		
		self.trans_file_select.grid(row=0, column=0, rowspan=999, padx=5, pady=5, sticky=tk.NSEW)

		self.editor_frame = ctk.CTkFrame(self.tabs.tab(self.tab_ttl_1))
		self.editor_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)

		self.editor_frame.grid_rowconfigure(0, weight=1)
		self.editor_frame.grid_rowconfigure(1, weight=0)
		self.editor_frame.grid_columnconfigure(0, weight=1)

		self.text_box = ctk.CTkTextbox(self.editor_frame, 
									   wrap='word',
									   activate_scrollbars=True,
									   font=self.font)
		self.text_box.grid(row=0, column=0, sticky=tk.NSEW)

		if self.debug:
			self.text_box.insert(tk.END, "it's a miraculous encounter, encounter, i'm going to faint... ")
			self.text_box.insert(tk.END, "it's a miraculous encounter, i do not let you so oh it's a dream! ")
			self.text_box.insert(tk.END, "Why do i feel this way? Why do you do it in this way? ")
			self.text_box.insert(tk.END, "Tick. Ticktick. Tick.")
			logger.debug("Displaying test lyrics.")


		# AUDIO TIMELINE

		self.bottom_box = ctk.CTkFrame(self.editor_frame, fg_color='transparent')
		self.bottom_box.grid(row=1, column=0, pady=(15, 0), sticky=tk.EW)

		self.bottom_box.grid_columnconfigure(0, weight=1)
		self.bottom_box.grid_rowconfigure(1, weight=1)

		self.audio_time = ctk.IntVar(value=0)
		self.audio_volume = ctk.IntVar(value=75)

		self.time_slider_frame = ctk.CTkFrame(self.bottom_box, fg_color='transparent')
		self.time_slider_frame.grid(row=1, column=0, sticky=tk.EW)

		self.time_slider_frame.grid_rowconfigure(0, weight=3)
		self.time_slider_frame.grid_rowconfigure(1, weight=0)
		self.time_slider_frame.grid_columnconfigure(0, weight=1)
		self.time_slider_frame.grid_columnconfigure(1, weight=1)

		self.time_slider = ctk.CTkSlider(self.time_slider_frame,
										 from_=0,
										 to=100,
										 variable=self.audio_time,
										 orientation='horizontal')
		self.time_slider.grid(row=0, column=0, columnspan=2, padx=10, sticky=tk.EW)

		label_text_color = 'gray45'

		self.audio_timeline = ctk.CTkLabel(self.time_slider_frame,
										 text='Audio Timeline', #NEEDSSTRING
										 font=self.font_sm,
										 text_color=label_text_color)
		self.audio_timeline.grid(row=1, column=0, padx=(15, 0), sticky=tk.W)

		self.duration_label = ctk.CTkLabel(self.time_slider_frame,
										   text='0:00 / 0:37', #NEEDSSTRING
										   font=self.font_sm,
										   text_color=label_text_color)
		self.duration_label.grid(row=1, column=1, padx=(0, 15), sticky=tk.E)

		self.button_frame = ctk.CTkFrame(self.bottom_box, height=40)
		self.button_frame.grid(row=2, column=0, columnspan=2, sticky='')

		self.button_frame.grid_rowconfigure(0, weight=1)

		trans_button_width = 80

		# play button
		self.play_audio_btn = ctk.CTkButton(self.button_frame, 
											image=self.play_ico,
											text='',
											width=trans_button_width,
											command=lambda: self.play_audio())
		self.play_audio_btn.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
		self.play_audio_btn_tt = CTkToolTip(self.play_audio_btn, delay=self.tt_delay, message=self.L('play'), font=self.font)

		# pause/unpause button
		self.pause_audio_btn = ctk.CTkButton(self.button_frame, 
											image=self.pause_ico,
											text='', 
											width=trans_button_width, 
											command=lambda: self.pause_audio())
		self.pause_audio_btn.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
		self.pause_audio_btn_tt = CTkToolTip(self.pause_audio_btn, delay=self.tt_delay, message=self.L('pause'), font=self.font)

		# stop button
		self.stop_audio_btn = ctk.CTkButton(self.button_frame, 
											image=self.stop_ico,
											text='',
											width=trans_button_width,
											command=lambda: self.stop_audio())
		self.stop_audio_btn.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
		self.stop_audio_btn_tt = CTkToolTip(self.stop_audio_btn, delay=self.tt_delay, message=self.L('stop'), font=self.font)

		# save button
		self.save_lbl_btn = ctk.CTkButton(self.button_frame,
										  image=self.save_ico,
										  text='',
										  width=trans_button_width,
										  command=lambda: self.save_label())
		self.save_lbl_btn.grid(row=0, column=3, padx=5, pady=5, sticky=tk.NSEW)
		self.save_lbl_btn_tt = CTkToolTip(self.save_lbl_btn, delay=self.tt_delay, message=self.L('save'), font=self.font)

		#Volume slider
		self.volume_frame = ctk.CTkFrame(self.button_frame, fg_color='transparent')
		self.volume_frame.grid(row=0, column=4, padx=5, pady=5, sticky=tk.EW)

		self.volume_frame.grid_columnconfigure(0, weight=0)
		self.volume_frame.grid_rowconfigure(0, weight=1)

		self.volume_label = ctk.CTkLabel(self.volume_frame,
										 text='Volume', #NEEDSSTRING
										 font=self.font_sm,
										 text_color=label_text_color)
		self.volume_label.grid(row=0, column=0, padx=(0, 5), sticky=tk.W)

		self.volume_slider = ctk.CTkSlider(self.volume_frame,
										   from_=0,
										   to=100,
										   variable=self.audio_volume,
										   orientation='horizontal')
		self.volume_slider.grid(row=1, column=0, pady=(0, 5), sticky=tk.NSEW)

		self.trans_option_frame = ctk.CTkFrame(
			self.tabs.tab(self.tab_ttl_1),
			border_width=3,
		)
		self.trans_option_frame.grid(row=0, column=2, padx=5, pady=5, rowspan=999, sticky=tk.NSEW)

		self.trans_label = ctk.CTkLabel(self.trans_option_frame,
										text='Transcription Options', #NEEDSSTRING
										font=self.font_sm,
										text_color=label_text_color)
		self.trans_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky=tk.NW)

		self.language_label = ctk.CTkLabel(
			self.trans_option_frame,
			text=self.L('lang_choice'),
			font=self.font_sm,
			text_color=label_text_color
		)
		self.language_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.NW)

		def language_combo_cb(choice):
			if self.debug:	
				logger.info(f'self.language_combo chose {choice}')

		self.language_choice = ctk.StringVar(value='EN')

		self.language_combo = ctk.CTkComboBox(
			self.trans_option_frame,
			values='',
			command=language_combo_cb,
			variable=self.language_choice,
			font=self.font,
			dropdown_font=self.font,
			state='readonly',
			justify='center'
		)
		self.language_combo.grid(row=2, column=0, columnspan=2, padx=15, pady=2.5, sticky=tk.EW)

		if self.debug:
			self.language_combo.configure(values=sorted(['EN', 'FR', 'JA', 'ZH', 'KO']))
		
		self.trans_model_label = ctk.CTkLabel(
			self.trans_option_frame,
			text=self.L('wh_model'),
			font=self.font_sm,
			text_color=label_text_color
		)
		self.trans_model_label.grid(row=3, column=0, padx=10, pady=2.5, sticky=tk.NW)

		def trans_model_cb(choice):
			if self.debug:
				logger.info(f'self.trans_model_combo chose {choice}')
		
		self.trans_model_choice = ctk.StringVar(value='distil-whisper/distil-large-v3')
		
		self.trans_model_combo = ctk.CTkComboBox(
			self.trans_option_frame,
			values='',
			command=trans_model_cb,
			variable=self.trans_model_choice,
			font=self.font_sm,
			dropdown_font=self.font_sm,
			state='readonly',
			justify='center'
		)
		self.trans_model_combo.grid(row=4, column=0, columnspan=2, padx=15, pady=5, sticky=tk.EW)

		trans_button_height = 50
		# transcribe button
		self.trns_btn = ctk.CTkButton(
			self.trans_option_frame,
			text=self.L('run_trns'),
			command=lambda: self.run_transcriber(),
			image=self.trns_ico,
			compound=tk.LEFT,
			font=self.font,
			height=trans_button_height
		)
		self.trns_btn.grid(row=9, column=0, padx=(10, 2.5), pady=(10, 5), sticky=tk.EW)
		self.trns_btn_tt = CTkToolTip(self.trns_btn, delay=self.tt_delay, message=self.L('run_trns_tt'), font=self.font)

		# transcription editor button
		self.batch_trans_btn = ctk.CTkButton(
			self.trans_option_frame,
			text='Transcribe All', #NEEDSSTRING
			command=lambda: self.open_transcription_editor(),
			image=self.trns_edit_ico,
			compound=tk.LEFT,
			font=self.font,
			height=trans_button_height
		)
		self.batch_trans_btn.grid(row=9, column=1, padx=(2.5, 10), pady=(10, 5), sticky=tk.EW)
		self.batch_trans_btn_tt = CTkToolTip(self.batch_trans_btn, delay=self.tt_delay, message=self.L('transcription_editor_tt'), font=self.font) #NEEDSSTRING








		#
		#	Alignment Tab GUI Codes
		#

		# grid configs
		self.tabs.tab(self.tab_ttl_2).grid_columnconfigure((0, 1), weight=1)
		self.tabs.tab(self.tab_ttl_2).grid_rowconfigure((0, 1), weight=1)
		self.tabs.tab(self.tab_ttl_2).grid_rowconfigure(2, weight=3)

		self.model_choice = ctk.StringVar(value='tgm_sofa_en')
		self.op_mode = ctk.StringVar(value='htk')
		self.op_choices = ['htk', 'TextGrid']

		# choose sofa model
		self.model_lbl = ctk.CTkLabel(self.tabs.tab(self.tab_ttl_2),
									  text=self.L('model_lbl'),
									  font=self.font)
		self.model_lbl.grid(row=0, column=0, padx=5, pady=(10, 5), sticky=tk.N)
		self.model_lbl_tt = CTkToolTip(self.model_lbl, delay=self.tt_delay, message=self.L('model_lbl_tt'), font=self.font)

		# model choice combobox
		self.model_cmbo = ctk.CTkComboBox(self.tabs.tab(self.tab_ttl_2),
										  values=self.sofa_models['models'],
										  variable=self.model_choice,
										  font=self.font,
										  dropdown_font=self.font,
										  justify='center')
		self.model_cmbo.set(self.model_choice.get())
		self.model_cmbo.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)

		# choose format
		self.op_lbl = ctk.CTkLabel(self.tabs.tab(self.tab_ttl_2),
								   text=self.L('op_lbl'),
								   font=self.font)
		self.op_lbl.grid(row=0, column=1, padx=5, pady=(10, 5), sticky=tk.N)
		self.op_lbl_tt = CTkToolTip(self.op_lbl, delay=self.tt_delay, message=self.L('op_lbl_tt'), font=self.font)

		# model choice combobox
		self.op_cmbo = ctk.CTkComboBox(self.tabs.tab(self.tab_ttl_2),
									   values=self.op_choices,
									   variable=self.op_mode,
									   font=self.font,
									   dropdown_font=self.font,
									   justify='center')
		self.op_cmbo.set(self.op_mode.get())
		self.op_cmbo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)

		# align button
		self.align_btn = ctk.CTkButton(self.tabs.tab(self.tab_ttl_2),
									   text=self.L('run_align'),
									   command=lambda: self.run_sofa(
				   							self.sofa_models['models'][self.model_cmbo.get()]['ckpt_path'],
				   							self.sofa_models['models'][self.model_cmbo.get()]['dict_path'],
				   							self.sofa_models['models'][self.model_cmbo.get()]['g2p'],
				   							self.sofa_models['models'][self.model_cmbo.get()]['g2p_model'],
				   							self.sofa_models['models'][self.model_cmbo.get()]['g2p_cfg']),
									   image=self.align_ico,
									   compound=tk.LEFT,
									   font=self.font)
		self.align_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
		self.align_btn_tt = CTkToolTip(self.align_btn, delay=self.tt_delay, message=self.L('run_align_tt'), font=self.font)

		#
		#	Fix Label Tab GUI Code
		#

		self.tabs.tab(self.tab_ttl_3).grid_columnconfigure((0, 1), weight=1)
		self.tabs.tab(self.tab_ttl_3).grid_rowconfigure(0, weight=0)
		self.tabs.tab(self.tab_ttl_3).grid_rowconfigure((1, 2), weight=1)
		self.tabs.tab(self.tab_ttl_3).grid_rowconfigure(3, weight=3)

		# help label
		self.labbu_help = ctk.CTkLabel(self.tabs.tab(self.tab_ttl_3),
									   text=self.L('labbu_help'),
									   font=self.font_sm,
									   text_color='lightgray',)
		self.labbu_help.grid(row=0, column=0, columnspan=2, padx=5, pady=2.5, sticky=tk.NSEW)

		# dxer box
		self.dxer = ctk.BooleanVar(value=True)
		self.dxer_cb = ctk.CTkCheckBox(self.tabs.tab(self.tab_ttl_3),
									   variable=self.dxer,
									   onvalue=True,
									   offvalue=False,
									   text=self.L('dxer'),
									   font=self.font)
		self.dxer_cb.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)
		self.dxer_cb_tt = CTkToolTip(self.dxer_cb, delay=self.tt_delay, message=self.L('dxer_tt'), font=self.font)

		# uhr merge
		self.uhr_merge = ctk.BooleanVar(value=True)
		self.uhr_merge_cb = ctk.CTkCheckBox(self.tabs.tab(self.tab_ttl_3),
											variable=self.uhr_merge,
											onvalue=True,
											offvalue=False,
											text=self.L('uhr_merge'),
											font=self.font)
		self.uhr_merge_cb.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)
		self.uhr_merge_tt = CTkToolTip(self.uhr_merge_cb, delay=self.tt_delay, message=self.L('uhr_merge_tt'), font=self.font)

		# merge duplicates
		self.merge_dupes = ctk.BooleanVar(value=True)
		self.merge_dupes_cb = ctk.CTkCheckBox(self.tabs.tab(self.tab_ttl_3),
											  variable=self.merge_dupes,
											  onvalue=True,
											  offvalue=False,
											  text=self.L('merge_dupes'),
											  font=self.font)
		self.merge_dupes_cb.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N)
		self.merge_dupes_tt = CTkToolTip(self.merge_dupes_cb, delay=self.tt_delay, message=self.L('merge_dupes_tt'), font=self.font)

		# merge h
		self.merge_h = ctk.BooleanVar(value=True)
		self.merge_h_cb = ctk.CTkCheckBox(self.tabs.tab(self.tab_ttl_3),
										  variable=self.merge_h,
										  onvalue=True,
										  offvalue=False,
										  text=self.L('short_h'),
										  font=self.font)
		self.merge_h_cb.grid(row=2, column=1, padx=5, pady=5, sticky=tk.N)
		self.merge_h_tt = CTkToolTip(self.merge_h_cb, delay=self.tt_delay, message=self.L('short_h_tt'), font=self.font)

		# run fix button
		self.run_fix_btn = ctk.CTkButton(self.tabs.tab(self.tab_ttl_3),
									     text=self.L('run_fix'),
									     command=lambda: self.run_label_fix(),
									     image=self.fix_ico,
									     compound=tk.LEFT,
									     font=self.font)
		self.run_fix_btn.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
		self.run_fix_tt = CTkToolTip(self.run_fix_btn, delay=self.tt_delay, message=self.L('run_fix_tt'), font=self.font)

		#
		#	Settings Tab GUI Code
		#

		# grid configure
		self.tabs.tab(self.tab_ttl_4).grid_columnconfigure((0, 1), weight=1)
		self.tabs.tab(self.tab_ttl_4).grid_rowconfigure((0, 1, 2, 3), weight=1)

		# choose display language
		self.set_lang_lbl = ctk.CTkLabel(self.tabs.tab(self.tab_ttl_4),
									     text=self.L('disp_lang'),
									     font=self.font)
		self.set_lang_lbl.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N)
		self.set_lang_lbl_tt = CTkToolTip(self.set_lang_lbl, delay=self.tt_delay, message=self.L('disp_lang_tt'), font=self.font)

		# model choice combobox
		self.set_lang_cmbo = ctk.CTkComboBox(self.tabs.tab(self.tab_ttl_4),
										  	 values=self.L.lang_list,
										  	 command=lambda x: self.refresh(self.clang.get()),
										  	 variable=self.clang,
										  	 font=self.font,
										  	 dropdown_font=self.font,
										  	 justify='center')
		self.set_lang_cmbo.set(self.clang.get())
		self.set_lang_cmbo.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N)

		# choose whisper model label
		self.set_wh_lbl = ctk.CTkLabel(self.tabs.tab(self.tab_ttl_4),
									   text=self.L('wh_model'),
									   font=self.font)
		self.set_wh_lbl.grid(row=0, column=1, padx=5, pady=5, sticky=tk.N)
		self.set_wh_lbl_tt = CTkToolTip(self.set_wh_lbl, delay=self.tt_delay, message=self.L('wh_model_tt'), font=self.font)

		# whisper label combobox
		self.set_wh_cmbo = ctk.CTkComboBox(self.tabs.tab(self.tab_ttl_4),
										   values=self.wh_models,
										   command=lambda x: self.update_wh_model(),
										   variable=self.inf_wh_model,
										   font=self.font,
										   dropdown_font=self.font,
										   justify='center')
		self.set_wh_cmbo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.N)

		# tensorcore checkbox
		self.matmul_ckbx = ctk.CTkCheckBox(self.tabs.tab(self.tab_ttl_4),
										   variable=self.matmul_var,
										   onvalue=True,
										   offvalue=False,
										   text=self.L('use_tensorcore'),
										   command=lambda: self.update_matmul(),
										   font=self.font)
		if self.cfg['matmul']:
			self.matmul_ckbx.select()
		elif not self.cfg['matmul']:
			self.matmul_ckbx.deselect()

		self.matmul_ckbx.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N)
		self.matmul_ckbx_tt = CTkToolTip(self.matmul_ckbx, delay=self.tt_delay, message=self.L('use_tensorcore_tt'), font=self.font)

		# force CPU rendering checkbox
		self.force_cpu_ckbx = ctk.CTkCheckBox(self.tabs.tab(self.tab_ttl_4),
											  variable=self.force_cpu,
											  onvalue=True,
											  offvalue=False,
											  text=self.L('force_cpu'),
											  command=lambda: self.update_cpu_render(),
											  font=self.font)
		self.force_cpu_ckbx.grid(row=2, column=1, padx=5, pady=5, sticky=tk.N)
		self.force_cpu_ckbx_tt = CTkToolTip(self.force_cpu_ckbx, delay=self.tt_delay, message=self.L('force_cpu_tt'), font=self.font)

		# appearance checkbox
		self.appearance_rbtn = ctk.CTkCheckBox(self.tabs.tab(self.tab_ttl_4),
											   variable=self.dark_mode,
											   onvalue=True,
											   offvalue=False,
											   text=self.L('dark_mode'),
											   command=lambda: self.change_appearance(),
											   font=self.font)
		self.appearance_rbtn.grid(row=3, column=0, padx=5, pady=5, sticky=tk.N)
		self.appearance_rbtn_tt = CTkToolTip(self.appearance_rbtn, delay=self.tt_delay, message=self.L('dark_mode_tt'), font=self.font)

	def refresh(self, choice):
		# Better option for updating the display language tbh.
		self.cfg['disp_lang'] = choice
		with open(Path(ASSETS / 'cfg.yaml'), 'w', encoding='utf-8') as f:
			yaml.dump(self.cfg, f, default_flow_style=False)
			f.close()
		self.L.load_lang(choice)

		logger.info(f'Set display language to {choice}')

		self.destroy()
		app = LabelMakr()
		app.mainloop()

	def open_transcription_editor(self):
		if self.tr_editor is None or not self.tr_editor.winfo_exists():
			self.tr_editor = transcriptEditor(L=self.L, clang=self.clang, font=self.font)
			self.tr_editor.after(10, self.tr_editor.lift)
		else:
			self.tr_editor.focus()

	def update_matmul(self):
		self.cfg['matmul'] = self.matmul_var.get()

		with open(Path(ASSETS / 'cfg.yaml'), 'w', encoding='utf-8') as f:
			yaml.dump(self.cfg, f, default_flow_style=False)
			f.close()

		logger.info(f'Updated matmul setting')

	def run_transcriber(self):
		# initialize the whisper transcriber class
		logger.info('Initializing Whisper')

		# forces small Whisper model upon using "CPU" only mode so your PC don't explode
		inference_model = self.inf_wh_model.get()
		if self.force_cpu.get():
			inference_model = 'small'

		trnsr = whisper_func.Transcriber(self.trans_lang_choice.get(), inference_model)

		x = threading.Thread(target=whisper_func.Transcriber.run_transcription, args=(trnsr, self.trans_lang_choice.get(),))
		x.start()

	def run_sofa(self,
				 ckpt: str,
				 dictionary: str,
				 g2p_bool: bool,
				 g2p_model: str,
				 g2p_cfg: str
		):
		x = threading.Thread(target=sofa_func.infer_sofa(ckpt, dictionary, self.op_cmbo.get(), self.matmul_var.get(), self.lang_cmbo.get(), g2p_bool, g2p_model, g2p_cfg,))
		x.start()

	def startfile(self, filename):
		try:
			os.startfile(filename)
		except:
			subprocess.Popen(['xdg-open', filename])

	def startfolder(self, foldername):
			"""
			Open a folder in file explorer
			If the folder doesn't exist, create it.
			"""
			folder = Path(foldername)
			#create the folder if it doesn't exist
			if(not folder.is_dir()):
				folder.mkdir()
			self.startfile(folder)

	def update_wh_model(self):
		self.inf_wh_model.set(self.set_wh_cmbo.get())
		self.cfg['whisper_model'] = self.set_wh_cmbo.get()
		with open(Path(ASSETS / 'cfg.yaml'), 'w', encoding='utf-8') as f:
			yaml.dump(self.cfg, f, default_flow_style=False)
			f.close()
		logger.info(f"Set Whisper Model to {self.set_wh_cmbo.get()}")

	def update_cpu_render(self):
		'''
		wip
		'''
		return 0

	def run_label_fix(self):
		# uses labbu to fix the files

		corpus_list = [name for name in os.listdir(str(Path(CORPUS))) if os.path.isdir(str(Path(CORPUS / name)))]

		for singer in corpus_list:
			for file in glob(str(Path(f'./corpus/{singer}/labels/*.lab')), recursive=True):
				self.labu.load(file)

				if self.dxer_cb.get():
					self.labu.dxer()
				if self.uhr_merge_cb.get():
					self.labu.fix_uh_r()
				if self.merge_h_cb.get():
					self.labu.merge_short_hh()
				if self.merge_dupes_cb.get():
					self.labu.merge_dupes()

				self.labu.save(file)
		logger.info('Finished fixing labels!')

	def change_transcription_language(self):
		if self.lang_cmbo.get() == 'EN':
			self.dxer_cb.select()
			self.dxer_cb.configure(state="normal")
			self.uhr_merge_cb.select()
			self.uhr_merge_cb.configure(state="normal")
		else:
			self.dxer_cb.deselect()
			self.dxer_cb.configure(state="disabled")
			self.uhr_merge_cb.deselect()
			self.uhr_merge_cb.configure(state="disabled")

	def change_appearance(self):
		self.dark_mode = self.appearance_rbtn.get()

		self.cfg['dark_mode'] = self.dark_mode

		with open(Path(ASSETS / 'cfg.yaml'), 'w', encoding='utf-8') as f:
			yaml.dump(self.cfg, f, default_flow_style=False)
			f.close()

		if self.dark_mode:
			ctk.set_appearance_mode('dark')
			logger.info('Toggled dark mode.')
		else:
			ctk.set_appearance_mode('light')
			logger.info('Toggled light mode.')

class transcriptEditor(ctk.CTkToplevel):
	def __init__(self, L, clang, font):
		super().__init__()
		# carry over needed things from the main class
		self.L = L
		self.clang = clang
		self.font = font
		self.tt_delay = 1

		# custom mixer wrapper cuz the pause function is weird
		self.player = mixer_wrapper()

		self.main_window()

	def main_window(self):

		# configure window
		self.title(self.L('transcription_editor'))
		self.geometry(f"{710}x{361}")
		self.resizable(height=True, width=True)
		self.minsize(width=710, height=361)

		if sys.platform == 'win32':
			if Path(ASSETS / 'tgm.icon').exists():
				self.wm_iconbitmap(ASSETS / 'tgm.ico')
			self.after(200, lambda: self.iconbitmap(Path('assets/tgm.ico')))

		self.grid_columnconfigure((0, 1), weight=1)
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure((1, 2), weight=1)

		#
		#	Image variable initilization
		#

		if Path(ASSETS / 'labelmakr.png').exists():
			self.labelmakr_logo = ctk.CTkImage(light_image=Image.open(Path(ASSETS / 'labelmakr.png')), size=(300,30))
		if Path(ASSETS / 'play.png').exists():
			self.play_ico = ctk.CTkImage(light_image=Image.open(Path(ASSETS / 'play.png')))
		if Path(ASSETS / 'pause.png').exists():
			self.pause_ico = ctk.CTkImage(light_image=Image.open(Path(ASSETS / 'pause.png')))
		if Path(ASSETS / 'stop.png').exists():
			self.stop_ico = ctk.CTkImage(light_image=Image.open(Path(ASSETS / 'stop.png')))
		if Path(ASSETS / 'save.png').exists():
			self.save_ico = ctk.CTkImage(light_image=Image.open(Path(ASSETS / 'save.png')))
		if Path(ASSETS / 'fastfw.png').exists():
			self.next_ico = ctk.CTkImage(light_image=Image.open(Path(ASSETS / 'fastfw.png')))

		#
		#	Image at the top
		#

		# logo at the top
		self.title_lbl = ctk.CTkLabel(self, image=self.labelmakr_logo, text='')
		self.title_lbl.grid(padx=(10, 0), pady=(10, 5), sticky=tk.NW, columnspan=2)

		#
		#	TEXT BOX
		#

		self.text_box = ctk.CTkTextbox(self, 
									   wrap='word',
									   activate_scrollbars=True,
									   font=self.font)
		self.text_box.grid(row=1, column=0, padx=(5, 0), pady=(5, 0), sticky=tk.NSEW)

		#
		#	FILE FRAME (Scrollable)
		#

		# file frame

		self.file_list = [
	    		os.path.relpath(path, CORPUS)
	    		for path in glob(str(Path(CORPUS / '**/*.txt')), recursive=True)
		]

		# listbox
		self.file_sel = CTkListbox(self, width=155,
								   multiple_selection=False,
								   font=self.font)
		self.file_sel.bind("<<ListboxSelect>>", lambda x: self.load_label())

		# placing all label files into the thingymajig.
		self.file_list_index = {}
		for i, file in enumerate(self.file_list):
			self.file_sel.insert(i, file)
			self.file_list_index[file] = i
		
		self.file_sel.grid(row=1, column=1, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)

		#
		#	BUTTON FRAME
		#

		
	def load_label(self):

		self.text_box.delete("0.0", tk.END)

		# load audio
		sound_name = CORPUS / Path(self.file_sel.get()).resolve()

		self.player.load(Path(sound_name).with_suffix('.wav'))

		open_path = CORPUS / Path(self.file_sel.get(self.file_sel.curselection()))

		with open(open_path, 'r', encoding='utf-8') as lbl:
			self.text_box.insert("0.0", lbl.read())
			lbl.close()

	def save_label(self):

		save_path = Path(CORPUS / self.file_sel.get(self.file_sel.curselection()))
		
		try:
			with open(save_path, 'w+', encoding='utf-8') as lbl:
				lbl.write(self.text_box.get("0.0", tk.END))
				lbl.close()
		except:
			logger.warning(f"Cannot write label for {self.file_sel.get(self.file_sel.curselection())}. ",
				  "Make sure you do not have it open in an external program.")

		logger.info(f'Wrote label as {str(save_path)}')

	def save_and_next(self):
		# of course, save the label first
		self.save_label()
		index = self.file_sel.curselection()
		try:
			self.file_sel.activate(index+1)
			self.load_label()
		except:
			logger.warning('Cannot load next label')

	def play_audio(self):
		try:
			x = threading.Thread(target=self.player.play(), args=())
			x.start()
		except:
			logger.warning(f"Unable to play audio file {Path(sound_name).with_suffix('.wav')}")

	def pause_audio(self):
		try:
			if self.player.busy:
				self.pause_audio_btn.configure(image=self.play_ico)
			else:
				self.pause_audio_btn.configure(image=self.pause_ico)
			self.player.pause()
		except:
			logger.info('No audio to stop.')

	def stop_audio(self):
		try:
			self.player.stop()
			self.pause_audio_btn.configure(image=self.pause_ico)
		except:
			logger.warning('Cannot stop music. Run for your life.')

def main(debug: bool):
	app = LabelMakr(debug)
	app.mainloop()

if __name__ == "__main__":
	import click
	
	@click.command(help='LabelMakr - An intuitive GUI tool to assist in labelling SVS datasets.')
	@click.option('--debug', '-d', is_flag=True, type=bool, default=False, help='Display debugging messages.')
	def main_wrapper(debug: bool):
		main(debug)
	main_wrapper()
