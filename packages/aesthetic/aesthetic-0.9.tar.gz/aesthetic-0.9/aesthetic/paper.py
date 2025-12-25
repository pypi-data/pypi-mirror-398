from collections import OrderedDict

def abbreviate_the_bibliography(input_bib, output_bib):
    """
    Zotero generates long journal names. Abbreviate them in bulk to conform to
    the AAS style guide, and to have a shorter bibliography.

    Args:
        input_bib (str): path with long names, e.g., '/foo/bar/bibliography.bib'
        output bib (str): path to be created, e.g., '/foo/bar/abbrev.bib'
    """

    mdict = OrderedDict({})

    mdict['The Astrophysical Journal Letters'] = r'\apjl'
    mdict['The Astrophysical Journal Supplement Series'] = r'\apjs'
    mdict['The Astronomical Journal'] = r'\aj'
    mdict['Annual Review of Astronomy and Astrophysics'] = r'\araa'
    mdict['The Astrophysical Journal'] = r'\apj'
    mdict['Publications of the Astronomical Society of the Pacific'] = r'\pasp'
    mdict['Astronomy and Astrophysics'] = r'\aap'
    mdict['Astronomy & Astrophysics'] = r'\aap'
    mdict['Astronomy \& Astrophysics'] = r'\aap'
    mdict['Monthly Notices of the Royal Astronomical Society: Letters'] = r'\mnras:l'
    mdict['Monthly Notices of the Royal Astronomical Society'] = r'\mnras'
    mdict['Nature'] = r'\nat'

    # Sometimes, zotero randomly adds the arXiv ID as a note, even for
    # published papers.
    fdict = OrderedDict({})
    fdict['note = {arXiv:'] = ''

    with open(input_bib, 'r') as f:
        lines = f.readlines()

    for k,v in mdict.items():
        for ix, l in enumerate(lines):
            if k in l:
                _newline = l.replace(k, v)
                lines[ix] = _newline

    for k in fdict.keys():
        for ix, l in enumerate(lines):
            if k in l:
                lines.pop(ix)

    with open(output_bib, 'w') as f:
        f.writelines(lines)

    print(f'made {output_bib}')
