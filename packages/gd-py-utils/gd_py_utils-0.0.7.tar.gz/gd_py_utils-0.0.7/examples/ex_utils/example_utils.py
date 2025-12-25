"""
Example script demonstrating the usage of gdutils.utils modules:
- IO helpers
- Timer
- Decorators
"""

import time
import gdutils as gd
from gdutils.utils.decorators import timer, debug


def main():
    # -------------------------------------------------------------------------
    # 1. IO Utils
    # -------------------------------------------------------------------------
    print("--- IO Utils ---")
    
    # Create a directory for outputs relative to this script
    out_dir = gd.fPath(__file__, "out", mkdir=True)
    print(f"Working directory: {out_dir}")

    # Create some files
    f1 = out_dir / "data1.txt"
    f2 = out_dir / "data2.log"
    
    gd.dump_str(f1, "Important data")
    gd.dump_str(f2, "Log entry")
    print("Created files.")

    # List and read
    print(f"Content of {f1.name}: {gd.load_str(f1)}")

    # Copy files
    backup_dir = out_dir / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    gd.copy_files(out_dir / "*.txt", backup_dir)
    print(f"Copied .txt files to {backup_dir}")

    # -------------------------------------------------------------------------
    # 2. Timer
    # -------------------------------------------------------------------------
    print("\n--- Timer ---")
    
    # Simple context manager
    with gd.Timer() as t:
        time.sleep(0.2)
    print(f"Code block took {t.secs:.4f} seconds")

    # -------------------------------------------------------------------------
    # 3. Decorators
    # -------------------------------------------------------------------------
    print("\n--- Decorators ---")

    @timer
    def heavy_processing(duration):
        """Simulate work"""
        time.sleep(duration)
        return "Done"

    @debug
    def calculate_metrics(data, normalize=False):
        """Simulate function with args"""
        return {"mean": 0.5, "std": 1.2}

    # Run decorated functions
    res = heavy_processing(0.3)
    metrics = calculate_metrics([1, 2, 3], normalize=True)

    # -------------------------------------------------------------------------
    # Cleanup (Optional)
    # -------------------------------------------------------------------------
    print("\n--- Cleanup ---")
    gd.clean_dir(out_dir)
    print("Cleaned up output directory.")


if __name__ == "__main__":
    main()

