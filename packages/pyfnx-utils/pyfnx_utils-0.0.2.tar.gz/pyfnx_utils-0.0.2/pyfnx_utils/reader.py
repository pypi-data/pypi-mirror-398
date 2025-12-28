import tarfile
import json

from pyfnx_utils.models.manifest import Manifest
from pyfnx_utils.models.meta import MetaEntry
from pyfnx_utils.models.env import Python3_CondaPip


class Reader:
    def __init__(self, model_path: str):
        with tarfile.open(model_path, "r:*") as tar:
            self.manifest = Manifest.from_dict(
                json.loads(self._get_file(tar, "manifest.json"))
            )
            self.metadata = [
                MetaEntry(**m) for m in json.loads(self._get_file(tar, "meta.json"))
            ]
            self.env = json.loads(self._get_file(tar, "env.json"))

        if "python3::conda_pip" in self.env:
            self.pyenv = Python3_CondaPip.from_dict(self.env["python3::conda_pip"])

    def _get_file(self, tar: tarfile.TarFile, target: str):
        member = tar.getmember(target)
        f = tar.extractfile(member)
        if not f:
            raise ValueError(f"Could not locate `{target}`")
        content = f.read()
        return content.decode("utf-8")
