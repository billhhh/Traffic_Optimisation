###
### 3- Generate the network file (env1.net.xml) using the netconvert
###

# netconvert --osm-files env1.osm --lefthand --output.street-names -o env1.net.xml
# netconvert --osm-files env1.osm -o env1.net.xml --output.street-names true --output.original-names true
# netconvert --osm-files env1.osm --lefthand --output.street-names true -o env1.net.xml --roundabouts.guess --tls.guess
# netconvert --osm-files env1.osm --output.street-names true --output.original-names true -o env1.net.xml



###
### 4- Imports polygons from OSM-data and produces a Sumo-polygon file
###

# polyconvert --xml-validation --net-file env1.net.xml --osm-files env1.osm --type-file typemap.xml -o env1.poly.xml
# polyconvert --net-file env1.net.xml --osm-files env1.osm --type-file typemap.xml -o env1.poly.xml
polyconvert --net-file env1.net.xml --type-file typemap.xml -o env1.poly.xml



###
### 5- Generate the vehicular traffic demand
###

# python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n env1.net.xml -e 100 -l
python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n env1.net.xml -r cars.rou.xml \
-t "type=\"car\" departSpeed=\"max\" departLane=\"best\"" -c passenger --additional-files car.add.xml -p 1.2 -e 50000 --fringe-factor 10


# saving customized weights
python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n env1.net.xml -r cars.rou.xml \
-t "type=\"car\" departSpeed=\"max\" departLane=\"best\"" -c passenger --additional-files car.add.xml \
-p 1.2 -e 50000 --fringe-factor 10 --weights-output-prefix env1

# loading customized weights
python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n env1.net.xml -r cars.rou.xml \
-t "type=\"car\" departSpeed=\"max\" departLane=\"best\"" -c passenger --additional-files car.add.xml \
-p 0.8 -e 50000 --fringe-factor 10 --weights-prefix env1



###
### 6- Generate the pedestrian traffic demand
###

# python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n env1.net.xml -r env1.rou.xml -e 100 -l
python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n env1.net.xml -r peds.rou.xml -t "type=\"ped\"" \
-c pedestrian --pedestrians --additional-files ped.add.xml --max-dist 800 -p 30.0 -e 50000 -l

sumo-gui -c env1.sumo.cfg