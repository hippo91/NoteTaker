#!/usr/bin/env python3
"""
A very simple notetaker for command line
"""
from pathlib import Path
import click

from notetaker import load_notes, save_notes


PATH_TO_YAML = '/tmp/notes.yaml'


@click.command()
@click.argument('note', required=False, type=str)
@click.option('-d', '--delete', 'delete', type=int, help="Delete a note by its id")
@click.option('-s', '--search', 'search', help="Search a note by its id or one of its label")
def launch(note=None, delete=None, search=None):
    """ n is as simpe notetaker for the command line. """
    notetaker = load_notes(Path(PATH_TO_YAML))

    if note is None:
        if delete is None and search is None:
            print(notetaker)
        elif delete is not None:
            notetaker.delete_note(delete)
            save_notes(notetaker, Path('/tmp/notes.yaml'))
            print("Note deleted")
        elif search is not None:
            try:
                f_i = int(search)
            except ValueError:
                f_i = search
            print("\n".join(
                f"{note_id} : {note}" for note_id, note in notetaker.find_note(f_i).items()))
    else:
        if '@' in note:
            message, labels = note.split('@')
            labels = [lab.strip() for lab in labels.split()]
        else:
            message = note
            labels = []
        notetaker.add_note(message.strip(), *labels)
        save_notes(notetaker, Path(PATH_TO_YAML))
        print("Note added")


if __name__ == "__main__":
    launch()
