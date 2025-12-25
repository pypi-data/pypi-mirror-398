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
class SimpleBagRecorder(Node):

    def __init__(self):

        super().__init__('simple_bag_recorder')

        self.console = Console()
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

        tf_topic_info = rosbag2_py._storage.TopicMetadata(
            name='tf',
            type='tf2_msgs/msg/TFMessage',
            serialization_format='cdr')
        
        
        fruit_states_topic_info = rosbag2_py._storage.TopicMetadata(
            name = "/_fruit_info",
            type = "std_msgs/msg/String",
            serialization_format = "cdr"
        )
        
        self.writer.create_topic(tf_topic_info)
        self.writer.create_topic(fruit_states_topic_info)
        
        self.subscription = self.create_subscription(
            TFMessage,
            'tf',
            self.topic_callback,
            10)
        self.create_subscription(
            String,
            '/_fruit_info',
            self.fruit_states_callback,
            10
        )
        self.timer_count = 0
        self.tf_cb_status = False
        self.timer_value = 8
        self.first_cb_status = False

        self.timer = self.create_timer(1.0, self.timer_callback)
        
    def topic_callback(self, msg):
        if not self.first_cb_status:
            self.timer_count = 0
        try:
            self.writer.write(
                'tf',
                serialize_message(msg),
                self.get_clock().now().nanoseconds)
            self.tf_cb_status = True
            self.first_cb_status = True
        except:
            self.tf_cb_status = False

    
    def fruit_states_callback(self,data):
        self.writer.write(
            '/_fruit_info',
            serialize_message(data),
            self.get_clock().now().nanoseconds
        )
    

    def timer_callback(self):
        if not self.tf_cb_status:
            self.console.print(f'[red]-> TF not published yet :( Waiting for data...[/red]')
        else:
            self.console.print(f'[green]-> Collecting TF data...[/green]')

        if self.timer_count > self.timer_value:
            raise SystemExit

        self.timer_count = self.timer_count + 1

def evaluate():
    
    result = {}
    console = Console()

    rclpy.init()
    sbr = SimpleBagRecorder()

    try:
        rclpy.spin(sbr)
    except KeyboardInterrupt:
        console.print(f"[red]\n-> Keyboard Interrupt :( Exiting...\nPlease try again without any interrupt![/red]")
    except SystemExit:
        console.print(f'[green]-> Data collection completed! Thankyou for being patient ;)\nFollow instructions on portal mdbook to submit task 1B.[/green]')

    result["generate"] = False

    return result

if __name__ == "__main__":
    evaluate()
