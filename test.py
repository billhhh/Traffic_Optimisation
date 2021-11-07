import os
import sys
import numpy as np
import platform

# Set mode
dev_flag = platform.node()
if dev_flag == "bill-XPS-8930":
    print("Running in DEV_MODE!")
    # added for using of PyCharm
    # os.environ['SUMO_HOME'] = '/usr/share/sumo'
    # sumoBinary = "/usr/bin/sumo-gui"
    os.environ['SUMO_HOME'] = '/media/bill/1T/program_files/sumo-0.32.0'
    sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin/sumo-gui')

    # sumoConfig = "data/env1-2way-2lane-prob/env1.sumo.cfg"
    # sumoConfig = "data/Manhattan-2way/Manhattan.sumo.cfg"
    sumoConfig = "data/Manhattan-2way-2lane/Manhattan.sumo.cfg"

    load_path = "save/model/model_best.h5"
else:
    print("Running in SERVER_MODE!")
    sumoBinary = "/home/h0/hwang/tl/sumo-0.32.0/bin/sumo"

    sumoConfig = sys.argv[1]
    load_path = sys.argv[2]


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare the environment variable 'SUMO_HOME'")

import traci
from model.agent import Agent
from scripts.utils import load_multi_agents,\
    per_light_waiting, get_junction_list

import model.adj as adj_matrix


def main():

    # Control code here
    # sumoCmd = [sumoBinary, "-c", sumoConfig, "--start"]
    sumoCmd = [sumoBinary, "-c", sumoConfig, "--start",
               "--default.action-step-length", "0.8", "--xml-validation", "never"]
    # sumoCmd = [sumoBinary, "-c", sumoConfig, "--start", "--waiting-time-memory", "20"]
    traci.start(sumoCmd)

    if sumoConfig.startswith("data/RegionalTransportSim"):
        env = adj_matrix.suzhou_edges
    elif sumoConfig.startswith("data/Manhattan-2way"):
        env = adj_matrix.manhattan_edges
    elif sumoConfig.startswith("data/env1-2way-2lane-prob"):
        env = adj_matrix.env1_edges
    elif sumoConfig.startswith("data/RegionSim20181113"):
        env = adj_matrix.RegionSim20181113_edges
    else:
        env = None

    agent = Agent(traci,
                  use_detector=True,
                  exploration=0.0,
                  Y_cnt=0,
                  change_phase_R=0,
                  dropout=0.0,
                  tls_state=True,
                  env=env,
                  )

    load_multi_agents(load_path, [agent])
    tls = traci.trafficlights.getIDList()
    junction_list = get_junction_list(tls)

    if sumoConfig.startswith("data/RegionalTransportSim"):
        STEP_LEN = 1
    else:
        STEP_LEN = 0.1
    SIM_STEPS = 1000

    # init done
    sec_steps = int(1 / STEP_LEN)  # how many steps a sec
    total_sim_steps = sec_steps * SIM_STEPS

    agent.reset()
    simulation_steps = 0
    atom_time = sec_steps * 2
    pl_wt = np.zeros(len(tls), dtype=np.float32)

    while simulation_steps < total_sim_steps:
        agent.agentAct()  # agent act once

        # each atom_time simulationStep() once
        for j in range(atom_time):
            traci.simulationStep()
            if j % sec_steps == 0:  # Cul cost each sec
                agent.agentCulCost()
                pl_wt += per_light_waiting(junction_list)

        agent.agentCulReward(is_sim=True)  # agent cul reward
        simulation_steps += atom_time
    # The END of simulationSteps loop

    # print log on screen
    agent.printScreen()
    traci.close()

    print("per line waiting time:")
    print(pl_wt)
    print("Total Cost time:")
    print(sum(pl_wt))


if __name__ == '__main__':
    main()
