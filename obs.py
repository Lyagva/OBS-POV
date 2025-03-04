import obsws_python as obs
import config

# Acquire lock to safely read configuration values
with config.lock:
    host = config.obs_host
    port = config.obs_port
    password = config.obs_password

# Initialize OBS WebSocket client with the given connection parameters
obs_client = obs.ReqClient(host=host, port=port, password=password)

# Retrieve and print the OBS Studio version
resp = obs_client.get_version()
print(f"OBS Version: {resp.obs_version}")


def get_scene_list():
    """
    Fetch and return a list of available scenes from OBS Studio.
    The list is reversed to maintain a specific order.

    Returns:
        list: A list of scene names available in OBS Studio.
    """
    scenes = [i["sceneName"] for i in obs_client.get_scene_list().scenes][::-1]
    return scenes


def set_active_scene(scene_name: str):
    """
    Set the active scene in OBS Studio to the specified scene name.

    Args:
        scene_name (str): The name of the scene to activate.
    """
    obs_client.set_current_program_scene(scene_name)


if __name__ == "__main__":
    """
    If the script is run directly, retrieve the list of scenes.
    """
    get_scene_list()