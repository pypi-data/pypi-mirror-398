import rclpy
import shutil
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rosbag2_py
from rich.console import Console
from gazebo_msgs.msg import LinkStates
from std_msgs.msg import String
from rosgraph_msgs.msg import Clock
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
import rclpy
import shutil
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rosbag2_py
import tf2_ros
from rich.console import Console
from tf2_msgs.msg import TFMessage
from gazebo_msgs.msg import LinkStates
from std_msgs.msg import String
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped

class SimpleBagRecorder(Node):
    def __init__(self):
        super().__init__('simple_bag_recorder')
        self.console = Console()
        self.writer = rosbag2_py.SequentialWriter()

        # Delete old bag
        try:
            shutil.rmtree("my_bag")
        except FileNotFoundError:
            pass

        # Open storage
        storage_options = rosbag2_py._storage.StorageOptions(
            uri='my_bag',
            storage_id='sqlite3'
        )
        converter_options = rosbag2_py._storage.ConverterOptions('', '')
        self.writer.open(storage_options, converter_options)

        # Create topics
        tcp_topic_info = rosbag2_py._storage.TopicMetadata(
            name='tcp_pose_raw',
            type='geometry_msgs/msg/PoseStamped',
            serialization_format='cdr'
        )
        joint_topic_info = rosbag2_py._storage.TopicMetadata(
            name='joint_states',
            type='sensor_msgs/msg/JointState',
            serialization_format='cdr'
        )
        clock_topic_info = rosbag2_py._storage.TopicMetadata(
            name='/clock',
            type='rosgraph_msgs/msg/Clock',
            serialization_format='cdr'
        )

        self.writer.create_topic(tcp_topic_info)
        self.writer.create_topic(joint_topic_info)
        self.writer.create_topic(clock_topic_info)

        # QoS profiles
        reliable_qos = QoSProfile(
            depth=500,
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST
        )

        best_effort_qos = QoSProfile(
            depth=500,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST
        )

        # Subscriptions
        self.create_subscription(Clock, '/clock', self.clock_callback, best_effort_qos)
        self.create_subscription(JointState, 'joint_states', self.joint_states_callback, reliable_qos)
        self.create_subscription(PoseStamped, 'tcp_pose_raw', self.tcp_pose_callback, 10)

        self.get_logger().info("\033[92m DATA COLLECTION STARTED \033[00m", once=True)

    # Callbacks
    def tcp_pose_callback(self, msg):
        # print("TCP POSE CALLBACK",msg)
        self.writer.write('tcp_pose_raw', serialize_message(msg), self.get_clock().now().nanoseconds)

    def joint_states_callback(self, msg):
        self.writer.write('joint_states', serialize_message(msg), self.get_clock().now().nanoseconds)

    def clock_callback(self, msg):
        self.writer.write('/clock', serialize_message(msg), self.get_clock().now().nanoseconds)

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


