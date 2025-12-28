import os
import urllib.request
import pathlib
import platform


HOME = pathlib.Path(os.path.expanduser("~")) / ".sdk_download"
if not HOME.exists():
    HOME.mkdir(parents=True)
PUBLIC = "https://baai-datasets.ks3-cn-beijing.ksyuncs.com/public/"


def ks3util():
    system = platform.system().lower()

    util_path = HOME / "ks3util"
    if system == "windows":
        util_path = HOME / "ks3util.exe"

    if util_path.exists():
       return util_path.absolute().__str__()

    filename = f"ks3util-{use_plat()}"
    print(f"正在下载 ks3util-{use_plat()}...")
    url = f"http://baai-datasets.ks3-cn-beijing.ksyuncs.com/public/utils/{filename}"
    save_path = os.path.join(HOME, util_path.name)
    # 下载文件
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        urllib.request.urlretrieve(url, save_path)
        # 添加执行权限
        os.chmod(save_path, 0o755)
        print(f"ks3util 已下载到: {save_path}")
    except Exception as e:
        print(f"下载失败: {e}")

    return util_path.absolute().__str__()


def use_plat():
    machine = platform.machine()
    system = platform.system().lower()

    cpu_use = machine
    if machine == "x86_64":
         cpu_use = "amd64"

    sys_use = system
    if system == "darwin":
        sys_use = f"mac"
    return f"{sys_use}-{cpu_use}"
