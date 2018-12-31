#!/usr/bin/env python3
"""
This module implements the Note and NoteTaker classes
"""
import datetime
import os
import re
from typing import List, Union, Dict, cast, NewType
from ruamel.yaml import YAML, yaml_object, SafeConstructor


YAML_INST = YAML()
NoteId = NewType('NoteId', int)
NoteLabel = NewType('NoteLabel', str)


@yaml_object(YAML_INST)
class Note:
    """
    This class represent a note which is composed of a message, optionnally some labels
    and a timestamp

    >>> import datetime
    >>> from ruamel.yaml import YAML
    >>> import sys
    >>> new_n = Note('My first note ever', ['todo'], datetime.date(1981, 7, 13))
    >>> print(new_n)
    @todo [81/07/13 00:00:00] : My first note ever
    >>> YAML().dump(new_n, sys.stdout)
    !note '@todo [81/07/13 00:00:00] : My first note ever'
    >>> last_n = YAML().load('!note "@todo, @job [18/12/31 12:36:11] : Solve bug 42"')
    >>> print(last_n)
    @todo, @job [18/12/31 12:36:11] : Solve bug 42
    """
    yaml_tag = u'!note'
    # This pattern represent a note. First there are labels beginning with an arobase.
    # Each label is separated from its follower by a period and a blank.
    # After label there is the date in between square brackets then a blank, a column
    # a blank again and the message
    # Warning : should match the output of __str__ method
    note_pattern = re.compile(r'(@.*)\s\[(.*)\]\s:\s(.*)')
    date_format = "%y/%m/%d %H:%M:%S"

    def __init__(self, message: str, labels: List[NoteLabel], date: datetime.date):
        """
        Constructor

        :param message: the note's message
        :param labels: the note's labels
        :param date: the note's creation timestamp
        """
        self.message = message
        self.labels = labels
        self.date = date

    def __str__(self) -> str:
        """
        Furnishes a string representation of the note
        """
        f_labels = ', '.join(('@' + lab for lab in self.labels))
        f_date = self.date.strftime(f"[{Note.date_format}]")
        return f"{f_labels} {f_date} : {self.message}"

    @classmethod
    def to_yaml(cls, representer, node):
        """
        A way to dump the note into yaml object
        """
        return representer.represent_scalar(cls.yaml_tag, f'{str(node)}')

    @classmethod
    def from_yaml(cls, constructor, node):  # pylint:disable=unused-argument
        """
        A way to load the note from a yaml object
        """
        found = Note.note_pattern.search(node.value).groups()
        labels, date, message = found
        labels = labels.split(', ')
        labels = [lab[1:] for lab in labels]  # removing @ at the beginning of the label
        date = datetime.datetime.strptime(date, Note.date_format)
        return cls(message, labels, date)


