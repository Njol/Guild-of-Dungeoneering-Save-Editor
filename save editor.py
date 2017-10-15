
import os, math, sys

from AMF3 import AMF3

from console_utils import *




# constants and utility methods

# make console big enough (also disables scrolling)
# width: for unlocks
# height: for battle scars
console_width = 135
console_height = 32
os.system("mode con: cols={} lines={}".format(console_width, console_height))


# other stuff

def make_backup(file):
	if not os.path.isfile(file+'.original'):
		os.rename(file, file+'.original') 
		return
	if os.path.isfile(file+'.bak5'):
		os.remove(file+'.bak5')
	for i in range(5,0,-1):
		if os.path.isfile(file+'.bak'+str(i - 1)):
			os.rename(file+'.bak'+str(i - 1), file+'.bak'+str(i))
	os.rename(file, file+'.bak0')








# main program
def main():
	
	save_dir = None
	with open(os.path.join(os.path.dirname(sys.argv[0]), 'save_dir.txt'), 'r') as f:
		save_dir = f.readlines()[0:0]
	old_save_dir = save_dir
	
	if not save_dir:
		save_dir = os.path.join(os.path.expanduser("~"),'AppData','Roaming','dungeoneering','Local Store')
	
	while save_dir == None or not os.path.isdir(save_dir):
		import tkinter as tk
		from tkinter import filedialog
		root = tk.Tk()
		root.withdraw()
		save_dir = filedialog.askdirectory(title='Select Guild of Dungeoneering save directory', initialdir=os.path.expanduser("~"))
		if not save_dir:
			return
	
	if save_dir != old_save_dir:
		with open(os.path.join(os.path.dirname(sys.argv[0]), 'save_dir.txt'), 'w') as f:
			f.write(save_dir)
	
	# save slot loop
	while True:
		
		# load saves
		slots = [None, None, None]
		slots_amf = [None, None, None]
		for i in range(3):
			slot = i + 1
			save_file = os.path.join(save_dir, 'slot'+str(slot)+'.sav')
			if os.path.isfile(save_file):
				try:
					slot_amf = AMF3()
					slot_data = slot_amf.read_file(save_file)
					if AMF3().serialize(slot_data) != slot_amf.data:
						raise ValueError("Serialized data different from source data")
					slots[i] = slot_data
					slots_amf[i] = slot_amf
				except:
					print()
					print(' Could not load save slot '+str(slot)+' properly.')
					print(' Error:', sys.exc_info()[0])
					print()
					input()
		
		options = Options(header=[''],footer=['',' (use left/right and enter to choose a slot, or type its number directly)'])
		for i in range(3):
			slot = slots[i]
			if not slot is None:
				options.set(0, i, Option([
					' ┌────────────────┐ ',
					' │     slot '+str(i+1)+'     │ ',
					' │ {: ^14s} │ '.format('gold: '+str(slot['glory'])),
					' │ {: ^14s} │ '.format('heroes: '+str(len(slot['heroes']))),
					' └────────────────┘ '
				], shortcut_key=[b'1', b'2', b'3'][i]))
			else:
				options.set(0, i, Padding([
					' ┌────────────────┐ ',
					' │     slot '+str(i+1)+'     │ ',
					' │    [empty]     │ ',
					' │                │ ',
					' └────────────────┘ '
				]))
		
		selected_option = options.execute()
		if selected_option is None:
			return
		current_slot = int(selected_option.shortcut_key) - 1
		data = slots[current_slot]
		old_save = slots_amf[current_slot]
		
		
		
		# main loop
		while True:
			
			new_save = AMF3()
			new_save.serialize(data)
			has_changes = new_save.data != old_save.data
			
			options = Options(header=['',' Slot '+str(current_slot + 1),''], footer=['', ' (type letter in brackets or use up/down and enter to select an option)'], left=' ')
			options.options = [
				[Option(['[G] Gold: '+str(data['glory'])], b'g')],
				[Option(['[R] Rooms and Blessings'], b'r')],
				[Option(['[H] Heroes'], b'h')],
				[Padding([''])],
				[Option(['[S] '+(bold+'* ' if has_changes else '')+'save'+(' *' if has_changes else '')], b's')],
				[Option(['[Q] quit'], b'q')],
				[Option(['[L] load another save'], b'l')],
			]
			options.add_hidden(Option([], b'd'))
			options.add_hidden(Option([], b'\x1b')) # ESC
			options.altF4_option = Option([], b'q')
			
			selected_option = options.execute()
			option = selected_option.shortcut_key
			print()
			if option == b'g':
				try:
					data['glory'] += int(input(' Amount of gold to add: '))
				except ValueError:
					pass
			elif option == b'h':
				handle_heroes(data)
			elif option == b'r':
				handle_unlocks(data)
				fix_save(data)
			elif option == b's':
				new_save = AMF3()
				new_save.serialize(data)
				if new_save.data != old_save.data:
					make_backup(save_file)
					new_save.write_file(save_file)
					old_save = new_save
			elif option == b'q' or option == b'l' or option == b'\x1b':
				new_save = AMF3()
				new_save.serialize(data)
				if new_save.data != old_save.data:
					while True:
						r = input(' Do you want to save your changes? (y/n) ').upper()
						if r == 'Y':
							make_backup(save_file)
							new_save.write_file(save_file)
							old_save = new_save
							break
						if r == 'N':
							break
				if option == b'q':
					return
				else: # load or escape
					break
			elif option == b'd': # debug
				import pprint
				clear()
				os.system("mode con: lines=1000")
				pprint.PrettyPrinter().pprint(data)
				input()

