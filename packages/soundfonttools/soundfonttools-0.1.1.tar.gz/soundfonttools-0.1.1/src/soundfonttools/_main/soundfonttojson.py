# soundFontToJSON - scans SoundFont file and constructs JSON text file
#
# author: Dr. Thomas Tensi
# version: 2025-08

#====================
# IMPORTS
#====================

import argparse
import json
import sys

from basemodules.operatingsystem import OperatingSystem
from basemodules.simpleassertion import Assertion
from basemodules.simplelogging import Logging, Logging_Level
from basemodules.simpletypes import \
    Boolean, Natural, Object, ObjectList, String, StringList
from basemodules.ttbase import iif2
from basemodules.validitychecker import ValidityChecker

from multimedia.audio.wavefile import WaveFile
from multimedia.midi.soundfontfile import SoundFontFileReader
from multimedia.midi.soundfont import \
    SoundFont, SoundFontName, SoundFontSample, SoundFontSampleKind, \
    SoundFontWaveData

#====================

_programName = "soundFontToJSON"
_newline = "\n"

#--------------------
# error messages
#--------------------

_ErrMsg_duplicateSampleName = ("wave file export not possible:"
                               + " duplicate name '%s'")

#--------------------

def _findDuplicateNames (nameList : StringList) -> StringList:
    """Returns list of duplicates in <nameList>"""

    Logging.trace(">>: %s", nameList)

    nameSet = set()
    result = []

    for name in nameList:
        if name in nameSet:
            result.append(name)

        nameSet.add(name)

    Logging.trace("<<: %s", result)
    return result

#--------------------

def _sanitizeSampleNameForFileName (sampleName : SoundFontName,
                                    channelIsKept : Boolean) -> String:
    """Replaces all characters in <sampleName> that may not be in a
       file name; if <channelIsKept> is not set, the last L or R
       letter is removed"""

    Logging.trace(">>: sampleName = '%s', channelIsKept = %s",
                  sampleName, channelIsKept)

    result = (str(sampleName)
              .replace(" ", "_")
              .replace(":", "_")
              .replace("?", "_")
              .replace("/", "_"))

    if not channelIsKept:
        lastCharacter = result[-1].upper()

        if lastCharacter in ("L", "R"):
            result = result[:-1]

        result = result.rstrip("_")

    Logging.trace("<<: '%s'", result)
    return result

#--------------------

_writeMessage = OperatingSystem.showMessageOnConsole

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
        soundFontFilePath     = argumentList.soundFontFilePath
        waveFileDirectoryPath = argumentList.waveFileDirectoryPath

        if soundFontFilePath is not None:
            ValidityChecker.isReadableFile(soundFontFilePath,
                                           "soundFontFilePath")

        if loggingFilePath is not None:
            ValidityChecker.isWritableFile(loggingFilePath,
                                           "loggingFilePath")

        if waveFileDirectoryPath is not None:
            ValidityChecker.isDirectory(waveFileDirectoryPath,
                                        "waveFileDirectoryPath")

        Logging.trace("<<")

    #--------------------

    @classmethod
    def read (cls):
        """Reads commandline options and sets variables appropriately;
           returns tuple of variables read"""

        Logging.trace(">>")

        programDescription = ("Generates JSON output and optionally"
                              + " sample wave files from a SoundFont file")
        p = argparse.ArgumentParser(description=programDescription)

        p.add_argument("-i",
                       dest = "soundFontFilePath",
                       required = True,
                       help = ("defines the path of the SoundFont"
                               + " source file to be converted"))
        p.add_argument("-idx", "--indexing_kind",
                       dest = "objectIDIndexingKind",
                       choices = ["uuid", "nat" ],
                       default = "nat",
                       help = ("tells the kind of identification indexing"
                               + " for all objects: 'uuid' generates"
                               + " unique identification indices, 'nat'"
                               + " numbers the objects with natural"
                               + " numbers starting at zero"))
        p.add_argument("-l", "--logging_file",
                       dest = "loggingFilePath",
                       help = ("defines the path for the logging file;"
                              + " activates logging when given"))
        p.add_argument("-sf", "--sample_format",
                       dest = "sampleFormatKind",
                       choices = ["n", "i16", "i24", "i32"],
                       default = "n",
                       help = ("gives the sample format of the wave files"
                               + " (if they are generated): 'i16' is a"
                               + " 16-bit integer format, 'i24' is a 24-bit"
                               + " integer format, 'i32' a 32-bit integer"
                               + " format; 'n' stands for the native format"
                               + " (either i16 or i24 depending on the"
                               + " SoundFont version)"))
        p.add_argument("-sn", "--sample_naming",
                       dest = "namingForSampleFiles",
                       choices = ["i", "n"],
                       default = "n",
                       help = ("tells the naming conventions for the wave"
                               + " file names (if they are generated):"
                               + " 'i' uses the sample identification,"
                               + " 'n' uses the sample name"))
        p.add_argument("-w", "--wave_file_directory",
                       dest = "waveFileDirectoryPath",
                       help = ("defines the (optional) path to the"
                               + " target directory for wave files;"
                               + " if this option is not set, only the"
                               + " plain JSON output is produced"))
        result = p.parse_args()

        Logging.trace("<<: %s", result)
        return result

