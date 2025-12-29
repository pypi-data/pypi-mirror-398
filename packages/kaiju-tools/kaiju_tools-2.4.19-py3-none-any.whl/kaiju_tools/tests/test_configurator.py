import os
import uuid
from importlib.resources import files

from kaiju_tools.app import ConfigLoader


RESOURCES = files('kaiju_tools.tests.resources')


def test_config_loader(tmp_path, logger):
    RESOURCES.iterdir()
    configurator = ConfigLoader(
        base_config_paths=[str(RESOURCES / 'sample_config.yml')], base_env_paths=[str(RESOURCES / 'sample_env.json')]
    )
    os_env_var = uuid.uuid4().hex
    os.environ['etc_system_locale'] = os_env_var
    cmd, config = configurator.configure()
    logger.debug(config)
    os.unsetenv('etc_system_locale')
    assert config['etc']['system_locale'] == os_env_var, 'must update env vars from OS'
