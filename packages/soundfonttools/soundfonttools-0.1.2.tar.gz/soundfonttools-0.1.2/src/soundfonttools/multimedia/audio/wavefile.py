# WaveFile - a audio wave file with several channels
#
# author: Dr. Thomas Tensi
# version: 2022-07

#====================
# IMPORTS
#====================

import array
import wave

from basemodules.simpleassertion import Assertion
from basemodules.simplelogging import Logging
from basemodules.simpletypes import List, Natural, Real, RealList, \
                                    String, Tuple
from basemodules.ttbase import iif, iif2

#====================

_WaveDataBuffer = List[RealList]

#====================

class WaveFile:
    """Represents a WAV audio file"""

    #--------------------

    def __init__ (self,
                  name : String):
        """Sets a WAV file with <name>"""

        Logging.trace(">>: %s", name)

        self._fileName = name

        Logging.trace("<<: %s", self)

    #--------------------

    def __repr__ (self) -> String:
        """Returns string representation of wave file"""

        clsName = self.__class__.__name__
        template = "%s(fileName = %s)"
        return template % (clsName, self._fileName)
    
    #--------------------

    def readParams (self) -> Tuple:
        """Returns tuple of channel count, data point width, data
           point rate and data point count"""

        Logging.trace(">>: %s", self)

        audioFile = wave.open(self._fileName, "rb")
        channelCount, dataPointWidth, dataPointRate, dataPointCount, _, _ = \
            audioFile.getparams()
        audioFile.close()
        result = (channelCount, dataPointWidth, dataPointRate, dataPointCount)

        Logging.trace("<<: %r", result)
        return result

    #--------------------

    def readData (self) -> _WaveDataBuffer:
        Logging.trace(">>: %s", self)

        audioFile = wave.open(self._fileName, "rb")
        channelCount, dataPointWidth, dataPointRate, dataPointCount, _, _ = \
            audioFile.getparams()
        byteList = audioFile.readframes(dataPointCount)
        audioFile.close()

        byteCount = len(byteList)
        byteCountPerFrame = channelCount * dataPointWidth
        scalingFactor = 1.0 / (1 << (dataPointWidth * 8 - 1))
        result = []

        for i in range(channelCount):
            byteListSlice = lambda x: byteList[x:x + dataPointWidth]
            intValueList = \
                [ int.from_bytes(byteListSlice(offset),
                                 byteorder = 'little',
                                 signed = True)
                  for offset in range(i * dataPointWidth, byteCount,
                                      byteCountPerFrame) ]
            dataPointList = [ scalingFactor * value
                              for value in intValueList ]
            result.append(dataPointList)

        Logging.trace("<<")
        return result

    #--------------------

    def write (self,
               channelCount : Natural,
               dataPointCount : Natural,
               waveDataBuffer : _WaveDataBuffer,
               dataPointRate : Real,
               dataPointWidth : Natural,
               dataPointKind : String):
        """Writes WAV file from <waveDataBuffer> using <channelCount>
           channels with each <dataPointCount> data points, a rate of
           <dataPointRate>, a sample width of <dataPointWidth> and the
           kind (int, float) given by <dataPointKind>"""

        Assertion.pre(channelCount > 0,    "channel count must be positive")
        Assertion.pre(dataPointCount > 0,  "data point count must be positive")
        Assertion.pre(dataPointRate > 0.0, "data point rate must be positive")
        Assertion.pre(dataPointWidth > 0,  "data point with must be positive")

        Logging.trace(">>: waveFile = %s,"
                      + " channelCount = %d, dataPointCount = %d,"
                      + " dataPointRate = %s, dataPointWidth = %d,"
                      + " dataPointKind = %s)",
                      self, channelCount, dataPointCount,
                      dataPointRate, dataPointWidth, dataPointKind)

        if dataPointKind == "f":
            Logging.traceError("float not supported")
        else:
            scalingFactor = float(1 << (dataPointWidth * 8 - 1))
            adaptationProc = \
                lambda x: int(scalingFactor
                              * (0.99999999 if x >= 1.0
                                 else -1.0 if x < -1.0
                                 else x))
            Logging.trace("--: type adaptation start")

            for channelIndex in range(channelCount):
                waveDataBuffer[channelIndex] = \
                    list(map(adaptationProc, waveDataBuffer[channelIndex]))

            Logging.trace("--: type adaptation end")

            # make a single data point buffer for quicker write
            totalDataPointCount = dataPointCount * channelCount

            if channelCount == 1:
                rawDataPointList = waveDataBuffer[0]
            else:
                referenceDataPoint = waveDataBuffer[0][0]
                Logging.trace("--: before buffer allocation:"
                              + " dataPointCount = %d,"
                              + " totalDataPointCount = %d",
                              dataPointCount, totalDataPointCount)

                # weave the samples into raw data point list
                rawDataPointList = [ referenceDataPoint ] * totalDataPointCount
                Logging.trace("--: before weaving")

                for channelIndex in range(channelCount):
                    rawDataPointList[channelIndex::channelCount] = \
                        waveDataBuffer[channelIndex]

            byteCount = totalDataPointCount * dataPointWidth
            Logging.trace("--: copy start for %d bytes", byteCount)
            byteSequence = [ value.to_bytes(dataPointWidth, 'little',
                                            signed = True)
                             for value in rawDataPointList ]
            byteArray = b''.join(byteSequence)

            with wave.open(self._fileName, "wb") as audioFile:
                audioFile.setnchannels(channelCount)
                audioFile.setsampwidth(dataPointWidth)
                audioFile.setframerate(dataPointRate)
                audioFile.setnframes(dataPointCount)
                Logging.trace("--: writing frames to file")
                audioFile.writeframesraw(byteArray)

        Logging.trace("<<")

