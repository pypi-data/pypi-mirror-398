import subprocess
import os

class Xylo:
    def __init__(self):
        self.name = None
        self.pid = None
        self.dll = None

        self.exe = os.path.join(
            os.path.dirname(__file__),
            "bin",
            "xylo.exe"
        )

    def Name(self, value: str):
        self.name = value
        return self

    def Pid(self, value: int):
        self.pid = value
        return self

    def Dll(self, value: str):
        self.dll = value
        return self

    def Inject(self):
        if not self.dll:
            raise ValueError("DLL is missing")

        cmd = [self.exe]

        if self.name:
            cmd += ["--name", self.name]

        if self.pid:
            cmd += ["--pid", str(self.pid)]

        cmd += ["--dll", self.dll]
        cmd += ["--inject"]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
