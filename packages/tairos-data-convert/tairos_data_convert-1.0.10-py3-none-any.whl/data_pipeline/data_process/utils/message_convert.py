import numpy as np


def convert_message(msg, data_type=None):
    msg_type = type(msg).__name__
    if msg_type == "_sensor_msgs__CompressedImage":
        return convert_compressed_image(msg)
    if msg_type == "_data_msgs__ComponentObservation":
        return convert_component_observation(msg, data_type)
    if msg_type == "_data_msgs__ComponentAction":
        return convert_component_action(msg, data_type)
    if msg_type == "str":
        return msg

    raise ValueError(f"message type {msg_type} not supported")


def convert_compressed_image(msg):
    return np.frombuffer(msg.data, dtype=np.uint8)


def convert_component_observation(msg, data_type):
    if data_type == "pose":
        pose = msg.multibody_pose.pose
        return np.array([
            pose.position.x, pose.position.y, pose.position.z,
            pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w
        ])
    if data_type == "joint":
        return np.array([state_msg.q for state_msg in msg.multibody_state.states])
    raise ValueError(f"data_type {data_type} not supported")


def convert_component_action(msg, data_type):
    if data_type == "pose":
        pose = msg.pose_command.pose
        return np.array([
            pose.position.x, pose.position.y, pose.position.z,
            pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w
        ])
    if data_type == "joint":
        return np.array(msg.joint_commands)
    raise ValueError(f"data_type {data_type} not supported")
