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
import tf2_ros
from rich.console import Console

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
        topic_info = rosbag2_py._storage.TopicMetadata(
            name='tf',
            type= 'geometry_msgs/msg/TransformStamped', #'std_msgs/msg/String',
            serialization_format='cdr')
        self.writer.create_topic(topic_info)
        self.create_timer(0.1, self.topic_callback)

    def topic_callback(self):
        try:
            self.tool_link = self.tf_buffer.lookup_transform('base_link', "tool0", rclpy.time.Time())
            # print(type(self.tool_link))
            self.get_logger().info("\033[92m DATA COLLECTION STARTED \033[00m", once=True)
            self.writer.write('tf', serialize_message(self.tool_link), self.get_clock().now().nanoseconds)
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
    except KeyboardInterrupt:
        console.print(f"[green]\nExiting Gracefully[/green]")
    # rclpy.shutdown()
    result["generate"] = False
    return result