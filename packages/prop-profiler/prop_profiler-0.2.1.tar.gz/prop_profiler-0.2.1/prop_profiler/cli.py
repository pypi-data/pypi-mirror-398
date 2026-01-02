import argparse
import logging
import sys

import pandas as pd

from prop_profiler.utils import chem_helpers as chem
from prop_profiler.utils.logging import configure_logging
from prop_profiler.profiler import profile_molecules


def main() -> None:
    """Run the command-line interface for molecule profiling."""
    parser = argparse.ArgumentParser(
        description="Profile molecules with optional CNS-MPO/Stoplight scores"
    )
    parser.add_argument(
        '-i', '--input', required=True,
        help='Input SDF, CSV or SMI file'
    )
    parser.add_argument(
        '--no-header', action='store_true',
        help='Indicates that the input file has no header row'
    )
    parser.add_argument(
        '-c', '--column', default='smiles',
        help='Name of the SMILES column in the file. If no header, it should be the first column'
    )
    parser.add_argument(
        '-o', '--output', required=True,
        help='Output CSV path'
    )
    parser.add_argument(
        '--keep-input-data', action='store_true',
        help='Output will include input data in the output CSV'
    )
    parser.add_argument(
        '--skip-cns-mpo', action='store_true',
        help='Omit CNS-MPO scoring'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Display progress bars'
    )
    parser.add_argument(
        '--device', default='cpu',
        help='Device to run the pKa model on, "cpu" or "cuda"'
    )

    args = parser.parse_args()
    configure_logging(logging.DEBUG if args.verbose else logging.INFO)

    try:
        # Load input
        fpath = args.input
        if fpath.endswith('.sdf'):
            df_in = chem.sdf_to_df(fpath, smiles_col='smiles')
        elif fpath.endswith('.smi') or fpath.endswith('.txt') or fpath.endswith('.csv'):
            if args.no_header:
                df_in = pd.read_csv(fpath, header=None)
                df_in.rename(columns={0: 'smiles'}, inplace=True)
            else:
                df_in = pd.read_csv(fpath)
                df_in.rename(columns={args.column: 'smiles'}, inplace=True)
        else:
            print('Error: Input file must be in SDF, SMI, TXT or CSV format.', file=sys.stderr)
            sys.exit(1)
        
        smiles = df_in['smiles'].tolist()

        # Profile
        df_out = profile_molecules(
            molecules=smiles,
            skip_cns_mpo=args.skip_cns_mpo,
            device=args.device,
            verbose=args.verbose
        )

        # Save
        if args.keep_input_data:
            df_out['smiles'] = [
                chem.canonicalize(s) if chem.get_mol(s) is not None else s 
                for s in df_out['smiles'] 
            ]
            df_out = pd.merge(df_in, df_out, on='smiles', how='left')
        df_out.to_csv(args.output, index=False)

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
