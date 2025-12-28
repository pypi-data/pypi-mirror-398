import os
import subprocess

from pyaudiodevice.audio_device_cmdlets import PyAudioDeviceCmdlets


class DefaultCommunicationPlayback(PyAudioDeviceCmdlets):
    def __init__(self):
        super().__init__()
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib\AudioDeviceCmdlets.dll")
        self._import = f'''Import-Module "{self.path}";'''

    '''
    Get the default communication playback device as <AudioDevice>
    '''

    def get_default_device(self):
        powershell_command = "Get-AudioDevice -PlaybackCommunication"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._format_data(data)

    '''
    Get the default communication playback device's mute state as <bool>
    '''

    def get_is_mute(self):
        powershell_command = "Get-AudioDevice -PlaybackCommunicationMute"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._convert_value(data)

    '''
    Get the default communication playback device's volume level on 100 as <float>
    '''

    def get_volume(self):
        powershell_command = "Get-AudioDevice -PlaybackCommunicationVolume"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._convert_value(data)

    '''
    Set the default communication playback device's mute state to the opposite of its current mute state
    '''

    def toggle_mute(self):
        powershell_command = "Set-AudioDevice -PlaybackCommunicationMuteToggle"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the default communication playback device's mute state to the given <bool>
    '''

    def set_mute(self, mute: bool):
        powershell_command = f"Set-AudioDevice -PlaybackCommunicationMute ${str(mute).lower()}"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the default communication playback device's volume level on 100 to the given <float>
    '''

    def set_volume(self, volume: float):
        powershell_command = f"Set-AudioDevice -PlaybackCommunicationVolume {volume}"
        self._exec_powershell(f"{self._import} {powershell_command}")