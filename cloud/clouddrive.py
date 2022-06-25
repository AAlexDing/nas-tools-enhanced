import requests
import log
from config import Config
from utils.functions import get_local_time
from utils.types import MediaType
import json
class CloudDrive:
    __username = None
    __password = None
    __host = None

    def __init__(self):
        self.init_config()

    def init_config(self):
        config = Config()
        clouddrive = config.get_config('cloud').get('clouddrive')
        if clouddrive:
            self.__host = clouddrive.get('host')
            if not self.__host.startswith('http://') and not self.__host.startswith('https://'):
                self.__host = "http://" + self.__host
            if not self.__host.endswith('/'):
                self.__host = self.__host + "/"
            self.__username = clouddrive.get('username')
            self.__password = clouddrive.get('password')
            self.__token = self.get_token()

    def get_token(self):
        if not self.__username or not self.__password:
            return None

        req_url = "%sapi/CloudFSService/GetToken?username=%s&password=%s" % (self.__host, self.__username, self.__password)
        
        try:
            res = requests.get(req_url, timeout=10)
            if res:
                return res.json().get('token')
            else:
                log.error("【CloudDrive】CloudFSService/GetToken 未获取到返回数据")
                return None
        except Exception as e:
            log.error("【CloudDrive】连接CloudFSService/GetToken 出错：" + str(e))
            return None
    
    def get_vars(self, property_name):
        '''
        获得网盘变量
        '''
        if not self.__token or not self.__host or not property_name:
            return None

        req_url = "%sapi/CloudAPI/GetVars?PropertyName=%s" % (self.__host, property_name)
        headers = {
            'accept': 'text/plain',
            'Authorization': 'Bearer %s' % self.__token
        }

        try:
            res = requests.get(req_url,headers=headers, timeout=10)
            if res:
                return res.json()
            else:
                log.error("【CloudDrive】CloudAPI/GetVars 未获取到返回数据")
                return None
        except Exception as e:
            log.error("【CloudDrive】连接CloudAPI/GetVars 出错：" + str(e))
            return None

    def set_vars(self,property_name,value):
        '''
        设置网盘变量
        '''
        if not self.__token or not self.__host or not property_name or not value:
            return False
        req_url = "%sapi/CloudAPI/SetVars" % (self.__host)
        headers = {
            'accept': '*/*',
            'Authorization': 'Bearer %s' % self.__token,
            'Content-Type': 'application/json'
        }
        data = {'propertyName': property_name, 'value': value}
        
        try:
            res = requests.post(req_url, headers=headers, data=json.dumps(data), timeout=10)
            if res:
                return True
            else:
                log.error("【CloudDrive】CloudAPI/SetVars 未获取到返回数据")
                return False
        except Exception as e:
            log.error("【CloudDrive】连接CloudAPI/SetVars 出错：" + str(e))
            return False


    def get_file_detail_properties(self, file_path):
        '''
        获得文件详细属性
        '''
        if not self.__token or not self.__host or not file_path:
            return None
        if not file_path.startswith('/'):
            file_path = '/' + file_path
        req_url = "%sapi/CloudStatus/FileDetailProperties" % (self.__host)
        headers = {
            'accept': '*/*',
            'Authorization': 'Bearer %s' % self.__token,
            'Content-Type': 'application/json'
        }
        data = '"'+file_path+'"'
        try:
            res = requests.post(req_url, headers=headers, data=data.encode(), timeout=10)
            if res:
                return res.json()
            else:
                log.error("【CloudDrive】CloudStatus/FileDetailProperties 未获取到返回数据")
                return None
        except Exception as e:
            log.error("【CloudDrive】连接 CloudStatus/FileDetailProperties 出错：" + str(e))
            return None

    

    def get_drive_list(self):
        '''
        获得网盘列表
        '''
        if not self.__token or not self.__host:
            return []
        req_url = "%sapi/CloudDrive/GetCloudAPIList"%self.__host
        headers = {
            'accept': 'text/plain',
            'Authorization': 'Bearer %s' % self.__token
        }

        try:
            res = requests.get(req_url,headers=headers, timeout=10)
            if res:
                return res.json()
            else:
                log.error("【CloudDrive】CloudDrive/GetCloudAPIList 未获取到返回数据")
                return []
        except Exception as e:
            log.error("【CloudDrive】连接CloudDrive/GetCloudAPIList 出错：" + str(e))
            return []


    def get_space_info(self,cloud_name,user_name):
        '''
        获得网盘空间信息
        '''
        if not self.__token or not self.__host:
            return None
        req_url = "%sapi/CloudAPI/GetSpaceInfo?CloudName=%s&UserName=%s" % (self.__host, cloud_name, user_name)
        headers = {
            'accept': 'text/plain',
            'Authorization': 'Bearer %s' % self.__token
        }

        try:
            res = requests.get(req_url,headers=headers, timeout=10)
            if res:
                return res.json()
            else:
                log.error("【CloudDrive】CloudAPI/GetSpaceInfo 未获取到返回数据")
                return None
        except Exception as e:
            log.error("【CloudDrive】连接CloudAPI/GetSpaceInfo 出错：" + str(e))
            return None



    def get_all_space_info(self):
        '''
        获得所有网盘空间信息
        '''
        drive_list = self.get_drive_list()
        space_info_list = []
        for drive in drive_list:
            space_info = self.get_space_info(drive.get('cloudName'),drive.get('userName'))
            if space_info:
                space_info['cloudName'] = drive.get('cloudName')
                space_info['userName'] = drive.get('userName')
                space_info['rootFolderPath'] = drive.get('rootFolderPath')
                space_info_list.append(space_info)

        return space_info_list