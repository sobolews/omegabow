import yaml
import re
import sys
from os import walk
from os.path import join

EMPTY_STRING = ""
DIRECTION_STRINGS = ["dir", "blss", "down", "run"]
KOROK_TYPES = {}
korokfile = open('korok-types.csv', 'r')
for line in korokfile.readlines():
	kid, ktype = line.strip().split(",")
	KOROK_TYPES[kid] = ktype
korokfile.close()

# checks if string is a direction
def isdirection(step):
	for s in DIRECTION_STRINGS:
		if s in step.lower():
			return True
	return False

def split_camel_case(string):
	return " ".join(re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', string))

def split_colon(string):
	return re.split("::",string)

def split_brackets(string):
	trimmed_string = string.replace(">","")
	return re.split("<",trimmed_string)

# todo
def koroktype(kid):
	return KOROK_TYPES[kid]

# functions for cleaning goal strings
TYPE_STRINGS = [".", "(", ")", "dir", "item", "loc", "npc", "rune", "boss", "enemy", "!!", "code"]
def clean_types(string):
	result_string = string.replace(","," +")
	for s in TYPE_STRINGS:
		result_string = result_string.replace(s, "")
	return result_string

def clean_preset(string):
	result_string = string # string.replace("_","")
	components = split_colon(string)
	if len(components) == 1:
		components = split_brackets(string)

	if components[0] == "_Boss":
		boss_type = components[1]
		if len(components) < 3:
			result_string = boss_type
		else:
			boss_subtype = components[2]
			if boss_subtype == "Stal":
				result_string = "Stalnox"
			else:
				result_string = boss_subtype + " " + boss_type

	elif components[0] == "_Chest":
		suffix = split_brackets(components[1])
		if len(suffix) > 1:
			result_string = suffix[1] + " Chest"
		else:
			result_string = components[1] + " Chest"

	elif components[0] == "_Cook":
		result_string = components[1]

	elif components[0] == "_Discover":
		result_string = components[0].replace("_","").upper() + " " + components[1]

	elif components[0] == "_Equipment":
		result_string = split_brackets(components[1])[1]

	elif components[0] == "_Korok":
		result_string = components[1] + " " + koroktype(components[1])

	elif components[0] == "_Material":
		result_string = components[1]

	elif components[0] in ["_Memory", "_Shrine"]:
		result_string = split_camel_case(components[1])

	elif components[0] == "_Npc":
		npc_name = components[1]
		suffix = split_brackets(npc_name)
		if len(suffix) > 1:
			npc_name = suffix[1]
		if npc_name == "Zora Monument":
			result_string = npc_name
		else:
			result_string = components[0].replace("_","").upper() + " " + npc_name

	elif components[0] == "_Shop":
		result_string = components[1]

	elif components[0] == "_Snap":
		suffix = components[1]
		snap_target = split_brackets(suffix)[1]
		result_string = "SNAP " + snap_target

	elif components[0] == "_Tod":
		result_string = "Make " + components[1]

	elif components[0] == "_Tower":
		result_string = split_camel_case(components[1]) + " Tower"

	elif components[0] == "_Warp":
		if len(components) == 2:
			result_string = "Warp to " + split_camel_case(components[1])
		else:
			warp_type = components[1]
			warp_target = components[2]
			if warp_type == "Shrine":
				result_string = "Warp to " + split_camel_case(warp_target)
			elif warp_type in ["TechLab", "Tower"]:
				result_string = "Warp to " + warp_target + " " + warp_type

	return result_string

def get_gale_and_fury_count(step):
	gale_count = 0
	fury_count = 0
	if 'gale' in step:
		gale_count = step['gale']
	if 'fury' in step:
		fury_count = step['fury']
	return gale_count, fury_count

# translation
def celer2csv(celer_data):
	csv = ""
	# for key in celer_data.keys():
		# print("\n" + key.upper())
		# route = celer_data[key]

	current_dir = EMPTY_STRING
	current_goal = None
	current_comment = EMPTY_STRING
	line_number = 1
	current_gale = 0
	current_fury = 0

	for line in celer_data:
		this_step = None
		if isinstance(line, str):
			this_step = line
		else: # if not string, must be dictionary
			this_step = list(line.keys())[0]
			g, f = get_gale_and_fury_count(line[this_step])
			current_gale += g
			current_fury += f

			# print(this_step + " " + str(current_gale))
			# print(line)
			if 'comment' in line[this_step]:
				current_comment = clean_types(line[this_step]['comment'])
			# if 'gale' in line[this_step]:
			# 	current_comment += " " + str(line[this_step]['gale']) + " gales"
			# if 'fury' in line[this_step]:
			# 	current_comment += " " + str(line[this_step]['fury']) + " furies"

		# check if this_step is a movement direction
		if isdirection(this_step):
			current_dir = clean_types(this_step)
			current_goal = None
		else:
			current_goal = clean_types(clean_preset(this_step))

		# if goal is set, write line
		if current_goal is not None:
			gale_string = str(current_gale) + " GALE"
			fury_string = str(current_fury) + " FURY"

			current_dir = current_dir.replace("gale", gale_string)
			current_goal = current_goal.replace("gale", gale_string)
			current_comment = current_comment.replace("gale", gale_string)
			current_dir = current_dir.replace("fury", fury_string)
			current_goal = current_goal.replace("fury", fury_string)
			current_comment = current_comment.replace("fury", fury_string)

			csv += str(current_dir) + "," + current_goal + "," + current_comment + "\n"
			# print(str(current_dir) + "," + current_goal + "," + current_comment)
			# reset
			current_dir = EMPTY_STRING
			current_goal = None
			current_comment = EMPTY_STRING
			current_gale = 0
			current_fury = 0
	return csv

if __name__ == "__main__":
	branch_dir = sys.argv[1]

	# load main file
	with open("main.celer", "r") as stream:
		main = yaml.safe_load(stream)

	# load branches
	files = []
	for (dirpath, dirnames, filenames) in walk(branch_dir):
	    files.extend(filenames)
	    break
	branches = {}
	for f in files:
		with open(join(branch_dir,f), 'r') as stream:
			branches.update(yaml.safe_load(stream))

	# print(celer2csv(branches["Vah Ruta"]))
	# for kid in KOROK_TYPES.keys():
	# 	print(kid + " -> " + KOROK_TYPES[kid])

	# write csv
	for line in main['_route']:
		if isinstance(line, str):
			print(line)
		else:
			subheading = list(line.keys())[0]
			print(subheading.upper())
			for item in line[subheading]:
				if "__use__" in item:
					branch_name = item.replace("__use__ ","")
					print(celer2csv(branches[branch_name]))