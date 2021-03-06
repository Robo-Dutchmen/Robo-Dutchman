#!/usr/bin/env python
# license removed for brevity

# Reference web pages
# http://wiki.ros.org/hebiros
# https://github.com/HebiRobotics/HEBI-ROS
# https://github.com/HebiRobotics/HEBI-ROS/blob/master/hebiros_basic_examples/src/example_04_trajectory_node.cpp#L105
# http://wiki.ros.org/actionlib_tutorials/Tutorials/SimpleActionClient
# https://github.com/ros/common_tutorials/blob/hydro-devel/actionlib_tutorials/scripts/fibonacci_client.py
# http://wiki.ros.org/actionlib_tutorials/Tutorials/Writing%20a%20Callback%20Based%20Simple%20Action%20Client
# http://wiki.ros.org/actionlib
# https://docs.ros.org/api/actionlib/html/classactionlib_1_1simple__action__server_1_1SimpleActionServer.html


import rospy
import actionlib
import numpy as np
import kinematics as kin

from hebiros.srv import EntryListSrv, AddGroupFromNamesSrv, SizeSrv, SetCommandLifetimeSrv
from hebiros.msg import WaypointMsg, TrajectoryAction, TrajectoryGoal

import hebiros.msg
from sensor_msgs.msg import JointState
from std_msgs.msg import String

global NODE_NAME, NaN
global GROUP_NAME, FAMILY_NAME, NAME_1, NAME_2, NAME_3, NAME_4
global WAYPOINT_PERIOD
NODE_NAME = "arm_planner_node"
NaN = float("NaN")

# Hebi names
GROUP_NAME = "RoboDutchmanArm"
GROUP_SIZE = 4
FAMILY_NAME = "RoboDutchman"
NAME_1 = "Shoulder"
NAME_2 = "Elbow"
NAME_3 = "Wrist1"
NAME_4 = "Wrist2"

COMMAND_LIFETIME = 0
WAYPOINT_PERIOD = 0.2

