'''
To evaluate Task 1C of CL eYRC23-24
Name: Ravikumar C.
Credit: e-Yantra, IIT Bombay
CDate: 13-09-2023
'''

import rclpy
import shutil
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rosbag2_py
import tf2_ros
from rich.console import Console
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped


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
        self.writer.create_topic(topic_info_tf)
        topic_info_odom = rosbag2_py._storage.TopicMetadata(
            name='odom',
            type= 'geometry_msgs/msg/PoseStamped', #'std_msgs/msg/String',
            serialization_format='cdr')
        self.writer.create_topic(topic_info_odom)
        self.odom_sub = self.create_subscription(Odometry, 'odom', self.record_odom, 10)
        self.odom_sub
        self.create_timer(0.1, self.topic_callback)

    def record_odom(self, msg):
        self.odom_raw=msg
        

    def topic_callback(self):
        try:
            self.ebot_base_link_msg = self.tf_buffer.lookup_transform('odom', "ebot_base_link", rclpy.time.Time())
            self.odom_msg=PoseStamped()
            self.odom_msg.header=self.odom_raw.header
            self.odom_msg.pose=self.odom_raw.pose.pose

            self.get_logger().info("\033[92m DATA COLLECTION STARTED FOR TASK 1C \033[00m", once=True)
            self.writer.write('odom', serialize_message(self.odom_msg), self.get_clock().now().nanoseconds)
            self.writer.write('tf', serialize_message(self.ebot_base_link_msg), self.get_clock().now().nanoseconds)
        except Exception as e:
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