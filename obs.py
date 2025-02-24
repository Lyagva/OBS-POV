# obs.py
import obsws_python as obs
import config

with config.lock:
    host = config.obs_host
    port = config.obs_port
    password = config.obs_password

# obs_client = obs.ReqClient(host=host, port=port, password=password)
obs_client = obs.ReqClient()

resp = obs_client.get_version()
print(f"OBS Version: {resp.obs_version}")


def get_scene_list():
    scenes = [i["sceneName"] for i in obs_client.get_scene_list().scenes][::-1]
    return scenes

def set_active_scene(scene_name: str):
    obs_client.set_current_program_scene(scene_name)


if __name__ == "__main__":
    get_scene_list()