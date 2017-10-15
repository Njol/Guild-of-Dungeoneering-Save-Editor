
import os, msvcrt


# console styles
reset = '\x1b[0m'
bold = '\x1b[1m'
italic = '\x1b[3m'
underlined = '\x1b[4m'

def fg(r,g,b):
	return '\x1b[38;2;{};{};{}m'.format(r,g,b)
def bg(r,g,b):
	return '\x1b[48;2;{};{};{}m'.format(r,g,b)

selection_fg = fg(255,200,100)
disabled_fg = fg(120,120,120)

clear_code = '\x1bc'
hide_cursor_code = '\x1b[?25l'
def clear():
	print(clear_code + hide_cursor_code, end='')




class Option:
	
	lines = []
	shortcut_key = None # as bytes
	
	selectable = True
	
	arrow_key_pressed = None
	
	def __init__(self, lines, shortcut_key=None, selectable=True):
		if type(lines) is str:
			lines = [lines]
		self.lines = lines
		self.shortcut_key = shortcut_key
		self.selectable = selectable
	
	def get_lines(self):
		if not self.selectable:
			return [disabled_fg + line for line in self.lines]
		return self.lines

# an Option that only displays something and is not selectable
class Padding(Option):
	
	def __init__(self, lines):
		super().__init__(lines, selectable=False)
	
	def get_lines(self):
		# overridden to have normal colour
		return self.lines


class Options:
	
	options = [] # options[row][col]
	hidden_options = []
	
	# special options
	escape_option = None
	altF4_option = None # if not set, exits the program
	
	selected_option_index = [0,0] # row, col
	
	header=[]
	footer=[]
	left=''
	right=''
	
	def __init__(self, header=[], footer=[], left='', right=''):
		self.options = []
		self.hidden_options = []
		self.header = header
		self.footer = footer
		self.left = left
		self.right = right
		self.selected_option_index = [0,0]
	
	def add_row(self, options):
		self.options.append(options)
	def set(self, row, col, option):
		while len(self.options) <= row:
			self.options.append([])
		while len(self.options[row]) <= col:
			self.options[row].append(None)
		self.options[row][col] = option
	
	# useful shortcut key for a hidden option: ESC (b'\x1b')
	def add_hidden(self, option):
		self.hidden_options.append(option)
	
	def get_left(self, line):
		return self.left
	def get_right(self, line):
		return self.right
	
	def selected_option(self):
		if self.selected_option_index[0] >= len(self.options): return None
		options_row = self.options[self.selected_option_index[0]]
		if self.selected_option_index[1] >= len(options_row): return None
		option = options_row[self.selected_option_index[1]]
		if option is None or not option.selectable: return None
		return option
	
	def execute(self):
		# make sure an actual option is selected (if any exists)
		if self.selected_option() is None:
			for row, options_row in enumerate(self.options):
				for col, option in enumerate(options_row):
					if option.selectable:
						self.selected_option_index = [row, col]
						break
				else:
					continue
				break
		
		while True:
			# get display for selection
			lines = []
			line_num = 0
			for row, options_row in enumerate(self.options):
				for col, option in enumerate(options_row):
					selected = [row, col] == self.selected_option_index
					option_lines = option.get_lines()
					for i in range(len(option_lines)):
						if line_num + i >= len(lines):
							lines.append('')
						lines[line_num + i] += (selection_fg if selected else reset) + option_lines[i]
				line_num += max([len(o.lines) for o in options_row]) # uses .lines instead of .get_lines() deliberately (not used any more though)
			
			# actually display selection
			text = clear_code
			for line in self.header:
				text += line + '\n'
			for ln, line in enumerate(lines):
				text += reset + self.get_left(ln) + line + reset + self.get_right(ln) + '\n'
			for line in self.footer:
				text += line + '\n'
			text += reset + hide_cursor_code
			print(text, end='')
			
			# handle input
			while True:
				c = msvcrt.getch()
				#print(c)
				if c == b'\xe0':
					c = msvcrt.getch()
					selected_option = self.selected_option()
					if selected_option is None:
						continue # if there are no options, arrow keys do nothing
					dir = None
					if c == b'P': # down arrow
						dir = [1,0]
					elif c == b'H': # up arrow
						dir = [-1,0]
					elif c == b'M': # right arrow
						dir = [0,1]
					elif c == b'K': # left arrow
						dir = [0,-1]
					if not dir is None:
						while True:
							if dir[0] != 0:
								self.selected_option_index[0] = (self.selected_option_index[0] + dir[0]) % len(self.options)
							else:
								options_row = self.options[self.selected_option_index[0]]
								self.selected_option_index[1] = (self.selected_option_index[1] + dir[1]) % len(options_row)
							new_selected_option = self.selected_option()
							if new_selected_option is not None and new_selected_option.selectable:
								break
						if selected_option.arrow_key_pressed:
							selected_option.arrow_key_pressed(dir)
						break # redraw
				if c == b'\r': # enter
					return self.selected_option()
				if c == b'\x00':
					c = msvcrt.getch()
					if c == b'k': # alt + F4
						if self.altF4_option is not None:
							return self.altF4_option
						exit()
				# direct shortcuts
				for option_row in self.options:
					for option in option_row:
						if not option is None and option.selectable and c == option.shortcut_key:
							return option
				for option in self.hidden_options:
					if not option is None and c == option.shortcut_key:
						return option
			
