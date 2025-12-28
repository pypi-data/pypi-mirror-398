import argparse
import time


def with_cmdargs():

    root_parser = argparse.ArgumentParser(add_help=False)

    parser = argparse.ArgumentParser(prog='baai-flagdataset-ks3util', description="baai-flagdataset-ks3util 命令行工具")
    subparsers = parser.add_subparsers(dest='command')

    init_parser = subparsers.add_parser('init', help='init', parents=[root_parser])
    init_parser.add_argument('--network', type=str, default="private", help='network')
    init_parser.add_argument('--bandwidth', type=int, default="100", help='bandwidth')
    init_parser.add_argument('--parallel', type=int, default="200", help='parallel')
    init_parser.set_defaults(func=init_with_cmdargs)

    cmd_args = parser.parse_args()
    if hasattr(cmd_args, 'func'):
        try:
            cmd_args.func(cmd_args)
        except Exception: # noqa
            pass
        except KeyboardInterrupt:
            print()
            pass
    else:
        parser.print_help()


def init_with_cmdargs(cmd_args):

    try:
        from ..baai_helper import baai_print

        from baai_flagdataset_ks3util.share_url import get_share_url
        from baai_flagdataset_ks3util import multi_download


        baai_print.print_figlet()

        share_url, access_code = get_share_url("ks3://baai-datasets/d714895cca28be958783d0b358ba9e56")
        print("share_url:", share_url)
        print("access_code:", access_code)
        time.sleep(2)

        use_loc = "."
        network = cmd_args.network
        parallel = cmd_args.parallel

        multi_download(use_loc, network, parallel, share_url, access_code)

    except Exception as e:
        print(e)
