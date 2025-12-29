# jsonToSoundFont - scans JSON text file and constructs SoundFont file
#
# author: Dr. Thomas Tensi
# version: 2025-09

#====================
# IMPORTS
#====================

import argparse
import json
import struct
import sys

from basemodules.operatingsystem import OperatingSystem
from basemodules.simplelogging import Logging, Logging_Level
from basemodules.simpletypes import \
    Boolean, Class, Object, RealList, String, StringSet
from basemodules.ttbase import iif
from basemodules.validitychecker import ValidityChecker

from multimedia.audio.wavefile import WaveFile
from multimedia.midi.soundfont import \
    ErrorHandler, SoundFont, SoundFontSample, SoundFontSampleKind
from multimedia.midi.soundfontfile import SoundFontFileWriter

#====================

_programName = "jsonToSoundFont"
_newline = "\n"

#--------------------
# error messages
#--------------------

_ErrMsg_badWaveChannelCount = "bad channel count %d"
_ErrMsg_noWaveFiles         = "wave files not found %s"

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

        jsonFilePath          = argumentList.jsonFilePath
        loggingFilePath       = argumentList.loggingFilePath
        soundFontFilePath     = argumentList.soundFontFilePath
        waveFileDirectoryPath = argumentList.waveFileDirectoryPath

        ValidityChecker.isReadableFile(jsonFilePath, "jsonFilePath")
        ValidityChecker.isWritableFile(soundFontFilePath,
                                       "soundFontFilePath")
        ValidityChecker.isDirectory(waveFileDirectoryPath,
                                    "waveFileDirectoryPath")

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

        programDescription = ("Generates SoundFont file from JSON input"
                              + " and sample wave files")
        p = argparse.ArgumentParser(description=programDescription)

        p.add_argument("-i",
                       dest = "jsonFilePath",
                       required = True,
                       help = "defines the path of the JSON source file")
        p.add_argument("-l", "--logging_file",
                       dest = "loggingFilePath",
                       help = ("defines the path of the logging file;"
                              + " activates logging when given"))
        p.add_argument("-o",
                       dest = "soundFontFilePath",
                       required = True,
                       help = ("defines the path of SoundFont"
                               + " destination file to be written"))
        p.add_argument("-sf", "--sample_format",
                       dest = "sampleFormatKind",
                       choices = ["i16", "i24"],
                       default = "i16",
                       help = ("gives the sample format for the sound"
                               + " font: for 'i16' samples are stored"
                               + " in a 16-bit integer format, for 'i24'"
                               + " samples are stored in 24-bit integer"
                               + " format (assuming that the SoundFont"
                               + " version is at least 2.04)"))
        p.add_argument("-df", "--debug_file_path",
                       dest = "debugFilePath",
                       default = "",
                       help = ("defines an optional path to a JSON file"
                               + " showing the data read into internal"
                               + " SoundFont model from input JSON"
                               + " file"))
        p.add_argument("-w", "--wave_file_directory",
                       dest = "waveFileDirectoryPath",
                       required = True,
                       help = ("defines the path to the source"
                               + " directory for wave files"))
        result = p.parse_args()

        Logging.trace("<<: %s", result)
        return result

#====================

