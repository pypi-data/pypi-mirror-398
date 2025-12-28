from data_pipeline.data_process.utils.data_read import BagReader


def get_legacy_episode_states(data_path: str):
    episode_states = []
    with BagReader(data_path) as bag_reader:
        topics = bag_reader.get_topics()

        if "episode_state" in topics:
            return []

        event_topic = None
        for topic in topics:
            if topic.endswith("/event"):
                event_topic = topic
                break
        if event_topic is None:
            return []

        last_timestamp = bag_reader.get_start_time()
        for topic, msg, t in bag_reader.read_messages(topics=[event_topic]):
            if msg.event_type == "step_finished":
                episode_states.append({
                    "timestamp": last_timestamp,
                    "event_detail": msg.event_detail,
                })
                last_timestamp = t

            if msg.event_type == "step_started":
                episode_states.append({
                    "timestamp": t,
                    "event_detail": msg.event_detail,
                })

    return episode_states


def modify_topic_to_msg_with_legacy_episode_states(topic_to_msg: dict, timestamp: float, legacy_episode_states: list):
    event_detail = None
    for episode_state in legacy_episode_states:
        if timestamp > episode_state["timestamp"]:
            event_detail = episode_state["event_detail"]

    if event_detail:
        topic_to_msg["episode_state"] = event_detail
