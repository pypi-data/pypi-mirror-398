import click
from dataset_down.config.constants import VERSION
from dataset_down.downloader.downloader import download as download_inner
from dataset_down.downloader.downloader import login as login_inner
from dataset_down.update.update_check import update_check
from dataset_down.utils.system_utils import stop_dataset_down_process
from dataset_down.client.AuthClient import auth_client
def validate_input(ctx, param, value):
    if not value or value.strip() == "":
        raise click.BadParameter("input can not be blank")
    return value

@click.group()
def cli():
    pass

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version')
@click.pass_context
def cli(ctx, version):
    if version:
        click.echo(f"{VERSION}")
        ctx.exit()

@cli.command()
@click.option("--dataset-id", required=True, help="dataset ID",callback=validate_input)
@click.option("--version", default="master", help="version,default is master",callback=validate_input)
@click.option("--source-path", required=True, help="source path,if it is a directory，then download all content in it",callback=validate_input)
@click.option("--target-path", default=".", help="target local path (default: current directory)",callback=validate_input)
@click.option("--parallel", default= 1 , help = "concurrent download files number,default is 1")
@click.option("--limit-rate",  default="1M", help="limit rate,default is 1M", callback=validate_input)
@click.option("--enable-inner-network", is_flag=True,default=False,help="whether enable inner network download,True yes, False no,default is False")
def download(dataset_id: str, version: str, source_path: str , target_path: str,parallel:int,limit_rate: str,enable_inner_network: bool):
    """download a file or directory"""
    try:
        update_check()
        download_inner(
            dataset_id=dataset_id,
            source_path=source_path,
            target_path=target_path,
            version=version,
            parallel=parallel,
            limit_rate=limit_rate
        )
    except Exception as e:
        print(f"download failed: {e}")
        

@cli.command()
@click.option("--ak", required=True, help="Access Key")
@click.option("--sk", required=True, help="Secret Key")
def login(ak: str, sk: str):
    """login"""
    try:
        login_inner(ak, sk)
        update_check()
        click.echo("login success!")
    except Exception as e:
        click.echo(f"login failed,please check AK/SK! msg: {e}")



@cli.command()
def stop_running_downloading_process():
    """stop the running downloading process"""
    stop_dataset_down_process()

def main():
    cli()

if __name__ == "__main__":
    main()