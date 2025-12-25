import rclpy
import shutil
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rosbag2_py
import tf2_ros
from tf2_msgs.msg import TFMessage
from rich.console import Console
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped, Twist, TwistStamped
from ros_gz_interfaces.msg import Contacts
from std_msgs.msg import String
from rosgraph_msgs.msg import Clock
import json
import logging
from sensor_msgs.msg import JointState
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from ros2node.api import get_absolute_node_name, get_node_names, get_topics
from ros2topic.api import get_topic_names_and_types


class SimpleBagRecorder(Node):
    def __init__(self):
        super().__init__("simple_bag_recorder")
        self.tf_buffer = tf2_ros.buffer.Buffer()
        self.r = tf2_ros.TransformBroadcaster(self)
        self.listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.writer = rosbag2_py.SequentialWriter()
        try:
            shutil.rmtree("my_bag")
        except:
            pass
        storage_options = rosbag2_py._storage.StorageOptions(
            uri="my_bag", storage_id="sqlite3"
        )
        converter_options = rosbag2_py._storage.ConverterOptions("", "")
        self.writer.open(storage_options, converter_options)

        # topic_info_ros_info = rosbag2_py._storage.TopicMetadata(
        #     name='_ros_info',
        #     type= 'std_msgs/msg/String',
        #     serialization_format='cdr')

        self.topic_info_list = [
            rosbag2_py._storage.TopicMetadata(
                name="tf",
                type="tf2_msgs/msg/TFMessage",  #'std_msgs/msg/String',
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="odom",
                type="geometry_msgs/msg/PoseStamped",  #'std_msgs/msg/String',
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="detection_status",
                type="std_msgs/msg/String",  #'std_msgs/msg/String',
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="_shape_info",
                type="std_msgs/msg/String",  #'std_msgs/msg/String',
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="clock", type="rosgraph_msgs/msg/Clock", serialization_format="cdr"
            ),
            rosbag2_py._storage.TopicMetadata(
                name="cmd_vel",
                type="geometry_msgs/msg/Twist",
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="_ros_status",
                type="std_msgs/msg/String",
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="/_ros_node_topic_info",
                type="std_msgs/msg/String",
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="tcp_pose_raw",
                type="geometry_msgs/msg/PoseStamped",
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="joint_states",
                type="sensor_msgs/msg/JointState",
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="/_fruit_info",
                type="std_msgs/msg/String",
                serialization_format="cdr",
            ),
            rosbag2_py._storage.TopicMetadata(
                name="/_bad_fruit_positions",
                type="std_msgs/msg/String",
                serialization_format="cdr",
            ),
        ]

        for topic in self.topic_info_list:
            self.writer.create_topic(topic)

        self.odom = Odometry()
        self.shape_info = String()
        self.gazebo_clock = Clock()
        self.last_gazebo_write_time = 0
        self.twist_stamped_msg = TwistStamped()
        self.last_twist_write_time = 0
        self.ros_status = Contacts()
        self.tf_msg = TFMessage()
        self.last_tf_write_time = 0
        self.tcp_pose_msg = PoseStamped()
        self.last_tcp_pose_write_time = 0
        self.joint_state_msg = JointState()
        self.last_joint_state_write_time = 0
        self.fruit_info_msg = String()
        self.last_fruit_info_write_time = 0
        self.bad_fruit_position_msg = String()
        self.last_bad_fruit_position_write_time = 0
        self.detection_status = String()




        # QoS profiles
        self.reliable_qos = QoSProfile(
            depth=500,
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
        )
        self.best_effort_qos = QoSProfile(
            depth=500,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
        )

        self.odom_sub = self.create_subscription(
            Odometry, "odom", self.record_odom, qos_profile=self.reliable_qos
        )
        self.detection_status_sub = self.create_subscription(
            String,
            "detection_status",
            self.record_detection_status,
            qos_profile=self.reliable_qos,
        )
        self.shape_info_sub = self.create_subscription(
            String,
            "_shape_info",
            self.record_shape_info,
            qos_profile=self.reliable_qos,
        )
        self.clock_sub = self.create_subscription(
            Clock, "clock", self.record_clock, qos_profile=self.best_effort_qos
        )
        self.cmd_vel_sub = self.create_subscription(
            Twist, "cmd_vel", self.record_cmd_vel, qos_profile=self.reliable_qos
        )
        self.ros_status_sub = self.create_subscription(
            Contacts,
            "_ros_status",
            self.record_ros_status,
            qos_profile=self.reliable_qos,
        )
        self.create_subscription(
            JointState,
            "joint_states",
            self._joint_states_callback,
            qos_profile=self.reliable_qos,
        )
        self.create_subscription(
            PoseStamped,
            "tcp_pose_raw",
            self._tcp_pose_callback,
            qos_profile=self.reliable_qos,
        )
        self.create_subscription(
            TFMessage, "tf", self._tf_callback, qos_profile=self.reliable_qos
        )
        self.create_subscription(
            String,
            "/_fruit_info",
            self._fruit_info_callback,
            qos_profile=self.reliable_qos,
        )
        self.create_subscription(
            String,
            "/_bad_fruit_positions",
            self._bad_fruit_positions_callback,
            qos_profile=self.reliable_qos,
        )

        self.create_timer(0.1, self.timer_loop)
        self.create_timer(5.0, self.node_topic_status_callback)

    # Callbacks
    def _tf_callback(self, msg):
        self.tf_msg = msg
        current_time = self.get_clock().now().nanoseconds
        if current_time - self.last_tf_write_time > 1e8:  # 100 ms
            self.last_tf_write_time = current_time
            self._write_bag("tf", msg)

    def _tcp_pose_callback(self, msg):
        self.tcp_pose_msg = msg
        current_time = self.get_clock().now().nanoseconds
        if current_time - self.last_tcp_pose_write_time > 1e8:  # 100 ms
            self.last_tcp_pose_write_time = current_time
            self._write_bag("tcp_pose_raw", msg)

    def _joint_states_callback(self, msg):
        self.joint_state_msg = msg
        current_time = self.get_clock().now().nanoseconds
        if current_time - self.last_joint_state_write_time > 1e8:  # 100 ms
            self.last_joint_state_write_time = current_time
            self._write_bag("joint_states", msg)

    def _fruit_info_callback(self, msg):
        self.fruit_info_msg = msg
        current_time = self.get_clock().now().nanoseconds
        if current_time - self.last_fruit_info_write_time > 1e8:  # 100 ms
            self.last_fruit_info_write_time = current_time
            self._write_bag("/_fruit_info", msg)

    def _bad_fruit_positions_callback(self, msg):
        self.bad_fruit_position_msg = msg
        current_time = self.get_clock().now().nanoseconds
        if current_time - self.last_bad_fruit_position_write_time > 1e8:  # 100 ms
            self.last_bad_fruit_position_write_time = current_time
            self._write_bag("/_bad_fruit_positions", msg)
    # Helper to write messages
    def _write_bag(self, topic_name, msg):
        timestamp = self.get_clock().now().nanoseconds
        self.writer.write(topic_name, serialize_message(msg), timestamp)

    def record_odom(self, msg):
        self.odom = msg

    def record_detection_status(self, msg):
        self.detection_status = msg
        self._write_bag("detection_status", self.detection_status)

    def record_shape_info(self, msg):
        self.shape_info = msg
        self._write_bag("_shape_info", self.shape_info)

    def record_clock(self, msg):
        self.gazebo_clock = msg
        current_time = self.get_clock().now().nanoseconds
        if current_time - self.last_gazebo_write_time > 1e8:  # 100 ms
            self.last_gazebo_write_time = current_time
            self._write_bag("clock", self.gazebo_clock)

    def record_cmd_vel(self, msg):
        self.twist_stamped_msg.twist = msg
        self.twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()
        self._write_bag("cmd_vel", self.twist_stamped_msg.twist)

    def record_ros_status(self, msg):
        self.ros_status = msg
        # self.writer.write('_ros_status', serialize_message(self.ros_status), self.get_clock().now().nanoseconds)

    def node_topic_status_callback(self):
        try:
            node_names = get_node_names(node=self, include_hidden_nodes=True)
            node_topic_info = {"nodes": {}}
            for node in node_names:
                # abs_node_name = get_absolute_node_name(str(node))
                # print("Node:", node, str(node), "Absolute Name:", abs_node_name)
                publishers = get_topics(
                    remote_node_name=node.full_name,
                    func=self.get_publisher_names_and_types_by_node,
                    include_hidden_topics=True,
                )
                node_topic_info["nodes"][f"{node.full_name}"] = dict(publishers)
            # Properly wrap JSON string into a ROS 2 String message before serialization
            node_topic_info_msg = String()
            node_topic_info_msg.data = json.dumps(node_topic_info)
            self.writer.write(
                "/_ros_node_topic_info",
                serialize_message(node_topic_info_msg),
                self.get_clock().now().nanoseconds,
            )
            # print(node_topic_info_msg.data)
            # Also publish for any live consumers
            # self.ros_info_pub.publish(node_topic_info_msg)
        except Exception as e:
            logging.exception(
                f"Exception in recording node topic info data: {e}", exc_info=True
            )
            # self.get_logger().info(f"Exception in recording node topic info data: {e}")
            # SystemExit

    def timer_loop(self):
        try:
            self.ebot_base_link_msg = self.tf_buffer.lookup_transform(
                "odom", "ebot_base_link", rclpy.time.Time()
            )
            self.odom_msg = PoseStamped()
            self.odom_msg.header = self.odom.header
            self.odom_msg.pose = self.odom.pose.pose

            self.get_logger().info(
                "\033[92m DATA COLLECTION STARTED FOR TASK 3B \033[00m", once=True
            )

            self.writer.write(
                "odom",
                serialize_message(self.odom_msg),
                self.get_clock().now().nanoseconds,
            )
            # try:
            #     self._write_bag("_shape_info", self.shape_info)
            # except:
            #     pass

            # try:
            #     self._write_bag(
            #         "clock",
            #         self.gazebo_clock)
            # except:
            #     pass
                
            # try:
            #     self._write_bag(
            #         "tcp_pose_raw",
            #         self.tcp_pose_msg)
            # except:
            #     pass

            # try:
            #     if (
            #         abs(
            #             self.twist_stamped_msg.header.stamp.sec
            #             - self.odom.header.stamp.sec
            #         )
            #         < 0.1
            #     ):
            #         self._write_bag(
            #             "cmd_vel",
            #             self.twist_stamped_msg,
            #         )
            # except:
            #     pass

            # try:
            #     self._write_bag(
            #         "joint_states",
            #         self.joint_state_msg)
            # except:
            #     pass

            # try:
            #     self._write_bag(
            #         "/_fruit_info",
            #         self.fruit_info_msg)
            # except:
            #     pass

            # try:
            #     self._write_bag(
            #         "/_bad_fruit_positions",
            #         self.bad_fruit_position_msg)
            # except:
            #     pass

            # try:
            #     self._write_bag(
            #         "tf",
            #         self.tf_msg)
            # except:
            #     pass

            try:
                if (
                    abs(self.ros_status.header.stamp.sec - self.odom.header.stamp.sec)
                    < 0.1
                ):
                    collision_info = {
                        "time": self.ros_status.header.stamp.sec
                        + self.ros_status.header.stamp.nanosec * 1e-9,
                        "collisions": {},
                    }
                    for id, collision in enumerate(self.ros_status.contacts):
                        collision_info["collisions"][f"{id}"] = {
                            "collision1": collision.collision1.name,
                            "collision2": collision.collision2.name,
                        }
                    # Properly wrap JSON string into a ROS 2 String message before serialization
                    collision_info_msg = String()
                    collision_info_msg.data = json.dumps(collision_info)

                    self._write_bag(
                        "_ros_status",
                        collision_info_msg,
                    )
            except Exception as e:
                self.get_logger().info(
                    f"Exception in recording collision data: {e}", once=True
                )
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