# unlock constants
unlocks_ids = ['Rogue', 'Trickster', 'Melee', 'Warrior', 'Arts', 'Heal-Aid', 'Scholar', 'Crone', 'Smith', 'Leather', 'Wood', 'Curio']
unlocks_level_costs = [50, 500, 2000]
unlocks_level_costs_combined = [0, 50, 550, 2550]
unlocks_rooms = [
	['Hidden Den', 'Archery Range', 'Tavern'], [None, None, None], ['Training Yard', 'Campsite', 'Chapel'], [None, None, None], 
	['Theatre', 'Standing Stones', 'Games Room'], [None, None, None], ['Library', 'Laboratory', 'Mage Tower'], [None, None, None], 
	['Blacksmith', None, None], ['Leatherworker', None, None], ['Woodworker', None, None], ['Curio Shoppe', None, 'Workshop']]
unlockable_rooms = ['Hidden Den', 'Archery Range', 'Tavern', 'Training Yard', 'Campsite', 'Chapel', 'Theatre', 'Standing Stones', 'Games Room', 'Library', 'Laboratory', 'Mage Tower', 'Blacksmith', 'Leatherworker', 'Woodworker', 'Curio Shoppe', 'Workshop']
unlocks_heroes = [
	['Cat Burglar', 'Ranger', 'Troubador'], [None, None, None], ['Bruiser', 'Barbarian', 'Most Holy Grail Knight'], [None, None, None], 
	['Mime', 'Shapeshifter', 'Cartomancer'], [None, None, None], ['Apprentice', 'Alchemist', 'Mathemagician'], [None, None, None], 
	[None, None, None], [None, None, None], [None, None, None], [None, None, 'Artificer']]
unlockable_heroes = ['Cat Burglar', 'Ranger', 'Troubador', 'Bruiser', 'Barbarian', 'Most Holy Grail Knight', 'Mime', 'Shapeshifter', 'Cartomancer', 'Apprentice', 'Alchemist', 'Mathemagician', 'Artificer']
unlocks_names = [
	['Burglar', 'Ranger', 'Troubadour'], ['Trickster 1', 'Trickster 2', 'Trickster 3'], ['Bruiser', 'Barbarian', 'Grail Knight'], ['Warrior 1', 'Warrior 2', 'Warrior 3'],
	['Mime', 'Shapeshifter', 'Cartomancer'], ['Heal-Aid 1', 'Heal-Aid 2', 'Heal-Aid 3'], ['Apprentice', 'Alchemist', 'Mathemagician'], ['Crone 1', 'Crone 2', 'Crone 3'],
	['Blacksmith 1', 'Blacksmith 2', 'Blacksmith 3'], ['Leatherworker 1', 'Leatherworker 2', 'Leatherworker 3'], ['Woodworker 1', 'Woodworker 2', 'Woodworker 3'], ['Curio Shoppe', 'Weird and Wonderful', 'Artificer']]