@yaml_object(YAML_INST)
class NoteTaker:
    """
    This class represent a collection of notes

    >>> import datetime
    >>> from ruamel.yaml import YAML
    >>> import sys

    Create a new NoteTaker instance and add few notes
    >>> THE_NOTE_TAKER = NoteTaker()
    >>> THE_NOTE_TAKER.add_note("My first note")
    >>> THE_NOTE_TAKER.add_note("Call John", "todo", "perso")
    >>> THE_NOTE_TAKER.add_note("Solve bug 42", "tOdO", "job")

    Print the actual state of the NoteTaker instance
    >>> print(THE_NOTE_TAKER)
    0 -> @undefined [...] : My first note
    1 -> @todo, @perso [...] : Call John
    2 -> @todo, @job [...] : Solve bug 42
    <BLANKLINE>

    Also it is possible to dump the NoteTaker instance into a yaml stream
    >>> YAML().dump(THE_NOTE_TAKER, sys.stdout)
    !notetaker
    0: !note '@undefined [...] : My first note'
    1: !note '@todo, @perso [...] : Call John'
    2: !note '@todo, @job [...] : Solve bug 42'

    A note to delete?
    >>> THE_NOTE_TAKER.delete_note(1)
    >>> print(THE_NOTE_TAKER)
    0 -> @undefined [...] : My first note
    2 -> @todo, @job [...] : Solve bug 42
    <BLANKLINE>

    Of course a NoteTaker instance can be loaded from a yaml stream
    >>> new_note_str = \"\"\"!notetaker
    ... 0: !note '@todo, @job, @urgent [18/12/22 12:36:11] : Solve bug 122'
    ... 1: !note '@job, @urgent [18/12/26 12:36:11] : Solve bug 123'
    ... 2: !note '@todo, @urgent [18/12/24 12:36:11] : Solve bug 108'
    ... 3: !note '@todo [18/12/24 12:36:11] : Solve bug 109'
    ... 5: !note '@todo, @job, @urgent [18/12/31 12:36:11] : Solve bug 121'\"\"\"
    >>> NEW_NOTE_TAKER = YAML().load(new_note_str)
    >>> NEW_NOTE_TAKER.add_note("Buenos dias amigo!", "perso", "urgent")
    >>> NEW_NOTE_TAKER.delete_note(3)
    >>> print(NEW_NOTE_TAKER)
    0 -> @todo, @job, @urgent [18/12/22 12:36:11] : Solve bug 122
    1 -> @job, @urgent [18/12/26 12:36:11] : Solve bug 123
    2 -> @todo, @urgent [18/12/24 12:36:11] : Solve bug 108
    5 -> @todo, @job, @urgent [18/12/31 12:36:11] : Solve bug 121
    6 -> @perso, @urgent [...] : Buenos dias amigo!
    <BLANKLINE>

    How to look for a specific note from its label?
    >>> todos = NEW_NOTE_TAKER.find_note('todo')
    >>> print("\\n".join(f"{k} : {str(v)}" for k,v in todos.items()))
    0 : @todo, @job, @urgent [18/12/22 12:36:11] : Solve bug 122
    2 : @todo, @urgent [18/12/24 12:36:11] : Solve bug 108
    5 : @todo, @job, @urgent [18/12/31 12:36:11] : Solve bug 121

    Or if the note's id is already known
    >>> by_id = NEW_NOTE_TAKER.find_note(5)
    >>> print("\\n".join(f"{k} : {str(v)}" for k,v in by_id.items()))
    5 : @todo, @job, @urgent [18/12/31 12:36:11] : Solve bug 121
    """
    yaml_tag = u"!notetaker"

    def __init__(self):
        self.current_id = NoteId(0)
        # The main map associating an id with a Note object
        self.notes: Dict[NoteId, Note] = {}
        # A secondary map that associates a label to the corresponding notes id
        self.label_id_map: Dict[NoteLabel, List[NoteId]] = {}

    def add_note(self, message: str, *labels: NoteLabel):
        """
        Add a note to the collection

        :param message: the message of the new note
        :param labels: all labels that should be associated to the note
        """
        current_date = datetime.datetime.now()
        if not labels:
            note_labels = [NoteLabel("undefined")]
        else:
            note_labels = [NoteLabel(lab.lower()) for lab in labels]

        new_note = Note(message, note_labels, current_date)
        self.notes[self.current_id] = new_note

        for lab in new_note.labels:
            self.label_id_map.setdefault(lab, []).append(self.current_id)
        self.current_id += 1

    def delete_note(self, note_id: NoteId):
        """
        Delete a note

        :param note_id: the id of the note to be deleted
        """
        note = self.notes[note_id]
        self.notes.pop(note_id)
        for lab in note.labels:
            self.label_id_map[lab].remove(note_id)

    def find_note_id(self, label: NoteLabel) -> List[NoteId]:
        """
        Find a note by a label. Returns a list of notes id

        :param label: note's label
        :return: a list of matching notes ids
        """
        return [note_id for note_id in self.label_id_map[label] if note_id in self.notes]

    def find_note(self, field: Union[NoteId, NoteLabel]) -> Dict[NoteId, Note]:
        """
        Find a note by its id or by a label. Returns a list of note objects

        :param field: note's id or label
        :return: a list of matching notes
        """
        res: Dict[NoteId, Note] = {}
        note_id = cast(NoteId, field)
        if note_id in self.notes:
            res.update({note_id: self.notes[note_id]})
        try:
            label = cast(NoteLabel, field)
            res.update({n_id:self.notes[n_id] for n_id in self.find_note_id(label)})
        except KeyError:
            # In case field is a note_id (int) there is not key of such type in self.label_id_map
            pass
        return res

    def __str__(self) -> str:
        """
        Furnishes a string representation of all notes
        """
        msg = ""
        for key, value in self.notes.items():
            msg += f"{key} -> {str(value)}" + os.linesep
        return msg

    @classmethod
    def to_yaml(cls, representer, node):
        """
        A way to dump the notetaker into yaml object
        """
        return representer.represent_mapping(cls.yaml_tag, node.notes)
        #return representer.represent_dict(node.notes)

    @classmethod
    def from_yaml(cls, constructor, node):  # pylint:disable=unused-argument
        """
        A way to load the notetaker from a yaml object
        """
        new_obj = cls()
        new_obj.notes = dict()
        yield new_obj
        new_dict = SafeConstructor.construct_mapping(constructor, node, deep=True)
        new_obj.notes.update(new_dict)
        new_obj.current_id = max(new_dict.keys()) + 1
        for note_id, note in new_dict.items():
            for lab in note.labels:
                new_obj.label_id_map.setdefault(lab, []).append(note_id)


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