class TrajectoryGenerator(object):
    global NODE_NAME, NaN
    global WAYPOINT_PERIOD

    # times: time stamps of wapyoints of length m
    # names: names of joints
    # waypoints: a 5 x m matrix of waypoints
    def __init__(self, names):
        # input validation
        self.names = names
        self.times = list([0])
        self.waypoints = [ [0], [0], [0], [0], [0] ]
        self.elbow_up = list([0])
        self.initialPoseSet = False


    def addWaypoint(self, waypoint, duration, elbow_up):
        if (not len(waypoint) == 5):
            rospy.logwarn("Need 5 values for waypoint")

        self.times.append(duration + self.times[-1])

        for i in range(0,5):
            self.waypoints[i].append(waypoint[i])

        self.elbow_up.append(elbow_up)

    def validate(self):
        self.num_waypoints = len(self.times)
        self.num_joints = len(self.names)
        self.num_workspace_dof = len(self.waypoints)

        if (not self.num_waypoints == len(self.waypoints[0])):
            rospy.logwarn("num waypoints mismatch" + self.num_waypoints + "|" \
                    + len(waypoints[0]))
            return

        if (self.num_waypoints < 2):
            rospy.logwarn("invalid num waypoints")
            return

        if (not self.num_joints == 4):
            rospy.logwarn("number of joints isnt 4")
            return

        if (not len(self.waypoints) == 5):
            rospy.logwarn("invalid num workspace targets")
            return

        if (not len(self.elbow_up) == self.num_waypoints):
            rospy.logwarn("invalid length of elbow up")
            return


        self.interp_times = np.arange(0,self.times[-1] + WAYPOINT_PERIOD,WAYPOINT_PERIOD)
        self.num_interp_waypoints = len(self.interp_times)

        # a 5 x num_inter_waypoints matrix
        self.workspace_waypoints = list()

        # a num_interp_waypoints x 5 matrx
        self.configuration_waypoints = list()


    def interpolateWorkspaceWaypoints(self):
        self.workspace_waypoints = list()

        for dof in range (0,self.num_workspace_dof):
            interpolate = np.interp(self.interp_times,self.times, \
                    self.waypoints[dof], WAYPOINT_PERIOD)
            self.workspace_waypoints.append(interpolate)

    def generateGoal(self):
        self.goal = TrajectoryGoal()
        self.goal.times = self.interp_times
        self.goal.waypoints = []

        for i in range(0,self.num_interp_waypoints):
            waypoint = WaypointMsg()
            waypoint.names = self.names
            waypoint.velocities = [NaN,NaN,NaN,NaN]
            waypoint.accelerations = [NaN,NaN,NaN,NaN]

            workspace_waypoint = []

            # construct workspace waypoint
            for j in range(0,self.num_workspace_dof):
                workspace_waypoint.append( \
                        self.workspace_waypoints[j][i])

            # get elbow up
            elbow = self.elbow_up[0]
            for j in range(0,self.num_waypoints):
                if (self.interp_times[i] <= self.times[j]):
                    elbow = self.elbow_up[j]


            # run ik to get configspace waypoint
            configuration_waypoint = kin.ik(workspace_waypoint,elbow)
            waypoint.positions = configuration_waypoint

            self.goal.waypoints.append(waypoint)

        self.goal.waypoints[0].velocities = [0,0,0,0]
        self.goal.waypoints[0].accelerations = [0,0,0,0]
        self.goal.waypoints[-1].velocities = [0,0,0,0]
        self.goal.waypoints[-1].accelerations = [0,0,0,0]



    def set_initial_pose(self,cur_pos):
        if (cur_pos == None):
            return

        self.times[0] = 0
        self.elbow_up[0] = kin.get_elbow(cur_pos)

        cur_pos_workspace = kin.fk(cur_pos)
        print cur_pos_workspace
        for i in range(0,5):
            self.waypoints[i][0] = cur_pos_workspace[0]

        self.initialPoseSet = True


    def createTrajectory(self,cur_pose = None):
        if (not self.initialPoseSet):
            self.set_initial_pose(cur_pose)
        self.validate()
        self.interpolateWorkspaceWaypoints()
        self.generateGoal()
        return self.goal

	# time in seconds
	# rospy.get_time()
        #
    def getDuration(self):
        return self.times[-1]

    def getJointStateCommand(self, time):
        cmd = JointState();
        cmd.name = self.names;

        # find previous which leg we are on
        if (time < 0 or time > self.times[-1]):
            return null;

        index = -1
        for i in range(0,len(self.times)-1):
            if (self.times[i] <= time and time <= self.times[i+1]):
                index = i
                break

        if (index == -1):
            return null

        cmd.position = list([0,0,0,0])
        cmd.velocity = list([0,0,0,0])
        cmd.effort = list([NaN,NaN,NaN,NaN])

        epsilon = 0.001
        leg_duration = self.times[index+1] - self.times[index]
        leg_percentage = 1.0 - ((self.times[index+1] - time) / leg_duration)
        leg_percentage_epsilon = 1.0 - ((self.times[index+1] - (time+epsilon)) / leg_duration)

        print leg_percentage
        print leg_percentage_epsilon

        # Calculate current workspace waypoint
        wayp = list([0,0,0,0,0])
        wayp_epsilon = list([0,0,0,0,0])
        prev_wayp = \
                [self.waypoints[0][index],
                self.waypoints[1][index],
                self.waypoints[2][index],
                self.waypoints[3][index],
                self.waypoints[4][index]]

        next_wayp = \
                [self.waypoints[0][index+1],
                self.waypoints[1][index+1],
                self.waypoints[2][index+1],
                self.waypoints[3][index+1],
                self.waypoints[4][index+1]]

        for dof in range(0,5):
            difference = next_wayp[dof] - prev_wayp[dof]
            wayp[dof] = prev_wayp[dof] + (leg_percentage * difference)
            wayp_epsilon[dof] = prev_wayp[dof] + (leg_percentage_epsilon * difference)


        print wayp
        print wayp_epsilon

        cmd.position = kin.ik(wayp,self.elbow_up[index])
        position_epsilon = kin.ik(wayp_epsilon,self.elbow_up[index])

        for joint in range(0,4):
            cmd.velocity[joint] = (cmd.position[joint] - position_epsilon[joint]) / epsilon

        # Calculate current joint velocity)

        # Calculate workspace waypoint a small time in the future
        wayp_epsilon = list([0,0,0,0,0])

        for dof in range(0,5):
            difference = next_wayp[dof] - prev_wayp[dof]
            wayp[dof] = prev_wayp[dof] + (leg_percentage * leg_duration)

        return cmd

if __name__ == '__main__':
    t = TrajectoryGenerator(["a","b","c","d"])
    t.set_initial_pose(kin.ik([0.2,0,0,0,0],True))
    t.addWaypoint([0.6,0,0,0,0],1,True)

    time = 0
    while(time <= t.getDuration()):
        cmd = t.getJointStateCommand(time)
        print kin.fk(cmd.position)
        print cmd.velocity
        print "\n"
        time = time + 0.1