unlocks_short_name_length = 8
unlocks_short_names = [ # exactly 8 characters each
	['Burglar ', ' Ranger ', 'Troubad.'], ['Trick. 1', 'Trick. 2', 'Trick. 3'], ['Bruiser ', ' Barbar.', ' Knight '], ['Warrior1', 'Warrior2', 'Warrior3'],
	['  Mime  ', 'SShifter', ' Cartom.'], [' Heal 1 ', ' Heal 2 ', ' Heal 3 '], ['Apprent.', ' Alchem.', 'Mathmage'], [' Crone 1', ' Crone 2', ' Crone 3'],
	['Smithy 1', 'Smithy 2', 'Smithy 3'], ['Leather1', 'Leather2', 'Leather3'], [' Wood 1 ', ' Wood 2 ', ' Wood 3 '], [' Curio  ', ' Weird  ', 'Artific.']]
# special note: curio 3 does not require curio 2

def handle_unlocks(data):
	
	def is_unlocked(kind, level):
		return unlocks_ids[kind] in data['unlockData'] and data['unlockData'][unlocks_ids[kind]][level]
	def set_unlocked(kind, level, unlocked):
		if not unlocks_ids[kind] in data['unlockData']:
			data['unlockData'][unlocks_ids[kind]] = [0,0,0]
		data['unlockData'][unlocks_ids[kind]][level] = (1 if unlocked else 0)
	
	selected_kind = 0
	selected_level = 0
	selected_option_index = [0,0]
	
	while True:
		# note: console size is set at the start of this script
		
		options = Options(header=['',
			'                ┌──────────┐                '*3,
			'                │  Might   │                                │  Magic   │                                │   Loot   │',
			' ┌──────────────┴──────────┴──────────────┐ '*3],
			left=' │', right='│',
			footer=[
			' └────────────────────────────────────────┘ '*3,
			'',
			' Gold: '+str(data['glory']),
			'',
			' Select a room with arrows key and press enter to buy or sell it',
			' Press ESC to return to main screen.'
			])
		options.selected_option_index = selected_option_index
		for level in range(3):
			options_row = []
			for kind in range(12):
				unlocked = is_unlocked(kind, level)
				option = Option([
					'╔════════╗' if unlocked else '┌╴╶╴╶╴╶╴╶┐',
					('║' if unlocked else '│')+unlocks_short_names[kind][level]+('║' if unlocked else '│'),
					'╚════════╝' if unlocked else '└╴╶╴╶╴╶╴╶┘'])
				option.level = level
				option.kind = kind
				options_row.append(option)
				if kind == 3 or kind == 7:
					options_row.append(Padding(['│  │', '│  │', '│  │']))
			options.add_row(options_row)
		options.add_hidden(Option([], b'\x1b'))
		
		selected = options.execute()
		
		if selected.shortcut_key == b'\x1b': # ESC
			return
		
		was_unlocked = is_unlocked(selected.kind, selected.level)
		set_unlocked(selected.kind, selected.level, not was_unlocked)
		
		data['glory'] += (1 if was_unlocked else -1) * unlocks_level_costs[selected.level]
		
		selected_option_index = options.selected_option_index



hero_gender = ['female','male']
hero_skins = [0,150,151]
hero_skins_names = ['white','gray','black']
hero_hair = [-1,129,126,141,132,138,135,144,147]
hero_hair_names = ['bald','sides','very short','short','lock','long','mohawk','tied up','two knots']
#hero_facial = [0,120]
#hero_tattoos = [-1,123,124,125]
#hero_tattoos_names = [-1,123,124,125]
#hero_scars = [-1,121,122]
#hero_scars_names = [-1,121,122]
hero_hair_colors = [0,1,2]
hero_hair_colors_names = ['white','gray','black']

hero_visuals = [# id, name, shortcut displayed, shortcut binary, list, name list
		['gender', 'gender', 'G', b'g', hero_gender, hero_gender],
		['skin', 'skin colour', 'S', b's', hero_skins, hero_skins_names],
		['hair', 'hair style', 'H', b'h', hero_hair, hero_hair_names],
		['hairColour', 'hair colour', 'C', b'c', hero_hair_colors, hero_hair_colors_names]]

