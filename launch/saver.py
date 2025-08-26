from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


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

    rosbag_recording_dir = DeclareLaunchArgument(
        'rosbag_recording_dir',
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
            'rosbag_recording_dir': LaunchConfiguration('rosbag_recording_dir')
        }]
    )

    return LaunchDescription([
        pub_period_arg,
        out_topic_arg,
        selected_topics_topic_arg,
        available_topics_arg,
        recording_status_topic_arg,
        rosbag_recording_dir,
        saver_node
    ])