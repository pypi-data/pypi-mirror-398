"""
.. run::

    from example import whatever, wrap60

    lorem = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
        " Pellentesque faucibus vestibulum est id consequat."
        " Cras sed enim sed ex maximus blandit."
        " Donec risus orci, facilisis nec tortor ac, consectetur volutpat urna."
    )
"""

import textwrap


def whatever():
    """Do Nothing.

    .. run::

        for i in range(5):
            print(f"Hello world! ({i})")
    """
    pass


def wrap60(text):
    """Wrap text to 60 columns.

    .. run::

        for line in wrap60(lorem):
            print("| " + line)
    """
    return textwrap.wrap(text, width=60)
