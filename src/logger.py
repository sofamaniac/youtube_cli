"""Just a simple logger"""
import logging

logging.basicConfig(
    level=logging.DEBUG,
    filename="parselog.txt",
    filemode="w",
    format="%(asctime)s:%(filename)10s:%(message)s",
)
