ALL OF THE BELOW IN ONE COMMAND (after: colcon build --symlink-install && source install/setup.bash):

ros2 launch scout_mini_nav bringup.launch.py
  options: rviz:=false slam:=false laser_projector:=false
           render_rate_hz:=0 stream_frames:=false   (old one-shot laser mode)
           lidar_x:=0.206 lidar_y:=-0.085 lidar_z:=0.10   (lidar mount, metres)
           lidar_angle_min:=-1.5707963 lidar_angle_max:=1.5707963   (scan window, radians; front 180 deg)

INDIVIDUAL COMMANDS (what bringup.launch.py runs):


CHECK CAN: candump can0


ros2 launch scout_base scout_base.launch.py     is_scout_mini:=true is_omni_wheel:=false port_name:=can0

ros2 launch scout_mini_nav custom_navigation.launch.py params_file:=src/scout_mini_nav/config/nav2_params.yaml use_sim_time:=False

ros2 launch nav2_bringup rviz_launch.py
SET FIXED FRAME TO ODOM IN RVIZ

ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false

ros2 run urg_node urg_node_driver --ros-args -p serial_port:=/dev/ttyACM0 -p laser_frame_id:=laser -p angle_min:=-1.5707963 -p angle_max:=1.5707963

ros2 run tf2_ros static_transform_publisher --x 0.206 --y -0.085 --z 0.10 --frame-id base_link --child-frame-id laser

 ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link base_footprint

 ros2 launch laser_projection_ros laser_projection.launch.py


eventually add ros2 launch astra_camera astra_mini.launch.py but not doing anything with it right now, later i need to make a person detector and then use that information somehow