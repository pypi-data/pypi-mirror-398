from data_pipeline.data_process.utils.message_convert import convert_message


def get_data_for_value(topic_to_msg, value, data_source):
    if value in topic_to_msg:
        return convert_message(topic_to_msg[value])

    if data_source == 1:
        return get_umi_data_for_value(topic_to_msg, value)
    elif data_source == 2:
        return get_xtrainer_data_for_value(topic_to_msg, value)
    elif data_source == 3:
        return get_agibot_data_for_value(topic_to_msg, value)

    raise ValueError(f"value {value} not supported for data source {data_source}")


def get_umi_data_for_value(topic_to_msg, value):
    if value == "head/camera/color":
        return convert_message(topic_to_msg["/robot/data/head_realsense/color_image"])
    if value == "left_wrist/camera/color":
        return convert_message(topic_to_msg["/robot/data/left_hand_realsense/color_image"])
    if value == "right_wrist/camera/color":
        return convert_message(topic_to_msg["/robot/data/right_hand_realsense/color_image"])

    if value == "left_gripper/joint/state":
        return convert_message(topic_to_msg["/robot/data/changingtek_hand_left/observation"], data_type="joint")
    if value == "right_gripper/joint/state":
        return convert_message(topic_to_msg["/robot/data/changingtek_hand_right/observation"], data_type="joint")
    if value == "left_gripper/joint/command":
        return convert_message(topic_to_msg["/robot/data/changingtek_hand_left/action"], data_type="joint")
    if value == "right_gripper/joint/command":
        return convert_message(topic_to_msg["/robot/data/changingtek_hand_right/action"], data_type="joint")

    if value == "left_wrist/pose/state":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_left/observation"], data_type="pose")
    if value == "right_wrist/pose/state":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_right/observation"], data_type="pose")
    if value == "left_wrist/pose/command":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_left/action"], data_type="pose")
    if value == "right_wrist/pose/command":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_right/action"], data_type="pose")

    if value == "left_wrist/joint/state":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_left/observation"], data_type="joint")
    if value == "right_wrist/joint/state":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_right/observation"], data_type="joint")

    raise ValueError(f"value {value} not supported for umi data")


def get_agibot_data_for_value(topic_to_msg, value):
    if value == "head/camera/color":
        return convert_message(topic_to_msg["/robot/data/head_realsense/color_image"])
    if value == "left_wrist/camera/color":
        return convert_message(topic_to_msg["/robot/data/left_gripper/color_image"])
    if value == "right_wrist/camera/color":
        return convert_message(topic_to_msg["/robot/data/right_gripper/color_image"])

    if value == "left_gripper/joint/state":
        return convert_message(topic_to_msg["/robot/data/changingtek_hand_left/observation"], data_type="joint")
    if value == "right_gripper/joint/state":
        return convert_message(topic_to_msg["/robot/data/changingtek_hand_right/observation"], data_type="joint")
    if value == "left_gripper/joint/command":
        return convert_message(topic_to_msg["/robot/data/changingtek_hand_left/action"], data_type="joint")
    if value == "right_gripper/joint/command":
        return convert_message(topic_to_msg["/robot/data/changingtek_hand_right/action"], data_type="joint")

    if value == "left_wrist/pose/state":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_left/observation"], data_type="pose")
    if value == "right_wrist/pose/state":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_right/observation"], data_type="pose")
    if value == "left_wrist/pose/command":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_left/action"], data_type="pose")
    if value == "right_wrist/pose/command":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_right/action"], data_type="pose")

    if value == "left_wrist/joint/state":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_left/observation"], data_type="joint")
    if value == "right_wrist/joint/state":
        return convert_message(topic_to_msg["/robot/data/jaka_arm_right/observation"], data_type="joint")

    raise ValueError(f"value {value} not supported for agibot data")


def get_xtrainer_data_for_value(topic_to_msg, value):
    if value == "head/camera/color":
        return convert_message(topic_to_msg["/robot/data/head_realsense/color_image"])
    if value == "left_wrist/camera/color":
        return convert_message(topic_to_msg["/robot/data/left_hand_realsense/color_image"])
    if value == "right_wrist/camera/color":
        return convert_message(topic_to_msg["/robot/data/right_hand_realsense/color_image"])

    if value == "left_gripper/joint/state":
        if "/robot/data/left_hand/observation" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/left_hand/observation"], data_type="joint")
        return convert_message(topic_to_msg["/robot/data/aloha_left_hand/observation"], data_type="joint")
    if value == "right_gripper/joint/state":
        if "/robot/data/right_hand/observation" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/right_hand/observation"], data_type="joint")
        return convert_message(topic_to_msg["/robot/data/aloha_right_hand/observation"], data_type="joint")
    if value == "left_gripper/joint/command":
        if "/robot/data/left_hand/action" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/left_hand/action"], data_type="joint")
        return convert_message(topic_to_msg["/robot/data/aloha_left_hand/action"], data_type="joint")
    if value == "right_gripper/joint/command":
        if "/robot/data/right_hand/action" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/right_hand/action"], data_type="joint")
        return convert_message(topic_to_msg["/robot/data/aloha_right_hand/action"], data_type="joint")

    if value == "left_wrist/pose/state":
        if "/robot/data/left_arm/observation" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/left_arm/observation"], data_type="pose")
        return convert_message(topic_to_msg["/robot/data/aloha_left_arm/observation"], data_type="pose")
    if value == "right_wrist/pose/state":
        if "/robot/data/right_arm/observation" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/right_arm/observation"], data_type="pose")
        return convert_message(topic_to_msg["/robot/data/aloha_right_arm/observation"], data_type="pose")

    if value == "left_wrist/joint/state":
        if "/robot/data/left_arm/observation" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/left_arm/observation"], data_type="joint")
        return convert_message(topic_to_msg["/robot/data/aloha_left_arm/observation"], data_type="joint")
    if value == "right_wrist/joint/state":
        if "/robot/data/right_arm/observation" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/right_arm/observation"], data_type="joint")
        return convert_message(topic_to_msg["/robot/data/aloha_right_arm/observation"], data_type="joint")
    if value == "left_wrist/joint/command":
        if "/robot/data/left_arm/action" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/left_arm/action"], data_type="joint")
        return convert_message(topic_to_msg["/robot/data/aloha_left_arm/action"], data_type="joint")
    if value == "right_wrist/joint/command":
        if "/robot/data/right_arm/action" in topic_to_msg:
            return convert_message(topic_to_msg["/robot/data/right_arm/action"], data_type="joint")
        return convert_message(topic_to_msg["/robot/data/aloha_right_arm/action"], data_type="joint")

    raise ValueError(f"value {value} not supported for xtrainer data")
