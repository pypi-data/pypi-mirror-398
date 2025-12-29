import os
import platform
from io import StringIO
from pathlib import Path
from typing import Dict

import typer


class CLIFunctions:
    @staticmethod
    def buildConfigFromDict(dictFile: Dict):
        environmentVariables = {}
        prefixName = StringIO()
        for key, value in dictFile.items():
            beforeLength = len(prefixName.getvalue())
            prefixName.write(key.upper().replace(" ", "_"))
            if "input" in value:
                userInput = typer.prompt(value.get("prompt", key))
                value["input"] = userInput
                if "isEnv" in value and value.get("isEnv", False):
                    environmentVariables[prefixName.getvalue()] = userInput
            else:
                CLIFunctions.nestedBuildFromDict(
                    dictFile=value,
                    environmentVariables=environmentVariables,
                    prefixName=prefixName,
                )
            prefixName.truncate(beforeLength)
            prefixName.seek(beforeLength)
        return (dictFile, environmentVariables)

    @staticmethod
    def nestedBuildFromDict(
        dictFile: Dict, environmentVariables: Dict[str, str], prefixName: StringIO
    ):
        for key, value in dictFile.items():
            beforeLength = len(prefixName.getvalue())
            prefixName.write(".")
            prefixName.write(key.upper().replace(" ", "_"))
            if "input" in value:
                userInput = typer.prompt(value.get("prompt", key))
                value["input"] = userInput
                if "isEnv" in value and value.get("isEnv", False):
                    environmentVariables[prefixName.getvalue()] = userInput
            else:
                CLIFunctions.nestedBuildFromDict(
                    dictFile=value,
                    environmentVariables=environmentVariables,
                    prefixName=prefixName,
                )
            prefixName.truncate(beforeLength)
            prefixName.seek(beforeLength)


class CacheFunction:
    @staticmethod
    def getOSCacheDir():
        system = platform.system()
        match system:
            case "Windows":
                return Path(os.environ["LOCALAPPDATA"])
            case "Darwin":
                return Path.home() / "Library" / "Caches"
            case _:
                return Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
