import os
import unidecode

def formatSurroundingQuotes(s):
	# if value has single quotes in it ('), these must be escaped by using double quote ''
	s = s.replace("'", "''")
	#for sql, use single quotes 'value', not double quotes "value"
	if s[0] == "\"":
		s = s[1:]
	if s[-1] == "\"":
		s = s[:-1]
	if s[0] != "'":
		s = "'" + s
	if s[-1] != "'":
		s = s + "'"
	return s

with open(os.path.join("google_transit", "stops.txt"), "r", encoding='utf-8') as inFile:
	with open("stopsTableSqlCommands_noAccents.txt", "w") as outFile:

		# outFile.write("CREATE TABLE stops(stop_id char(10) NOT NULL, \
		# 	stop_code int NOT NULL,stop_name char(60) NOT NULL, \
		# 	stop_desc char(10),stop_lat float,stop_lon float, \
		# 	zone_id char(10),stop_url char(10),location_type int, \
		#	PRIMARY KEY (stop_id));\n")

		lines = inFile.readlines()
		for line in lines[1:]:		# ignore header comment
			line = line.strip()
			line = line.split(",")
			#print(line)
			stop_id = formatSurroundingQuotes(line[0])
			if line[1] == "":		#stop_code is missing, do not add this entry to database
				print(",".join(line))
			else:
				stop_code = int(line[1])
				stop_name = unidecode.unidecode(formatSurroundingQuotes(line[2]))
				stop_name = stop_name.replace('\\', '/') #make all slashes forward facing for consistency
				stop_desc = formatSurroundingQuotes(line[3]) if line[3] != "" else 'NULL'
				stop_lat = float(line[4])
				stop_lon = float(line[5])
				zone_id = formatSurroundingQuotes(line[6]) if line[6] != "" else 'NULL'
				stop_url = formatSurroundingQuotes(line[7]) if line[7] != "" else 'NULL'
				location_type = int(line[8])

				outFile.write("INSERT INTO stops VALUES ({}, {}, {}, {}, {}, {}, {}, {}, {});\n".format(
					stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon, zone_id, stop_url, location_type))