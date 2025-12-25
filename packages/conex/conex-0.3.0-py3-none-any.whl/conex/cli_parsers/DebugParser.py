import argparse
import logging


def setup(parser):
    parser.add_argument("--debug", default=False, action='store_true', help=argparse.SUPPRESS)
