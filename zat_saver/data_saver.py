# © 2026 Hochschule Bonn-Rhein-Sieg <https://www.h-brs.de/>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.
"""A ROS node that records selected sensor and pipeline topics to rosbag files on demand.

Subscribers:
- selected_topics_topic (std_msgs/String, default: '/saver/selected_topics'): comma/semicolon-separated list of topics (and types) to record
- recording_status_topic (std_msgs/String, default: '/saver/event_in'): start/stop recording events ('start'/'true' or 'stop'/'false')
Publishers:
- out_topic (std_msgs/String, default: '/saver/status'): current recording status (true/false)
- available_topics_topic (zat_ros2_msgs/TopicList, default: '/saver/available_topics'): list of predefined topics with their active status
Parameters:
- out_topic (str, default: '/saver/status')
- pub_period (float, default: 0.5)
- selected_topics_topic (str, default: '/saver/selected_topics')
- available_topics_topic (str, default: '/saver/available_topics')
- recording_status_topic (str, default: '/saver/event_in')
- rosbag_recording_external_dir (str, default: '/media/zat/sn-backup-1')
- rosbag_recording_local_dir (str, default: '~/zat_recordings')
Description:
This node maintains a predefined list of default topics from the ZAT sensor pipeline (game state,
emotions, poses, engagement score, camera image, Movella IMU data, eSense stream, EmotiBit
channels, and BCI/EEG data) and periodically publishes which of them are currently active. On
receiving a start event, it launches 'ros2 bag record' for the currently selected topics, saving
to an external drive if mounted or otherwise to a local directory; on a stop event it terminates
the recording process. The set of topics to record can be updated at runtime via the selected
topics subscriber, which restarts an in-progress recording with the new topic list.
Author:
Behrouz Ghamkhar <behrouz.ghamkhar@smail.inf.h-brs.de>
Michal Stolarz <michal.stolarz@h-brs.de>
"""

import os
import subprocess
from datetime import datetime

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from zat_ros2_msgs.msg import (
    BciData,
    EmotibitMsg,
    Emotions,
    EngagementScore,
    EsenseStream,
    GameEntry,
    GameEntryResult,
    MovellaData,
    Poses,
    TopicInfo,
    TopicList,
)


class DataSaver(Node):
    """Class representing a data saver for the sensor case pipeline."""

    def __init__(
            self,
            out_topic: str = '/saver/status',
            pub_period: float = 0.5,
            selected_topics_topic: str = '/saver/selected_topics',
            available_topics_topic: str = '/saver/available_topics',
            recording_status_topic: str = '/saver/event_in',
            rosbag_recording_external_dir: str = '/media/zat/sn-backup-1',
            rosbag_recording_local_dir: str = '~/zat_recordings'):
        """Initialize ROS components."""
        super().__init__('data_saver')

        # Declare parameters
        self.declare_parameters(
            namespace='',
            parameters=[
                ('out_topic', out_topic),
                ('pub_period', pub_period),
                ('available_topics_topic', available_topics_topic),
                ('selected_topics_topic', selected_topics_topic),
                ('recording_status_topic', recording_status_topic),
                ('rosbag_recording_external_dir', rosbag_recording_external_dir),
                ('rosbag_recording_local_dir', rosbag_recording_local_dir)
            ])

        self.pub_period = self.get_parameter('pub_period').value
        self.out_topic = self.get_parameter('out_topic').value
        self.available_topics_topic = self.get_parameter('available_topics_topic').value
        self.selected_topics_topic = self.get_parameter('selected_topics_topic').value
        self.recording_status_topic = self.get_parameter('recording_status_topic').value
        self.rosbag_recording_local_dir = self.get_parameter('rosbag_recording_local_dir').value
        self.rosbag_recording_external_dir = self.get_parameter('rosbag_recording_external_dir').value
        self.rosbag_process = None

        # Updated topics with your actual mappings
        self.default_topics = [
            ('/language_learning/game/controller/state', GameEntry),
            ('/language_learning/game/gui/state', GameEntryResult),
            ('/cam1/face/emotions', Emotions),
            ('/cam1/pose/landmarks', Poses),
            ('/cam1/engagement/score', EngagementScore),
            ('/camera/cam_1/color/image_raw', Image),
            ('/sensor/movella/imu_data', MovellaData),
            ('/sensor/esense/data', EsenseStream),
            ('/emotibit/acc', EmotibitMsg),
            ('/emotibit/gyro', EmotibitMsg),
            ('/emotibit/mag', EmotibitMsg),
            ('/emotibit/ppg', EmotibitMsg),
            ('/emotibit/eda', EmotibitMsg),
            ('/emotibit/temp', EmotibitMsg),
            ('/bci/eeg', BciData)
        ]

        self.active_topics = self.default_topics.copy()
        self.is_recording = False

        self.output_dir = self.rosbag_recording_local_dir

        # Status publisher
        self.status_publisher = self.create_publisher(String, self.out_topic, 10)
        self.timer = self.create_timer(self.pub_period, self._publish_status)

        # Topics publisher
        self.topics_publisher = self.create_publisher(TopicList, self.available_topics_topic, 10)
        self.topic_timer = self.create_timer(5.0, self._publish_topics)  # Update every 5 seconds

        # Event subscribers
        self.event_sub = self.create_subscription(
            String,
            self.recording_status_topic,
            self.event_callback,
            10)

        self.topics_sub = self.create_subscription(
            String,
            self.selected_topics_topic,
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
                topic_info.active = bool(self.get_publishers_info_by_topic(topic_name))
                topic_list.topics.append(topic_info)

            self.topics_publisher.publish(topic_list)
            self.get_logger().debug(f"Published topic list: {[(t.name, t.active) for t in topic_list.topics]}",
                                    throttle_duration_sec=5.0)

        except (RuntimeError, ValueError) as e:
            self.get_logger().error(f"Error in topic discovery: {e!r}")

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
        except ValueError as e:
            self.get_logger().error(f"Error parsing topics: {e!r}")

    def start_recording(self):
        """Record the active topics and save them in rosbag."""
        if self.is_recording:
            self.get_logger().warn("Recording already in progress")
            return

        timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
        bag_name = f"zat_recording_{timestamp}"

        self.output_dir = self.rosbag_recording_local_dir
        if os.path.ismount(self.rosbag_recording_external_dir):
            self.output_dir = self.rosbag_recording_external_dir + "/zat_recordings"

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
        """Stop recording."""
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
        except RuntimeError as err:
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
        selected_topics_topic='/saver/selected_topics',
        available_topics_topic='/saver/available_topics',
        rosbag_recording_external_dir='/media/zat/sn-backup-1',
        rosbag_recording_local_dir='~/zat_recordings',
        recording_status_topic='/saver/event_in')

    try:
        rclpy.spin(saver_node)
    except KeyboardInterrupt:
        pass
    finally:
        saver_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()