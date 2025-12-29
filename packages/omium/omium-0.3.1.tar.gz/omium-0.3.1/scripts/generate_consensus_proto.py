"""
Generate Python code from consensus proto files.
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    """Generate Python proto code."""
    # Get paths
    script_dir = Path(__file__).parent
    sdk_dir = script_dir.parent.parent
    project_root = sdk_dir.parent.parent
    proto_dir = project_root / "shared" / "proto"
    consensus_proto = proto_dir / "consensus" / "consensus.proto"
    output_dir = sdk_dir / "omium" / "proto" / "consensus"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if proto file exists
    if not consensus_proto.exists():
        print(f"Error: Proto file not found: {consensus_proto}")
        sys.exit(1)
    
    # Check if grpc_tools is installed
    try:
        import grpc_tools
    except ImportError:
        print("Error: grpc_tools not installed. Install with: pip install grpcio-tools")
        sys.exit(1)
    
    print(f"Generating Python code from: {consensus_proto}")
    print(f"Output directory: {output_dir}")
    
    # Generate Python code
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={proto_dir}",
        f"--proto_path={proto_dir / 'common'}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        str(consensus_proto),
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error generating proto code:")
        print(result.stderr)
        sys.exit(1)
    
    print("✅ Proto code generated successfully!")
    print(f"Files generated in: {output_dir}")
    
    # Create __init__.py
    init_file = output_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Consensus proto generated code."""\n')
    
    print("✅ Done!")

if __name__ == "__main__":
    main()

