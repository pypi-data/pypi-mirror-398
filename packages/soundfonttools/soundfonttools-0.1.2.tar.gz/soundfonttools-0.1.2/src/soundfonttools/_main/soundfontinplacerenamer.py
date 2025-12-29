# soundfontInPlaceRenamer - scans soundfont file and applies renamings
#                           from a text file to samples, instruments
#                           and presets
#
# author: Dr. Thomas Tensi
# version: 2025-08

#====================
# IMPORTS
#====================

import argparse
import re
import sys

from basemodules.configurationfile import ConfigurationFile
from basemodules.operatingsystem import OperatingSystem
from basemodules.simplelogging import Logging, Logging_Level
from basemodules.simpletypes import \
    ByteList, Map, Object, String, StringMap
from basemodules.stringutil import deserializeToMap
from basemodules.ttbase import iif2
from basemodules.validitychecker import ValidityChecker

from multimedia.midi.soundfontfile import \
    ChunkTreeNode, SoundFontFileReader

#====================

_nulCharacter = '\0'

#====================

class _CommandLineOptions:
    """This module handles command line options and checks them."""

    #--------------------

    @classmethod
    def checkArguments (cls,
                        argumentList : Object):
        """Checks whether command line options given in <argumentList>
           are okay"""

        Logging.trace(">>")

        loggingFilePath       = argumentList.loggingFilePath
        configurationFilePath = argumentList.configurationFilePath
        soundFontFilePath     = argumentList.soundFontFilePath

        ValidityChecker.isReadableFile(soundFontFilePath,
                                       "soundFontFilePath")

        ValidityChecker.isReadableFile(configurationFilePath,
                                       "configurationFilePath")

        if loggingFilePath is not None:
            ValidityChecker.isWritableFile(loggingFilePath,
                                           "loggingFilePath")

        Logging.trace("<<")

    #--------------------

    @classmethod
    def read (cls):
        """Reads commandline options and sets variables appropriately;
           returns tuple of variables read"""

        Logging.trace(">>")

        programDescription = ("Does an in-place replacement of names"
                              + " in a SoundFont file based on a"
                              + " configuration file")
        p = argparse.ArgumentParser(description=programDescription)

        p.add_argument("-l", "--logging_file",
                       dest = "loggingFilePath",
                       help = ("path for the logging file;"
                              + " activates logging when given"))
        p.add_argument("-c", "--configuration_file",
                       dest = "configurationFilePath",
                       required = True,
                       help = ("path to configuration file containing"
                               + " the replacement patterns for name"
                               + " update"))
        p.add_argument("soundFontFilePath",
                       help = "name of SoundFont source file")
        result = p.parse_args()

        Logging.trace("<<: %s", result)
        return result

#====================

def _writeErrorMessage (message : String):
    """Writes message to STDERR terminated by a newline (and
       additionally to log)"""

    sys.stderr.write(message + "\n")
    Logging.traceError(message)

#====================

def _finalize ():
    Logging.finalize()

#--------------------

def _initialize ():
    Logging.initialize()
    Logging.setLevel(Logging_Level.verbose)

#--------------------
#--------------------

def _readFile (fileName : String) -> ByteList:
    """Reads binary file named <fileName>"""

    Logging.trace(">>: '%s'", fileName)

    file = open(fileName, "rb")
    result = file.read()
    file.close()
    
    Logging.trace("<<: count = %d", len(result))
    return result

#--------------------

def _readReplacementMapFromFile (configurationFilePath : String) -> Map:
    """Reads map from configuration file <configurationFilePath>"""

    Logging.trace(">>: '%s'", configurationFilePath)

    result = {}

    if not OperatingSystem.hasFile(configurationFilePath):
        _writeErrorMessage("cannot find '%s'" % configurationFilePath)
    else:
        replacementFile = ConfigurationFile(configurationFilePath)
        kindList = ("global", "instrument", "preset", "sample")

        for kind in kindList:
            variableName = kind + "NameReplacementMap"
            mapAsString = replacementFile.value(variableName, "{}")
            dictionary = deserializeToMap(mapAsString)
            Logging.trace("--: dictionary = %r", dictionary)
            replacementMap = {}

            for pattern, replacement in dictionary.items():
                Logging.trace("--: pattern = '%s', replacement = '%s'",
                              pattern, replacement)

                try:
                    regexp = re.compile(pattern)
                    replacementMap[regexp] = replacement
                except:
                    errorMessage = "bad pattern '%s'" % pattern
                    _writeErrorMessage(errorMessage)

            Logging.trace("--: replacementMap[%s] = %r",
                          kind, replacementMap)
            result[kind] = replacementMap

    Logging.trace("<<: %r", result)
    return result
    
