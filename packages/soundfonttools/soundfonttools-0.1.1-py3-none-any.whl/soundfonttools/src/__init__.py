# dispatcher for the soundfonttools programs adapting the
# module/packages paths accordingly

import os
import sys

# redirect sys.path to current project package directory and also
# include "_main" package
import soundfonttools
_currentModulePath = soundfonttools.__path__[0] + "/src"
sys.path.append(_currentModulePath)
sys.path.append(_currentModulePath + "/_main")

#--------------------

import _main
import _main.jsontosoundfont
import _main.soundfontanalyser
import _main.soundfontinplacerenamer
import _main.soundfonttojson

#--------------------

def _writeMessage (st):
    sys.stderr.write(st + "\n")

#--------------------

def main ():
    """Dispatch on name of calling program"""

    programPath = sys.argv[0]
    programName = os.path.basename(programPath).lower()
    # _writeMessage("program name = %s" % programName)

    if programName.startswith("jsontosoundfont"):
        _main.jsontosoundfont.main()
    elif programName.startswith("soundfonttojson"):
        _main.soundfonttojson.main()
    elif programName.startswith("soundfontinplacerenamer"):
        _main.soundfontinplacerenamer.main()
    elif programName.startswith("soundfontanalyser"):
        _main.soundfontanalyser.main()
    else:
        _writeMessage("unknown program name: %s" % programName)
