"""
Command-line interface for optimization-benchmarks package.

Provides utilities to evaluate benchmark functions from the command line,
supporting single evaluations, batch processing from CSV files, function
introspection, and metadata queries.

Version 0.1.1 adds metadata support for bounds, dimensions, and known minima.

Part of the optimization-benchmarks package[1].

References:
-----------
[1] Adorio, E. P. (2005). MVF - Multivariate Test Functions Library in C.
"""

import argparse
import csv
import inspect
import json
import sys

from optimization_benchmarks import BENCHMARK_SUITE, functions, get_all_functions, get_function_info


def get_available_functions():
    """
    Retrieve a sorted list of all available function names.
    Now uses metadata module for consistency.
    """
    return get_all_functions()


def print_function_list():
    """
    Print the list of available functions with metadata information.
    Enhanced in v0.1.1 to show dimensions and known minima.
    """
    print("=" * 80)
    print("Available Benchmark Functions")
    print("=" * 80)
    print(f"{'Function':<25} | {'Dim':>3} | {'Known Min':>12} | {'Bounds'}")
    print("-" * 80)

    for name in get_all_functions():
        if name in BENCHMARK_SUITE:
            meta = BENCHMARK_SUITE[name]
            bounds_str = str(meta["bounds"][0]) if len(meta["bounds"]) == 1 else "varied"
            print(
                f"{name:<25} | {meta['default_dim']:3d} | {meta['known_minimum']:12.4f} | {bounds_str}"
            )
        else:
            # Fallback for functions not in metadata
            print(f"{name:<25} | {'?':>3} | {'?':>12} | ?")

    print("=" * 80)
    print(f"Total: {len(get_all_functions())} functions")


def print_function_info(func_name):
    """
    Print comprehensive information for the specified function.
    Enhanced in v0.1.1 to include metadata.
    """
    if not hasattr(functions, func_name):
        print(f"Error: Function '{func_name}' not found.", file=sys.stderr)
        sys.exit(1)

    func = getattr(functions, func_name)
    doc = inspect.getdoc(func)

    print("=" * 80)
    print(f"Function: {func_name}")
    print("=" * 80)

    # Show documentation
    if doc:
        print(f"\nDocumentation:\n{doc}\n")
    else:
        print("\nNo documentation available.\n")

    # Show metadata if available
    if func_name in BENCHMARK_SUITE:
        meta = BENCHMARK_SUITE[func_name]
        print("Metadata:")
        print(f"  Dimension:      {meta['default_dim']}")
        print(f"  Bounds:         {meta['bounds']}")
        print(f"  Known minimum:  {meta['known_minimum']}")
        if meta["optimal_point"] is not None:
            print(f"  Optimal point:  {meta['optimal_point']}")
    else:
        print("Metadata: Not available")

    print("=" * 80)


def print_metadata(func_name):
    """
    Print only metadata for the specified function.
    New in v0.1.1.
    """
    if func_name not in BENCHMARK_SUITE:
        print(f"Error: No metadata available for function '{func_name}'.", file=sys.stderr)
        sys.exit(1)

    meta = BENCHMARK_SUITE[func_name]

    metadata_dict = {
        "function": func_name,
        "default_dimension": meta["default_dim"],
        "bounds": meta["bounds"],
        "known_minimum": meta["known_minimum"],
        "optimal_point": meta["optimal_point"],
    }

    print(json.dumps(metadata_dict, indent=2))


def evaluate_function(func_name, values):
    """
    Evaluate the given function with the provided input values.
    Returns a dictionary containing the input and the result.
    """
    if not hasattr(functions, func_name):
        print(f"Error: Function '{func_name}' not found.", file=sys.stderr)
        sys.exit(1)

    func = getattr(functions, func_name)

    try:
        # Convert input values to float
        x = [float(v) for v in values]
    except ValueError as e:
        print(f"Error: Unable to convert input values to float: {e}", file=sys.stderr)
        sys.exit(1)

    result = func(x)
    return {"input": x, "result": result}


