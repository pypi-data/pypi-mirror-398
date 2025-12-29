import os
import logging
from shutil import copyfile


class ExtLog:

    def __init__(self, name, path, level):
        self.__name__ = name
        self.__path__ = os.path.join(path, self.__name__)
        if not os.path.exists(self.__path__):
            os.makedirs(self.__path__)
        self.log = logging.getLogger(name)
        self.log_file = os.path.join(self.__path__, "%s.log" % self.__name__)
        formatter = logging.Formatter("%(levelname)s : %(asctime)s : %(message)s")
        fileHandler = logging.FileHandler(self.log_file, mode="w")
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)
        self.log.setLevel(level)
        self.log.addHandler(fileHandler)
        self.log.addHandler(streamHandler)


class PypeLogger(ExtLog):

    def __init__(self, name, path, profile, level=logging.INFO):
        ExtLog.__init__(self, name, path, level=level)
        self.log.info("Writing logs to folder %s", self.__path__)
        self.programs_logs = {}
        pype_env = [x for x in os.environ.keys() if x.startswith("PYPE")]
        for env_var in pype_env:
            self.log.info("%s=%s", env_var, os.environ[env_var])
        try:
            copyfile(profile.__path__, os.path.join(self.__path__, "profile.yaml"))
            self.log.info("Using profile %s", profile.__name__)
        except IOError as e:
            self.log.error("Profile IOError %s", e)
            raise e

    def add_log(self, name, level=logging.INFO):
        self.programs_logs[name] = ExtLog(name, self.__path__, level=level)
