"""File containing all the code pertaining to the configuration of the app"""

from appdirs import AppDirs
from parser.parser import evaluate

dirs = AppDirs("youtube_cli", "sofamaniac")
with open(dirs.user_config_dir + "/youtube_cli.init", "a+") as config_file:
    config_file.seek(0)
    config = config_file.readlines()
    config = "".join(config)
    evaluate(config)
