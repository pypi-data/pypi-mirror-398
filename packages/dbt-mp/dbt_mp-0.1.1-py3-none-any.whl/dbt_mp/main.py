import argparse
import json
import subprocess
import sys
import logging

def run_dbt_ls(select_statement: str = ''):
    """
    Runs the 'dbt ls' command with the given selection statement
    and returns a list of JSON objects, one for each resource.
    """
    # Corrected command: removed 'macro' from resource types
    try:
        command = [
            "dbt", 
            "ls", 
            "--resource-type", 
            "model", 
            "source", 
            "--output", 
            "json"
            ] 
        command = command + ["--select", select_statement] if select_statement else command
        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        # The output is a series of JSON objects, one per line.
        return [line for line in result.stdout.strip().split('\n') if line]
    except FileNotFoundError:
        print("Error: 'dbt' command not found. Make sure dbt is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error executing dbt command: {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def slim_node(node):
    """
    Returns a slimmed-down version of a manifest node dictionary,
    based on the keys defined in memory.md.
    """
    config = node.get('config', {})
    return {
        'schema': node.get('schema'),
        'name': node.get('name'),
        'resource_type': node.get('resource_type'),
        'unique_id': node.get('unique_id'),
        'config': {
            'materialized': config.get('materialized'),
            'enabled': config.get('enabled'),
            'incremental_strategy': config.get('incremental_strategy')
        },
        'tags': node.get('tags'),
        'columns': node.get('columns'),
        'raw_code': node.get('raw_code'),
        'refs': node.get('refs'),
        'sources': node.get('sources'),
        'depends_on': node.get('depends_on'),
        'compiled_code': node.get('compiled_code')
    }
    
def slim_source(source):
    """
    Returns a slimmed-down version of a manifest source dictionary.
    """
    return {
        'database': source.get('database'),
        'schema': source.get('schema'),
        'name': source.get('name'),
        'unique_id': source.get('unique_id'),
        'description': source.get('description')
    }

def slim_macro(macro):
    """
    Returns a slimmed-down version of a manifest macro dictionary.
    """
    return {
        'unique_id': macro.get('unique_id'),
        'macro_sql': macro.get('macro_sql')
    }


def main():
    """
    Main entry point for the dbt-mp CLI tool.
    """
    parser = argparse.ArgumentParser(
        description="A CLI tool to parse and filter dbt manifest.json files."
    )

    parser.add_argument(
        "--select",
        required=False,
        help="The dbt selection syntax to filter the manifest. (e.g., '+stg_orders')",
    )

    parser.add_argument(
        "--manifest-path",
        default="target/manifest.json",
        help="The path to the manifest.json file. Defaults to 'target/manifest.json'."
    )
    
    parser.add_argument(
        "--out-file",
        help="The path to write the filtered manifest JSON file.",
        default='manifest_slim.json'
    )

    args = parser.parse_args()

    # Compile and load the full manifest.json
    try:
        compile_command = ["dbt", "compile", "--select", args.select] if args.select else ["dbt", "compile"]
        print("Compiling models sql with command: " + ' '.join(compile_command))
        subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            check=True,
        )
        
        with open(args.manifest_path, 'r') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"Error: Manifest file not found at '{args.manifest_path}'", file=sys.stderr)
        print("Please run 'dbt compile' or another dbt command to generate it.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{args.manifest_path}'.", file=sys.stderr)
        sys.exit(1)
    
    # Run 'dbt ls' to get the list of selected models and sources
    ls_output_lines = run_dbt_ls(args.select)
    
    selected_unique_ids = []
    for line in ls_output_lines:
        if line.startswith('{'):
            try:
                json_line = json.loads(line)
                selected_unique_ids.append(json_line.get('unique_id'))
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from dbt ls output line: {line}", file=sys.stderr)
        else:
            print(line)
            
    selected_unique_ids = [uid for uid in selected_unique_ids if uid]
    print(f"Found {len(selected_unique_ids)} matching models and sources from 'dbt ls'.")


    # Find all dependent macros
    dependent_macros = set()
    for unique_id in selected_unique_ids:
        node = manifest['nodes'].get(unique_id)
        if node:
            # Add macros from the 'depends_on' dictionary
            macros_in_node = node.get('depends_on', {}).get('macros', [])
            for macro_id in macros_in_node:
                dependent_macros.add(macro_id)

    print(f"Found {len(dependent_macros)} dependent macros.")
    
    # Combine the selected nodes with their dependent macros
    final_selection_set = set(selected_unique_ids) | dependent_macros

    # Filter the manifest and slim it down
    slim_manifest = {
        'nodes': {},
        'sources': {},
        'macros': {}
    }

    # Filter and slim nodes
    for unique_id, node in manifest.get('nodes', {}).items():
        if unique_id in final_selection_set:
            slim_manifest['nodes'][unique_id] = slim_node(node)
            
    # Filter and slim sources
    for unique_id, source in manifest.get('sources', {}).items():
        if unique_id in final_selection_set:
            slim_manifest['sources'][unique_id] = slim_source(source)

    # Filter and slim macros
    for unique_id, macro in manifest.get('macros', {}).items():
        if unique_id in final_selection_set:
            slim_manifest['macros'][unique_id] = slim_macro(macro)

    # 5. Write the result to the output file
    try:
        with open(args.out_file, 'w') as f:
            json.dump(slim_manifest, f, indent=2)
        print(f"Successfully wrote slimmed manifest to '{args.out_file}'")
    except IOError as e:
        print(f"Error writing to file '{args.out_file}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()