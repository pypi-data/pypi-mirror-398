import argparse
import os
import sys
try:
    from .pipeline import preprocess_and_save
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from vtissue.preprocessing.pipeline import preprocess_and_save

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--gene-list", default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'human_genome_GRCh38.p14.txt')))
    parser.add_argument("--output", default=None)
    parser.add_argument("--input-layer", default=None)
    parser.add_argument("--norm-method", default=None)
    parser.add_argument("--cofactor", type=float, default=5.0)
    parser.add_argument("--skip-mapping", action="store_true")
    args = parser.parse_args()
    
    # Expand directories
    all_inputs = []
    for path in args.input:
        if os.path.isdir(path):
            print(f"Scanning directory recursively: {path}")
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".h5ad") and not file.endswith("_preprocessed.h5ad"):
                        all_inputs.append(os.path.join(root, file))
        else:
            all_inputs.append(path)
            
    # Sort for deterministic order
    all_inputs.sort()
    
    if len(all_inputs) == 0:
        print("Error: No input .h5ad files found.")
        sys.exit(1)

    print(f"Inputs: {len(all_inputs)} files found")
    print(f"Gene list: {args.gene_list}")
    
    # Determine default filename base
    base = "combined"
    if len(all_inputs) == 1:
         base = os.path.splitext(os.path.basename(all_inputs[0]))[0]
    default_name = f"{base}_preprocessed.h5ad"

    out = args.output
    if out is None:
        # Use location of first file/dir provided by user to determine output dir
        first_input = args.input[0]
        if os.path.isdir(first_input):
            in_dir = os.path.abspath(first_input)
        else:
            in_dir = os.path.dirname(os.path.abspath(first_input))
        out = os.path.join(in_dir, default_name)
    else:
        # If user provided output path
        # Check if it looks like a directory (no .h5ad extension)
        if not out.endswith('.h5ad'):
            out = os.path.join(out, default_name)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    print(f"Output: {out}")
    print(f"Input layer: {args.input_layer}")
    print(f"Normalization: {args.norm_method}")
    print(f"Skip mapping: {args.skip_mapping}")
    path = preprocess_and_save(
        inputs=all_inputs,
        gene_list_path=args.gene_list,
        output_path=out,
        input_layer=args.input_layer,
        normalization_method=args.norm_method,
        normalization_cofactor=args.cofactor,
        skip_mapping=bool(args.skip_mapping)
    )
    print(path)

if __name__ == "__main__":
    main()