hero_battle_scars = [None,"HardHeaded$1","HardHeaded$2","PunchDrunk$1","PunchDrunk$2","Hulking$1","Hulking$2","FleshWound$1","FleshWound$2","Scrounger$1","Scrounger$2","Gullible$1","Gullible$2","Hubris$1","Hubris$2","FountainAddict$1","FountainAddict$2","Tricksy$1","Tricksy$2","Pyromaniac$1","Pyromaniac$2","Paranoid$1","Paranoid$2","Veteran","Scarred","Zealot","Mystical","Naturist","Agile"]
hero_battle_scars_names = {None:"empty","HardHeaded$1":"Hard Headed 1","HardHeaded$2":"Hard Headed 2","PunchDrunk$1":"Punch Drunk 1","PunchDrunk$2":"Punch Drunk 2","Hulking$1":"Hulking 1","Hulking$2":"Hulking 2","FleshWound$1":"Flesh Wound 1","FleshWound$2":"Flesh Wound 2","Scrounger$1":"Scrounger 1","Scrounger$2":"Scrounger 2","Gullible$1":"Gullible 1","Gullible$2":"Gullible 2","Hubris$1":"Hubris 1","Hubris$2":"Hubris 2","FountainAddict$1":"Fountain Addict 1","FountainAddict$2":"Fountain Addict 2","Tricksy$1":"Tricksy 1","Tricksy$2":"Tricksy 2","Pyromaniac$1":"Pyromaniac 1","Pyromaniac$2":"Pyromaniac 2","Paranoid$1":"Paranoid 1","Paranoid$2":"Paranoid 2","Veteran":"Veteran","Scarred":"Scarred","Zealot":"Zealot","Mystical":"Mystical","Naturist":"Naturist","Agile":"Agile"}
hero_battle_scars_descs = {None:"","HardHeaded$1":"+1 ♥\n-1 starting hand size in battle","HardHeaded$2":"+2 ♥\n-1 starting hand size in battle","PunchDrunk$1":"Start with Stupidity +I","PunchDrunk$2":"Start with Stupidity +I\nStupidity gains Block 1 Any","Hulking$1":"+1 ♥","Hulking$2":"+1 ♥\nStart with Stupidity I","FleshWound$1":"-1 ♥","FleshWound$2":"-1 ♥\nTenacious (can\'t be killed unless on 1 ♥ at start of round)","Scrounger$1":"One loot choice is of a higher level than normal","Scrounger$2":"One loot choice is of a higher level than normal\nCan not take coins instead of loot","Gullible$1":"One loot choice is of a lower level than normal","Gullible$2":"One loot choice is of a lower level than normal\n+1 to all gold gained from Treasure","Hubris$1":"Convinced they cannot lose. Seeks out higher-level monsters","Hubris$2":"Convinced they cannot lose. Seeks out higher-level monsters\n+1 ♥ vs higher-level monsters","FountainAddict$1":"Attracted to Fountains\nFirst tile card each turn has a Fountain","FountainAddict$2":"Attracted to Fountains\nFirst tile card each turn has a Fountain\nIgnore negative fountain effects","Tricksy$1":"Start with Level 1 loot choice","Tricksy$2":"Start with Level 1 loot choice\nNo gold earned from Treasure","Pyromaniac$1":"Start with Fire I","Pyromaniac$2":"Start with Fire I\nBurn (both fighters take 1 damage each turn)","Paranoid$1":"Start with Armour I","Paranoid$2":"Start with Armour I\nStart with Stupidity I","Veteran":"Start with Blade I","Scarred":"Start with Crush I","Zealot":"Start with Holy I","Mystical":"Start with Arcane I","Naturist":"Start with Growth I","Agile":"Start with Swift I"}

