from bluer_options.env import load_config, load_env, get_env

load_env(__name__)
load_config(__name__)


abcli_is_github_workflow = get_env("GITHUB_ACTIONS")

abcli_display_fullscreen = get_env("abcli_display_fullscreen")

BLUER_AI_GIT_SSH_KEY_NAME = get_env("BLUER_AI_GIT_SSH_KEY_NAME")

bluer_ai_gpu_status_cache = get_env("bluer_ai_gpu_status_cache")

abcli_path_abcli = get_env("abcli_path_abcli")

ABCLI_PATH_IGNORE = get_env("ABCLI_PATH_IGNORE")

ABCLI_MLFLOW_STAGES = get_env("ABCLI_MLFLOW_STAGES")

BLUER_AI_GITHUB_TOKEN = get_env("BLUER_AI_GITHUB_TOKEN")
