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

from rich.console import Console, ConsoleRenderable, RenderGroup
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, FileSizeColumn, TotalFileSizeColumn, \
    TimeRemainingColumn, TimeElapsedColumn
from rich.table import Table
from rich.rule import Rule

error_console = Console(stderr=True)
console = Console()
progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TextColumn("[progress.speed]{task.speed}"),
    FileSizeColumn(),
    TotalFileSizeColumn(),
    TimeElapsedColumn(),
    console=console,
    # 瞬时 transient=True,
)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CowUpload:
    def __init__(self, slight=False, silence=True, cookies="1610272831475", **requests_kwargs):
        self.silence: bool = silence
        self.slight: bool = slight
        if silence:  # 静默优先级高
            self.sight = False
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
        self.cookies: dict = {"cf-cs-k-20181214": cookies}  # cookies 中"cf-cs-k-20181214"（必须）
        self.offset = 0
        self._ctx = list()
        self.headers: dict = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75",
            "Accept": "application/json",
            "Origin": "https://cowtransfer.com",
            "Referer": "https://cowtransfer.com/"
        }  # 请求头
        self.uploadHeaders: dict = self.headers  # 上传文件请求头
        self._chunk: int = 4194304  # 区大小
        self.start_time = time.time()
        self.file: dict = dict()  # 文件信息
        self.raw: dict = dict()  # 输出结果

    def _request_logs(self, url, res, upload=False, length=""):
        console.log(Panel("[bold blue]PointEnd:[/]", expand=False))
        console.log(url)
        console.log(Panel("[bold magenta]Headers:[/]", expand=False))
        console.log(res.request.headers)
        console.log(Panel("[bold cyan]Body:[/bold cyan]", expand=False))
        if upload:
            console.log("[bold green]File-length:[/bold green][cyan]{}[/]".format(length))
        else:
            console.log(res.request.body)
        console.log(Panel("[bold green]Return:[/bold green]", expand=False))
        console.log(res.json())

    def _convertBytes(self, bytes, lst=None):  # 进制转换
        if lst is None:
            lst = ["Bytes", "KB", "MB", "GB", "TB", "PB"]
        i = int(math.floor(  # 舍弃小数点，取小
            math.log(bytes, 1024)  # 求对数(对数：若 a**b = N 则 b 叫做以 a 为底 N 的对数)
        ))

        if i >= len(lst):
            i = len(lst) - 1
        return ("%.2f" + " " + lst[i]) % (bytes / math.pow(1024, i))

    def _look_file(self, path):  # 文件信息读取
        self.file["size"]: int = os.path.getsize(path)  # 上传文件大小
        self.file["type"]: str = magic.Magic(mime=True, uncompress=True).from_file(path)  # 上传文件类型
        self.file["original_name"]: str = re.search("[^\\\\]+$", path)[0]  # 上传文件名字
        self.file["name"]: str = parse.quote(self.file["original_name"])  # 上传文件名字(Url编码)
        self.file["path"] = path  # 文件地址
        if self.slight and not self.silence:  # 详细日志
            console.log(Rule("[bold yellow]Step 1/7 [/][bold cyan]File Scan[/]"))
            table = RenderGroup(
                Panel(self.file["name"], title="文件名称", title_align="left"),
                Panel(self.file["type"], title="文件属性", title_align="left"),
                Panel(str(self.file["size"]), title="[yellow]文件大小[Bytes][/]", title_align="left"),
                Panel(self.file["path"], title="[cyan]文件路径[/]", title_align="left")
            )
            # self._convertBytes(self.file["size"], ["Bytes", "KB", "MB", "GB", "TB", "PB"])
            console.log(Panel(table, title="[magenta]文件信息[/]"))

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
                "totalSize": str(self.file["size"]),
                "message": message,
                "notifyEmail": notifyEmail,
                "validDays": str(validDays),
                "saveToMyCloud": str(json.dumps(saveToMyCloud)),
                "downloadTimes": str(downloadTimes),
                "smsReceivers": smsReceivers,
                "emailReceivers": emailReceivers,
                "enableShareToOthers": str(json.dumps(enableShareToOthers)),
                "language": language,
                "enableDownload": str(json.dumps(enableDownload)),
                "enablePreview": str(json.dumps(enablePreview))
            },
            boundary="----WebKitFormBoundaryJ2aGzfsg35YqeT7X"
        )
        self.headers["Content-Type"] = multipart.content_type
        res = requests.post(self._prepareSend, headers=self.headers, data=multipart, cookies=self.cookies,
                            **self.requests_kwargs)
        self.cookies.update(res.cookies.get_dict())  # 更新cookies中JSESSIONID，SERVERID（必须）
        result = res.json()
        if self.slight and not self.silence:  # 详细日志
            console.log(Rule("[bold yellow]Step 2/7 [/][bold cyan]Prepare Upload[/]"))
            self._request_logs(self._prepareSend, res)
        if result["error"]:
            error_console.log(Panel("[yellow]{}[/yellow]".format(result["error_message"]),
                                    title="[bold red]错误信息[/bold red]"))
        self.uploadHeaders["Authorization"] = "UpToken " + result["uptoken"]  # 添加uptoken密钥
        self.transferGuid: str = result["transferguid"]
        self.prefix: str = result["prefix"]
        self.raw["qrcode"]: str = result["qrcode"]
        self.raw["uniqueurl"]: str = result["uniqueurl"]
        self.key: str = self.prefix + "/" + self.transferGuid + "/" + self.file["name"]
        self._key: str = self._tobase64(self.key.encode("utf-8"))
        return self._before()

    def _before(self):
        multipart = MultipartEncoder(
            fields={
                "type": self.file["type"],
                "fileId": "",
                "fileName": self.file["name"],
                "originalName": self.file["original_name"],
                "fileSize": str(self.file["size"]),
                "transferGuid": self.transferGuid,
                "storagePrefix": self.prefix,
                "unfinishPath": "",
            },
            boundary="----WebKitFormBoundaryJ2aGzfsg35YqeT7X"
        )
        self.headers["Content-Type"] = multipart.content_type
        res = requests.post(self._beforeUpload, headers=self.headers, data=multipart, cookies=self.cookies,
                            **self.requests_kwargs)
        result = res.json()
        if self.slight and not self.silence:  # 详细日志
            console.log(Rule("[bold yellow]Step 3/7 [/][bold cyan]Before Upload[/]"))
            self._request_logs(self._beforeUpload, res)
        self.fileGuid = result["fileGuid"]
        return self._uploader()

    def _uploader(self):
        num = 0
        sum = math.ceil(self.file["size"] / (self._chunk - 135))
        upload_bar = progress.add_task("[cyan]Upload...", total=self.file["size"])
        if self.silence:
            progress.update(upload_bar, visible=False)
        with open(self.file["path"], "rb") as f:  # 流式上传
            file = bytes()
            # if self.file["size"] < (self._chunk - 123)
            with progress:
                while True:
                    temp = f.read(self._chunk)
                    file += temp
                    if len(temp) != 0:
                        length = len(temp)
                        url = self._uploadInitEndpoint.format(str(length))

                        self.uploadHeaders["Content-Type"] = "application/octet-stream; " \
                                                             "boundary=----WebKitFormBoundaryJ2aGzfsg35YqeT7X"
                        res = requests.post(url, headers=self.uploadHeaders, data=temp, **self.requests_kwargs)
                        result = res.json()
                        num += 1
                        # 进度条更新
                        progress.update(upload_bar,
                                        advance=len(temp),
                                        description="[cyan]Upload...[/][magenta]Block:{}/{}[/]".format(num, sum))

                        if self.slight and not self.silence:  # 详细日志
                            console.log(Rule("[bold yellow]Step 4/7 [/][bold cyan]Uploading...[/]"))
                            console.log(
                                Rule("[bold magenta]Block {}/{} [/][bold cyan]Uploading...[/]".format(num, sum)))
                            self._request_logs(url, res, True, str(length))
                        self._ctx.append(result["ctx"])
                        self.offset += result["offset"]
                    else:
                        self.fileHash = hash(file)
                        break
        return self._merge_file()

    def _merge_file(self):
        fname = self._tobase64(self.file["name"].encode("utf-8"))
        url = self._uploadMergeFile.format(self.file["size"], self._key, fname)
        ctx = ",".join(self._ctx)
        self.uploadHeaders["Content-Type"] = "text/plain; boundary=----WebKitFormBoundaryJ2aGzfsg35YqeT7X"
        res = requests.post(url, data=ctx,
                            headers=self.uploadHeaders, **self.requests_kwargs)
        result = res.json()
        if self.slight and not self.silence:  # 详细日志
            console.log(Rule("[bold yellow]Step 5/7 [/][bold cyan]Merge File[/]"))
            self._request_logs(url, res)  # 详细日志
        try:
            self.raw["hash"]: str = result["hash"]
        except KeyError:
            error_console.log(Panel("[yellow]{}[/yellow]".format(result["error"]), title="[bold red]错误信息[/]"))
        return self._uploaded()

    def _uploaded(self):
        multipart = MultipartEncoder(
            fields={
                "fileGuid": str(self.fileGuid),
                "hash": str(self.raw["hash"]),
                "transferGuid": str(self.transferGuid)
            },
            boundary="----WebKitFormBoundaryJ2aGzfsg35YqeT7X"
        )

        self.headers["Content-Type"] = multipart.content_type
        res = requests.post(self._uploadFinish, data=multipart,
                            headers=self.headers,
                            cookies=self.cookies, **self.requests_kwargs)

        result = res.json()
        if not result:
            error_console.log(Panel("[bold yellow]上传失败[/]", title="[bold red]错误信息[/]"))
        if self.slight and not self.silence:  # 详细日志
            console.log(Rule("[bold yellow]Step 6/7 [/][bold cyan]Uploaded[/]"))
            self._request_logs(self._uploadFinish, res)

        return self._complete()

    def _complete(self):
        multipart = MultipartEncoder(
            fields={
                "transferGuid": str(self.transferGuid)
            },
            boundary="----WebKitFormBoundaryJ2aGzfsg35YqeT7X"
        )
        self.headers["Content-Type"] = multipart.content_type
        res = requests.post(self._uploadComplete, data=multipart, headers=self.headers, cookies=self.cookies,
                            **self.requests_kwargs)
        result = res.json()
        self.raw["tempDownloadCode"]: int = result["tempDownloadCode"]
        self.raw["complete"]: bool = result["complete"]
        if self.slight and not self.silence:  # 详细日志
            console.log(Rule("[bold yellow]Step 7/7 [/][bold cyan]Complete Upload[/]"))
            self._request_logs(self._uploadComplete, res)
            console.log(Rule("[bold cyan]详细日志结束[/]"))
        end_time = time.time()
        self.raw['time']: str = (end_time - self.start_time).__str__()
        if result["complete"] and not self.silence:
            console.log(Panel(self.file["original_name"], title="文件名称"))
            console.log(
                Columns([Panel("{} Bytes".format(self.file["size"]), title="文件大小"),
                         Panel("[bold magenta]{}[/]".format(self.raw['time'] + " s"),
                               title="[magenta]消耗时间[/]"),
                         Panel("[bold blue]{}[/]".format(self.raw["uniqueurl"]), title="[blue]下载地址[/]"),
                         Panel("[bold yellow]{}[/]".format(self.raw["tempDownloadCode"]), title="[yellow]取件密码[/]")])
            )
        elif not result["complete"]:
            error_console.log(Panel("[bold yellow]上传失败[/]", title="[bold red]错误信息[/]"))

    def upload(self,
               path: str = "",
               message: str = "",
               notifyEmail: str = "",
               validDays: int = -1,
               saveToMyCloud: bool = False,
               downloadTimes: int = -1,
               smsReceivers: str = "",
               emailReceivers: str = "",
               enableShareToOthers: bool = False,
               language: str = "cn",
               enableDownload: bool = True,
               enablePreview: bool = True
               ) -> dict:
        self._prepare(path, message, notifyEmail, validDays, saveToMyCloud, downloadTimes, smsReceivers,
                      emailReceivers, enableShareToOthers, language, enableDownload, enablePreview)
        return {'file': self.file, 'raw': self.raw}