def handle_heroes(data):
	
	selected_option_index = [0,0]
	while True:
		
		options = Options(header=['',' Heroes: '+str(len(data['heroes'])), ''], left=' ', footer=[])
		
		options.add_row([Option(['• Resurrect a dead hero (dead heroes: '+str(len(data['deadHeroes']))+')'], b'r', selectable=len(data['deadHeroes']) > 0)])
		options.add_row([Padding([''])])
		options.add_row([Padding(['Modify hero:'])])
		for hero in data['heroes']:
			option = Option([' • '+hero['name']+' ('+hero['heroClass']+')'])
			option.hero = hero
			options.add_row([option])
		options.add_hidden(Option([], b'\x1b'))
		
		options.selected_option_index = selected_option_index
		selected_option = options.execute()
		selected_option_index = options.selected_option_index
		
		if selected_option.shortcut_key == b'\x1b':
			return
		if selected_option.shortcut_key == b'r':
			handle_hero_resurrection(data)
			continue
		
		hero = selected_option.hero
		options = Options(header=['',' '+hero['name']+' ('+hero['heroClass']+')', ''], left=' ')
		options.add_hidden(Option([], b'\x1b'))
		while True:
			all_options = []
			for visual in hero_visuals:
				attribute = visual[0]
				name = visual[1]
				list = visual[4]
				name_list = visual[5]
				option = Option([''], visual[3])
				option.get_lines = lambda name=name,visual=visual,name_list=name_list,list=list,attribute=attribute: ['['+visual[2]+'] '+name+': ◂ '+name_list[list.index(hero[attribute])]+' ▸']
				def f(dir,name=name,name_list=name_list,list=list,attribute=attribute):
					if dir[1] != 0:
						hero[attribute] = list[(list.index(hero[attribute]) + dir[1]) % len(list)]
				option.arrow_key_pressed = f
				all_options.append([option])
			
			battle_scars = []
			for p in hero['personality']:
				battle_scars.append(p['trait'])
			battle_scar_1_option = Option(['[1] Battle scar 1: '+(hero_battle_scars_names[battle_scars[0]] if len(battle_scars) > 0 else 'empty')], b'1')
			battle_scar_2_option = Option(['[2] Battle scar 2: '+(hero_battle_scars_names[battle_scars[1]] if len(battle_scars) > 1 else 'empty')], b'2', selectable=len(battle_scars)>0)
			
			options.options = all_options + [[Padding([''])], [Padding(['battle scars:'])], [battle_scar_1_option], [battle_scar_2_option]]
			
			selected_option = options.execute()
			if selected_option.shortcut_key == b'\x1b':
				break
			if selected_option.shortcut_key in [b'1', b'2']:
				handle_battle_scar(hero, [b'1', b'2'].index(selected_option.shortcut_key))
				continue
			else: # skin/hair
				options.selected_option_index = [options.options.index([selected_option]), 0]


def battle_scar_description(battle_scar, line_num):
	if line_num == 0: return ''
	lines = hero_battle_scars_descs[battle_scar].split('\n')
	name = hero_battle_scars_names[battle_scar]
	cols = max(max([len(line) for line in lines]), len(name) + 2)
	if line_num == 1:
		x = cols - len(name)
		return ' ┌'+'─'*math.floor(x/2)+' '+name+' '+'─'*math.ceil(x/2)+'┐'
	i = line_num - 2
	if i < len(lines): return (' │ {: <'+str(cols)+'s} │').format(lines[i])
	if i == len(lines): return ' └─'+'─'*cols+'─┘'
	return ''
def handle_battle_scar(hero, scar_index):
	options = Options(header=[''], footer=[], left=' ')
	options.add_hidden(Option([], b'\x1b'))
	longest_name_length = max([len(hero_battle_scars_names[n]) for n in hero_battle_scars])
	for battle_scar in hero_battle_scars:
		option = Option(('• {: <'+str(longest_name_length)+'s}').format(hero_battle_scars_names[battle_scar]), selectable=(len(hero['personality']) <= 1-scar_index or battle_scar is None or hero['personality'][1-scar_index]['trait'][:-2] != battle_scar[:-2]))
		option.battle_scar = battle_scar
		options.add_row([option])
		if scar_index < len(hero['personality']) and hero['personality'][scar_index]['trait'] == battle_scar:
			options.selected_option_index = [len(options.options)-1, 0]
	options.get_right = lambda line_num: battle_scar_description(options.selected_option().battle_scar, line_num)
	
	selected_option = options.execute()
	if selected_option.shortcut_key == b'\x1b':
		return
	if selected_option.battle_scar == None:
		if scar_index < len(hero['personality']):
			del hero['personality'][scar_index]
		return
	if scar_index == 1 and len(hero['personality']) == 0:
		scar_index = 0
	if scar_index >= len(hero['personality']):
		hero['personality'].append(None)
	hero['personality'][scar_index] = {'trait': selected_option.battle_scar, 'ver': 1}
	

