import logging
import os
import gdutils as gd


def main():
    log.info("Starting TempContainer example")

    # TempContainer creates a temporary directory that is automatically
    # cleaned up when the context manager exits.
    with gd.TempContainer() as tmp:
        log.info(f"Temporary root created at: {tmp.path}")

        # Use it just like a normal Container
        # Create a file using the slash operator
        data_file = tmp / "data.txt"

        # Write some content
        with open(data_file, "w") as f:
            f.write("Hello from TempContainer!")

        log.info(f"Created file: {tmp.data}")

        # Access registered files
        assert tmp.data.exists()
        log.info("File exists inside the context manager.")

        # Verify physical path
        assert os.path.isdir(tmp.path)

        # Save the path to check later
        temp_path = tmp.path

    # After the block, the directory should be cleaned up
    if not os.path.exists(temp_path):
        log.info(f"Cleanup successful: {temp_path} is gone.")
    else:
        log.error(f"Cleanup failed: {temp_path} still exists.")


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()
    main()
