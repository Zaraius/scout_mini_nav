"""Whole robot in one command: base, lidar, TF, SLAM, Nav2, RViz, laser projector.

    ros2 launch scout_mini_nav bringup.launch.py
    ros2 launch scout_mini_nav bringup.launch.py rviz:=false slam:=false
    ros2 launch scout_mini_nav bringup.launch.py render_rate_hz:=0 stream_frames:=false

Check CAN first (needs sudo, so it is not in here):  candump can0

Frames (REP-105 style, all in metres, x forward / y left / z up):
    odom -> base_link          scout_base_node (wheel odometry)
    base_link -> laser         static, Hokuyo mount (lidar_x/y/z args)
    base_link -> base_footprint static identity (same as the Scout URDF; slam_toolbox uses it)
    map -> odom                slam_toolbox (only if slam:=true; Nav2 itself plans in odom)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def include(package, launch_file, arguments, condition=None):
    path = os.path.join(get_package_share_directory(package), "launch", launch_file)
    return IncludeLaunchDescription(PythonLaunchDescriptionSource(path),
                                    launch_arguments=arguments.items(), condition=condition)


def generate_launch_description():
    nav_share = get_package_share_directory("scout_mini_nav")
    arg = LaunchConfiguration
    args = [
        DeclareLaunchArgument("rviz", default_value="true"),
        DeclareLaunchArgument("slam", default_value="true"),
        DeclareLaunchArgument("laser_projector", default_value="true"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/ttyACM0"),
        # Lidar: 10 cm behind the front edge (Scout Mini ~0.612 m long, so the front edge
        # is ~0.306 m ahead of base_link), 8.5 cm right of centre (right = -y), 10 cm up.
        DeclareLaunchArgument("lidar_x", default_value="0.206"),
        DeclareLaunchArgument("lidar_y", default_value="-0.085"),
        DeclareLaunchArgument("lidar_z", default_value="0.10"),
        # Scan window in radians, 0 = straight ahead, + = left. The Hokuyo covers 240 deg
        # (blind 120 deg at the back notch); keep only the front 180 deg (+-90 deg) so the
        # camera behind/left of the lidar does not show up as an obstacle.
        DeclareLaunchArgument("lidar_angle_min", default_value="-1.5707963"),
        DeclareLaunchArgument("lidar_angle_max", default_value="1.5707963"),
        # Laser projector flags (see laser_intent README).
        DeclareLaunchArgument("render_rate_hz", default_value="30"),
        DeclareLaunchArgument("stream_frames", default_value="true"),
    ]

    robot = [
        include("scout_base", "scout_base.launch.py",
                {"is_scout_mini": "true", "is_omni_wheel": "false", "port_name": "can0"}),
        Node(package="urg_node", executable="urg_node_driver", name="urg_node", output="screen",
             parameters=[{"serial_port": arg("lidar_port"), "laser_frame_id": "laser",
                          "angle_min": arg("lidar_angle_min"),
                          "angle_max": arg("lidar_angle_max")}]),
        Node(package="tf2_ros", executable="static_transform_publisher", name="lidar_tf",
             arguments=["--x", arg("lidar_x"), "--y", arg("lidar_y"), "--z", arg("lidar_z"),
                        "--frame-id", "base_link", "--child-frame-id", "laser"]),
        Node(package="tf2_ros", executable="static_transform_publisher", name="footprint_tf",
             arguments=["--frame-id", "base_link", "--child-frame-id", "base_footprint"]),
    ]

    # Start the consumers once odometry/lidar/TF are up, to avoid a burst of
    # "frame does not exist" warnings while they wait for TF.
    consumers = TimerAction(period=3.0, actions=[
        include("slam_toolbox", "online_async_launch.py",
                {"use_sim_time": "false",
                 "slam_params_file": os.path.join(nav_share, "config", "slam_params.yaml")},
                condition=IfCondition(arg("slam"))),
        include("scout_mini_nav", "custom_navigation.launch.py",
                {"params_file": os.path.join(nav_share, "config", "nav2_params.yaml"),
                 "use_sim_time": "False"}),
        include("nav2_bringup", "rviz_launch.py",
                {"rviz_config": os.path.join(nav_share, "rviz", "nav2_odom_view.rviz")},
                condition=IfCondition(arg("rviz"))),
        include("laser_projection_ros", "laser_projection.launch.py",
                {"render_rate_hz": arg("render_rate_hz"),
                 "stream_frames": arg("stream_frames")},
                condition=IfCondition(arg("laser_projector"))),
    ])

    return LaunchDescription(args + robot + [consumers])