#====================

def _convertSoundFontToJSON (soundFontFilePath : String,
                             waveFileDirectoryPath : String,
                             namingForSampleFiles : String,
                             objectIDIndexingKind : String,
                             sampleFormatKind : String):
    """Writes information about SoundFont in <soundFontFile> to
       standard output; wave files are written to
       <waveFileDirectoryPath> (if set) using <namingForSampleFiles>
       to describe the naming convention and <sampleFormatKind> for
       the format of the sample files; <objectIDIndexingKind> tells
       the kind of identification indexing kind for all objects"""

    Logging.trace(">>: soundFontFilePath = '%s',"
                  + " waveFileDirectoryPath = '%s',"
                  + " namingForSampleFiles = '%s',"
                  + " objectIDIndexingKind = '%s',"
                  + " sampleFormatKind = '%s'",
                  soundFontFilePath, waveFileDirectoryPath,
                  namingForSampleFiles, objectIDIndexingKind,
                  sampleFormatKind)

    soundFontFileReader = \
        SoundFontFileReader(soundFontFilePath)
    soundFont = soundFontFileReader.readSoundFont(objectIDIndexingKind)
    waveFilesAreWritten = (waveFileDirectoryPath is not None)
    SoundFontSample.enableNormalizedWaveReferences(waveFilesAreWritten)
    propertyMap = soundFont.toPropertyMap()
    lineList = json.dumps(propertyMap, indent = 4).split("\n")
    sys.stdout.write(_newline.join(lineList) + _newline)

    if waveFilesAreWritten:
        # ensure that there are no duplicates in the sample names
        nameList = [ sample.name for sample in soundFont.sampleList ]
        duplicateNameList = _findDuplicateNames(nameList)

        if len(duplicateNameList) == 0:
            _writeWaveFiles(soundFont, waveFileDirectoryPath,
                            namingForSampleFiles, sampleFormatKind)
        else:
            for name in duplicateNameList:
                _writeMessage(_ErrMsg_duplicateSampleName % name)

    Logging.trace("<<")

#--------------------

def _writeSampleWaveFile (soundFont : SoundFont,
                          sampleList : ObjectList,
                          waveFilePath : String,
                          sampleFormatKind : String):
    """Writes a wave file named <waveFilePath> with wave data for all
       sample headers in <sampleList> belonging to <soundFont>
       using <sampleFormatKind> for the sample format"""

    Assertion.pre(len(sampleList) > 0,
                  "sample header list must not be empty")
    
    Logging.trace(">>: sampleList = %s, waveFilePath = '%s',"
                  + " sampleFormatKind = '%s'",
                  sampleList, waveFilePath, sampleFormatKind)

    # sample settings
    waveData = soundFont.waveData
    widthSpec = sampleFormatKind[1:]

    sampleKind = "i"
    sampleWidth = (2      if widthSpec == "16"
                   else 3 if widthSpec == "24"
                   else 4 if widthSpec == "32"
                   else waveData.bytesPerDataPoint())

    getSampleWaveData = (lambda sample:
                         waveData.slice(sample.sampleStartPosition,
                                        sample.sampleEndPosition))

    # parameters for the wave file
    firstSample  = sampleList[0]
    channelCount = len(sampleList)
    sampleBuffer = [ getSampleWaveData(sample) for sample in sampleList ]
    sampleCount  = len(sampleBuffer[0])
    sampleRate   = firstSample.sampleRate

    waveFile = WaveFile(waveFilePath)
    waveFile.write(channelCount, sampleCount, sampleBuffer,
                   sampleRate, sampleWidth, sampleKind)

    Logging.trace("<<")

#--------------------

