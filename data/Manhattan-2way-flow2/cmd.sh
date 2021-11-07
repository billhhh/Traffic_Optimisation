###
### 3- Generate the network file (Manhattan.net.xml) using the netconvert
###

# netconvert --osm-files Manhattan.osm --lefthand --output.street-names -o Manhattan.net.xml
# netconvert --osm-files Manhattan.osm -o Manhattan.net.xml --output.street-names true --output.original-names true
# netconvert --osm-files Manhattan.osm --lefthand --output.street-names true -o Manhattan.net.xml --roundabouts.guess --tls.guess
# netconvert --osm-files Manhattan.osm --output.street-names true --output.original-names true -o Manhattan.net.xml



###
### 4- Imports polygons from OSM-data and produces a Sumo-polygon file
###

# polyconvert --xml-validation --net-file Manhattan.net.xml --osm-files Manhattan.osm --type-file typemap.xml -o Manhattan.poly.xml
# polyconvert --net-file Manhattan.net.xml --osm-files Manhattan.osm --type-file typemap.xml -o Manhattan.poly.xml
polyconvert --net-file Manhattan.net.xml --osm-files Manhattan.osm --type-file typemap.xml -o Manhattan.poly.xml



###
### 5- Generate the vehicular traffic demand
###

# python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n Manhattan.net.xml -e 100 -l
python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n Manhattan.net.xml -r cars.rou.xml \
-t "type=\"car\" departSpeed=\"max\" departLane=\"best\"" -c passenger --additional-files car.add.xml -p 1.0 -e 50000 -l



###
### 6- Generate the pedestrian traffic demand
###

# python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n Manhattan.net.xml -r Manhattan.rou.xml -e 100 -l
python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n Manhattan.net.xml -r peds.rou.xml -t "type=\"ped\"" \
-c pedestrian --pedestrians --additional-files ped.add.xml --max-dist 800 -p 30.0 -e 50000 -l

sumo-gui -c Manhattan.sumo.cfg