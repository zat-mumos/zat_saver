"""Node for saving data from the ZAT sensor case pipeline."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import subprocess
import os
from datetime import datetime
from zat_ros2_msgs.msg import GameEntry, GameEntryResult, Emotions, Poses, EngagementScore, MovellaData, PhysioSensor, TopicInfo, TopicList
from sensor_msgs.msg import Image


class DataSaver(Node):
    """Class representing a data saver for the sensor case pipeline."""

    def __init__(
            self,
            out_topic: str = '/saver/status',
            pub_period: float = 0.5,
            topics_topic: str = '/saver/available_topics'):
        """Initialize ROS components."""
        super().__init__('data_saver')

        # Declare parameters
        self.declare_parameters(
            namespace='',
            parameters=[
                ('out_topic', out_topic),
                ('pub_period', pub_period),
                ('topics_topic', topics_topic)
            ])

        self.pub_period = self.get_parameter('pub_period').value
        self.out_topic = self.get_parameter('out_topic').value
        self.topics_topic = self.get_parameter('topics_topic').value
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
        self.output_dir = os.path.expanduser('~/zat_recordings')
        os.makedirs(self.output_dir, exist_ok=True)

        # Status publisher
        self.status_publisher = self.create_publisher(String, self.out_topic, 10)
        self.timer = self.create_timer(self.pub_period, self._publish_status)

        # Topics publisher
        self.topics_publisher = self.create_publisher(TopicList, self.topics_topic, 10)
        self.topic_timer = self.create_timer(5.0, self._publish_topics)  # Update every 5 seconds

        # Event subscribers
        self.event_sub = self.create_subscription(
            String,
            '/saver/event_in',
            self.event_callback,
            10)

        self.topics_sub = self.create_subscription(
            String,
            '/saver/topics',
            self.topics_callback,
            10)

    def _publish_topics(self):
        """Publish the list of predefined default topics with their active status."""
        try:
            # Prepare topic list message
            topic_list = TopicList()

            for topic_name, topic_type in self.default_topics:
                topic_info = TopicInfo()
                topic_info.name = topic_name
                topic_info.type = str(topic_type)
                topic_info.active = True if self.get_publishers_info_by_topic(topic_name) else False
                topic_list.topics.append(topic_info)

            self.topics_publisher.publish(topic_list)
            self.get_logger().debug(f"Published topic list: {[(t.name, t.active) for t in topic_list.topics]}",
                                    throttle_duration_sec=5.0)

        except Exception as e:
            self.get_logger().error(f"Error in topic discovery: {str(e)}")

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
                    # Find matching default topic
                    matching_topic = next((t for t in self.default_topics
                                           if t[0] == topic.strip() and str(t[1]) == msg_type.strip()), None)
                    if matching_topic:
                        topics_list.append(matching_topic)
                    else:
                        self.get_logger().error(f"Topic not available for recording: {topic} ({msg_type})")

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
        self.get_logger().info(f"Starting recording with topics: {topic_args}")

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
        out_topic='/saver/status',
        pub_period=0.5,
        topics_topic='/saver/available_topics')

    try:
        rclpy.spin(saver_node)
    except KeyboardInterrupt:
        pass
    finally:
        saver_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
