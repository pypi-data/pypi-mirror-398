from bluer_objects import file, path

from bluer_ai.plugins.git import version


def test_git_increment_version():
    assert version.increment(
        path.absolute(
            "../../",
            file.path(__file__),
        )
    )
