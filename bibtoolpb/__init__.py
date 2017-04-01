"""
BibToolPB is a bibtex management tool.
"""

import click

def parse_good_key(key):
    """
    Good key has format <author>-<venue><dd>
    """

    head, dd = key[:-2], key[-2:]
    if not (len(dd) == 2 and dd.isdigit()):
        raise ValueError("Failed to parse key: %s" % key)

    head = head.split("-", 1)
    if len(head) != 2:
        raise ValueError("Failed to parse key: %s" % key)

    dd = int(dd)
    if dd > 70:
        dd = 1900 + dd
    else:
        dd = 2000 + dd

    return head[0], head[1], int(dd)

@click.group()
def cli():
    """
    BibToolPB is a bibtex management tool.
    """

    pass

import bibtoolpb.fmt
