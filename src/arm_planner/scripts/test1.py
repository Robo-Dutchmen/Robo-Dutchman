#!/usr/bin/env python

import rospy
import actionlib
import arm_planner.msg


global NODE_NAME
NODE_NAME = "arm_planner_test_1_node"


class arm_test_1(object):
    def __init__(self):

        rospy.init_node(NODE_NAME, anonymous=True)

        self.ArmTrajectoryClient = actionlib.SimpleActionClient(\
                "/arm_planner/ArmTrajectory",
                arm_planner.msg.ArmTrajectoryAction)
        self.ArmTrajectoryClient.wait_for_server()
        rospy.loginfo("APT1: Server is online")

        goal = arm_planner.msg.ArmTrajectoryGoal()
        self.ArmTrajectoryClient.send_goal(goal,
                self.done_cb,
                self.active_cb,
                self.feedback_cb)

        rospy.loginfo("APT1: Sent goal")
        rospy.spin()

    def done_cb(self, state, result):
        rospy.loginfo("APT1: Client is done");
        rospy.loginfo(state);
        rospy.loginfo(result);

    def active_cb(self):
        rospy.loginfo("APT1:Cient is active");

    def feedback_cb(self,msg):
        rospy.loginfo("APT1: feedback");
        rospy.loginfo(msg);

if __name__ == '__main__':
    try:
        arm_test_1()
    except rospy.ROSInterruptException:
        pass
