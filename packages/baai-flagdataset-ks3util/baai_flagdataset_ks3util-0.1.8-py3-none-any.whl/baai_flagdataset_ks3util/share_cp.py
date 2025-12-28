import os
import time
import pathlib
import subprocess


from .baai_prepare import ks3util


def debug_cmd_share_cp(cmd_args):
    print(" ".join(cmd_args))


def share_cp_with_cmdargs_output(
        share_url,
        access_code,
        use_loc,
        max_parallel: int,
        config_path:str,
        prefix=None,
        key=None,
        debug=False,
        proxy=None
):
    import colorama

    colorama.init()

    local_dir = pathlib.Path(use_loc).absolute().__str__()

    cmd_args = [
        ks3util(),
        "share-cp",
        share_url,
        local_dir,
        "--access-code",
        access_code,
        "-c",
        config_path,
        "-u",
        "-j",
        f"{max_parallel}"
    ]

    if prefix:
        cmd_args.append("--prefix")
        cmd_args.append(prefix)

    if key:
        cmd_args.append("--key")
        cmd_args.append(key)

    if debug:
        debug_cmd_share_cp(cmd_args)

    if proxy and proxy.startswith("http"):
        cmd_args.append("--proxy")
        cmd_args.append(proxy)

    if os.path.exists("output.log"):
        os.remove("output.log")

    with open("process.log", "w", encoding="utf-8") as f:
        process = subprocess.Popen(
            cmd_args,
            stdout=f,  # 直接写入文件，最可靠
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1
        )

    last_size = 0
    while process.poll() is None:
        current_size = os.path.getsize("process.log")
        if current_size > last_size:
            # 读取新增内容并显示
            with open("process.log", "r", encoding="utf-8") as read_f:
                read_f.seek(last_size)
                new_content = read_f.read()
                if new_content.startswith("["):
                    pbar_format_output(new_content)
                last_size = current_size

        time.sleep(0.1)  # 避免过于频繁检查

    # 读取最后的内容
    with open("process.log", "r", encoding="utf-8") as read_f:
        read_f.seek(last_size)
        final_content = read_f.read()

        pos = final_content.find("Succeed")
        try:
            pbar_format_output("[" + final_content[:pos].rsplit("[")[-1])
        except Exception: # noqa
            pass

        print("")
        print(final_content[pos:], end='', flush=True)


def pbar_format_output(message):


    print('\033[2K\033[1G' + message.replace('\n', '').replace('\r', ''), end="", flush=True)
    pass