class WaveData:
    """Encapsulates the conversion of wave files to SoundFont wave
       data"""

    #--------------------
    # PRIVATE METHODS
    #--------------------

    @classmethod
    def _collectFromWaveFile (cls : Class,
                              soundFont : SoundFont,
                              waveFileDirectoryPath : String,
                              hasExtendedWaveData : Boolean,
                              sample : SoundFontSample,
                              processedSampleIDSet : StringSet,
                              errorHandler : ErrorHandler):
        """Collects wave data from wave file in <waveFileDirectoryPath>
           for <sample> and updates that record of <soundFont>
           accordingly; error messages are appended to <errorHandler> (if
           set)"""

        sampleName = str(sample.name)
        Logging.trace(">>: waveFileDirectoryPath = '%s',"
                      + " hasExtendedWaveData = %s,"
                      + " sampleName = '%s'",
                      waveFileDirectoryPath, hasExtendedWaveData,
                      sampleName)

        isStereoSample = (sample.partner is not None)
        filePathProc = lambda x: "%s/%s.wav" % (waveFileDirectoryPath, x)
        adaptedSampleName = (sampleName
                             .replace(" ", "_")
                             .replace(":", "_")
                             .replace("?", "_")
                             .replace("/", "_"))
        fileNameList = [ filePathProc(adaptedSampleName) ]

        if isStereoSample and adaptedSampleName[-1].lower() in "lr":
            fileName = filePathProc(adaptedSampleName[:-1].rstrip("_"))
            fileNameList.append(fileName)

        for fileName in fileNameList:
            fileNameIsOkay = OperatingSystem.hasFile(fileName)

            if fileNameIsOkay:
                break

        errorHandler.setErrorContext("%s %s" % ("sample", sampleName))

        if not fileNameIsOkay:
            errorMessage = _ErrMsg_noWaveFiles % fileNameList
            errorHandler.appendErrorMessage(errorMessage)
        else:
            waveFile = WaveFile(fileName)
            channelCount, dataPointWidth, dataPointRate, dataPointCount = \
                waveFile.readParams()

            if channelCount not in (1, 2):
                errorHandler.appendErrorMessage(_ErrMsg_badWaveChannelCount
                                                % channelCount)
            else:
                if not isStereoSample or channelCount == 1:
                    sampleList = (sample,)
                elif sample.kind == SoundFontSampleKind.leftSample:
                    sampleList = (sample, sample.partner)
                else:
                    sampleList = (sample.partner, sample)

                waveDataBuffer = waveFile.readData()

                for sample, waveData in zip(sampleList, waveDataBuffer):
                    processedSampleIDSet.add(sample.identification)
                    cls._updateSample(soundFont, hasExtendedWaveData,
                                      sample, waveData)

        Logging.trace("<<")

    #--------------------

    @classmethod
    def _updateSample (cls : Class,
                       soundFont : SoundFont,
                       hasExtendedWaveData : Boolean,
                       sample : SoundFontSample,
                       sampleData : RealList):
        """Updates <sample> and wave data table in <soundFont> using
           <sampleData>"""

        Logging.trace(">>: sample = '%s', hasExtendedWaveData = %s",
                      sample.name, hasExtendedWaveData)

        waveData = soundFont.waveData
        sampleDataCount = len(sampleData)
        startPosition = sample.sampleStartPosition
        offset = waveData.dataPointCount() - startPosition

        # update the sample record
        sample.sampleStartPosition += offset
        sample.loopStartPosition   += offset
        sample.loopEndPosition     += offset
        sample.sampleEndPosition    = (sample.sampleStartPosition
                                       + sampleDataCount)
        
        # update the SoundFont wave data and append 46 zero data
        # points as defined in the specification
        waveData.extendByRealList(sampleData + [ 0 ] * 46)
        
        Logging.trace("<<")

    #--------------------
    # EXPORTED METHODS
    #--------------------

    @classmethod
    def collectFromFiles (cls : Class,
                          soundFont : Object,
                          waveFileDirectoryPath : String,
                          hasExtendedWaveData : Boolean,
                          errorHandler : ErrorHandler):
        """Collects wave data from wave files in
           <waveFileDirectoryPath> and updates <soundFont>; error
           messages are appended to <errorHandler> (if set)"""

        Logging.trace(">>: waveFileDirectoryPath = '%s',"
                      + " hasExtendedWaveData = %s",
                      waveFileDirectoryPath, hasExtendedWaveData)

        soundFont.waveData.clear(hasExtendedWaveData)
        processedSampleIDSet = set()

        for sample in soundFont.sampleList:
            if sample.identification in processedSampleIDSet:
                Logging.trace("--: skip '%s'", sample.name)
            else:
                cls._collectFromWaveFile(soundFont,
                                         waveFileDirectoryPath,
                                         hasExtendedWaveData, sample,
                                         processedSampleIDSet,
                                         errorHandler)

        Logging.trace("<<")

#====================

