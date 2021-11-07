import os
import sys
import re
import numpy as np
import torch
import pickle as pk
import scipy.sparse as sp

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
    import traci

GREEN = 0
YELLOW = 1
RED = 2
pre_total_cost = float('inf')


def changeToYellow(light):
    return re.sub('[^r]', 'y', light)


def getRYG(light):
    return traci.trafficlights.getRedYellowGreenState(light)


def setRYG(light, ryg):
    traci.trafficlights.setRedYellowGreenState(light, ryg)


"""
actionPhases: action vec
bufferRYGs: to store the action should be taken
controlStates: to indicate each tl should be GREEN, YELLOW or RED
previousPhases: previous phases of each tl
tlids: control tls
phaseDefs: full definition of phases
"""


def act(actionPhases, bufferRYGs, controlStates, previousPhases, tlids, phaseDefs,
        is_stable, verbose=False):
    """add yellow red phases between light change for all controlled TLs simultaneously"""
    for ind, light in enumerate(tlids):

        if controlStates[ind] == YELLOW:
            ryg = getRYG(light)
            ryg = len(ryg) * 'r'
            setRYG(light, ryg)
            controlStates[ind] = RED

        # If current phase is RED, set in buffer phase
        elif controlStates[ind] == RED:
            # change to real phase
            controlStates[ind] = GREEN
            setRYG(light, bufferRYGs[ind])
            is_stable[ind] = True

        # GREEN & changed
        elif actionPhases[ind] != previousPhases[ind]:
            # change to yellow
            ryg = getRYG(light)
            ryg = changeToYellow(ryg)

            # get bufferPhases
            bufferRYGs[ind] = phaseDefs[ind][actionPhases[ind]]
            if verbose:
                print(bufferRYGs[ind])

            # set to yellow
            setRYG(light, ryg)
            controlStates[ind] = YELLOW
            previousPhases[ind] = actionPhases[ind]
            is_stable[ind] = False


"""
act with Yellow phase count down
"""


def act_Y_cnt(actionPhases, bufferRYGs, controlStates, previousPhases, tlids, phaseDefs,
              is_stable, Y_cnt_vec, verbose=False):
    for ind, light in enumerate(tlids):
        if controlStates[ind] == YELLOW:
            # if Yellow need more time
            if Y_cnt_vec[ind] > 0:
                Y_cnt_vec[ind] -= 1
                continue

            ryg = getRYG(light)
            ryg = len(ryg) * 'r'
            setRYG(light, ryg)
            controlStates[ind] = RED

        # If current phase is RED, set in buffer phase
        elif controlStates[ind] == RED:
            # change to real phase
            controlStates[ind] = GREEN
            setRYG(light, bufferRYGs[ind])
            is_stable[ind] = True

        # GREEN & changed
        elif actionPhases[ind] != previousPhases[ind]:
            # change to yellow
            ryg = getRYG(light)
            ryg = changeToYellow(ryg)

            # get bufferPhases
            bufferRYGs[ind] = phaseDefs[ind][actionPhases[ind]]
            if verbose:
                print(bufferRYGs[ind])

            # set to yellow
            setRYG(light, ryg)
            controlStates[ind] = YELLOW
            previousPhases[ind] = actionPhases[ind]
            is_stable[ind] = False


def get_loop_state(detectorIDs):
    """Get dets' states by detsIDs"""
    state = []
    for detector in detectorIDs:
        speed = traci.inductionloop.getLastStepMeanSpeed(detector)
        state.append(speed)
    for detector in detectorIDs:
        veh_num = traci.inductionloop.getLastStepVehicleNumber(detector)
        state.append(veh_num)
    state = np.array(state)
    return state


def get_control_lanes(controlTLIds):
    """Get lanes by tls"""
    controlLanes = []
    for tl in controlTLIds:
        lanes = traci.trafficlight.getControlledLanes(tl)
        controlLanes += sorted(set(lanes), key=lanes.index)  # delete dup lanes
    return controlLanes


