import os

from bluer_options import string

from bluer_ai.modules.terraform.functions import poster
from bluer_ai import env


def test_terraform_poster():
    filename = os.path.join(
        env.ABCLI_PATH_IGNORE,
        "background{}.jpg".format(string.timestamp()),
    )
    assert poster(filename)
