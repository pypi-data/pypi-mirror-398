import os

from pyaudiodevice.audio_device_cmdlets import PyAudioDeviceCmdlets


class DefaultCommunicationPlayback(PyAudioDeviceCmdlets):
    def __init__(self):
        super().__init__()
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib\AudioDeviceCmdlets.dll")
        self._import = f'''Import-Module "{self.path}";'''

    '''
    Get the default communication recording device as <AudioDevice>
    '''
    def get_default_device(self):
        powershell_command = "Get-AudioDevice -RecordingCommunication"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._format_data(data)

    '''
    Get the default communication recording device's mute state as <bool>
    '''
    def get_is_mute(self):
        powershell_command = "Get-AudioDevice -RecordingCommunicationMute"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._convert_value(data)

    '''
    Get the default communication recording device's volume level on 100 as <float>
    '''
    def get_volume(self):
        powershell_command = "Get-AudioDevice -RecordingCommunicationVolume"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._convert_value(data)

    '''
    Set the default communication recording device's mute state to the opposite of its current mute state
    '''

    def toggle_communication_recording_device_mute(self):
        powershell_command = "Set-AudioDevice -RecordingCommunicationMuteToggle"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the default communication recording device's mute state to the given <bool>
    '''

    def set_communication_recording_device_mute(self, mute: bool):
        powershell_command = f"Set-AudioDevice -RecordingCommunicationMute ${str(mute).lower()}"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the default communication recording device's volume level on 100 to the given <float>
    '''

    def set_communication_recording_device_volume(self, volume: float):
        powershell_command = f"Set-AudioDevice -RecordingCommunicationVolume {volume}"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the default recording device's mute state to the opposite of its current mute state
    '''

    def toggle_recording_device_mute(self):
        powershell_command = "Set-AudioDevice -RecordingMuteToggle"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the default recording device's mute state to the given <bool>
    '''

    def set_recording_device_mute(self, mute: bool):
        powershell_command = f"Set-AudioDevice -RecordingMute ${str(mute).lower()}"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the default recording device's volume level on 100 to the given <float>
    '''

    def set_recording_device_volume(self, volume: float):
        powershell_command = f"Set-AudioDevice -RecordingVolume {volume}"
        self._exec_powershell(f"{self._import} {powershell_command}")
