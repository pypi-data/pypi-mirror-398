from cbor2 import CBOREncoder

from craftlet.models.Cacheable import Cacheable


def repoUrlToZipUrl(repoUrl: str):
    zipUrl = (
        repoUrl.replace("github.com", "codeload.github.com") + "/zip/refs/heads/main"
    )
    return zipUrl


def cborGithubTemplateReferenceEncoder(encoder: CBOREncoder, data: Cacheable):
    encoder.encode({0: data.coreData})
