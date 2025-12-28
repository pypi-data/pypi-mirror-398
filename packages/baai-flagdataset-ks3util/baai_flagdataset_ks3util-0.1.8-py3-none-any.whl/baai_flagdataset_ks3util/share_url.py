import os
import subprocess
import pathlib

from .baai_prepare import ks3util


home = pathlib.Path(os.path.expanduser("~")) / ".sdk_download"
if not home.exists():
    home.mkdir(parents=True)

config_public = home / "ks3utilconfig"
if not config_public.exists():
    with config_public.open("w") as f:
        f.write("""[Credentials]
language
accessKeyID=public
accessKeySecret=secret
endpoint=ks3-cn-beijing.ksyuncs.com
loglevel=info""")


def _get_share_url(output: str):
    lines = output.split("\n")
    for line in lines:
        if line.startswith("http"):
            return line
    print("未找到分享链接: \n",  output)
    raise Exception("无法生成分享链接")


def get_share_url(dir_path, ak=None, sk=None):
    import random


    # 生产6位随机数
    access_code = f"{random.randint(100000, 999999)}"

    cmd_args = [
        ks3util(),
        "share-create",
        "--access-code",
        access_code,
        "--valid-period",
        "30d",
        "-c",
        config_public,
        dir_path,
    ]

    if ak and sk:
        cmd_args.append("-i")
        cmd_args.append(ak)
        cmd_args.append("-k")
        cmd_args.append(sk)

    result = subprocess.run(
        cmd_args,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    return _get_share_url(result.stdout), access_code

