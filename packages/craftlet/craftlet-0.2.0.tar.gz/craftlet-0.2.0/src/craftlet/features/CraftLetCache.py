import hashlib
import sys
import tarfile
from io import BytesIO
from pathlib import Path
from tarfile import TarInfo
from zipfile import ZipFile

import cbor2
import typer

from craftlet.models.Cacheable import Cacheable, GithubTemplate, GithubTemplateReference
from craftlet.utils.exceptions import CraftLetException
from craftlet.utils.hashUtils import HashWriter
from craftlet.utils.mappers import cborGithubTemplateReferenceEncoder


class CraftLetCache:
    @staticmethod
    def isRunningInEnvironment():
        currentPrefix = sys.prefix
        basePrefix = sys.base_prefix

        if basePrefix != currentPrefix:
            return True
        return False

    @staticmethod
    def showCache(cacheDir: Path):
        if cacheDir.exists():
            typer.echo(f"📦 Cache location: {cacheDir}\n")
            dirArr = list(cacheDir.iterdir())
            dirSize = len(dirArr)
            for index, entry in enumerate(dirArr):
                connector = "└── " if index == dirSize - 1 else "├── "
                typer.echo(connector + entry.name)
        else:
            typer.echo(f"📦 Cache location: {cacheDir} don't exist")

    # ============================================================================
    # OFFLINE CACHE METHODS
    # ============================================================================
    @staticmethod
    def cacheOffline(path: Path, data: Cacheable):
        match data:
            case GithubTemplateReference():
                CraftLetCache.cacheGithubTemplateRefrence(data=data, path=path)
            case GithubTemplate():
                CraftLetCache.cacheGithubTemplate(data=data, path=path)
            case _:
                raise CraftLetException(
                    f"An unidentified cacheable data(type: {type(data).__name__}) is requested."
                )

    @staticmethod
    def cacheGithubTemplateRefrence(data: Cacheable, path: Path):
        exactPath = (
            path
            / "craftlet"
            / ".cache"
            / "offline"
            / "template"
            / "github-reference"
            / data.name
        )
        cborBinary = cbor2.dumps(obj=data, default=cborGithubTemplateReferenceEncoder)

        with open(exactPath, "wb") as f:
            for byte in cborBinary:
                f.write(bytes([byte]))

    @staticmethod
    def cacheGithubTemplate(data: Cacheable, path: Path):
        zipBuffer = BytesIO(data.coreData)
        exactPath = (
            path / "craftlet" / ".cache" / "offline" / "template" / "github" / data.name
        )
        tarFilePath = exactPath / "template.tar.gz"
        tarFilePath.parent.mkdir(parents=True, exist_ok=True)
        hashFilePath = exactPath / "template.sha256"
        isHashAvailable = True

        if data.payload and data.payload.get("sha256Hash", None):
            hashFilePath.write_text(data.payload.get("sha256Hash", "") + "\n")
        else:
            typer.echo(f"sha256 hashcode for the template {data.name} is missing. Will be created in process")
            isHashAvailable = False
        hashObj = hashlib.sha256()
        with open(tarFilePath, "wb") as fileOut:
            if not isHashAvailable:
                fileOut = HashWriter(rawWriter=fileOut, hashWriter=hashObj)
            with ZipFile(zipBuffer) as zipFile:
                with tarfile.open(fileobj=fileOut, mode="w:gz") as tarFile:
                    for zipInfo in sorted(zipFile.infolist(), key= lambda x: x.filename):
                        if zipInfo.is_dir():
                            continue

                        tarInfo = TarInfo(name=zipInfo.filename)
                        tarInfo.size = zipInfo.file_size
                        tarInfo.mtime = 0
                        tarInfo.uid = 0
                        tarInfo.gid = 0
                        tarInfo.uname = ""
                        tarInfo.gname = ""
                        tarInfo.mode = 0o644

                        with zipFile.open(zipInfo) as streamSource:
                            tarFile.addfile(tarInfo, fileobj=streamSource)
        if not isHashAvailable:
            finalHash = hashObj.hexdigest()
            hashFilePath.write_text(finalHash + "\n")
    # ============================================================================
    # ONLINE CACHE METHODS
    # ============================================================================
