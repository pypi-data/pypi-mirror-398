
import requests
import os
import subprocess
import psutil
import time


class dcn:
    
    # 服务配置
    _SERVICES = [
        {
            "name": "configService",
            "cmd": "/usr/local/bin/configService",
            "args": []
        },
        {
            "name": "dcService",
            "cmd": "/usr/local/bin/dcService",
            "args": ["-c", "/etc/dc.cnf"]
        }
    ]

    @staticmethod 
    def is_service_running(service_name):
        """检查服务是否正在运行"""
        for proc in psutil.process_iter(['name', 'cmdline']):
            if proc.info['name'] == service_name or (
                proc.info['cmdline'] and service_name in ' '.join(proc.info['cmdline'])
            ):
                return True
        return False

    @staticmethod
    def _start_service(service):
        """启动服务（如果未运行）"""
        if not dcn.is_service_running(service['name']):
            try:
                full_cmd = [service['cmd']] + service['args']
                subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✅ 已启动服务: {service['name']}")
                return True
            except Exception as e:
                print(f"❌ 启动服务 {service['name']} 失败: {e}")
                return False
        else:
            print(f"⏩ 服务已运行: {service['name']}")
            return True

    @staticmethod
    def start_service():
        """先检查服务是否启动，若没有启动则启动"""
        # 确保 psutil 已安装
        try:
            import psutil
        except ImportError:
            print("正在安装依赖库 psutil...")
            subprocess.check_call(['pip', 'install', 'psutil'])
            import psutil
    
        # 检查并启动所有服务
        for service in dcn._SERVICES:
            dcn._start_service(service)
    
        # 可选：简单验证服务是否存活
        time.sleep(1)
        print("\n服务状态验证:")
        for service in dcn._SERVICES:
            status = "运行中" if dcn.is_service_running(service['name']) else "未运行"
            print(f"{service['name']}: {status}")

    
    @staticmethod 
    def token_request(user, password, url = "http://127.0.0.1:12301/dbm/token"):
        """
        获取认证token
        :param user: 用户名
        :param password: 密码
        :return: 服务器响应（包含token）
        """
        
        headers = {'content-type': 'application/json'}
        data = {
            "user": user,
            "password": password
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()  # 如果请求失败会抛出HTTPError异常
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return None

    @staticmethod
    def token_value():
        # 获取token示例
        token_response = dcn.token_request(
            user="root",
            password="rootroot"
        )
        
        if token_response:
            if token_response.get("status") == "ok":
                return token_response["token"]
        return None


    @staticmethod
    def put_data(tag, key, val, BASE_URL = "http://127.0.0.1:12302/dbm/dc"):
        """
        向服务端存储数据
        :param token: 认证token
        :param tag: 数据标签
        :param key: 键名
        :param val: 值
        :return: 服务器响应
        """
        token = dcn.token_value()
        url = f"{BASE_URL}/put"
        headers = {'content-type': 'application/json'}
        data = {
            "token": token,
            "tag": tag,
            "key": key,
            "val": val
        }
        
        response = requests.post(url, json=data, headers=headers)
        return response.json()


    @staticmethod
    def get_data(tag, key, BASE_URL = "http://127.0.0.1:12302/dbm/dc"):
        """
        从服务端获取数据
        :param token: 认证token
        :param tag: 数据标签
        :param key: 键名
        :return: 服务器响应

        examples
        --------------------------------
        # 获取数据示例
        res = dcn.get_data(
            tag="测试",
            key="current_step"
        )
        res  # {'res': '第2步成功执行结束; 第3步，状态正在状态', 'status': 'ok'}

        """
        token = dcn.token_value()
        url = f"{BASE_URL}/get"
        headers = {'content-type': 'application/json'}
        data = {
            "token": token,
            "tag": tag,
            "key": key
        }
        
        response = requests.post(url, json=data, headers=headers)
        return response.json()
    
    
