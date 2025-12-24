"""Mokaccino simple example."""

import sys
import mokaccino_py as mp

def main() -> None:
    """Main function."""
    result = mp.sum_as_string(3, 5)
    print(f"The result of adding 3 and 5 is: {result}")       
    return 0

if __name__ == "__main__":
    # Call main function from here
    sys.exit(main())