import shutil
from rich.console import Console

import rclpy
from rclpy.node import Node
from rclpy.serialization import serialize_message
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

import rosbag2_py

from rosgraph_msgs.msg import Clock
from tf2_msgs.msg import TFMessage
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String


class SimpleBagRecorder(Node):
    def __init__(self):
        super().__init__('simple_bag_recorder')
        self.console = Console()
        self.writer = rosbag2_py.SequentialWriter()

        # Remove existing bag
        try:
            shutil.rmtree("my_bag")
        except FileNotFoundError:
            pass

        # Open rosbag2 writer
        storage_options = rosbag2_py._storage.StorageOptions(uri='my_bag', storage_id='sqlite3')
        converter_options = rosbag2_py._storage.ConverterOptions('', '')
        self.writer.open(storage_options, converter_options)

        # Define topics metadata
        self.topics_info = [
            rosbag2_py._storage.TopicMetadata(name='tf', type='tf2_msgs/msg/TFMessage', serialization_format='cdr'),
            rosbag2_py._storage.TopicMetadata(name='tcp_pose_raw', type='geometry_msgs/msg/PoseStamped', serialization_format='cdr'),
            rosbag2_py._storage.TopicMetadata(name='joint_states', type='sensor_msgs/msg/JointState', serialization_format='cdr'),
            rosbag2_py._storage.TopicMetadata(name='/clock', type='rosgraph_msgs/msg/Clock', serialization_format='cdr'),
            rosbag2_py._storage.TopicMetadata(name='/_fruit_info', type='std_msgs/msg/String', serialization_format='cdr'),
            rosbag2_py._storage.TopicMetadata(name='/_bad_fruit_positions', type='std_msgs/msg/String', serialization_format='cdr')
            
        ]
        
        # Create topics
        for topic in self.topics_info:
            self.writer.create_topic(topic)

        # QoS profiles
        self.reliable_qos = QoSProfile(depth=500, reliability=QoSReliabilityPolicy.RELIABLE, history=QoSHistoryPolicy.KEEP_LAST)
        self.best_effort_qos = QoSProfile(depth=500, reliability=QoSReliabilityPolicy.BEST_EFFORT, history=QoSHistoryPolicy.KEEP_LAST)

        # Subscriptions
        self.create_subscription(Clock, '/clock', self._clock_callback, self.best_effort_qos)
        self.create_subscription(JointState, 'joint_states', self._joint_states_callback, self.reliable_qos)
        self.create_subscription(PoseStamped, 'tcp_pose_raw', self._tcp_pose_callback, self.reliable_qos)
        self.create_subscription(TFMessage, 'tf', self._tf_callback, self.reliable_qos)
        self.create_subscription(String, '/_fruit_info', self._fruit_info_callback, self.reliable_qos)
        self.create_subscription(String, '/_bad_fruit_positions', self._bad_fruit_positions_callback, self.reliable_qos)
        self.get_logger().info("\033[92mDATA COLLECTION STARTED\033[00m")

    # Callbacks
    def _tf_callback(self, msg):
        self._write_bag('tf', msg)

    def _tcp_pose_callback(self, msg):
        self._write_bag('tcp_pose_raw', msg)

    def _joint_states_callback(self, msg):
        self._write_bag('joint_states', msg)

    def _clock_callback(self, msg):
        self._write_bag('/clock', msg)

    def _fruit_info_callback(self, msg):
        self._write_bag('/_fruit_info', msg)

    def _bad_fruit_positions_callback(self, msg):
        self._write_bag('/_bad_fruit_positions', msg)

    # Helper to write messages
    def _write_bag(self, topic_name, msg):
        timestamp = self.get_clock().now().nanoseconds
        self.writer.write(topic_name, serialize_message(msg), timestamp)


# Keep your evaluate() function exactly as it is
def evaluate():
    result = {}
    console = Console()
    rclpy.init()
    sbr = SimpleBagRecorder()
    try:
        rclpy.spin(sbr)
    except KeyboardInterrupt:
        console.print(f"[green]\nExiting Gracefully[/green]")
    # rclpy.shutdown()
    result["generate"] = False
    return result
