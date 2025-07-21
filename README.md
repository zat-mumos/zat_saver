# zat_saver

Package for storing the data from the zat sensor case pipeline.
It accepts the following messages (on the corresponding topics) and saves them as rosbag files.
- `GameEntry.msg` (zat_ros2_msgs)
- `GameEntryResult.msg` (zat_ros2_msgs)
- `Emotions.msg` (zat_ros2_msgs)
- `Poses.msg` (zat_ros2_msgs)
- `EngagementScore.msg` (zat_ros2_msgs)
- `Image.msg`
- `MovellaData.msg` (zat_ros2_msgs)
- `PhysioSensor.msg` (zat_ros2_msgs)


## Table of Contents

- [Installation](#installation)
- [Running](#running)
- [License](#license)

## Installation

### Python dependencies
```console
pip install -r requirements.txt
```

### Building the package
```console
cd zat_ws/src
colcon build
```

## Running
### Using zat_saver
Run the ROS node:
```console
ros2 run zat_saver saver
```

Run the ROS launch:
```console
ros2 launch zat_saver saver.py
```

### Trigerring zat_saver
To start saving:
```console
ros2 topic pub /zat_saver/event_in std_msgs/msg/String "{data: 'true'}"
```

To stop saving:
```console
ros2 topic pub /zat_saver/event_in std_msgs/msg/String "{data: 'false'}"
```

### Configuring zat_saver
Specify what topics `zat_saver` should listen to:
```console
ros2 topic pub /zat_saver/topics std_msgs/msg/String "{data: '[(/camera/cam_1/color/image_raw, Image.msg), (...), ...]'}"
```

**Important!** By default `zat_saver` listens to all the topics and saves all the messages mentioned in the introduction.

### ROS parameters
`zat_saver` exposes the following parameters (that can be set in a launch file):
- topic name of the status topic (read below)
- subscription frequency (of the data to be saved)

### Status check
`zat_saver` continuously publishas a message of type `String.msg` on the topic `/zat_saver/status`, with the following content:
- `{data: 'false'}` if the component is deactivated
- `{data: 'true'}` if the component is activated

## License

`zat_saver` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.