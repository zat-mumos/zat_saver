
# zat_saver

ROS 2 package for recording sensor data from the ZAT pipeline to rosbag2 files.

## Features

- Records multiple message types simultaneously  
- Dynamic topic configuration during runtime  
- Simple start/stop control via ROS topics  
- Configurable through parameters  
- Status monitoring capability  

## Supported Messages and Topics

| Message Type                     | Default Topic                                      |
|---------------------------------|----------------------------------------------------|
| `GameEntry`        | `/language_learning/game/controller/state`         |
| `GameEntryResult`  | `/language_learning/game/gui/state`                |
| `Emotions`         | `/cam1/face/emotions`                              |
| `Poses`            | `/cam1/pose/landmarks`                             |
| `EngagementScore`  | `/cam1/engagement/score`                           |
| `Image`              | `/camera/cam_1/color/image_raw`                    |
| `MovellaData`      | `/sensor/movella/data`                             |
| `PhysioSensor`     | `/sensor/esense_data`                              |
| `EmotibitMsg`     | `/emotibit/acc`<br>`/emotibit/gyro`<br>`/emotibit/mag`<br>`/emotibit/ppg`<br>`/emotibit/eda`<br>`/emotibit/temp`                              |
| `BciData`     | `/bci/eeg`                              |

## Table of Contents

1. [Installation](#installation)  
2. [Usage](#usage)  
   - [Basic Operation](#basic-operation)  
   - [Topic Configuration](#topic-configuration)  
   - [Parameters](#parameters)  
3. [Output](#output)  
4. [License](#license)  

---

## Installation

### Prerequisites

- ROS 2 Humble (or newer)  
- Python 3.8+  

### Build Instructions

```bash
cd zat_ws/src

# Clone the package
git clone git@git.inf.h-brs.de:zat-rhein-ruhr/zat-prototype-demo/zat_saver.git

# Install dependencies
cd zat_saver
pip install -r requirements.txt

# Build the package
cd ../..   #(zat_ws)
colcon build --packages-select zat_saver
source install/setup.bash
```

---

## Usage

### Basic Operation

Using the launch file:

```bash
ros2 launch zat_saver saver.py
```

Control recording:

```bash
# Start recording
ros2 topic pub --once /zat_saver/event_in std_msgs/msg/String "{data: 'true'}"

# Stop recording
ros2 topic pub --once /zat_saver/event_in std_msgs/msg/String "{data: 'false'}"
```

---

### Topic Configuration

**Default Behavior**  
Records all supported topics listed in the table above.

**Custom Topic Selection**  

```bash
ros2 topic pub /zat_saver/topics std_msgs/msg/String "{data: '/camera/cam_1/color/image_raw,Image;/language_learning/game/controller/state,GameEntry'}"
```

**Format Specifications:**

```text
"<topic1>,<message_type1>;<topic2>,<message_type2>"
```

**Example with multiple topics:**

```bash
ros2 topic pub /zat_saver/topics std_msgs/msg/String "{data: '/cam1/face/emotions,Emotions;/cam1/pose/landmarks,Poses;/cam1/engagement/score,EngagementScore'}"
```

---

### Parameters

**Available Parameters:**

| Parameter      | Type    | Default             | Description                          |
|----------------|---------|---------------------|--------------------------------------|
| `status_topic` | string  | `/zat_saver/status` | Topic for publishing recorder status |


---

## Status Monitoring

The node continuously publishes its status:

```bash
ros2 topic echo /zat_saver/status
```

### Status check
`zat_saver` continuously publishas a message of type `String.msg` on the topic `/zat_saver/status`, with the following content:
- `{data: 'false'}` if the component is deactivated
- `{data: 'true'}` if the component is activated

## Output

- **Location**: `~/zat_recordings/`  
- **Naming Format**: `zat_recording_<timestamp>`  


---

## License

`zat_saver` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.