def get_lane_waiting_cars(lane, thres=5):
    """count number of cars under speed thres.
    also compute the average speed of the lane."""
    count = 0
    total_speed = 0
    total_count = 0.001
    total_wt = 0
    cars = traci.lane.getLastStepVehicleIDs(lane)
    for car in cars:
        speed = traci.vehicle.getSpeed(car)
        total_speed += speed
        total_count += 1
        # total_wt += traci.vehicle.getAccumulatedWaitingTime(car)
        total_wt += traci.vehicle.getWaitingTime(car)
        if speed < thres:
            count += 1
    return count, total_speed / total_count, total_wt


def lane_waiting(controlTLIds):
    """Total waiting time of lanes by tls."""

    controlLanes = get_control_lanes(controlTLIds)
    total_wt = 0
    ncars = 0
    for lane in controlLanes:
        ncar, ave_speed, wt = get_lane_waiting_cars(lane)
        ncars += ncar
        total_wt += wt
    return total_wt + ncars * max((20 - ave_speed), 0)


def get_lane_state(controlTLIds):
    """Get only car num by tls."""
    state = []
    controlLanes = get_control_lanes(controlTLIds)
    for lane in controlLanes:
        ncars, _, _ = get_lane_waiting_cars(lane)
        state.append(ncars)
    state = np.array(state)
    return state


def get_tls_state_by_TLIDs(controlTLIds):
    """Get tls state (ordered by tls) by TLIDs, without detector"""
    idx_features_labels = []
    max_len = -1
    for tl in controlTLIds:
        # get each tl's state
        lanes = get_control_lanes([tl])
        idx_features_label = []
        for lane in lanes:
            ncars, _, _ = get_lane_waiting_cars(lane)
            idx_features_label.append(ncars)
        idx_features_labels.append(idx_features_label)
        if len(idx_features_label) > max_len:
            max_len = len(idx_features_label)

    # set idx in a same dim
    for idx in idx_features_labels:
        idx.extend([0]*(max_len-len(idx)))

    # process raw features
    states = sp.csr_matrix(idx_features_labels, dtype=np.float32)
    return states


def get_tls_state_withDet_by_TLIDs(controlTLIds):
    """Get tls state (ordered by tls) by TLIDs, with detector"""
    idx_features_labels = []
    max_len = -1
    for tl in controlTLIds:
        # get each tl's state
        lanes = get_control_lanes([tl])
        idx_features_label = []
        for lane in lanes:
            ncars, _, _ = get_lane_waiting_cars(lane)
            idx_features_label.append(ncars)
            # add detectors' info
            lane_dets = get_lanes_dets([lane])
            dets_state = get_loop_state(lane_dets).tolist()
            idx_features_label += dets_state
        idx_features_labels.append(idx_features_label)
        if len(idx_features_label) > max_len:
            max_len = len(idx_features_label)

    # set idx in a same dim
    for idx in idx_features_labels:
        idx.extend([0] * (max_len - len(idx)))

    # process raw features
    states = sp.csr_matrix(idx_features_labels, dtype=np.float32)
    return states


def save_multi_agents(save_path, save_path_best, condition,
                      agent_list, is_tf=False, is_explore=False):
    """Keep agent_list order"""
    global pre_total_cost
    if condition:
        # Calculate totalCost in each epoch, for calculation the best model
        cul_total_cost = 0
        for agent in agent_list:
            if is_explore:
                cul_total_cost += agent.totalCost * agent.learner.exploration
            else:
                cul_total_cost += agent.totalCost

        if not is_tf:  # pytorch
            # normal save
            dicts_to_save = []
            for agent in agent_list:
                dicts_to_save.append(agent.learner.returnSaveDict())
            torch.save(dicts_to_save, save_path)
            # print("dicts_to_save:")
            # print(dicts_to_save)

            # save the best model
            if cul_total_cost < pre_total_cost:
                torch.save(dicts_to_save, save_path_best)
                pre_total_cost = cul_total_cost
        else:  # tf
            # normal save
            for agent in agent_list:
                agent.learner.saveModel(save_path)

            # save the best model
            if cul_total_cost < pre_total_cost:
                for agent in agent_list:
                    agent.learner.saveModel(save_path_best)
                pre_total_cost = cul_total_cost


