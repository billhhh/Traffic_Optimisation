"""
Controls all tls in parallel by predicting all actions
"""

import os
import sys
import platform

# Set mode
dev_flag = platform.node()
if dev_flag == "bill-XPS-8930":
    print("Running in DEV_MODE!")
    # added for using of PyCharm
    os.environ['SUMO_HOME'] = '/media/bill/1T/program_files/sumo-0.32.0'
    sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin/sumo')

    # sumoConfig = "data/env1-2way-2lane-prob/env1.sumo.cfg"
    # sumoConfig = "data/Manhattan-2way/Manhattan.sumo.cfg"
    sumoConfig = "data/Manhattan-2way-2lane/Manhattan.sumo.cfg"

    save_path = "save/model/model.h5"
    save_path_best = "save/model/model_best.h5"
    out_file_path = "save/model/output_model.txt"
else:
    print("Running in SERVER_MODE!")
    sumoBinary = "/home/h0/hwang/tl/sumo-0.32.0/bin/sumo"

    sumoConfig = sys.argv[1]
    save_folder = sys.argv[2]
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    save_path = save_folder + "/model.h5"
    save_path_best = save_folder + "/model_best.h5"
    out_file_path = save_folder + "/output.txt"


if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare the environment variable 'SUMO_HOME'")

resume_path = None
# resume_path = "save/model/model_best.h5"

import traci
from model.agent import Agent
from scripts.utils import save_multi_agents, load_multi_agents

import model.adj as adj_matrix


def main():

    # Control code here
    # sumoCmd = [sumoBinary, "-c", sumoConfig, "--start"]
    sumoCmd = [sumoBinary, "-c", sumoConfig, "--start", "--default.action-step-length", "0.8"]
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
                  exploration=0.5,
                  Y_cnt=0,
                  change_phase_R=0,
                  dropout=0.3,
                  tls_state=True,
                  env=env,
                  )
    traci.close()

    resume = False
    if resume:
        load_multi_agents(resume_path, [agent])

    TOTAL_EPOCH = 500
    if sumoConfig.startswith("data/RegionalTransportSim"):
        STEP_LEN = 1
    else:
        STEP_LEN = 0.1
    SIM_STEPS = 1000

    # init done
    sec_steps = int(1 / STEP_LEN)  # how many steps a sec
    total_sim_steps = sec_steps * SIM_STEPS
    outfile = open(out_file_path, 'w')
    # epoch loop
    for epoch in range(TOTAL_EPOCH):
        print("Epoch ", epoch)
        traci.start(sumoCmd)

        agent.reset()
        simulation_steps = 0
        atom_time = sec_steps*2

        # simulation loop
        while simulation_steps < total_sim_steps:
            agent.agentAct()  # agent act once

            # each atom_time simulationStep() once
            for j in range(atom_time):
                traci.simulationStep()
                if j % sec_steps == 0:  # Cul cost each sec
                    agent.agentCulCost()

            agent.agentCulReward(is_sim=False)  # agent cul reward
            simulation_steps += atom_time
        # The END of simulationSteps loop

        traci.close()

        agent.printLog(outfile, epoch)
        outfile.write('\n')
        outfile.flush()

        # save model while condition == True
        save_multi_agents(save_path, save_path_best,
                          epoch % 5 == 0, [agent],
                          is_explore=True)
    # The END of epoch loop


if __name__ == '__main__':
    main()
    print("Training process done!")
