import os
import pathlib
import traceback

__all__ = [
    "multi_download",
]


def multi_download(
        use_loc: str,
        network: str,
        max_parallel: int,
        share_url: str,
        access_code=str,
        prefix=None,
        key=None,
        debug=False
):

    from .share_cp import share_cp_with_cmdargs_output

    home = pathlib.Path(os.path.expanduser("~")) / ".sdk_download"
    if not home.exists():
        home.mkdir(parents=True)

    config_public = home / "ks3utilconfig.public"
    if not config_public.exists():
        with config_public.open("w") as f:
            f.write("""[Credentials]
language
accessKeyID=public
accessKeySecret=secret
endpoint=ks3-cn-beijing.ksyuncs.com
loglevel=info""")

    config_private = home / "ks3utilconfig.private"
    if not config_private.exists():
        with config_private.open("w") as f:
            f.write("""[Credentials]
language
accessKeyID=private
accessKeySecret=secret
endpoint=ks3-cn-beijing-internal.ksyuncs.com
loglevel=info
""")

    try:
        config_path = config_private.absolute().__str__()
        if network == "public":
            config_path = config_public.absolute().__str__()

        share_cp_with_cmdargs_output(
            share_url,
            access_code,
            use_loc,
            max_parallel,
            config_path,
            prefix=prefix,
            key=key,
            debug=debug
        )
    except Exception as e:
        if debug:
            print(e)
            traceback.print_exc()