def save_simple_model(save_path, condition, agent_list, is_tf=False):
    """Save simple model without calculate cost(for A3C use)"""
    if condition:
        if not is_tf:  # pytorch
            # normal save
            dicts_to_save = []
            for agent in agent_list:
                dicts_to_save.append(agent.learner.returnSaveDict())
            torch.save(dicts_to_save, save_path)


def save_auction_model(save_path, save_path_best, condition, agent_list):
    global pre_total_cost
    if condition:
        # Calculate totalCost in each epoch, for calculation the best model
        cul_total_cost = 0
        for agent in agent_list:
            cul_total_cost += agent.totalCost

        dicts_to_save = []
        for agent in agent_list:
            dicts_to_save.append(agent.learner.returnSaveDict())
        with open(save_path, 'wb') as f:
            pk.dump(dicts_to_save, f)

        # save the best model
        if cul_total_cost < pre_total_cost:
            with open(save_path_best, 'wb') as f:
                pk.dump(dicts_to_save, f)
            pre_total_cost = cul_total_cost


def load_multi_agents(load_path, agent_list, is_tf=False):
    """load model for multi agents"""
    if not is_tf:
        dicts_to_load = torch.load(load_path)
        # print("dicts_to_load:")
        # print(dicts_to_load)
        for i, dict_to_load in enumerate(dicts_to_load):
            agent_list[i].learner.loadModel(dict_to_load)
    else:  # tf
        for agent in agent_list:
            agent.learner.loadModel(load_path)


def load_auction_model(load_path, agent_list):
    with open(load_path, 'rb') as f:
        params_to_load = pk.load(f)
    for i, params in enumerate(params_to_load):
        agent_list[i].learner.loadModel(params)


def get_junction_list(tls):
    juncs_dets_list = []
    for tl in tls:
        junc_dets_list = {}  # dets in single junc
        lanes = get_control_lanes([tl])
        for lane in lanes:
            junc_dets_list[lane] = get_lanes_dets([lane])
        juncs_dets_list.append(junc_dets_list)

    return juncs_dets_list


def per_light_waiting(junction_list):
    pl_wt = np.zeros(len(junction_list), dtype=np.float32)
    for i, junction in enumerate(junction_list):
        for lane in junction:
            ncar, ave_speed, wt = get_lane_waiting_cars(lane)
            pl_wt[i] += wt + ncar * max((20 - ave_speed), 0)
    return pl_wt


def get_lanes_dets(lanes):
    """return dets IDs by lanes"""
    detector_list = []
    for lane in lanes:
        detector_list.append(lane + "loop1")
        detector_list.append(lane + "loop2")
    return detector_list


def get_tls_dets(tls):
    """return dets IDs by tls"""
    lanes = get_control_lanes(tls)
    return get_lanes_dets(lanes)


def is_same_ndarr(arr1, arr2):
    return (arr1 == arr2).all()


def get_edge_by_tlid(TLId):
    controlLanes = get_control_lanes([TLId])
    edges = {}
    for lane in controlLanes:
        edge = traci.lane.getEdgeID(lane)
        edge = edge.strip('-')
        edges[edge] = lane
    return edges


def get_len_by_tls(TLId1, TLId2):
    """Get edge length by end tls"""
    tl1_edges = get_edge_by_tlid(TLId1)
    tl2_edges = get_edge_by_tlid(TLId2)
    edge = tl1_edges.keys() & tl2_edges.keys()
    if len(edge) == 1:
        length = traci.lane.getLength(tl1_edges[list(edge)[0]])
    else:
        print(TLId1, 'and', TLId2, 'have', len(edge), 'common edges')
        length = 100  # if common edges == 0 or too many, set a long range
    return length


if __name__ == "__main__":
    print(changeToYellow('grGrsruoO'))
