import subprocess


class CommandExecutor:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def execute(self, command: str):
        if not self.enabled:
            print(f"[Executor disabled] Command would have run: {command}")
            return None
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout
