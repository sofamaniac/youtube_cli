"""Just a simple logger"""
import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="youtube_cli.log",
    filemode="w",
    format="%(asctime)s:%(filename)10s:%(message)s",
)
