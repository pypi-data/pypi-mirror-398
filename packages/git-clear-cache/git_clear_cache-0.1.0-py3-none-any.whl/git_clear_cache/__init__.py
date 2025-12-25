import argparse
from .core import GitCacheRemover


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*', type=str)
    parser.add_argument('--recursive', '-r', action='store_true')
    parser.add_argument('--force', '-f', action='store_true')
    parser.add_argument('--log', '-l', action='store_true')

    args = parser.parse_args()
    remover = GitCacheRemover(*args.paths, recursive=args.recursive, force=args.force, log_mode=args.log)
    remover.run()


if __name__ == '__main__':
    main()
