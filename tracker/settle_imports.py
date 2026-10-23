"""python -m tracker.settle_imports [--write]; default is read-only."""
import argparse
from pathlib import Path
from .journal import journal
from .storage import LocalStore
from .results import verify_pending, save_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    store = LocalStore(Path('.'))
    candidates, errors = verify_pending(journal(store))
    for error in errors:
        print(error)
    print('Confirmed results:', len(candidates))
    if args.write:
        print('Saved:', save_results(store, candidates))


if __name__ == '__main__':
    main()