def _writeWaveFiles (soundFont : SoundFont,
                     waveFileDirectoryPath : String,
                     namingForSampleFiles : String,
                     sampleFormatKind : String):
    """Writes wave files in <soundFont> to <waveFileDirectoryPath>
       using <namingForSampleFiles> to describe the naming convention
       and <sampleFormatKind> for the sample format"""

    Logging.trace(">>: waveFileDirectoryPath = '%s',"
                  + " namingForSampleFiles = '%s',"
                  + " sampleFormatKind = '%s'",
                  waveFileDirectoryPath, namingForSampleFiles,
                  sampleFormatKind)

    sampleList = soundFont.sampleList
    getSampleCount = \
        lambda sample: sample.sampleEndPosition - sample.sampleStartPosition
    sampleIdSet = set()
   
    for sample in sampleList:
        identification = sample.identification
        name           = sample.name

        if identification not in sampleIdSet:
            Logging.trace("--: processing sample '%s' - '%s'",
                          name, identification)
            sampleIdSet.add(identification)

            fileName = (identification if namingForSampleFiles == "i"
                        else name)
            fileName = _sanitizeSampleNameForFileName(fileName, True)
            partnerSample = sample.partner
            hasPartner = partnerSample is not None
            sampleList = []

            if not hasPartner:
                sampleList.append(sample)
            else:
                sampleKind = sample.kind
                sampleCount = getSampleCount(sample)
                otherSampleCount = getSampleCount(partnerSample)

                if sampleCount != otherSampleCount:
                    Logging.trace("--: linked samples have different"
                                  + " lengths => split them")
                    sampleList.append(sample)
                else:
                    fileName = _sanitizeSampleNameForFileName(name, False)
                    sampleIdSet.add(partnerSample.identification)

                    if sampleKind == SoundFontSampleKind.leftSample:
                        sampleList.append(sample)
                        sampleList.append(partnerSample)
                    else:
                        sampleList.append(partnerSample)
                        sampleList.append(sample)

            Logging.trace("--: identification = '%s', channelCount = %d",
                          identification, len(sampleList))

            # write data to file
            waveFilePath = "%s/%s.wav" % (waveFileDirectoryPath, fileName)
            _writeSampleWaveFile(soundFont, sampleList, waveFilePath,
                                 sampleFormatKind)

    Logging.trace("<<")

#====================

def _finalize ():
    Logging.finalize()

#--------------------

def _initialize ():
    Logging.initialize()
    Logging.setTracingWithTime(True, 3)

#--------------------
#--------------------

def _process (soundFontFilePath : String,
              loggingFilePath : String,
              waveFileDirectoryPath : String,
              namingForSampleFiles : String,
              objectIDIndexingKind : String,
              sampleFormatKind : String):
    """Processes SoundFont file named <soundFontFilePath>, does
       logging to <loggingFilePath> (if set) and writes wave files to
       <waveFileDirectoryPath> (if set) using <namingForSampleFiles>
       to describe the naming convention; <objectIDIndexingKind> tells
       the kind of identification indexing kind for all objects"""

    if loggingFilePath is None:
        Logging.setLevel(Logging_Level.noLogging)
    else:
        Logging.setFileName(loggingFilePath)
        Logging.setLevel(Logging_Level.verbose)

    Logging.trace(">>: soundFontFilePath = '%s',"
                  + " loggingFilePath = '%s',"
                  + " waveFileDirectoryPath = '%s',"
                  + " namingForSampleFiles = '%s',"
                  + " objectIDIndexingKind = '%s',"
                  + " sampleFormatKind = '%s'",
                  soundFontFilePath, loggingFilePath,
                  waveFileDirectoryPath, namingForSampleFiles,
                  objectIDIndexingKind, sampleFormatKind)

    _convertSoundFontToJSON(soundFontFilePath, waveFileDirectoryPath,
                            namingForSampleFiles, objectIDIndexingKind,
                            sampleFormatKind)

    Logging.trace("<<")

#--------------------
#--------------------

def main ():
    """The main program"""

    _initialize()
    argumentList = _CommandLineOptions.read()
    _CommandLineOptions.checkArguments(argumentList)

    _process(argumentList.soundFontFilePath,
             argumentList.loggingFilePath,
             argumentList.waveFileDirectoryPath,
             argumentList.namingForSampleFiles,
             argumentList.objectIDIndexingKind,
             argumentList.sampleFormatKind)

    _finalize()

#--------------------
#--------------------

if __name__ == "__main__":
    main()
