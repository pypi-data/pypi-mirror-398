import struct
import os
import io
import requests
from requests_ntlm import HttpNtlmAuth
from typing import Union, Optional
import logging

class SimpleIPP:
    def __init__(self, printer_url: str, service_user_id: str, service_password: Optional[str] = None):
        """
        :param printer_url: 打印机地址
        :param service_user_id: 连接账号 (Service Account / Robot)
        :param service_password: 连接密码
        """
        if printer_url.startswith("ipp://"):
            self.url = printer_url.replace("ipp://", "http://")
        else:
            self.url = printer_url

        self.service_user_id = service_user_id
        self.service_password = service_password

    def print_job(self, data: Union[str, bytes, io.BytesIO], job_name: str = "RPA_Job", target_user_id: Optional[str] = None) -> bool:
        """
        通用打印方法，支持多种输入格式。

        :param data: 可以是文件路径(str)、二进制数据(bytes) 或 内存流(io.BytesIO)
        :param job_name: 任务名称
        :param target_user_id: 业务归属人 (SSO User)，不填则默认为连接账号
        """

        # 1. 数据清洗：统一转为 bytes
        content = b""
        source_type = "unknown"

        try:
            if isinstance(data, str):
                # 情况 A: 文件路径
                if not os.path.exists(data):
                    logging.error(f"错误: 文件不存在 {data}")
                    return False
                source_type = "File Path"
                with open(data, "rb") as f:
                    content = f.read()

            elif isinstance(data, io.BytesIO):
                # 情况 B: BytesIO 内存对象
                source_type = "BytesIO Stream"
                content = data.getvalue()  # 获取全部二进制流

            elif isinstance(data, bytes):
                # 情况 C: 纯二进制
                source_type = "Raw Bytes"
                content = data

            else:
                logging.error(f"错误: 不支持的数据类型 {type(data)}")
                return False

            if not content:
                logging.error("错误: 打印内容为空！")
                return False

            # 2. 确定归属人
            final_owner = target_user_id if target_user_id else self.service_user_id

            # 3. 构建 IPP 包
            ipp_data = self._build_ipp_request(job_name, content, final_owner)

            # 4. 配置认证
            auth_obj = None
            if self.service_password:
                auth_obj = HttpNtlmAuth(self.service_user_id, self.service_password)

            logging.info(f"🖨️  正在发送任务...")
            logging.info(f"    ├─ 来源类型: {source_type}")
            logging.info(f"    ├─ 数据大小: {len(content) / 1024:.2f} KB")
            logging.info(f"    └─ 归属用户: {final_owner}")

            response = requests.post(
                self.url,
                data=ipp_data,
                headers={"Content-Type": "application/ipp"},
                auth=auth_obj,
                verify=False,
                timeout=45  # 传大文件时稍微延长时间
            )

            if response.status_code == 200:
                logging.info(f"成功！任务 [{job_name}] 已发送。")
                return True
            else:
                logging.error(f"失败，状态码: {response.status_code}")
                return False

        except Exception as e:
            logging.error(f"异常: {e}")
            return False

    def _build_ipp_request(self, job_name, content, requesting_user_name):
        # ... (这部分协议组装代码保持不变，复用 v2.0 即可) ...
        # 为了完整性，这里简写，实际上你需要把 v2.0 的 _build_ipp_request 复制过来
        version = b'\x01\x01'
        operation_id = b'\x00\x02'
        request_id = b'\x00\x00\x00\x01'
        start_attr = b'\x01'

        def add_attr(tag, name, value):
            if isinstance(value, str):
                value = value.encode('utf-8')
            return (
                    struct.pack('!b', tag) +
                    struct.pack('!h', len(name)) + name.encode('utf-8') +
                    struct.pack('!h', len(value)) + value
            )

        attributes = b''
        attributes += add_attr(0x47, 'attributes-charset', 'utf-8')
        attributes += add_attr(0x48, 'attributes-natural-language', 'en-us')
        attributes += add_attr(0x45, 'printer-uri', self.url)
        attributes += add_attr(0x42, 'requesting-user-name', requesting_user_name)
        attributes += add_attr(0x42, 'job-name', job_name)
        end_attr = b'\x03'

        return version + operation_id + request_id + start_attr + attributes + end_attr + content
