'''
To evaluate Task 1B of CL eYRC23-24
Name: Jaison J.
Credit: e-Yantra, IIT Bombay
CDate: 12-09-2023
'''

import rclpy
import shutil
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rosbag2_py
from rich.console import Console
from gazebo_msgs.msg import LinkStates
from std_msgs.msg import String

class SimpleBagRecorder(Node):
    def __init__(self):
        super().__init__('simple_bag_recorder')
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
        topic_info = rosbag2_py._storage.TopicMetadata(
            name='/_makeit/link_states',
            type= 'gazebo_msgs/msg/LinkStates',
            serialization_format='cdr')
        topic2_info = rosbag2_py._storage.TopicMetadata(
            name='/_sprunner',
            type= 'std_msgs/msg/String',
            serialization_format='cdr')
        self.writer.create_topic(topic_info)
        self.writer.create_topic(topic2_info)
        # self.create_timer(0.5, self.topic_callback)

        self.create_subscription(LinkStates, '/_makeit/link_states', self.topic_callback, 10)
        self.create_subscription(String, '/_sprunner', self.topic2_callback, 10)

        self.get_logger().info("\033[92m DATA COLLECTION STARTED \033[00m", once=True)

    def topic_callback(self, data):
        self.writer.write('/_makeit/link_states', serialize_message(data), self.get_clock().now().nanoseconds)
    
    def topic2_callback(self, data):
        self.writer.write('/_sprunner', serialize_message(data), self.get_clock().now().nanoseconds)

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