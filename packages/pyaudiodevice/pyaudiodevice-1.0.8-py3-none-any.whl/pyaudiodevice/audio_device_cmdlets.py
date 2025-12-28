import os
import re
import subprocess


class PyAudioDeviceCmdlets:
    def __init__(self):
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib\AudioDeviceCmdlets.dll")
        self._import = f'''Import-Module "{self.path}";'''

    def _exec_powershell(self, cmd):
        # 使用subprocess模块调用PowerShell
        result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)

        if result.stderr != "":
            raise ValueError(result.stderr)
        else:
            return result.stdout

    def _convert_value(self, value):
        value = value.strip()
        if value.isdigit():
            return int(value)
        elif value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        elif value.find("%") > 0:
            return float(value.replace("%", ""))
        else:
            return value

    def _format_data(self, data):
        entries = re.split(r'\n\n+', data.strip())
        entry_dict = {}
        for entry in entries:
            lines = entry.split('\n')
            for line in lines:

                key, value = re.split(r'\s*:\s*', line)
                entry_dict[key.strip()] = self._convert_value(value)
        return entry_dict


