# Azure import is dropped because we need to to do runtime import of azure module to support our package running on Snowflake Notebook
from . import config, snowflake, client, local

# note: user must do `import relationalai.clients.azure` to get `azure` submodule
__all__ = ['snowflake', 'config', 'client', 'local']
