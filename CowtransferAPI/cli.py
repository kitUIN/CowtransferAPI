import typer
from typing import Optional
from CowtransferAPI.upload import CowUpload
from CowtransferAPI.__version__ import __version__

app = typer.Typer()


@app.command()
def version():
    """
    查看版本号
    """
    typer.echo(f'当前CowtransferAPI版本为:   ' + typer.style(__version__, fg=typer.colors.GREEN, bold=True))


@app.command()
def upload(path: str = typer.Argument(..., help="请输入您需要上传文件的路径"),
           cookie: str = typer.Argument('1610272831475', help="上传所需的cookie: cf-cs-k-20181214"),
           proxies: str = typer.Argument(None, help="代理端口例如127.0.0.1:10809"),
           verify: bool = typer.Argument(True, help="是否检查证书"),
           slight: bool = typer.Option(False, help="是否开启精细化日志"),
           silence: bool = typer.Argument(False, help="是否开启静默模式")):
    """上传文件
    """
    upload_session = CowUpload(slight, cookies=cookie, silence=silence, proxies={'http': proxies}, verify=verify)
    upload_session.upload(path=path)



