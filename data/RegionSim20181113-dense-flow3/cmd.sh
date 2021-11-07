###
### 3- Generate the network file (osm.net.xml) using the netconvert
###

# netconvert --osm-files osm.osm --lefthand --output.street-names -o osm.net.xml
# netconvert --osm-files osm.osm -o osm.net.xml --output.street-names true --output.original-names true
# netconvert --osm-files osm.osm --lefthand --output.street-names true -o osm.net.xml --roundabouts.guess --tls.guess
# netconvert --osm-files osm.osm --output.street-names true --output.original-names true -o osm.net.xml



###
### 4- Imports polygons from OSM-data and produces a Sumo-polygon file
###

# polyconvert --xml-validation --net-file osm.net.xml --osm-files osm.osm --type-file typemap.xml -o osm.poly.xml
# polyconvert --net-file osm.net.xml --osm-files osm.osm --type-file typemap.xml -o osm.poly.xml
polyconvert --net-file osm.net.xml --type-file typemap.xml -o osm.poly.xml



###
### 5- Generate the vehicular traffic demand
###

# python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n osm.net.xml -e 100 -l
python /media/bill/1T/program_files/sumo-tools/randomTrips.py -n osm.net.xml -r cars.rou.xml \
-t "type=\"car\" departSpeed=\"max\" departLane=\"best\"" -c passenger --additional-files car.add.xml -p 1.4 -e 50000 --fringe-factor 10

sumo-gui -c osm.sumo.cfg