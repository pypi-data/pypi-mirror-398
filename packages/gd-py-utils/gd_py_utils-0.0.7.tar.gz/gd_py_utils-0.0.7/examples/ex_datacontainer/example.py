import logging
import numpy as np


import gdutils as gd


def main():
    out = gd.fPath(__file__, "out")

    # Create a clean container
    with gd.Container(out) as ct:
        # Explicit directory creation (optional)
        ct.mkdir("results")

        # Create file paths using '/'
        input_file = ct / "inputs/data.npy"

        # Write data
        x = np.arange(10)
        np.save(input_file, x)

        y = x**2
        ct.free("output")  # delete a key
        np.save(ct / "results/output.npy", y)
        np.save(ct / "results/tt/output1.npy", y)

        # Files are automatically registered
        # and can be accessed as attributes
        log.info(f"Input file : {ct.data}")
        log.info(f"Result file: {ct.output}")
        log.info(f"Result file: {ct.get('output')}")

    # Container is now closed, infos.json is written

    # Reopen container later
    ct = gd.Container(out)

    # Attribute access still works
    log.info("Reloaded:")
    log.info(f"  data  -> {ct.data}")
    log.info(f"  output-> {ct.output}")

    # log.info("--> Tree:")
    # log.info(ct.tree())


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
