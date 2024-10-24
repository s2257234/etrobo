'''Windows環境でシミュレータを起動するためのスクリプト。
このスクリプトからシミュレータを起動することで、Windows上の（WSL上ではない）プログラムから
シミュレータに対して命令/観測値を送受信することが可能となる。
'''
import argparse
import os
import pathlib
import subprocess
import time
import urllib.error
import urllib.request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='ETロボコンのシミュレータを起動する')
    parser.add_argument(
        'version', type=int, nargs='?', default=None, help='実行するシミュレータを指定する')
    parser.add_argument(
        '--list', default=False, action='store_true', help='バージョンの一覧を表示する')
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if 'HOMEPATH' not in os.environ:
        raise Exception('Home path is not found.')

    sim_path = pathlib.Path(os.environ['HOMEPATH']) / 'etrobosim'

    if not sim_path.is_dir():
        raise Exception(f'Simulator is not installed: {sim_path}')

    versions = [
        p.name for p in sorted(sim_path.iterdir(), reverse=True)
        if p.name.startswith('etrobosim')]

    if len(versions) == 0:
        raise Exception(f'Simulator is not found: {sim_path}')

    if args.list:
        for i, v in enumerate(versions, start=1):
            print(f'[{i}] {v}')
        return True

    if args.version is not None:
        version = versions[args.version - 1]
    else:
        version = versions[0]

    path = sim_path / version / 'etrobosim.exe'
    print(f'exec: {path}')
    subprocess.Popen([str(path)])

    while True:
        try:
            req = urllib.request.Request('http://127.0.0.1:54000/')
            with urllib.request.urlopen(req) as res:
                pass
            break
        except urllib.error.URLError:
            time.sleep(0.5)
            continue

    data = '{"athrillHost":"127.0.0.1"}'.encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:54000/', data=data)
    with urllib.request.urlopen(req) as res:
        print(res.read().decode('utf-8'))


if __name__ == '__main__':
    main()