#--------------------

def _replaceNamesInSoundFontFile (soundFontFilePath : String,
                                  configurationFilePath : String):
    """Performs an in place update of soundfont file named
       <soundfontFilePath> with data from replacement file named
       <configurationFilePath>"""

    Logging.trace(">>: soundFontFilePath = '%s',"
                  + " configurationFilePath = '%s'",
                  soundFontFilePath, configurationFilePath)

    # read replacement data into <replacementMap>
    replacementMap = _readReplacementMapFromFile(configurationFilePath)
    
    # read chunk data and their locations for later selective update
    soundFontFileReader = SoundFontFileReader(soundFontFilePath)
    nodeList = soundFontFileReader.readChunks()

    # apply the changes
    with open(soundFontFilePath, "r+b") as soundFontFile:
        for node in nodeList:
            _updateInPlace(soundFontFile, node, replacementMap)

    Logging.trace("<<")

#--------------------

def _updateInPlace (soundFontFile : Object,
                    node : ChunkTreeNode,
                    replacementMap : StringMap):
    """Updates <chunk> in place in <soundFontFile> using replacement
       data from <replacementMap>"""

    identification = node.identification
    kind = node.kind

    Logging.trace(">>: node = '%s', kind = %s",
                  identification, kind)

    elementNameLength = 20

    if kind not in ["inst", "phdr", "shdr"]:
        Logging.trace("--: skipped")
    else:
        localCategory = iif2(kind == "inst", "instrument",
                             kind == "phdr", "preset",
                             "sample")
        recordKey = iif2(kind == "inst", "instrumentName",
                         kind == "phdr", "presetName",
                         "sampleName")

        nameDescriptor = node.attributeToValueMap["name"]
        oldName = nameDescriptor.value
        Logging.trace("--: original name = '%s'", oldName)
        
        newName = oldName

        for category in ("global", localCategory):
            categoryMap = replacementMap[category]

            for pattern, replacement in categoryMap.items():
                match = pattern.search(newName)

                if match:
                    Logging.trace("--: match in '%s' for pattern '%s'",
                                  newName, pattern)

                    try:
                        newName = pattern.sub(replacement, newName)
                    except:
                        errorMessage = "bad replacement %s" % replacement
                        _writeMessage(errorMessage)

        if newName != oldName:
            Logging.trace("--: update to '%s'", newName)
            st = newName + _nulCharacter
            nameDescriptor.value = st[:elementNameLength]
            nameDescriptor.writeToFile(soundFontFile)
    
    Logging.trace("<<")

#--------------------

def _process (soundFontFilePath : String,
              configurationFilePath : String,
              loggingFilePath : String):
    """Performs an in place update of soundFont file named
       <soundFontFilePath> with data from replacement file named
       <configurationFilePath> with logging done to <loggingFilePath>"""

    if loggingFilePath is None:
        Logging.setLevel(Logging_Level.noLogging)
    else:
        Logging.setFileName(loggingFilePath)
        Logging.setLevel(Logging_Level.verbose)

    Logging.trace(">>: soundFontFilePath = '%s',"
                  + " configurationFilePath = '%s',"
                  + " loggingFilePath = '%s'",
                  soundFontFilePath, configurationFilePath,
                  loggingFilePath)

    _replaceNamesInSoundFontFile(soundFontFilePath,
                                 configurationFilePath)

    Logging.trace("<<")

#--------------------
#--------------------

def main ():
    """The main program"""

    _initialize()
    argumentList = _CommandLineOptions.read()
    _CommandLineOptions.checkArguments(argumentList)

    _process(argumentList.soundFontFilePath,
             argumentList.configurationFilePath,
             argumentList.loggingFilePath)

    _finalize()

#--------------------
#--------------------

if __name__ == "__main__":
    main()
