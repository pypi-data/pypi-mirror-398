import re

from pyaudiodevice.audio_device_cmdlets import PyAudioDeviceCmdlets


class AudioCommon(PyAudioDeviceCmdlets):
    '''
    Get the default communication playback device as <AudioDevice>
    '''

    def get_default_device(self):
        powershell_command = "Get-AudioDevice -Playback"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._format_data(data)
    

    '''
    Get the default speaker device as <AudioDevice>
    '''

    def get_default_speaker_device(self):
        powershell_command = "Get-AudioDevice -Playback"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._format_data(data)
    

    '''
    Get the default micphone device as <AudioDevice>
    '''

    def get_default_mic_device(self):
        powershell_command = "Get-AudioDevice -Recording"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._format_data(data)


    """
    Get the device with the ID corresponding to the given <string>
    """

    def get_audio_device_by_id(self, id):
        powershell_command = f"Get-AudioDevice -ID {id}"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._format_data(data)

    '''
    Get the device with the Index corresponding to the given <int>
    '''

    def get_audio_device_by_index(self, index: int):
        powershell_command = f"Get-AudioDevice -Index {str(index)}"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        return self._format_data(data)

    '''
    Get a list of all enabled devices as <AudioDevice>
    '''


    def get_audio_device_list(self):
        powershell_command = "Get-AudioDevice -List"
        data = self._exec_powershell(f"{self._import} {powershell_command}")
        entries = re.split(r'\n\n+', data.strip())

        result_dict = {}

        for entry in entries:
            if not entry.strip():
                continue  # 跳过空条目
            
            entry_dict = {}
            lines = entry.split('\n')
            current_key = None
            current_value = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue  # 跳过空行
                
                # 匹配 "Key : Value" 格式（只分割第一个冒号）
                colon_pos = line.find(':')
                if colon_pos != -1:
                    # 处理上一个未完成的键值对
                    if current_key is not None and current_value:
                        entry_dict[current_key] = self._convert_value(' '.join(current_value))
                        current_value = []
                    
                    # 提取新的键和值
                    current_key = line[:colon_pos].strip()
                    value_part = line[colon_pos+1:].strip()
                    if value_part:
                        current_value.append(value_part)
                else:
                    # 处理续行（无冒号的行，拼接至当前值）
                    if current_key is not None:
                        current_value.append(line.strip())
            
            # 保存最后一个键值对
            if current_key is not None and current_value:
                entry_dict[current_key] = self._convert_value(' '.join(current_value))
            
            # 生成设备唯一标识并加入结果
            dev_name = entry_dict.get('Name', 'Unknown')
            dev_type = entry_dict.get('Type', 'Unknown')
            name = f"{dev_name}:{dev_type}"
            if name and name != "Unknown:Unknown":
                result_dict[name] = entry_dict

        return result_dict

    '''
    Set the given playback/recording device as both the default device and the default communication device, for its type
    '''

    def set_default_communication_device(self, audio_device: str):
        powershell_command = f"Set-AudioDevice {audio_device}"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the given playback/recording device as the default communication device and not the default device, for its type
    '''

    def set_communication_only_device(self, audio_device: str):
        powershell_command = f"Set-AudioDevice {audio_device} -CommunicationOnly"
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the given playback/recording device as the default device and not the default communication device, for its type
    '''

    def set_default_only_device(self, audio_device: str):
        powershell_command = f"Set-AudioDevice {audio_device} -DefaultOnly"

        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the ID corresponding to the given <string> as both the default device and the default communication device, for its type
    '''

    def set_default_communication_device_by_name(self, name: str, device_type="Playback"):
        device_list = self.get_audio_device_list()
        powershell_command = f'''Set-AudioDevice -ID "{device_list.get(f"{name}:{device_type}").get('ID')}"'''
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the ID corresponding to the given <string> as the default communication device and not the default device, for its type
    '''

    def set_communication_only_device_by_name(self, name: str, device_type="Playback"):
        device_list = self.get_audio_device_list()

        powershell_command = f'''Set-AudioDevice -ID "{device_list.get(f"{name}:{device_type}").get('ID')}" -CommunicationOnly'''
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the ID corresponding to the given <string> as the default device and not the default communication device, for its type
    '''

    def set_default_only_device_by_name(self, name: str, device_type="Playback"):
        device_list = self.get_audio_device_list()
        powershell_command = f'''Set-AudioDevice -ID "{device_list.get(f"{name}:{device_type}").get('ID')}" -DefaultOnly'''
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the ID corresponding to the given <string> as both the default device and the default communication device, for its type
    '''

    def set_default_communication_device_by_id(self, device_id: str):
        powershell_command = f'''Set-AudioDevice -ID "{device_id}"'''
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the ID corresponding to the given <string> as the default communication device and not the default device, for its type
    '''

    def set_communication_only_device_by_id(self, device_id: str):
        powershell_command = f'''Set-AudioDevice -ID "{device_id}" -CommunicationOnly'''
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the ID corresponding to the given <string> as the default device and not the default communication device, for its type
    '''

    def set_default_only_device_by_id(self, device_id: str):
        powershell_command = f'''Set-AudioDevice -ID "{device_id}" -DefaultOnly'''
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the Index corresponding to the given <int> as both the default device and the default communication device, for its type
    '''

    def set_default_communication_device_by_index(self, device_index: int):
        powershell_command = f'''Set-AudioDevice -Index "{device_index}"'''
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the Index corresponding to the given <int> as the default communication device and not the default device, for its type
    '''

    def set_communication_only_device_by_index(self, device_index: int):
        powershell_command = f'''Set-AudioDevice -Index "{device_index}" -CommunicationOnly'''
        self._exec_powershell(f"{self._import} {powershell_command}")

    '''
    Set the device with the Index corresponding to the given <int> as the default device and not the default communication device, for its type
    '''

    def set_default_only_device_by_index(self, device_index: int):
        powershell_command = f'''Set-AudioDevice -Index "{device_index}" -DefaultOnly'''
        self._exec_powershell(f"{self._import} {powershell_command}")
