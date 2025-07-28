"""Node for saving data from the ZAT sensor case pipeline."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import os
from datetime import datetime
from zat_ros2_msgs.msg import GameEntry, GameEntryResult, Emotions, Poses, EngagementScore, MovellaData, PhysioSensor
from sensor_msgs.msg import Image


class DataSaver(Node):
    """Class representing a data saver for the sensor case pipeline."""

    def __init__(
            self,
            out_topic: str = '/zat_saver/status',
            pub_period: float = 0.5):
        """Initialize ROS components."""
        super().__init__('data_saver')

        # Declare parameters
        self.declare_parameters(
            namespace='',
            parameters=[
                ('out_topic', out_topic),
                ('pub_period', pub_period)
            ])

        self.pub_period = self.get_parameter('pub_period').value
        self.out_topic = self.get_parameter('out_topic').value
        self.rosbag_process = None

        # Updated topics with your actual mappings
        self.default_topics = [
            ('/language_learning/game/controller/state', GameEntry),
            ('/language_learning/game/gui/state', GameEntryResult),
            ('/cam1/face/emotions', Emotions),
            ('/cam1/pose/landmarks', Poses),
            ('/cam1/engagement/score', EngagementScore),
            ('/camera/cam_1/color/image_raw', Image),
            ('/sensor/movella/data', MovellaData),
            ('/sensor/esense_data', PhysioSensor)
        ]

        self.active_topics = self.default_topics.copy()
        self.is_recording = False
        self.writer = None
        self.output_dir = os.path.expanduser('~/zat_recordings')
        os.makedirs(self.output_dir, exist_ok=True)

        # Status publisher
        self.status_publisher = self.create_publisher(String, self.out_topic, 10)
        self.timer = self.create_timer(self.pub_period, self._publish_status)

        # Event subscribers
        self.event_sub = self.create_subscription(
            String,
            '/zat_saver/event_in',
            self.event_callback,
            10)

        self.topics_sub = self.create_subscription(
            String,
            '/zat_saver/topics',
            self.topics_callback,
            10)

    def event_callback(self, msg: String):
        """Handle start/stop recording events."""
        if msg.data.lower() in ['true', 'start'] and not self.is_recording:
            self.start_recording()
        elif msg.data.lower() in ['false', 'stop'] and self.is_recording:
            self.stop_recording()

    def topics_callback(self, msg: String):
        """Update the list of topics to record."""
        try:
            # Expected format: "topic1,type1;topic2,type2"
            topics_list = []
            for item in msg.data.split(';'):
                if item:
                    topic, msg_type = item.split(',')
                    topics_list.append((topic.strip(), eval(msg_type.strip())))

            if topics_list:
                self.active_topics = topics_list
                self.get_logger().info(f"Updated topics to record: {self.active_topics}")
                if self.is_recording:
                    self.restart_recording()
        except Exception as e:
            self.get_logger().error(f"Error parsing topics: {str(e)}")

    def start_recording(self):
        """Records the active topics and save them in rosbag."""

        if self.is_recording:
            self.get_logger().warn("Recording already in progress")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bag_name = f"zat_recording_{timestamp}"
        bag_path = os.path.join(self.output_dir, bag_name)

        # Create topic list
        topic_args = [topic for topic, _ in self.active_topics]
        self.get_logger().info(f"topic list: {topic_args}")

        # Launch rosbag record
        cmd = ['ros2', 'bag', 'record', '-o', bag_path] + topic_args
        self.rosbag_process = subprocess.Popen(cmd)
        self.is_recording = True
        self.get_logger().info(f"Started rosbag recording to: {bag_path}")

    def stop_recording(self):
        """Stops recording."""
        if not self.is_recording:
            self.get_logger().warn("No active recording to stop")
            return

        if self.rosbag_process:
            self.rosbag_process.terminate()
            self.rosbag_process.wait()
            self.rosbag_process = None

        self.is_recording = False
        self.get_logger().info("Stopped rosbag recording")

    def restart_recording(self):
        """Restart recording with new topic list."""
        if self.is_recording:
            self.stop_recording()
            self.start_recording()


    def _publish_status(self):
        """Publish status of the component (active/not active)."""
        try:
            status_msg = String()
            status_msg.data = str(self.is_recording).lower()
            self.status_publisher.publish(status_msg)
        except Exception as err:
            self.get_logger().error(repr(err))

    def __del__(self):
        """Ensure recording is stopped when node is destroyed."""
        if self.is_recording:
            self.stop_recording()


def main():
    """Manage the ROS wrapper for the data saver."""
    rclpy.init(args=None)

    saver_node = DataSaver(
        out_topic='/zat_saver/status',
        pub_period=0.5)

    try:
        rclpy.spin(saver_node)
    except KeyboardInterrupt:
        pass
    finally:
        saver_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()