def evaluate_function_batch(func_name, input_file):
    """
    Evaluate the given function on a batch of input vectors from a CSV file.
    Returns a list of dictionaries with inputs and results.
    """
    results = []

    if not hasattr(functions, func_name):
        print(f"Error: Function '{func_name}' not found.", file=sys.stderr)
        sys.exit(1)

    func = getattr(functions, func_name)

    try:
        with open(input_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row_num, row in enumerate(reader, start=1):
                if not row:
                    continue  # Skip empty lines

                try:
                    x = [float(v) for v in row]
                except ValueError as e:
                    print(f"Error: Invalid number in CSV at line {row_num}: {e}", file=sys.stderr)
                    sys.exit(1)

                result = func(x)
                results.append({"input": x, "result": result})

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file '{input_file}': {e}", file=sys.stderr)
        sys.exit(1)

    return results


def main():
    """
    Entry point for the optimization_benchmarks CLI.
    """
    parser = argparse.ArgumentParser(
        description="Command-line interface for evaluating optimization benchmark functions.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  optbench --list\n"
            "  optbench --info ackley\n"
            "  optbench --metadata ackley\n"
            "  optbench --function ackley --values 0 0 0\n"
            "  optbench --function rastrigin --input points.csv --output results.json\n"
        ),
    )

    parser.add_argument(
        "--list", action="store_true", help="List all available functions with metadata"
    )
    parser.add_argument(
        "--info",
        metavar="FUNCTION",
        help="Show documentation and metadata for the specified function",
    )
    parser.add_argument(
        "--metadata",
        metavar="FUNCTION",
        help="Show only metadata for the specified function (JSON format)",
    )
    parser.add_argument("--function", metavar="FUNCTION", help="Name of the function to evaluate")
    parser.add_argument(
        "--values",
        metavar="N",
        nargs="+",
        help="Input values for single evaluation (space-separated)",
    )
    parser.add_argument(
        "--input", metavar="FILE", help="CSV file with input vectors for batch evaluation"
    )
    parser.add_argument(
        "--output", metavar="FILE", help="Output file to write results in JSON format"
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        if args.info or args.metadata or args.function or args.values or args.input or args.output:
            print("Error: --list cannot be combined with other options.", file=sys.stderr)
            sys.exit(1)
        print_function_list()
        sys.exit(0)

    # Handle --info
    if args.info is not None:
        if args.metadata or args.function or args.values or args.input or args.output:
            print("Error: --info cannot be combined with other options.", file=sys.stderr)
            sys.exit(1)
        print_function_info(args.info)
        sys.exit(0)

    # Handle --metadata
    if args.metadata is not None:
        if args.info or args.function or args.values or args.input or args.output:
            print("Error: --metadata cannot be combined with other options.", file=sys.stderr)
            sys.exit(1)
        print_metadata(args.metadata)
        sys.exit(0)

    # From here, require --function
    if not args.function:
        print("Error: --function is required for evaluation.", file=sys.stderr)
        parser.print_usage(sys.stderr)
        sys.exit(1)

    func_name = args.function

    # Determine evaluation mode
    if args.values and args.input:
        print("Error: --values and --input cannot be used together.", file=sys.stderr)
        sys.exit(1)

    if not args.values and not args.input:
        print(
            "Error: Either --values or --input must be provided for function evaluation.",
            file=sys.stderr,
        )
        parser.print_usage(sys.stderr)
        sys.exit(1)

    output_data = {"function": func_name}

    # Single evaluation
    if args.values:
        result_entry = evaluate_function(func_name, args.values)
        output_data["result"] = result_entry["result"]
        output_data["input"] = result_entry["input"]

    # Batch evaluation
    elif args.input:
        results = evaluate_function_batch(func_name, args.input)
        output_data["results"] = results

    # Output results
    output_json = json.dumps(output_data, indent=2)

    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output_json)
        except Exception as e:
            print(f"Error writing to output file '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
