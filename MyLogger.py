import sys
import os
import logging

def basic_logger(name=__name__, output_dir='.', console_level=logging.INFO):
    """
    Created with help from http://aykutakin.wordpress.com/2013/08/06/logging-to-console-and-file-in-python/
    console_level is the level of logging that will be output to the console
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("LOG:%(name)s:%(levelname)8s:    %(message)s")

    # Create a console handler (Level: INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(console_level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create an error file handler (Level: ERROR)
    out_file = os.path.join(output_dir, "error.log")
    # Remove the old file if it exists
    try:
        os.remove(out_file)
    except OSError:
        pass
    handler = logging.FileHandler(out_file, "w", encoding=None, delay="true") # TODO: learn what these flags do
    handler.setLevel(logging.ERROR)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Create a debug file handler (Level: DEBUG)
    out_file = os.path.join(output_dir, "debug.log")
    try:
        os.remove(out_file)
    except OSError:
        pass
    handler = logging.FileHandler(out_file, "w")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
logger = basic_logger()