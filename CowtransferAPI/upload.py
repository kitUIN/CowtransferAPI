import base64
import json
import math
import os
import re
import time
from functools import wraps
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
from urllib import parse
import requests
import magic
import urllib3
from rich.columns import Columns

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

console = Console()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CowUpload:
    def __init__(self, slight=False, cookies='1610272831475', **requests_kwargs):
        self.slight: bool = slight
        self.requests_kwargs = requests_kwargs
        # ----------------------------网址----------------------------------------
        self._prepareSend: str = "https://cowtransfer.com/transfer/preparesend"
        self._setPassword: str = "https://cowtransfer.com/transfer/v2/bindpasscode"
        self._beforeUpload: str = "https://cowtransfer.com/transfer/beforeupload"
        self._uploadInitEndpoint: str = "https://upload.qiniup.com/mkblk/{}"
        self._uploadEndpoint: str = "https://upload.qiniup.com/bput/{}/{}"
        self._uploadFinish: str = "https://cowtransfer.com/transfer/uploaded"
        self._uploadComplete: str = "https://cowtransfer.com/transfer/complete"
        self._uploadMergeFile: str = "https://upload.qiniup.com/mkfile/{}/key/{}/fname/{}"
        # ----------------------------------------------------------------------
        self.cookies: dict = {'cf-cs-k-20181214': cookies}  # cookies 中'cf-cs-k-20181214'（必须）
        self.offset = 0
        self._ctx = list()
        self.headers: dict = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75",
            "Accept": "application/json",
            'Origin': 'https://cowtransfer.com',
            "Referer": "https://cowtransfer.com/"
        }  # 请求头
        self.uploadHeaders: dict = self.headers  # 上传文件请求头
        self._chunk: int = 4194304  # 区大小
        self.start_time = time.time()
        self.raw: dict = dict()  # 输出结果

    def _request_logs(self, url, res):
        console.log('\r\n[bold blue]PointEnd:[/]\r\n')
        console.log(url)
        console.log('\r\n[bold magenta]Headers:[/]\r\n')
        console.log(res.request.headers)
        console.log("\r\n[bold green]Return:[/bold green]\r\n")
        console.log(res.json())

    def _convertBytes(self, bytes, lst=None):  # 进制转换
        if lst is None:
            lst = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
        i = int(math.floor(  # 舍弃小数点，取小
            math.log(bytes, 1024)  # 求对数(对数：若 a**b = N 则 b 叫做以 a 为底 N 的对数)
        ))

        if i >= len(lst):
            i = len(lst) - 1
        return ('%.2f' + " " + lst[i]) % (bytes / math.pow(1024, i))

    def _look_file(self, path):  # 文件信息读取
        self.fileSize: int = os.path.getsize(path)  # 上传文件大小
        self.fileType: str = magic.Magic(mime=True, uncompress=True).from_file(path)  # 上传文件类型
        self.fileOriginalName: str = re.search('[^\\\\]+$', path)[0]  # 上传文件名字
        self.fileName: str = parse.quote(self.fileOriginalName)  # 上传文件名字(Url编码)
        self.path = path  # 文件地址
        if self.slight:  # 详细日志
            console.log(Rule('[bold yellow]Step 1/7 [/][bold cyan]File Scan[/]'))
            table = Table(title="文件属性", show_lines=True)
            table.add_column("文件名称")
            table.add_column(self.fileName)
            table.add_row("文件类型", self.fileType)
            table.add_row("文件大小", self._convertBytes(self.fileSize, ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']))
            table.add_row("文件路径", self.path)
            console.print(table)

    @staticmethod
    def _url_decode(data):  # Url解码
        return parse.unquote(data)

    @staticmethod
    def _tobase64(key):
        return base64.b64encode(key).decode()

    def _prepare(self, path, message, notifyEmail, validDays, saveToMyCloud, downloadTimes, smsReceivers,
                 emailReceivers, enableShareToOthers, language, enableDownload, enablePreview):
        self._look_file(path)  # 获取文件属性
        multipart = MultipartEncoder(
            fields={
                'totalSize': str(self.fileSize),
                'message': message,
                'notifyEmail': notifyEmail,
                'validDays': str(validDays),
                'saveToMyCloud': str(json.dumps(saveToMyCloud)),
                'downloadTimes': str(downloadTimes),
                'smsReceivers': smsReceivers,
                'emailReceivers': emailReceivers,
                'enableShareToOthers': str(json.dumps(enableShareToOthers)),
                'language': language,
                'enableDownload': str(json.dumps(enableDownload)),
                'enablePreview': str(json.dumps(enablePreview))
            },
            boundary='----WebKitFormBoundaryJ2aGzfsg35YqeT7X'
        )
        self.headers['Content-Type'] = multipart.content_type
        res = requests.post(self._prepareSend, headers=self.headers, data=multipart, cookies=self.cookies,
                            **self.requests_kwargs)
        self.cookies.update(res.cookies.get_dict())  # 更新cookies中JSESSIONID，SERVERID（必须）
        result = res.json()
        if self.slight:  # 详细日志
            console.log(Rule('[bold yellow]Step 2/7 [/][bold cyan]Prepare Upload[/]'))
            self._request_logs(self._prepareSend, res)
        if result['error']:
            console.log('[bold red]文件准备失败[/bold red]\r\n[yellow]错误信息：{}[/yellow]'.format(result['error_message']))
        self.uploadHeaders['Authorization'] = 'UpToken ' + result['uptoken']  # 添加uptoken密钥
        self.transferGuid: str = result['transferguid']
        self.prefix: str = result['prefix']
        self.raw['qrcode']: str = result['qrcode']
        self.raw['uniqueurl']: str = result['uniqueurl']
        self.key: str = self.prefix + '/' + self.transferGuid + '/' + self.fileName
        self._key: str = self._tobase64(self.key.encode('utf-8'))
        return self._before()

    def _before(self):
        multipart = MultipartEncoder(
            fields={
                "type": self.fileType,
                "fileId": '',
                "fileName": self.fileName,
                "originalName": self.fileOriginalName,
                "fileSize": str(self.fileSize),
                "transferGuid": self.transferGuid,
                "storagePrefix": self.prefix,
                "unfinishPath": '',
            },
            boundary='----WebKitFormBoundaryJ2aGzfsg35YqeT7X'
        )
        self.headers['Content-Type'] = multipart.content_type
        res = requests.post(self._beforeUpload, headers=self.headers, data=multipart, cookies=self.cookies,
                            **self.requests_kwargs)
        result = res.json()
        if self.slight:  # 详细日志
            console.log(Rule('[bold yellow]Step 3/7 [/][bold cyan]Before Upload[/]'))
            self._request_logs(self._beforeUpload, res)
        self.fileGuid = result['fileGuid']
        return self._uploader()

    def _bar(monitor):
        progress = (monitor.bytes_read / monitor.len) * 100
        print("\r上传进度：%d%%(%d/%d)"
              % (progress, monitor.bytes_read, monitor.len))

    def _uploader(self):
        file_num = self.fileSize
        block_num = 0
        num = math.ceil(self.fileSize / (self._chunk - 135))
        with open(self.path, 'rb') as f:
            file = bytes()
            # if self.fileSize < (self._chunk - 123)
            while True:
                temp = f.read(self._chunk - 135)
                file += temp
                if len(temp) != 0:
                    length = len(temp) + 135
                    url = self._uploadInitEndpoint.format(str(length))
                    multipart = MultipartEncoder({"file": temp}, boundary='----WebKitFormBoundaryJ2aGzfsg35YqeT7X')
                    # m = MultipartEncoderMonitor(multipart, self.bar)
                    self.uploadHeaders['Content-Type'] = multipart.content_type
                    res = requests.post(url, headers=self.uploadHeaders, data=multipart, **self.requests_kwargs)
                    result = res.json()
                    if self.slight:  # 详细日志
                        console.log(Rule('[bold yellow]Step 4/7 [/][bold cyan]Uploading...[/]'))
                        self._request_logs(url, res)
                    self._ctx.append(result['ctx'])
                    self.offset += result['offset']
                else:
                    self.fileHash = hash(file)
                    break
        return self._merge_file()

    def _merge_file(self):
        fname = self._tobase64(self.fileName.encode('utf-8'))
        url = self._uploadMergeFile.format(self.fileSize + 135, self._key, fname)
        ctx = ','.join(self._ctx)
        self.uploadHeaders['Content-Type'] = 'text/plain; boundary=----WebKitFormBoundaryJ2aGzfsg35YqeT7X'
        res = requests.post(url, data=ctx,
                            headers=self.uploadHeaders, **self.requests_kwargs)
        result = res.json()
        if self.slight:  # 详细日志
            console.log(Rule('[bold yellow]Step 5/7 [/][bold cyan]Merge File[/]'))
            self._request_logs(url, res)  # 详细日志
        self.hash: str = result['hash']

        return self._uploaded()

    def _uploaded(self):
        multipart = MultipartEncoder(
            fields={
                'fileGuid': str(self.fileGuid),
                'hash': str(self.hash),
                'transferGuid': str(self.transferGuid)
            },
            boundary='----WebKitFormBoundaryJ2aGzfsg35YqeT7X'
        )

        self.headers['Content-Type'] = multipart.content_type
        res = requests.post(self._uploadFinish, data=multipart,
                            headers=self.headers,
                            cookies=self.cookies, **self.requests_kwargs)

        result = res.json()
        assert [result, '文件上传失败']
        if self.slight:  # 详细日志
            console.log(Rule('[bold yellow]Step 6/7 [/][bold cyan]Uploaded[/]'))
            self._request_logs(self._uploadFinish, res)

        return self._complete()

    def _complete(self):
        multipart = MultipartEncoder(
            fields={
                'transferGuid': str(self.transferGuid)
            },
            boundary='----WebKitFormBoundaryJ2aGzfsg35YqeT7X'
        )
        self.headers['Content-Type'] = multipart.content_type
        res = requests.post(self._uploadComplete, data=multipart, headers=self.headers, cookies=self.cookies,
                            **self.requests_kwargs)
        result = res.json()
        self.tempDownloadCode: int = result['tempDownloadCode']
        if self.slight:  # 详细日志
            console.log(Rule('[bold yellow]Step 7/7 [/][bold cyan]Complete Upload[/]'))
            self._request_logs(self._uploadComplete, res)
            console.log(Rule('[bold yellow]Step X/7 [/][bold cyan]详细日志结束[/]'))
        end_time = time.time()
        if result['complete']:
            console.log(Columns([Panel('文件名称[{}]：\r\n{}'.format(self.fileOriginalName,
                                       self._convertBytes(self.fileSize, ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']))),
                                 Panel("[magenta]消耗时间：\r\n[/][bold magenta]{}[/]".format(
                                     (end_time - self.start_time).__str__() + ' s')),
                                 Panel("[blue]下载地址：[/][bold blue]{}[/]".format(self.raw['uniqueurl'])),
                                 Panel("[yellow]取件密码：[/][bold yellow]{}[/]".format(self.tempDownloadCode))]))
        else:
            console.log('[bold red]上传失败:[/]')

    def upload(self,
               path: str = '',
               message: str = '',
               notifyEmail: str = '',
               validDays: int = -1,
               saveToMyCloud: bool = False,
               downloadTimes: int = -1,
               smsReceivers: str = '',
               emailReceivers: str = '',
               enableShareToOthers: bool = False,
               language: str = 'cn',
               enableDownload: bool = True,
               enablePreview: bool = True
               ):
        return self._prepare(path, message, notifyEmail, validDays, saveToMyCloud, downloadTimes, smsReceivers,
                             emailReceivers, enableShareToOthers, language, enableDownload, enablePreview)
