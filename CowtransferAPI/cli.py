import typer
from typing import Optional
from CowtransferAPI.upload import CowUpload
from CowtransferAPI.__version__ import __version__

app = typer.Typer()
sli = None
sil = None


def main(slight: Optional[bool] = typer.Option(False, help="是否开启精细化日志"),
         silence: Optional[bool] = typer.Option(False, help="是否开启静默模式")):
    """上传文件

        Args:
            silence[bool] = 精细日志[默认：False]
            silence[bool] = 静默模式[默认：False]
        """
    global sli, sil
    sli = slight
    sil = silence


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
           verify: bool = typer.Argument(True),
           ):
    """上传文件

    Args:
        path[str]: 您需要上传文件的路径[默认：None]
        cookie[str]: 上传所需的cookie "cf-cs-k-20181214"[默认：'1610272831475']
        proxy[str]: 代理端口[默认：None]
        verify[bool] = 检查证书[默认：True]
        silence[bool] = 静默模式[默认：False]
    """
    upload_session = CowUpload(sli, cookies=cookie, silence=sil, proxies=proxy, verify=verify)
    upload_session.upload(path=path)


if __name__ == "__main__":
    app()
