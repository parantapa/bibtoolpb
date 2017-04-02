"""
Sanity check a BibTeX file.
"""

import re
from collections import defaultdict

import click
from pybtex.database import parse_file

from bibtoolpb import cli, parse_good_key

NEEDED_FIELDS = {
    "inproceedings": "title author booktitle year location pages doi",
    "article": "title author journal year volume number pages doi",
    "book": "title author|editor publisher year",
    "misc": "title author|key howpublished",
}
NEEDED_FIELDS = {k: set(v.split()) for k, v in NEEDED_FIELDS.items()}

def is_good_key(key):
    try:
        _ = parse_good_key(key)
        return True
    except ValueError:
        return False

def is_good_page(p):
    p = p.split(":")
    if len(p) == 1 and p[0].isdigit():
        return True
    if len(p) == 2 and p[0].isdigit() and p[1].isdigit():
        return True
    return False

def is_good_pages(e):
    if "pages" not in e.fields:
        return True

    pp = e.fields["pages"]
    pp = pp.split("--")
    return len(pp) == 2 and is_good_page(pp[0]) and is_good_page(pp[1]) and pp[0] != pp[1]

def get_missing_fields(e, fs):
    """
    Return the missing fields.
    """

    if "biblint" in e.fields:
        directives = e.fields["biblint"]
        directives = directives.strip().split(",")
        directives = set(directives)
    else:
        directives = set()

    missing = set()
    for f in fs:
        if "no" + f in directives:
            continue

        for x in f.split("|"):
            if x in e.fields or x in e.persons:
                break
        else:
            missing.add(f)

    return missing

def missing_fields(e):
    """
    Check if the entry has the required fields.
    """

    try:
        fs = NEEDED_FIELDS[e.type]
        return get_missing_fields(e, fs)
    except KeyError:
        return set()

def missing_acceptable(missing, e):
    missing = set(missing)
    try:
        _, vn, _ = parse_good_key(e.key)
        if vn in ("icwsm", "scirep"):
            missing.discard("pages")
        if vn in ("scirep",):
            missing.discard("number")
        if vn in ("aaai", "icwsm","emnlp","acl"):
            missing.discard("doi")
        return missing
    except ValueError:
        return missing

def empty_fields(e):
    """
    Check if there are any empty fields.
    """

    empty = []
    for k, v in e.fields.items():
        if not v.strip():
            empty.append(k)

    return empty

@cli.command()
@click.option("-d", "--disable-good-key-check", is_flag=True,
              help="Disable checking of good key")
@click.argument("fin", metavar="input",
                type=click.File("r"), default="-", required=False)
def check(disable_good_key_check, fin):
    """
    Check INPUT for inconsistancies.
    """

    db = parse_file(fin, "bibtex").lower()

    for key, e in db.entries.items():
        if not is_good_key(key) and disable_good_key_check is False:
            code = click.style("Bad key", fg="red")
            key = click.style(key, bold=True)
            msg = "%s: %s" % (code, key)
            click.echo(msg)

        if not is_good_pages(e):
            code = click.style("Bad pages", fg="yellow")
            key = click.style(key, bold=True)
            msg = "%s for %s: %s" % (code, key, e.fields["pages"])
            click.echo(msg)

        empty = empty_fields(e)
        if empty:
            code = click.style("Empty fields", fg="blue")
            key = click.style(key, bold=True)
            msg = "%s for %s: %s" % (code, key, " ".join(empty))
            click.echo(msg)

        missing = missing_fields(e)
        missing = missing_acceptable(missing, e)
        if missing:
            code = click.style("Missing fields", fg="magenta")
            key = click.style(key, bold=True)
            typ = click.style(e.type, fg="green")
            msg = "%s for %s: %s | %s" % (code, key, " ".join(missing), typ)
            click.echo(msg)

@cli.command()
@click.argument("fin", metavar="input",
                type=click.File("r"), default="-", required=False)
def dupcheck(fin):
    """
    Check INPUT for duplicate entries.
    """

    db = parse_file(fin, "bibtex").lower()

    tx_key_titles = defaultdict(list)
    for key, e in db.entries.items():
        if "title" not in e.fields:
            continue

        title = e.fields["title"]
        tx = title.lower()
        tx = "".join(c for c in tx if c.isalnum() or c.isspace())
        tx = " ".join(tx.split())

        tx_key_titles[tx].append((key, title))

    bold_wrap_len = len(click.style(" ", bold=True)) - 1
    for tx, key_titles in tx_key_titles.items():
        if len(key_titles) > 1:
            max_keylen = max(len(i) for i, _ in key_titles)
            fmt = "    (%%-%ds) |- %%s" % (max_keylen + bold_wrap_len)

            code = click.style("Duplicate title", fg="red")
            tx = click.style(tx, fg="yellow")
            click.echo("%s: %s" % (code, tx))

            for key, title in key_titles:
                key = click.style(key, bold=True)
                click.echo(fmt % (key, title))

def all_same(xs):
    t = xs[0][1]
    for x in xs[1:]:
        if x[1] != t:
            return False
    return True

@cli.command()
@click.argument("fin", metavar="input",
                type=click.File("r"), default="-", required=False)
def venuechk(fin):
    """
    Check consistancy in venue naming.
    """

    db = parse_file(fin, "bibtex").lower()

    venue_key_vnames = defaultdict(list)
    for key, e in db.entries.items():
        try:
            _, vn, _ = parse_good_key(key)
            if e.type == "article":
                vname = e.fields["journal"]
            if e.type == "inproceedings":
                vname = e.fields["booktitle"]
        except (ValueError, KeyError):
            continue

        vname = " ".join(vname.split())
        vname = re.sub(r"(20|19)\d{2}", "YYYY", vname)
        vname = re.sub(r"\d?(1st|2nd|3rd|\dth)", "Nth", vname)
        venue_key_vnames[vn].append((key, vname))

    bold_wrap_len = len(click.style(" ", bold=True)) - 1
    for vn, key_vnames in venue_key_vnames.items():
        if not all_same(key_vnames):
            max_keylen = max(len(i) for i, _ in key_vnames)
            fmt = "    (%%-%ds) |- %%s" % (max_keylen + bold_wrap_len)

            code = click.style("Different vn names", fg="red")
            vn = click.style(vn, fg="yellow")
            click.echo("%s: %s" % (code, vn))

            for key, vname in key_vnames:
                key = click.style(key, bold=True)
                click.echo(fmt % (key, vname))
