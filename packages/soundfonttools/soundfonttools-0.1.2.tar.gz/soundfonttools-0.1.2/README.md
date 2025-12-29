# SoundFontTools
**Tools for Conversion, In-Place-Renaming and Analysis of SoundFonts (v0.1)**

## Introduction

The SoundFontTools is a suite of several python scripts that allow to
read, modify, analyze and write SoundFont files.

They consist of

  - a converter from a SoundFont file to a JSON file plus wave files for
    the samples,
  - a converter from a JSON file plus sample wave files to a
    SoundFont file,
  - a in-place renaming utility for doing a pattern-based
    adaptation of the sample, instrument and preset names within a
    SoundFont file, and
  - a SoundFont file analyzer scanning for possible optimizations.

All those tools should help a SoundFont designer or someone analyzing
existing SoundFonts.

## Installation and Requirements

The script and its components are written in python and can be
installed as a single python package.  The package requires either
Python&nbsp;3.10 or later.

Installation is done from the PyPi repository via

    pip install soundfonttools

Make sure that the scripts directory of python is in the path for
executables on your platform.

## Further Information

The detailed manual is available *[here][reference:manual]*.

[reference:manual]: https://raw.githubusercontent.com/prof-spock/SoundFontTools/main/soundFontTools-documentation.pdf