def _convertJSONToSoundFont (jsonFilePath : String,
                             waveFileDirectoryPath : String,
                             soundFontFilePath : String,
                             sampleFormatKind : String,
                             debugFilePath : String):
    """Converts information about SoundFont in <jsonFilePath> using
       wave files from <waveFileDirectoryPath> to SoundFont file named
       <soundFontFilePath>; <sampleFormatKind> describes the target
       sample format; if <debugFilePath> is not empty, the SoundFont
       data read is written to that file (typically for debugging)"""

    Logging.trace(">>: jsonFilePath = '%s',"
                  + " waveFileDirectoryPath = '%s',"
                  + " soundFontFilePath = '%s',"
                  + " sampleFormatKind = '%s',"
                  + " debugFilePath = '%s'",
                  jsonFilePath, waveFileDirectoryPath, soundFontFilePath,
                  sampleFormatKind, debugFilePath)

    with open(jsonFilePath, "r") as jsonFile:
        lineList = [ line.rstrip() for line in jsonFile.readlines() ]

    Logging.trace("--: lineCount = %d", len(lineList))
    st = " ".join(lineList)
    propertyMap = json.loads(st)

    errorHandler = ErrorHandler()
    soundFont = SoundFont()
    soundFont.fillFromPropertyMap(propertyMap, errorHandler)
    hasExtendedWaveData = False
    WaveData.collectFromFiles(soundFont,
                              waveFileDirectoryPath,
                              hasExtendedWaveData, errorHandler)

    if debugFilePath > "":
        _writeSoundFontToJSONFile(soundFont, debugFilePath)

    if errorHandler.hasErrors():
        sys.stderr.write("\n".join(errorHandler.messageList) + "\n")
    else:
        soundFontFileWriter = SoundFontFileWriter(soundFontFilePath)
        soundFontFileWriter.writeSoundFont(soundFont)

    Logging.trace("<<")

#--------------------

def _writeSoundFontToJSONFile (soundFont : SoundFont,
                               destinationFilePath : String):
    """Writes <soundFont> to JSON file named <destinationFilePath>
       (for debugging)"""

    Logging.trace(">>: '%s'", destinationFilePath)

    destinationDirectoryPath = OperatingSystem.dirname(destinationFilePath)
    
    if not OperatingSystem.hasDirectory(destinationDirectoryPath):
        Logging.traceError("cannot write JSON file to directory '%s'",
                           destinationFilePath)
    else:
        waveFilesAreWritten = True
        SoundFontSample.enableNormalizedWaveReferences(waveFilesAreWritten)
        propertyMap = soundFont.toPropertyMap()
        lineList = json.dumps(propertyMap, indent = 4).split("\n")
        Logging.trace("--: lineListCount = %d", len(lineList))

        with open(destinationFilePath, "w") as file:
            Logging.trace("--: writing to file '%s'", destinationFilePath)
            file.write(_newline.join(lineList) + _newline)

    Logging.trace("<<")

#====================

def _finalize ():
    Logging.finalize()

#--------------------

def _initialize ():
    Logging.initialize()
    Logging.setTracingWithTime(True, 3)

#--------------------

def _process (jsonFilePath : String,
              waveFileDirectoryPath : String,
              soundFontFilePath : String,
              loggingFilePath : String,
              sampleFormatKind : String,
              debugFilePath : String):
    """Processes JSON file named <jsonFilePath> using wave files from
       <waveFileDirectoryPath> SoundFont file named
       <soundFontFilePath>, does logging to <loggingFilePath> (if
       set); <sampleFormatKind> describes the target sample format; if
       <debugFilePath> is not empty, the SoundFont data read is
       written to that file (typically for debugging)"""

    if loggingFilePath is None:
        Logging.setLevel(Logging_Level.noLogging)
    else:
        Logging.setFileName(loggingFilePath)
        Logging.setLevel(Logging_Level.verbose)

    Logging.trace(">>: jsonFilePath = '%s',"
                  + " waveFileDirectoryPath = '%s',"
                  + " soundFontFilePath = '%s',"
                  + " loggingFilePath = '%s',"
                  + " sampleFormatKind = '%s',"
                  + " debugFilePath = '%s'",
                  jsonFilePath, waveFileDirectoryPath, soundFontFilePath,
                  loggingFilePath, sampleFormatKind, debugFilePath)

    _convertJSONToSoundFont(jsonFilePath, waveFileDirectoryPath,
                            soundFontFilePath, sampleFormatKind,
                            debugFilePath)

    Logging.trace("<<")

#--------------------
#--------------------

def main ():
    """The main program"""

    _initialize()
    argumentList = _CommandLineOptions.read()
    _CommandLineOptions.checkArguments(argumentList)

    if True:
        _process(argumentList.jsonFilePath,
                 argumentList.waveFileDirectoryPath,
                 argumentList.soundFontFilePath,
                 argumentList.loggingFilePath,
                 argumentList.sampleFormatKind,
                 argumentList.debugFilePath)

    _finalize()

#--------------------
#--------------------

if __name__ == "__main__":
    main()
