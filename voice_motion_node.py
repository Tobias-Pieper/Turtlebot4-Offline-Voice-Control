#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from geometry_msgs.msg import TwistStamped
from rclpy.action import ActionClient
from irobot_create_msgs.action import Dock, Undock


class VoiceMotionNode(Node):

    FORWARD_SPEED = 0.12
    BACKWARD_SPEED = -0.10
    TURN_SPEED = 0.6

    MOVE_DURATION = 1.5
    TURN_DURATION = 1.2

    def __init__(self):
        super().__init__('voice_motion_node')

        self.cmd_pub = self.create_publisher(
            TwistStamped,
            '/cmd_vel',
            10
        )

        self.voice_sub = self.create_subscription(
            String,
            '/voice_command',
            self.voice_command_callback,
            10
        )

        self.get_logger().info(
            'VoiceMotionNode started. Listening on /voice_command...'
        )

        self.dock_client = ActionClient(
            self, 
            Dock, 
            '/dock'
        )

        self.undock_client = ActionClient(
            self, 
            Undock, 
            '/undock'
        )

    def send_dock_goal(self):
        self.dock_client.wait_for_server()
        goal_msg = Dock.Goal()
        self.dock_client.send_goal_async(goal_msg)
        self.get_logger().info("Docking goal sent.")    

    def send_undock_goal(self):
        self.undock_client.wait_for_server()
        goal_msg = Undock.Goal()
        self.undock_client.send_goal_async(goal_msg)
        self.get_logger().info("Undocking goal sent.")

    def publish_velocity(self, linear_x, angular_z):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
 
        msg.twist.linear.x = linear_x
        msg.twist.angular.z = angular_z

        self.cmd_pub.publish(msg)

    def stop_robot(self):
        self.publish_velocity(0.0, 0.0)
        self.get_logger().info('Robot stopped.')

    def move_for_duration(self, linear_x, angular_z, duration):
        end_time = time.time() + duration

        while time.time() < end_time:
            self.publish_velocity(linear_x, angular_z)
            time.sleep(0.05)

        self.stop_robot()

    def voice_command_callback(self, msg):
        command = msg.data.strip().upper()

        self.get_logger().info(f'Received voice command: {command}')

        if command == 'STOP':
            self.stop_robot()

        elif command == 'FORWARD':
            self.get_logger().info('Moving forward...')
            self.move_for_duration(
                self.FORWARD_SPEED,
                0.0,
                self.MOVE_DURATION
            )

        elif command == 'BACKWARD':
            self.get_logger().info('Moving backward...')
            self.move_for_duration(
                self.BACKWARD_SPEED,
                0.0,
                self.MOVE_DURATION
            )

        elif command == 'LEFT':
            self.get_logger().info('Turning left...')
            self.move_for_duration(
                0.0,
                self.TURN_SPEED,
                self.TURN_DURATION
            )

        elif command == 'RIGHT':
            self.get_logger().info('Turning right...')
            self.move_for_duration(
                0.0,
                -self.TURN_SPEED,
                self.TURN_DURATION
            )

        elif command == 'DOCK':
                self.get_logger().info('Docking command received...')
                self.send_dock_goal()

        elif command == 'UNDOCK':
                self.get_logger().info('Undocking command received...')
                self.send_undock_goal()

        elif command == 'LOOK':
                self.get_logger().info('LOOK command received. Ignoring in motion node.')

        else:
            self.get_logger().warn(
                f'Unknown command: {command}'
            )
            self.stop_robot()


def main(args=None):
    rclpy.init(args=args)

    node = VoiceMotionNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        node.stop_robot()

    finally:
        node.stop_robot()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
