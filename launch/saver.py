from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pub_period_arg = DeclareLaunchArgument(
        'pub_period',
        default_value='0.5',
        description='Period of published messages'
    )
    
    out_topic_arg = DeclareLaunchArgument(
        'out_topic',
        default_value='/saver/status',
        description='Topic with the status of saver.'
    )
    
    saver_node = Node(
        package='zat_saver',
        executable='saver',
        name='saver',
        output='screen',
        parameters=[{
            'pub_period': LaunchConfiguration('pub_period'),
            'out_topic': LaunchConfiguration('out_topic')
        }]
    )

    return LaunchDescription([
        pub_period_arg,
        out_topic_arg,
        saver_node
    ])