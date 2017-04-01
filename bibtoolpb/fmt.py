"""
Clean up the INPUT bibtex file and write to OUTPUT
"""

import click
from pybtex.database import parse_file
from pybtex.database.output.bibtex import Writer as _BaseWriter

from bibtoolpb import cli, parse_good_key

def entry_sort_fn(e):
    try:
        author, venue, dd = parse_good_key(e.key)
        return (-dd, venue, author)
    except ValueError:
        if "year" in e.fields and e.fields["year"].isdigit():
            return (-9999 + int(e.fields["year"]), e.key, "")
        else:
            return (-99999, e.key, "")

class Writer(_BaseWriter):
    """
    Output bibtex markup.
    """

    def write_entry(self, entry, stream):
        """
        Write single entry to the output.
        """

        key = entry.key
        stream.write('\n')

        stream.write('@%s' % entry.original_type)
        stream.write('{%s' % key)
#            for role in ('author', 'editor'):
        for role, persons in entry.persons.items():
            self._write_persons(stream, persons, role)
        for typ, value in entry.fields.items():
            self._write_field(stream, typ, value)
        stream.write('\n}\n')

    def write_stream(self, bib_data, stream):
        """
        Write the bibtex to the output.
        """

        self._write_preamble(stream, bib_data.preamble)

        first = True
        for entry in sorted(bib_data.entries.values(), key=entry_sort_fn):
            key = entry.key
            if not first:
                stream.write('\n')
            first = False

            stream.write('@%s' % entry.original_type)
            stream.write('{%s' % key)
#            for role in ('author', 'editor'):
            for role, persons in entry.persons.items():
                self._write_persons(stream, persons, role)
            for typ, value in entry.fields.items():
                self._write_field(stream, typ, value)
            stream.write('\n}\n')

@cli.command()
@click.argument("fin", metavar="INPUT",
                type=click.File("r"), default="-", required=False)
@click.argument("fout", metavar="OUTPUT",
                type=click.File("w"), default="-", required=False)
def fmt(fin, fout):
    """
    Clean up the INPUT bibtex file and write to OUTPUT
    """

    bib_data = parse_file(fin, "bibtex")

    writer = Writer()
    writer.write_stream(bib_data, fout)
