import cv2
import numpy as np
from rclpy.node import Node
from geometry_msgs.msg import Point
from nav_msgs.msg import OccupancyGrid
import rclpy


class BlobFinder(Node):
    def __init__(self):
        super().__init__('blob_finder')  # Initialize the node
        self.publisher_ = self.create_publisher(Point, '/bright_point', 10)  # Publisher for centroid
        self.map_subscription = self.create_subscription(
            OccupancyGrid,
            '/light_grid',
            self.map_callback,
            10
        )

    def map_callback(self, msg):
        """Callback to process the OccupancyGrid and find the centroid of the largest blob."""
        try:
            # Convert OccupancyGrid data to a 2D numpy array
            grid = np.array(msg.data, dtype=np.int8).reshape((msg.info.height, msg.info.width))

            # Debug grid properties
            self.get_logger().info(f"Grid Resolution: {msg.info.resolution}, Origin: ({msg.info.origin.position.x}, {msg.info.origin.position.y})")
            self.get_logger().info(f"Grid Size: {msg.info.width}x{msg.info.height}")

            # Normalize grid to binary image
            binary_grid = ((grid > 0) * 255).astype(np.uint8)

            # Find contours
            contours, _ = cv2.findContours(binary_grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Find the largest contour
                largest_contour = max(contours, key=cv2.contourArea)

                # Calculate the centroid of the largest blob
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])  # Centroid x in pixels
                    cy = int(M["m01"] / M["m00"])  # Centroid y in pixels

                    # Convert pixel coordinates to world coordinates
                    world_x = cx * msg.info.resolution + msg.info.origin.position.x
                    world_y = (msg.info.height - cy) * msg.info.resolution + msg.info.origin.position.y

                    # Debug centroid calculation
                    self.get_logger().info(f"Centroid (grid): ({cx}, {cy})")
                    self.get_logger().info(f"Centroid (world): ({world_x}, {world_y})")

                    # Publish the centroid
                    point = Point()
                    point.x = float(cx)
                    point.y = float(cy)
                    point.z = 0.0
                    self.publisher_.publish(point)

                else:
                    self.get_logger().warning("Largest blob has zero area.")
            else:
                self.get_logger().warning("No blobs found in the grid.")

        except Exception as e:
            self.get_logger().error(f"Error processing light grid: {e}")


def main(args=None):
    rclpy.init(args=args)
    blob_finder = BlobFinder()
    rclpy.spin(blob_finder)

    blob_finder.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
