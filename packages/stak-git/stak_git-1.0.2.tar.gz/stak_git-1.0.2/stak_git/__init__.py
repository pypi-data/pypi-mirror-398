"""stak - Minimal stacked changes for git."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the stak bash script."""
    # Find the stak script bundled with this package
    script_path = Path(__file__).parent / "stak"
    
    if not script_path.exists():
        print("Error: stak script not found in package", file=sys.stderr)
        sys.exit(1)
    
    try:
        result = subprocess.run(
            ["bash", str(script_path)] + sys.argv[1:],
            check=False
        )
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: bash is required to run stak", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()

