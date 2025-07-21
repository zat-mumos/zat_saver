"""Node for saving data from the ZAT sensor case pipeline."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class DataSaver(Node):
    """Class representing a data saver for the sensor case pipeline."""

    def __init__(
            self,
            out_topic: str = '/zat_saver/status',
            pub_period: float = 0.5):
        """Initialize ROS components."""
         
        super().__init__('data_saver')

        self.declare_parameters(
            namespace='',
            parameters = [
                ('out_topic', out_topic),
                ('pub_period', pub_period)
            ])
        
        pub_period = self.get_parameter('pub_period').value
        out_topic = self.get_parameter('out_topic').value

        # game speech publisher
        self._status_publisher = self.create_publisher(String, out_topic, 10)
        # timer
        self._timer = self.create_timer(pub_period, self._publish_status)

    def _publish_status(self):
        """Publish status of the component (active/not active)."""
        try:
            status_msg = String()
            status_msg.data = 'false'
            self._speech_publisher.publish(status_msg)
               
        except Exception as err:
            self.get_logger().error(repr(err))

        finally:
            self._game_controller_status = None

def main():
    """Manage the ROS wrapper for the data saver."""
    rclpy.init(args=None)
    
    saver_node = DataSaver(
        out_topic='/zat_saver/status',
        pub_period=0.5)
    
    rclpy.spin(saver_node)

    saver_node.destroy_node()

    rclpy.shutdown()

if __name__ == '__main__':
    main()