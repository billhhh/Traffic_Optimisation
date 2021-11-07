import os
import sys
import platform

# Set mode
dev_flag = platform.node()
if dev_flag == "bill-XPS-8930":
    print("Setting aux in DEV_MODE!")
    # added for using of PyCharm
    os.environ['SUMO_HOME'] = '/usr/share/sumo'
    sumoBinary = "/usr/bin/sumo"
else:
    print("Setting aux in SERVER_MODE!")
    sumoBinary = "/home/h0/hwang/tl/sumo-0.32.0/bin/sumo"

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare the environment variable 'SUMO_HOME'")

parent_dir = os.path.dirname(os.path.dirname(__file__))

# sumoConfigFile = "data/RegionalTransportSim/osm.sumocfg"
# sumoConfigFile = "data/Manhattan-3phases-netedit/Manhattan.sumo.cfg"
# sumoConfigFile = "data/Manhattan-2way/Manhattan.sumo.cfg"
sumoConfigFile = "data/Manhattan-2way-2lane/Manhattan.sumo.cfg"
# sumoConfigFile = "data/env1-2way/env1.sumo.cfg"
# sumoConfigFile = "data/env1-2way-2lane/env1.sumo.cfg"
# sumoConfigFile = "data/RegionSim20181113-dense/osm.sumo.cfg"

detFile = 'data/Manhattan-2way-2lane/Manhattan.det.double.xml'
sumoConfig = os.path.join(parent_dir, sumoConfigFile)

import traci


def makeDetectors(lanes):
    with open(os.path.join(parent_dir, detFile), 'w') as f:
        f.write("<additional>\n")
        for lane in lanes:
            if traci.lane.getLength(lane) > 10.0:
                f.write("\t<inductionLoop id='{}1' lane='{}' pos='{}' freq='100' "
                        "file='{}'/>\n".format(lane + "loop", lane, -5, "resultsOfDetectors.xml"))
                f.write("\t<inductionLoop id='{}2' lane='{}' pos='{}' freq='100' "
                        "file='{}'/>\n".format(lane + "loop", lane, -10, "resultsOfDetectors.xml"))
        f.write("</additional>")


def list_of_n_phases(TLIds):
    n_phases = []
    for light in TLIds:
        phases = traci.trafficlights.getCompleteRedYellowGreenDefinition(light)
        n_phases.append(len(phases[0]._phases) // 3)
    return n_phases


def makemap(TLIds):
    maptlactions = []
    n_phases = list_of_n_phases(TLIds)
    for n_phase in n_phases:
        mapTemp = []
        if len(maptlactions) == 0:
            for i in range(n_phase):
                maptlactions.append([i * 3])
        else:
            for state in maptlactions:
                for i in range(n_phase):
                    mapTemp.append(state+[i * 3])
            maptlactions = mapTemp
    return maptlactions


if __name__ == "__main__":
    sumoCmd = [sumoBinary, "-c", sumoConfig, "--start"]
    traci.start(sumoCmd)
    # controlTLIds = ['L122', 'L213', 'L212']
    controlTLIds = traci.trafficlights.getIDList()
    # lanes = traci.lane.getIDList()
    controlLanes = []
    # for lane in lanes:
    #     for tl in controlTLIds:
    #         if lane.startswith(tl):
    #             controlLanes.append(lane)
    # print(controlLanes)

    for tl in controlTLIds:
        lanes = traci.trafficlights.getControlledLanes(tl)
        for lane in lanes:
            controlLanes.append(lane)
    controlLanes = list(set(controlLanes))  # delete dup lanes
    makeDetectors(controlLanes)
    # TLIds = traci.trafficlights.getIDList()
    # print makemap(TLIds)
    traci.close()
