import json
from io import BytesIO
from pathlib import Path
from typing import Dict, List
from zipfile import ZipFile

import httpx

from craftlet.utils.helperFunctions import CLIFunctions
from craftlet.utils.mappers import repoUrlToZipUrl


class CraftLet:
    @staticmethod
    async def getTemplateBytesGithub(repoUrl: str):
        zipUrl = repoUrlToZipUrl(repoUrl=repoUrl)

        async with httpx.AsyncClient() as client:
            response = await client.get(zipUrl)
            response.raise_for_status()
            zipBytes = response.content
        return zipBytes

    @staticmethod
    async def loadTemplateGithub(repoUrl: str, targetDir: Path, generateEnv: bool):
        # zipUrl = repoUrlToZipUrl(repoUrl=repoUrl)

        # async with httpx.AsyncClient() as client:
        #     response = await client.get(zipUrl)
        #     response.raise_for_status()
        #     zipBytes = response.content
        zipBytes = await CraftLet.getTemplateBytesGithub(repoUrl=repoUrl)

        CraftLet.diskWrite(
            inputBytes=zipBytes, targetDestination=targetDir, generateEnv=generateEnv
        )

    @staticmethod
    def diskWrite(inputBytes: bytes, targetDestination: Path, generateEnv: bool):
        with ZipFile(BytesIO(inputBytes)) as z:
            root = z.namelist()[0].split("/")[0]
            templateConfig = CraftLet.loadTemplateConfigFile(
                zipFileInstance=z, root=root
            )
            personalTemplateConfig, environmentVariables = (
                CLIFunctions.buildConfigFromDict(dictFile=templateConfig)
            )

            for name in z.namelist():
                if name.endswith("/") or name.endswith("templateConfig.json"):
                    continue
                relativePath = Path(name).relative_to(root)
                dest = targetDestination / relativePath
                dest.parent.mkdir(parents=True, exist_ok=True)

                rawText = z.read(name).decode()
                dest.write_text(rawText)
            if generateEnv:
                CraftLet.configureEnvironmentVariables(
                    environmentVariables=environmentVariables,
                    targetDir=targetDestination,
                )

    @staticmethod
    def loadTemplateConfigFile(zipFileInstance: ZipFile, root: str):
        try:
            raw = zipFileInstance.read(f"{root}/templateConfig.json").decode()
            return json.loads(raw)
        except KeyError:
            return {}

    @staticmethod
    def configureEnvironmentVariables(
        environmentVariables: Dict[str, str], targetDir: Path
    ):
        envPath = targetDir / ".env"
        lines: List[str] = []
        for key, value in environmentVariables.items():
            lines.append(f"{key}={value}")
        envPath.write_text(("\n").join(lines))
