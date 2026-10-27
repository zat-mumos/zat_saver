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
"""ROS2 launch file for the standalone data saver (rosbag recording) node.

Nodes Launched:
- saver (zat_saver): records selected topics to rosbag files based on start/stop events
Parameters:
- pub_period (float, default: 4.0)
- out_topic (str, default: '/saver/status')
- selected_topics_topic (str, default: '/saver/selected_topics')
- available_topics_topic (str, default: '/saver/available_topics')
- recording_status_topic (str, default: '/saver/event_in')
- rosbag_recording_external_dir (str, default: '/media/zat/sn-backup-1')
- rosbag_recording_local_dir (str, default: '~/zat_recordings')
Description:
This launch file starts the 'saver' node on its own, configuring the topics used to report
status, list available topics, receive topic selections, and receive recording start/stop
events, along with the local and external directories used to store rosbag recordings.
Author:
Behrouz Ghamkhar <behrouz.ghamkhar@smail.inf.h-brs.de>
Michal Stolarz <michal.stolarz@h-brs.de>
"""

from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from launch import LaunchDescription


def generate_launch_description():
    pub_period_arg = DeclareLaunchArgument(
        'pub_period',
        default_value='4.0',
        description='Period of published messages'
    )

    out_topic_arg = DeclareLaunchArgument(
        'out_topic',
        default_value='/saver/status',
        description='Topic with the status of saver.'
    )

    selected_topics_topic_arg = DeclareLaunchArgument(
        'selected_topics_topic',
        default_value='/saver/selected_topics',
        description='Topic to configure data_saver topics for recording'
    )

    available_topics_arg = DeclareLaunchArgument(
        'available_topics_topic',
        default_value='/saver/available_topics',
        description='Topic to publish available topics list'
    )

    recording_status_topic_arg = DeclareLaunchArgument(
        'recording_status_topic',
        default_value='/saver/event_in',
        description='Topic to start and stop recording'
    )

    rosbag_recording_external_dir = DeclareLaunchArgument(
        'rosbag_recording_external_dir',
        default_value='/media/zat/sn-backup-1',
        description='Directory in which the rosbag recordings will be stored'
    )

    rosbag_recording_local_dir = DeclareLaunchArgument(
        'rosbag_recording_local_dir',
        default_value='~/zat_recordings',
        description='Directory in which the rosbag recordings will be stored'
    )

    saver_node = Node(
        package='zat_saver',
        executable='saver',
        name='saver',
        output='screen',
        parameters=[{
            'pub_period': LaunchConfiguration('pub_period'),
            'out_topic': LaunchConfiguration('out_topic'),
            'selected_topics_topic': LaunchConfiguration('selected_topics_topic'),
            'available_topics_topic': LaunchConfiguration('available_topics_topic'),
            'recording_status_topic': LaunchConfiguration('recording_status_topic'),
            'rosbag_recording_external_dir': LaunchConfiguration('rosbag_recording_external_dir'),
            'rosbag_recording_local_dir': LaunchConfiguration('rosbag_recording_local_dir')
        }]
    )

    return LaunchDescription([
        pub_period_arg,
        out_topic_arg,
        selected_topics_topic_arg,
        available_topics_arg,
        recording_status_topic_arg,
        rosbag_recording_external_dir,
        rosbag_recording_local_dir,
        saver_node
    ])