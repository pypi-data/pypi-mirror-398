import socket
import struct
import copy,platform,json, os, re, subprocess, io,time,random,string,shutil,datetime,threading
from typing import List, Tuple, Dict
import uuid
from .delete_safe_list import DeleteSafeList

class SUtil():
    @staticmethod
    def ExcuteCommandResult(cmd_path,command)->Tuple[str,str]:
        """等待命令执行完成，并返回输出

        Args:
            cmd_path (str): 命令执行目录
            command (str): 命令

        Returns:
            Tuple[str_stdout,str_stderr]: 命令行输出
        """        
        os.chdir(cmd_path)
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        stream_stdout = io.TextIOWrapper(proc.stdout, encoding='utf-8')
        stream_stderr = io.TextIOWrapper(proc.stderr, encoding='utf-8')
        
        str_stdout = str(stream_stdout.read())
        str_stderr = str(stream_stderr.read())
        return (str_stdout,str_stderr)

    @staticmethod
    def mkdir(path:str):
        """创建文件夹及子目录
        Args:
            path (str): 文件夹路径
        """        
        if os.path.exists(path)==False:
            os.makedirs(path)
    @staticmethod
    def CopyFloderToDest(sourceFloder,targetFloder):
        """复制文件夹到指定目录

        Args:
            sourceFloder (_type_): _description_
            targetFloder (_type_): _description_
        """        
        for files in os.listdir(sourceFloder):
            name = os.path.join(sourceFloder, files)
            back_name = os.path.join(targetFloder, files)
            if os.path.isfile(name):
                if os.path.isfile(back_name):                
                    shutil.copy(name,back_name)     
                else:
                    shutil.copy(name, back_name)
            else:
                if not os.path.isdir(back_name):
                    os.makedirs(back_name)
                SUtil.CopyFloderToDest(name, back_name)

    @staticmethod
    def GetOSPath(*args):
        sysstr = platform.system()
        if(sysstr == "Windows"):
            return ".\\"+"\\".join(args)
        elif(sysstr == "Linux"):
            return "./"+"/".join(args)
        else:
            return "/".join(args)
    @staticmethod
    def GetOSPathSpliter():
        sysstr = platform.system()
        if(sysstr == "Windows"):
            return "\\"
        elif(sysstr == "Linux"):
            return "/"
    @staticmethod
    def ContactOSPath(*args):
        sysstr = platform.system()
        if(sysstr == "Windows"):
            return "\\".join(args)
        elif(sysstr == "Linux"):
            return "/".join(args)
        else:
            return "/".join(args)

    def GetOSNewLineChar(self):
        sysstr = platform.system()
        if(sysstr == "Windows"):
            return "\n"
        elif(sysstr == "Linux"):
            return "\r"
        else:
            return "\r\n"
    @staticmethod
    def RemoveFile(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
    @staticmethod
    def ExistKeyInFile(file_path:str,key:str)->bool:
        """判断key是否在文件中

        Args:
            file_path (str): 文件路径
            key (str): 键

        Returns:
            bool: 是否存在
        """
        try:
            file_obj = open(file_path, 'r', encoding='utf-8')
            all_text=file_obj.read()
            if all_text and key in all_text:
                # print('exist',key)
                return True
        except Exception:
            pass
        return False
    @staticmethod
    def AppendString(file_path, content):        
        file_obj = open(file_path, 'a+', encoding='utf-8')
        file_obj.write(os.linesep+content)
        file_obj.close()
    def AppendLine(file_path, content):        
        file_obj = open(file_path, 'a+', encoding='utf-8')
        file_obj.write(content)
        file_obj.close()
    @staticmethod
    def LoadJson(file_path):
        with open(file_path, 'r', encoding='utf-8') as load_image:
            imageNames = json.load(load_image)
            load_image.close()
        return imageNames
    @staticmethod
    def ReadFileLines(file_path):
        with open(file_path,'r', encoding='utf-8') as r:
            lines=r.readlines()
            r.close()
            return lines
    @staticmethod
    def ReadFile(file_path):
        with open(file_path,'r', encoding='utf-8') as r:
            lines=r.read()
            r.close()
            return lines
    @staticmethod
    def GeneratePwd(length)->str:
        """
        生成密码函数
        
        该函数用于生成一个随机密码字符串。密码由大小写字母、数字和特殊字符组成，
        长度固定为length个字符。旨在为用户提供安全的随机密码。
        
        返回:
            str: 长度为length的随机密码字符串
        """
        length = length - 4
        src = string.ascii_letters + string.digits
        # count = input('请确认要生成几条密码： ')
        list_passwds = []

        list_passwd_all = random.sample(src, length) #从字母和数字中随机取5位
        list_passwd_all.extend(random.sample(string.digits, 1))  #让密码中一定包含数字
        list_passwd_all.extend(random.sample(string.ascii_lowercase, 1)) #让密码中一定包含小写字母
        list_passwd_all.extend(random.sample(string.ascii_uppercase, 1)) #让密码中一定包含大写字母
        random.shuffle(list_passwd_all) #打乱列表顺序
        str_passwd = ''.join(list_passwd_all) #将列表转化为字符串
        return str_passwd+"#&^*"

    @staticmethod
    def Now()->str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    @staticmethod
    def RandomPort()->int:
        p = random.randint(9101, 9999)
        return p

    @staticmethod
    def start_thread(func):
        def wrapper(*args, **kwargs):
            t = threading.Thread(target=func, args=(*args,))
            t.start()
            return True
        return wrapper

    @staticmethod
    def convert_time_from_str(date_string):
        date_format = '%Y-%m-%d %H:%M:%S'
        date_object = datetime.datetime.strptime(date_string, date_format)
        timestamp = int(date_object.timestamp())
        return timestamp

    @staticmethod
    def format_capacity(base_capacity):
        if 'Ki' in base_capacity:
            return f"{int(base_capacity.replace('Ki', '')) / 1024 / 1024:.2f}GB"
        elif 'Mi' in base_capacity:
            return f"{int(base_capacity.replace('Mi', '')) / 1024:.2f}GB"
        elif "Gi" in base_capacity:
            return f"{int(base_capacity.replace('Gi', '')) :.2f}GB"
        elif "Ti" in base_capacity:
            return f"{int(base_capacity.replace('Ti', '')) * 1024 :.2f}GB"
        elif "m" in base_capacity:
            return f"{int(base_capacity.replace('m', '')) /1024/1024/1024/1000 :.2f}GB"
        else:
            try:
                t = float(base_capacity)
                return f"{t/1024/1024/1024 :.2f}GB"
            except:
                return base_capacity
    @staticmethod
    def get_arg(jsonData,key,des='',default=None, missing_value_list=[]):
        v=jsonData.get(key,None)
        if v is None or v in missing_value_list:
            if default is None:
                raise Exception(f"参数{des}:{key}必须传入")
            else:
                return default
        return v
        
    def getBatchItems(my_list,step_size = 5):
        """循环从列表中获取指定个数的元素直到列表末尾

        Args:
            my_list (list): 列表对象
            step_size (int, optional): 每次获取数量. Defaults to 5.

        Yields:
            _type_: 列表切片
        """        
        list_length = len(my_list)
        # 从0开始到列表长度，步长为step_size
        for i in range(0, list_length, step_size):
            # 获取从i开始的5个元素
            chunk = my_list[i:i + step_size]
            yield chunk
    @staticmethod
    def slice_data(list_data,size=1000):
        '''将列表拆分'''
        for i in range(0,len(list_data),size):
            yield list_data[i:i+size]
    @staticmethod
    def get_pre_date(prehours:int)->datetime.datetime:
        """计算当天时间00:00 +对应时间

        Args:
            prehours (int): 可以为负数

        Returns:
            _type_: _description_
        """        
        now=datetime.datetime.now()
        begin=datetime.datetime(now.year, now.month, now.day)
        return begin+datetime.timedelta(hours=prehours)

    @staticmethod
    def split_message(message,length=200):
        """
        将消息拆分成多条消息，每条消息的长度不能超过length。

        Args:
            message: 要拆分的字符串。
        Returns:
            一个列表，包含所有拆分后的子消息。
        """

        lines = message.split("\n")
        messages = []
        currenMsg=''
        for line in lines:
            if len(currenMsg)+len(line)<=length:
                currenMsg+=line+"\n"
            else:
                messages.append(currenMsg)
                currenMsg=line+"\n"
        if currenMsg:
            messages.append(currenMsg)
        return messages
    @staticmethod
    def replace_keys(template: str, keys: Dict[str, object]):
        for k, v in keys.items():
            template = template.replace('${' + k + '}', str(v))
        return template
    
    @staticmethod
    def tranlate_cron_from_time(restore_time: str):
        time_fields = restore_time.split(":")
        if len(time_fields) == 3:
            return f"* {int(time_fields[1])} {int(time_fields[0])} * * * *"
        else:
                return ''
    @staticmethod
    def wait_for_condition(check_function, interval=5, timeout=None):  
        """  
        Wait for a condition to be True.  
    
        :param check_function: A function that returns True when the condition is met.  
        :param interval: The number of seconds to wait between checks.  
        :param timeout: The maximum number of seconds to wait. If None, wait indefinitely.  
        :return: True if the condition is met, False if timeout occurs.  
        """  
        start_time = time.time()  
        while True:  
            if check_function():  
                return True  
            if timeout is not None and (time.time() - start_time) >= timeout:  
                return False  
            time.sleep(interval)

    @staticmethod
    def is_valid_ipv4(ip):
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip):
            parts = ip.split('.')
            if all(0 <= int(part) <= 255 for part in parts):
                return True
        return False
    @staticmethod
    def get_machine_id():
        mac = uuid.getnode()
        return mac & 0xFFFF  # 取后16位作为machine_id
    @staticmethod
    def find_key_in_json(data, target_key, parent_key='', level_keys=None):
        """
        查找包含目标字符串的key，并打印key在JSON中的层级。
        
        :param data: JSON数据（字典或列表）
        :param target_key: 要查找的目标字符串
        :param parent_key: 当前key的父级路径（用于递归）
        :param level_keys: 存储找到的key及其层级（用于递归）
        """
        if level_keys is None:
            level_keys = []

        if isinstance(data, dict):
            for key, value in data.items():
                current_key = f"{parent_key}.{key}" if parent_key else key
                if target_key in key:
                    level_keys.append(current_key)
                SUtil.find_key_in_json(value, target_key, current_key, level_keys)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                current_key = f"{parent_key}[{index}]"
                SUtil.find_key_in_json(item, target_key, current_key, level_keys)
    @staticmethod
    def get_local_ip():
        '''通过ping8.8.8.8获取本机IP'''
        sock = None
        try:
            ip = os.environ.get('IP')
            if ip:
                return ip
            # 创建一个UDP套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到一个公共的IP地址和端口（这里使用Google的公共DNS服务器）
            sock.connect(("8.8.8.8", 80))
            # 获取本地IP地址
            local_ip = sock.getsockname()[0]
        finally:
            if sock:
                # 关闭套接字
                sock.close()
        return local_ip
