from data_pipeline.data_process.utils.data_read import BagReader
from data_pipeline.data_process.utils.topic_mapping import get_data_for_value
from data_pipeline.data_process.utils.legacy_episode_state import modify_topic_to_msg_with_legacy_episode_states


def populate_dof(topic_to_msg, frame_structure, data_source):
    for key, value in frame_structure.items():
        dof = 0
        for v in value["values"]:
            data = get_data_for_value(topic_to_msg, v, data_source)
            if value["type"] == "float32":
                dof += data.shape[0]

        if value["type"] == "float32":
            frame_structure[key]["dof"] = dof
    return


def populate_dof_from_data(frame_structure, data_path, data_source, legacy_episode_states):
    with BagReader(data_path) as bag_reader:
        start_time = bag_reader.get_start_time()
        last_t = start_time
        topic_to_msg = {}
        last_error = ""
        for topic, msg, t in bag_reader.read_messages():
            modify_topic_to_msg_with_legacy_episode_states(topic_to_msg, t, legacy_episode_states)
            topic_to_msg[topic] = msg

            if t > start_time + 1:
                raise ValueError(f"Cannot get all required values in the first second, last error: {last_error}")

            if t > last_t + 0.1:
                last_t = t
                try:
                    populate_dof(topic_to_msg, frame_structure, data_source)
                except (KeyError, ValueError) as e:
                    last_error = str(e)
                    continue

                return

    raise ValueError(f"Cannot get all required values in the first second, last error: {last_error}")
