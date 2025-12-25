
'''
Evaluator Task 2B LB eYRC24-25
Name: Siddharth
Credit: e-Yantra, IIT Bombay
CDate: 26-09-2024
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
from gazebo_msgs.msg import ModelStates
from std_msgs.msg import String
from gazebo_msgs.msg import LinkStates


class SimpleBagRecorder(Node):
    def __init__(self):
        super().__init__('simple_bag_recorder_task_2b')
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

        topic_info_odom = rosbag2_py._storage.TopicMetadata(
            name='odom',
            type= 'geometry_msgs/msg/PoseStamped', #'std_msgs/msg/String',
            serialization_format='cdr')
        self.writer.create_topic(topic_info_odom)

        topic_info_links = rosbag2_py._storage.TopicMetadata(
            name='/_makeit/link_states',
            type= 'gazebo_msgs/msg/LinkStates', #'std_msgs/msg/String',
            serialization_format='cdr')
        self.writer.create_topic(topic_info_links)

        topic_info_model = rosbag2_py._storage.TopicMetadata(
            name='_model_tf',
            type= 'gazebo_msgs/msg/ModelStates', #'std_msgs/msg/String',
            serialization_format='cdr')
        self.writer.create_topic(topic_info_model)
        
        topic_info_timer_state = rosbag2_py._storage.TopicMetadata(
            name='_timer_state',
            type= 'std_msgs/msg/String', #'std_msgs/msg/String',
            serialization_format='cdr')
        self.writer.create_topic(topic_info_timer_state)
        

        self.odom_sub = self.create_subscription(Odometry, 'odom', self.topic1, 10)
        self.model_sub = self.create_subscription(ModelStates, '/_demo/model_states_demo', self.topic2, 10)
        self.create_subscription(LinkStates, '/_makeit/link_states', self.topic_callback, 10)
        self.create_timer(0.1, self.topic3)

        self.get_logger().info("\033[92m DATA COLLECTION STARTED FOR TASK 2B \033[00m", once=True)


    def topic1(self, msg):
        self.odom_raw=msg
        self.odom_msg=PoseStamped()
        self.odom_msg.header=self.odom_raw.header
        self.odom_msg.pose=self.odom_raw.pose.pose
        self.writer.write('odom', serialize_message(self.odom_msg), self.get_clock().now().nanoseconds)
        
    def topic_callback(self, data):
        self.writer.write('/_makeit/link_states', serialize_message(data), self.get_clock().now().nanoseconds)

    def topic2(self, msg):
        self.writer.write('_model_tf', serialize_message(msg), self.get_clock().now().nanoseconds)
        

    def topic3(self):
        publisher_names = self.get_publishers_info_by_topic("/cmd_vel")
        pub_str=""
        if publisher_names:
            for publisher_name in publisher_names:
                pub_str=pub_str+publisher_name.node_name+", "
        pub_str_msg=String()
        pub_str_msg.data=pub_str
        self.writer.write('_timer_state', serialize_message(pub_str_msg), self.get_clock().now().nanoseconds)
 


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
