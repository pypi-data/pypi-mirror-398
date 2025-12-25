import rclpy
import shutil
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rosbag2_py
import tf2_ros
from rich.console import Console
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped, Twist
from ros_gz_interfaces.msg import Contacts
from std_msgs.msg import String
from rosgraph_msgs.msg import Clock
import json
import logging
from ros2node.api import get_absolute_node_name, get_node_names, get_topics
from ros2topic.api import get_topic_names_and_types


class SimpleBagRecorder(Node):
    def __init__(self):
        super().__init__('simple_bag_recorder')
        self.tf_buffer = tf2_ros.buffer.Buffer()
        self.r = tf2_ros.TransformBroadcaster(self)
        self.listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.writer = rosbag2_py.SequentialWriter()
        try:
            shutil.rmtree("my_bag")
        except:
            pass
        storage_options = rosbag2_py._storage.StorageOptions(
            uri='my_bag',
            storage_id='sqlite3')
        converter_options = rosbag2_py._storage.ConverterOptions('', '')
        self.writer.open(storage_options, converter_options)

        topic_info_tf = rosbag2_py._storage.TopicMetadata(
            name='tf',
            type= 'geometry_msgs/msg/TransformStamped', #'std_msgs/msg/String',
            serialization_format='cdr')
        topic_info_odom = rosbag2_py._storage.TopicMetadata(
            name='odom',
            type= 'geometry_msgs/msg/PoseStamped', #'std_msgs/msg/String',
            serialization_format='cdr')
        topic_info_detection_status = rosbag2_py._storage.TopicMetadata(
            name='detection_status',
            type= 'std_msgs/msg/String', #'std_msgs/msg/String',
            serialization_format='cdr')
        topic_info_shape_info = rosbag2_py._storage.TopicMetadata(
            name='_shape_info',
            type= 'std_msgs/msg/String', #'std_msgs/msg/String',
            serialization_format='cdr')
        topic_info_clock = rosbag2_py._storage.TopicMetadata(
            name='clock',
            type= 'rosgraph_msgs/msg/Clock',
            serialization_format='cdr')
        topic_info_cmd_vel = rosbag2_py._storage.TopicMetadata(
            name='cmd_vel',
            type= 'geometry_msgs/msg/Twist',
            serialization_format='cdr')
        topic_info_ros_status = rosbag2_py._storage.TopicMetadata(
            name='_ros_status',
            type= 'std_msgs/msg/String',
            serialization_format='cdr')
        topic_info_ros_node_topic_info = rosbag2_py._storage.TopicMetadata(
            name='/_ros_node_topic_info',
            type= 'std_msgs/msg/String',
            serialization_format='cdr')
        # topic_info_ros_info = rosbag2_py._storage.TopicMetadata(
        #     name='_ros_info',
        #     type= 'std_msgs/msg/String',
        #     serialization_format='cdr')

        self.writer.create_topic(topic_info_tf)
        self.writer.create_topic(topic_info_odom)
        self.writer.create_topic(topic_info_detection_status)
        self.writer.create_topic(topic_info_shape_info)
        self.writer.create_topic(topic_info_clock)
        self.writer.create_topic(topic_info_cmd_vel)
        self.writer.create_topic(topic_info_ros_status)
        self.writer.create_topic(topic_info_ros_node_topic_info)
        # self.writer.create_topic(topic_info_ros_info)

        self.odom=Odometry()
        self.shape_info=String()
        self.gazebo_clock=Clock()
        self.twist = Twist()
        self.ros_status = Contacts()
        self.odom_sub = self.create_subscription(Odometry, 'odom', self.record_odom, 10)
        self.detection_status_sub = self.create_subscription(String, 'detection_status', self.record_detection_status, 10)
        self.shape_info_sub = self.create_subscription(String, '_shape_info', self.record_shape_info, 10)
        self.clock_sub = self.create_subscription(Clock, 'clock', self.record_clock, 10)
        self.cmd_vel_sub = self.create_subscription(Twist, 'cmd_vel', self.record_cmd_vel, 10)
        self.ros_status_sub = self.create_subscription(Contacts, '_ros_status', self.record_ros_status, 10) ## Collision Topic
        # self.ros_info_pub = self.create_publisher(String, '_ros_info', 10) ## Collision republishing Topic
        self.create_timer(0.1, self.timer_loop)
        self.create_timer(5.0, self.node_topic_status_callback)

    def record_odom(self, msg):
        self.odom=msg

    def record_detection_status(self, msg):
        self.detection_status=msg
        self.writer.write('detection_status', serialize_message(self.detection_status), self.get_clock().now().nanoseconds)

    def record_shape_info(self, msg):
        self.shape_info=msg
        self.writer.write('_shape_info', serialize_message(self.shape_info), self.get_clock().now().nanoseconds)

    def record_clock(self, msg):
        self.gazebo_clock=msg
        # self.writer.write('clock', serialize_message(self.gazebo_clock), self.get_clock().now().nanoseconds)

    def record_cmd_vel(self, msg):
        self.twist=msg
        self.writer.write('cmd_vel', serialize_message(self.twist), self.get_clock().now().nanoseconds)

    def record_ros_status(self, msg):
        self.ros_status=msg
        # self.writer.write('_ros_status', serialize_message(self.ros_status), self.get_clock().now().nanoseconds)

    def node_topic_status_callback(self):
        try:
            node_names = get_node_names(node=self, include_hidden_nodes=True)
            node_topic_info = {"nodes": {}}
            for node in node_names:
                # abs_node_name = get_absolute_node_name(str(node))
                # print("Node:", node, str(node), "Absolute Name:", abs_node_name)
                publishers = get_topics(remote_node_name=node.full_name, func=self.get_publisher_names_and_types_by_node, include_hidden_topics=True)
                node_topic_info["nodes"][f"{node.full_name}"] = dict(publishers)
            # Properly wrap JSON string into a ROS 2 String message before serialization
            node_topic_info_msg = String()
            node_topic_info_msg.data = json.dumps(node_topic_info)
            self.writer.write('/_ros_node_topic_info', serialize_message(node_topic_info_msg), self.get_clock().now().nanoseconds)
            # print(node_topic_info_msg.data)
            # Also publish for any live consumers
            # self.ros_info_pub.publish(node_topic_info_msg)
        except Exception as e:
            logging.exception(f"Exception in recording node topic info data: {e}", exc_info=True)
            # self.get_logger().info(f"Exception in recording node topic info data: {e}")
            # SystemExit
        
        
    def timer_loop(self):
        try:
            self.ebot_base_link_msg = self.tf_buffer.lookup_transform('odom', "ebot_base_link", rclpy.time.Time())
            self.odom_msg=PoseStamped()
            self.odom_msg.header=self.odom.header
            self.odom_msg.pose=self.odom.pose.pose

            self.get_logger().info("\033[92m DATA COLLECTION STARTED FOR TASK 2A \033[00m", once=True)
            self.writer.write('tf', serialize_message(self.ebot_base_link_msg), self.get_clock().now().nanoseconds)
            self.writer.write('odom', serialize_message(self.odom_msg), self.get_clock().now().nanoseconds)
            # try:
            #     self.writer.write('detection_status', serialize_message(self.detection_status), self.get_clock().now().nanoseconds)
            # except:
            #     pass
            try:
                self.writer.write('_shape_info', serialize_message(self.shape_info), self.get_clock().now().nanoseconds)
            except:
                pass
            try:
                self.writer.write('clock', serialize_message(self.gazebo_clock), self.get_clock().now().nanoseconds)
            except:
                pass
            # try:
            #     self.writer.write('cmd_vel', serialize_message(self.twist), self.get_clock().now().nanoseconds)
            # except:
            #     pass
            try:
                if abs(self.ros_status.header.stamp.sec-self.odom.header.stamp.sec)<0.1:
                    collision_info = {"time": self.ros_status.header.stamp.sec+self.ros_status.header.stamp.nanosec*1e-9, "collisions": {}}
                    for id, collision in enumerate(self.ros_status.contacts):
                        collision_info["collisions"][f"{id}"] = {
                            "collision1": collision.collision1.name,
                            "collision2": collision.collision2.name,
                        }
                    # Properly wrap JSON string into a ROS 2 String message before serialization
                    collision_info_msg = String()
                    collision_info_msg.data = json.dumps(collision_info)
                    self.writer.write('_ros_status', serialize_message(collision_info_msg), self.get_clock().now().nanoseconds)
                    # Also publish for any live consumers
                    # self.ros_info_pub.publish(collision_info_msg)
            except Exception as e:
                # logging.exception(f"Exception in recording collision data: {e}", exc_info=True)
                self.get_logger().info(f"Exception in recording collision data: {e}", once=True)
                SystemExit
        except Exception as e:
            self.get_logger().info(f"Exception in recording data: {e}", once=True)
            self.get_logger().warning("WAITING FOR DATA", once=True)
            pass


def evaluate():
    result = {}
    console = Console()
    rclpy.init()
    sbr = SimpleBagRecorder()
    try:
        rclpy.spin(sbr)
    except KeyboardInterrupt or RuntimeError: 
        console.print(f"[green]\nExiting Gracefully[/green]")
    # rclpy.shutdown()
    result["generate"] = False
    return result