def handle_hero_resurrection(data):
	valid_dead_hero_classes = []
	valid_dead_heroes = []
	for hero in data['deadHeroes']:
		for tile in data['tiles']:
			if 'tile_class' in tile and hero['heroClass'] == tile['tile_class']:
				valid_dead_heroes.append(hero)
				break
	num_invalid_dead_heroes = len(data['deadHeroes']) - len(valid_dead_heroes)
	options = Options(header=[''], footer=['', (' (not showing '+str(num_invalid_dead_heroes)+' dead hero'+('es' if num_invalid_dead_heroes != 1 else '')+' whose room was sold)' if num_invalid_dead_heroes > 0 else ''), ' Note: resurrecting a hero will kill the current living hero of that class', ''], left=' ')
	options.add_hidden(Option([], b'\x1b'))
	all_hero_options = []
	start_index = 0
	visible_rows = console_height - 8
	invisible_rows = len(valid_dead_heroes) - visible_rows
	up_arrow = Padding('       ▲')
	down_arrow = Padding('       ▼')
	def update_visible_rows(dir, index):
		nonlocal start_index
		if dir[0] == -1 and index == start_index:
			start_index -= 1
			options.selected_option_index[0] = 1
			if start_index < 0:
				start_index = invisible_rows
				options.selected_option_index[0] = visible_rows
		elif dir[0] == 1 and index == start_index + visible_rows - 1:
			start_index += 1
			options.selected_option_index[0] = visible_rows
			if start_index > invisible_rows:
				start_index = 0
				options.selected_option_index[0] = 1
		options.options = ([[(up_arrow if start_index > 0 else Padding(['']))]]
				+ all_hero_options[start_index : start_index + visible_rows]
				+ [[(down_arrow if start_index < invisible_rows else Padding(['']))]])
	for i, hero in enumerate(valid_dead_heroes):
		option = Option('• '+hero['name']+' ('+hero['heroClass']+')')
		option.hero = hero
		if invisible_rows > 0:
			option.arrow_key_pressed = lambda dir, i=i: update_visible_rows(dir, i)
		all_hero_options.append([option])
	
	if invisible_rows <= 0:
		options.options = all_hero_options
	else:
		update_visible_rows([0,0],0)
	
	selected_option = options.execute()
	if selected_option.shortcut_key == b'\x1b':
		return
	
	hero = selected_option.hero
	if hero['heroClass'] in data['cooldown']:
		del data['cooldown'][hero['heroClass']]
	for living_hero in data['heroes']:
		if living_hero['heroClass'] == hero['heroClass']:
			for attrib in living_hero: # dead heroes have more attributes
				hero[attrib], living_hero[attrib] = living_hero[attrib], hero[attrib]
			break



# removes rooms that are not unlocked any more and such
def fix_save(data):
	
	def is_unlocked(kind, level):
		return unlocks_ids[kind] in data['unlockData'] and data['unlockData'][unlocks_ids[kind]][level]
	unlocked_rooms = []
	unlocked_heroes = []
	for kind in range(12):
		for level in range(3):
			if is_unlocked(kind, level):
				if unlocks_rooms[kind][level] in unlockable_rooms:
					unlocked_rooms.append(unlocks_rooms[kind][level])
				if unlocks_heroes[kind][level] in unlockable_heroes:
					unlocked_heroes.append(unlocks_heroes[kind][level])
	
	# remove sold rooms from guild tiles
	tiles = data['tiles']
	for i in range(len(tiles) - 1, -1, -1):
		if tiles[i]['tile'] in unlockable_rooms and not tiles[i]['tile'] in unlocked_rooms:
			del tiles[i]
	
	# kill sold heroes
	heroes = data['heroes']
	for i in range(len(heroes) - 1, -1, -1):
		hero = heroes[i]
		if hero['heroClass'] in unlockable_heroes and not hero['heroClass'] in unlocked_heroes:
			data['deadHeroes'].append(hero)
			hero['killedIn'] = 'Rats? How original!'
			hero['killedBy'] = None
			del heroes[i]
	# remove sold heroes from cooldown
	for hero in data['cooldown']:
		if hero in unlockable_heroes and not hero in unlocked_heroes:
			del data['cooldown'][hero]






# start the program
main()


