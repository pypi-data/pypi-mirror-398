from bluer_ai.help.generic import help_functions as generic_help_functions
from bluer_ai.help.actions import help_perform_action
from bluer_ai.help.assert_ import help_functions as help_assert
from bluer_ai.help.blueness import help_blueness
from bluer_ai.help.browse import help_browse
from bluer_ai.help.code import help_code
from bluer_ai.help.conda import help_functions as help_conda
from bluer_ai.help.env import help_functions as help_env
from bluer_ai.help.eval import help_eval
from bluer_ai.help.git import help_functions as help_git
from bluer_ai.help.gpu import help_functions as help_gpu
from bluer_ai.help.help import help_help
from bluer_ai.help.hr import help_hr
from bluer_ai.help.init import help_init
from bluer_ai.help.instance import help_functions as help_instance
from bluer_ai.help.latex import help_functions as help_latex
from bluer_ai.help.logging import help_cat
from bluer_ai.help.logging import help_functions as help_log
from bluer_ai.help.list import help_functions as help_list
from bluer_ai.help.not_ import help_not
from bluer_ai.help.open import help_open
from bluer_ai.help.options import help_functions as help_option
from bluer_ai.help.pause import help_pause
from bluer_ai.help.plugins import help_functions as help_plugins
from bluer_ai.help.repeat import help_repeat
from bluer_ai.help.sagemaker import help_functions as help_sagemaker
from bluer_ai.help.screen import help_functions as help_screen
from bluer_ai.help.seed import help_functions as help_seed
from bluer_ai.help.select import help_select
from bluer_ai.help.session import help_functions as help_session
from bluer_ai.help.ssh import help_functions as help_ssh
from bluer_ai.help.string import help_functions as help_string
from bluer_ai.help.storage import help_functions as help_storage
from bluer_ai.help.sleep import help_sleep
from bluer_ai.help.source import (
    help_source_caller_suffix_path,
    help_source_path,
)
from bluer_ai.help.terminal import help_badge
from bluer_ai.help.terraform import help_functions as help_terraform
from bluer_ai.help.wait import help_wait
from bluer_ai.help.watch import help_watch
from bluer_ai.help.wifi import help_functions as help_wifi

help_functions = generic_help_functions(plugin_name="bluer_ai")


help_functions.update(
    {
        "assert": help_assert,
        "badge": help_badge,
        "blueness": help_blueness,
        "browse": help_browse,
        "cat": help_cat,
        "code": help_code,
        "conda": help_conda,
        "env": help_env,
        "eval": help_eval,
        "git": help_git,
        "gpu": help_gpu,
        "help": help_help,
        "hr": help_hr,
        "init": help_init,
        "instance": help_instance,
        "latex": help_latex,
        "log": help_log,
        "list": help_list,
        "not": help_not,
        "open": help_open,
        "option": help_option,
        "pause": help_pause,
        "perform_action": help_perform_action,
        "plugins": help_plugins,
        "repeat": help_repeat,
        "sagemaker": help_sagemaker,
        "screen": help_screen,
        "seed": help_seed,
        "select": help_select,
        "sleep": help_sleep,
        "session": help_session,
        "storage": help_storage,
        "source_caller_suffix_path": help_source_caller_suffix_path,
        "source_path": help_source_path,
        "ssh": help_ssh,
        "string": help_string,
        "terraform": help_terraform,
        "wait": help_wait,
        "watch": help_watch,
        "wifi": help_wifi,
    }
)
