import asyncio
import importlib
import json
import os
import pathlib
import sys
import textwrap
import typer
from typing import Optional
from CowtransferAPI.upload import CowUpload
from CowtransferAPI.__version__ import __version__

app = typer.Typer()
sli = None


def main(slight: Optional[str] = typer.Option(False, help="是否开启精细化日志")):
    global sli
    sli = slight


@app.command()
def version():
    """
    查看版本号
    """
    typer.echo(f'当前CowtransferAPI版本为: ' + typer.style(__version__, fg=typer.colors.GREEN, bold=True))


@app.command()
def upload(path: str = typer.Argument(..., help="请输入您需要上传文件的路径"),
           cookie: str = typer.Argument('1610272831475'),
           proxy: str = typer.Argument(None),
           verify: bool = typer.Argument(False),
           ):
    """
        上传文件
    """
    upload_session = CowUpload(sli, cookies=cookie, proxies=proxy, verify=verify)
    upload_session.upload(path=path)


if __name__ == "__main__":
    app()
