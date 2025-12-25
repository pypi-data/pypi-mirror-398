import sys
import argparse

from . import CSVTree


def print_statistics(**kwargs) -> int:

    csvt = CSVTree(**kwargs)
    csvs = csvt.get_statistics()
    assert isinstance(csvs, dict), type(csvs)
    assert 0 < len(csvs)

    max_k_width = max(len(    k ) for k in csvs.keys  ())
    max_v_width = max(len(str(v)) for v in csvs.values())

    for k, v in csvs.items():
        k =     k .ljust(max_k_width)
        v = str(v).rjust(max_v_width)
        sys.stdout.write(f'{k}{" "*2}{v}\n')

    return 0


def main() -> int:
    
    # pr: parser root
    pr = argparse.ArgumentParser()

    pr.add_argument(
        'csv_file_path'
    )
    pr.set_defaults(
        func = print_statistics
    )

    args = pr.parse_args()
    del pr
    args = vars(args)
    
    func = args.pop('func')
    return func(**args)



if '__main__' == __name__:
    sys.exit(main())




