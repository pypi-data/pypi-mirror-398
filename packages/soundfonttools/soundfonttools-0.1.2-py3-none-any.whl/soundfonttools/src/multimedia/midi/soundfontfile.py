# soundfontfile - representation of a SoundFont file with routines
#                 for reading and writing
#
# author: Dr. Thomas Tensi
# version: 2025-08

#====================
# IMPORTS
#====================

from copy import deepcopy
import struct
from uuid import uuid4

from basemodules.operatingsystem import OperatingSystem
from basemodules.simpleassertion import Assertion
from basemodules.simplelogging import Logging
from basemodules.simpletypes import \
    Boolean, ByteList, Class, Integer, Map, Natural, Object, \
    ObjectList, String, StringMap, Tuple
from basemodules.ttbase import adaptToRange, iif, iif2, isInRange

from multimedia.midi.soundfont import \
    SoundFont, SoundFontGenerator, SoundFontGeneratorAmount, \
    SoundFontGeneratorKind, SoundFontHeader, SoundFontInstrument, \
    SoundFontModulator, SoundFontPreset, SoundFontSample, \
    SoundFontSampleKind, SoundFontVersion, SoundFontWaveData, \
    SoundFontZone, SoundFontZonedElement

#====================

_SFGA = SoundFontGeneratorAmount
_SFGK = SoundFontGeneratorKind

#--------------------
# CONSTANTS
#--------------------

_infinity = 999999999999
_nulCharacter = '\0'

_instrumentKeyLetter = "I"
_presetKeyLetter     = "P"
_keyLetterList = (_instrumentKeyLetter, _presetKeyLetter)

_childNodeKindPrefix    = "CHLD-"
_pdtaRootNodeKindSuffix = "-PDTA"

_soundFontNameLength = 20

_partnerGeneratorKindList = (_SFGK.instrument, _SFGK.sampleID)

#--------------------
# TYPES
#--------------------

CharacterList = ObjectList

GeneratorListMap  = Map  # map from "I" or "P" to list of generators

ModulatorListMap  = Map  # map from "I" or "P" to list of modulators

IntervalListMap   = Map  # map from "I" or "P" to list of index pairs
                         # specifying bag index intervals per preset or
                         # instrument

ZoneHeaderListMap = Map  # map from "I" or "P" to list of SoundFont
                         # bags plus a count information for each
                         # category

#--------------------
# SIMPLE FUNCTIONS
#--------------------

def _isObjectWithID (object : Object):
    return (isinstance(object, SoundFontZonedElement)
            or isinstance(object, SoundFontSample))

#--------------------

_sentinelName = lambda isPresets: iif(isPresets, "EOP", "EOI")

#--------------------

def _subListNOLOG  (byteList : ByteList,
                    startPosition : Natural,
                    endPosition : Natural) -> CharacterList:
    """Returns a slice of <byteList> going from <startPosition> to
       <endPosition> with at most ten bytes converted to a character
       list"""

    lastPosition = startPosition + 10
    subList = byteList[startPosition:lastPosition]
    result = [ chr(byte) for byte in subList ]

    if lastPosition < endPosition:
        result.append("...")

    return result

#====================

class AccessDescriptor:
    """Represents a tuple of data kind, position and byte count"""

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    Kind_bytes   = "b"
    Kind_integer = "i"
    Kind_natural = "n"
    Kind_string  = "s"

    #--------------------

    def __init__ (self,
                  kind : String,
                  position : Natural,
                  count : Natural,
                  value : Object = None):
        """Constructs new access descriptor"""

        Logging.trace(">>: kind = '%s', position = %d, count = %d,"
                      + " value = %s",
                      kind, position, count, value)

        self.kind     = kind
        self.position = position
        self.count    = count
        self.value    = value

        Logging.trace("<<: %s", self)
    
    #--------------------
    # type conversion
    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns string representation of <self>"""

        cls = self.__class__
        clsName = cls.__name__
        format = ("%s(kind = '%s', position = %s, count = %s,"
                  + " value = %s)")

        valueAsString = (None if self.value is None
                         else self.value if self.kind != cls.Kind_bytes
                         else _subListNOLOG(self.value,
                                            0, len(self.value)))

        st = (format
              % (clsName,
                 self.kind, self.position, self.count, valueAsString))
        return st

    #--------------------
    # change
    #--------------------

    def updateValue (self : Object,
                     value : Object) -> Boolean:
        """Updates value of <self> to <value>; does nothing when kind
           of value is wrong or exceeds the data range; returns
           whether value has changed"""

        Logging.trace(">>: self = %s, value = %s", self, value)

        cls = self.__class__
        kind  = self.kind
        count = self.count

        # type check
        stringKindList = (cls.Kind_bytes, cls.Kind_string)
        
        if kind in stringKindList:
            isOkay = isinstance(value, String)
        elif kind == cls.Kind_natural:
            isOkay = isinstance(value, Natural) and value >= 0
        else:
            isOkay = isinstance(value, Integer)

        if not isOkay:
            Logging.traceError("bad value type %s for %s",
                               value, self)
            hasChanged = False
        else:
            if kind in stringKindList:
                value = (value + count * _nulCharacter)[:count]
            else:
                if kind == cls.Kind_natural:
                    minValue, maxValue = 0, 1 << self.count * 8 - 1
                else:
                    maxValue = 1 << (self.count * 8 - 1) - 1
                    minValue = -maxValue - 1

                isOkay = isInRange(value, minValue, maxValue)

                if not isOkay:
                    Logging.traceError("value %d not in range (%d, %d) for %s",
                                       value, minValue, maxValue, self)
                    value = adaptToRange(value, minValue, maxValue)

            hasChanged = (value != self.value)
            self.value = value
            
        Logging.trace("<<: %s", hasChanged)
        return hasChanged
    
    #--------------------
    # access
    #--------------------

    def readFromByteList (self : Object,
                          byteList : ByteList):
        """Reads value of <self> from data in <byteList>; if kind is
           'string' also the count is updated"""

        Logging.trace(">>: kind = '%s', position = %d, count = %d",
                      self.kind, self.position, self.count)

        cls = self.__class__

        if self.kind == cls.Kind_string:
            # read characters until NUL character is found or
            # <byteList> is exhausted
            value = ""
            i = 0
            maxCount = self.count

            while True:
                ch = byteList[self.position + i]
                i += 1

                if ch == 0:
                    break
                else:
                    value += chr(ch)

                    if i == self.count:
                        break

        elif self.kind == cls.Kind_bytes:
            value = byteList[self.position : self.position + self.count]
        else:            
            # a number
            format = "<" + iif2(self.count == 1, "B",
                                self.count == 2, "H", "I")

            if self.kind == cls.Kind_integer:
                format = format.lower()

            value = struct.unpack_from(format, byteList, self.position)[0]

        self.value = value
        
        Logging.trace("<<: %s", self)
        
    #--------------------

    def writeToFile (self : Object,
                     file : Object):
        """Writes value <self> to random access file given by <file>"""

        Logging.trace(">>: %s", self)

        cls = self.__class__
        stringKindList = (cls.Kind_bytes, cls.Kind_string)
        kind = self.kind
        
        if kind in stringKindList:
            byteList = bytearray(self.value, encoding = "ascii")
        else:
            format = "<" + iif2(self.count == 1, "B",
                                self.count == 2, "H", "I")

            if kind == cls.Kind_integer:
                format = format.lower()

            byteList = struct.pack(format, self.value)

        file.seek(self.position)
        file.write(byteList)
        
        Logging.trace("<<")

#====================

# union types of plain type or access descriptor to that type
ByteListOrAccessDescriptor = Object
NaturalOrAccessDescriptor  = Object
IntegerOrAccessDescriptor  = Object
StringOrAccessDescriptor   = Object

#====================

class _ByteData:
    """Supports the creation of byte sequences from other data types"""

    @classmethod
    def fromNatural (cls : Class,
                     value : Natural,
                     byteCount : Natural) -> ByteList:
        """Returns a little endian byte list from natural <value> with
           length <byteCount>"""

        Logging.trace(">>: value = %d, byteCount = %d",
                      value, byteCount)
        result = value.to_bytes(byteCount, "little", signed = False)
        Logging.trace("<<: %s", result.hex())
        return result

    #--------------------

    @classmethod
    def fromInteger (cls : Class,
                     value : Integer,
                     byteCount : Natural) -> ByteList:
        """Returns a little endian byte list from integer <value> with
           length <byteCount>"""

        Logging.trace(">>: value = %d, byteCount = %d",
                      value, byteCount)
        result = value.to_bytes(byteCount, "little", signed = True)
        Logging.trace("<<: %s", result.hex())
        return result

    #--------------------

    @classmethod
    def fromString (cls : Class,
                    value : String,
                    isFilled : Boolean,
                    maxCount : Natural) -> ByteList:
        """Returns byte list for string <value> either filled to
           <maxCount> (when <isFilled> is set) or cut at end of
           string"""

        Logging.trace(">>: value = '%s', isFilled = %s, maxCount = %d",
                      value, isFilled, maxCount)

        nulCharacter = chr(0)
        value = value[:maxCount]

        if isFilled:
            length = len(value)
            value += nulCharacter * (maxCount - length)
        else:
            # fill string to even size with either one or two trailing
            # nul characters
            fillCount = 1 if len(value) % 2 == 1 else 2
            value += nulCharacter * fillCount
            
        result = bytearray(value, encoding="ascii", errors="replace")

        Logging.trace("<<: %s", result)
        return result

#====================

class _ByteListReader:
    """Encapsulates a sequential access to a slice of a byte list"""

    #--------------------
    # PRIVATE METHODS
    #--------------------

    def _readBytesNOLOG (self : Object,
                         kind : String,
                         count : Natural) -> AccessDescriptor:
        """Reads <count> bytes in byte list at current position and
           returns them as a access descriptor with given <kind>"""

        result = AccessDescriptor(kind, self._position, count)
        result.readFromByteList(self._byteList)
        newPosition = min(self._position + count, self._endPosition)
        self._position = newPosition
        return result
        
    #--------------------
    # EXPORTED METHODS
    #--------------------
    
    def __init__ (self : Object,
                  byteList : ByteList,
                  position : Natural = 0,
                  size : Natural = _infinity):
        """A reader wrapper for sequential reading the slice of
           <byteList> starting at <position> with a size of <size>"""

        Logging.trace(">>: position = %d, size = %d",
                      position, size)

        endPosition = size + position
        self._byteList    = byteList
        self._position    = position
        self._endPosition = min(size + position, len(byteList))
        
        Logging.trace("<<: %s", self)
        
    #--------------------

    def makeSlice (self : Object,
                   size : Natural) -> Object:
        """Returns a slice onto same byte list with <size> bytes
           starting at current position"""

        Logging.trace(">>: %d", size)
        result = _ByteListReader(self._byteList, self._position, size)
        Logging.trace("<<: %s", result)
        return result
    
    #--------------------
    # type conversion
    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns string representation of <self>"""

        clsName = self.__class__.__name__
        characterList = _subListNOLOG(self._byteList,
                                      self._position, self._endPosition)
        
        template = "%s(byteList = %s, position = %d, endPosition = %d)"
        st = (template
              % (clsName,
                 characterList, self._position, self._endPosition))
        return st
    
    #--------------------
    # measurement
    #--------------------

    def count (self : Object) -> Natural:
        """Returns the remaining length of the reader"""
        
        Logging.trace(">>")
        result = self._endPosition - self._position
        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def isDone (self : Object) -> Boolean:
        """Tells whether reader has been completely exhausted"""
        
        Logging.trace(">>")
        result = (self._endPosition <= self._position)
        Logging.trace("<<: %s", result)
        return result
    
    #--------------------
    # access
    #--------------------

    def readBytes (self : Object,
                   count : Natural) -> AccessDescriptor:
        """Reads <count> bytes in byte list at current position and
           returns them as a byte list access descriptor"""

        # Logging.trace(">>: position = %d, count = %d",
        #               self._position, count)

        result = self._readBytesNOLOG(AccessDescriptor.Kind_bytes,
                                      count)
        Assertion.check(len(result.value) == count,
                        "byte list too short")
        
        # Logging.trace("<<: position = %d", self._position)
        return result
        
    #--------------------

    def readNatural (self : Object,
                     count : Natural) -> AccessDescriptor:
        """Reads <count> bytes in byte list at current position and
           returns them as an (unsigned) natural access descriptor
           assuming little endian order"""

        #Logging.trace(">>: position = %d, count = %d",
        #              self._position, count)

        result = self._readBytesNOLOG(AccessDescriptor.Kind_natural,
                                      count)

        #Logging.trace("<<: result = %s, position = %d",
        #              result, self._position)
        return result
        
    #--------------------

    def readInteger (self : Object,
                     count : Natural) -> Integer:
        """Reads <count> bytes in byte list at current position and
           returns them as a (signed) integer access descriptor
           assuming little endian order"""

        # Logging.trace(">>: position = %d, count = %d",
        #               self._position, count)

        result = self._readBytesNOLOG(AccessDescriptor.Kind_integer,
                                      count)

        # Logging.trace("<<: result = %s, position = %d",
        #               result, self._position)
        return result
        
    #--------------------

    def readString (self : Object,
                    maxCount : Natural) -> AccessDescriptor:
        """Reads bytes in byte list at current position up to a
           terminating zero byte or to <maxCount> characters and
           returns them as a string access descriptor"""

        # Logging.trace(">>: position = %d, maxCount = %s",
        #               self._position, maxCount)

        result = self._readBytesNOLOG(AccessDescriptor.Kind_string,
                                      maxCount)

        # Logging.trace("<<: result = '%s', position = %d",
        #               result, self._position)
        return result

#====================

class NodeKind:
    """Node kinds"""

    # list of node kinds for bag chunks
    listForBags = ("ibag", "pbag")

    # list of node kinds for generator chunks
    listForGenerators = ("igen", "pgen")

    # list of node kinds for generator chunks
    listForModulators = ("imod", "pmod")

    # list of string-valued node kinds for the SoundFont header
    listForHeader_string = ("irom", "isng", "INAM", "ICRD", "IENG",
                            "IPRD", "ICOP", "ICMT", "ISFT")

    # list of version-valued node kinds for the SoundFont header
    listForHeader_version = ("ifil", "iver")

    # list of node kinds for the SoundFont header
    listForHeader = listForHeader_version + listForHeader_string

    # list of node kinds for instruments
    listForInstruments = ("ibag", "igen", "imod", "inst")

    # list of node kinds for presets
    listForPresets = ("pbag", "pgen", "phdr", "pmod")

    # list of RIFF chunk identifications
    listForRIFFLists = ("LIST", "RIFF")

    # list of node kinds for samples
    listForSamples = ("shdr",)

    # list of node kinds for sample wave data
    listForWaveData = ("smpl", "sm24")

#====================

class _ZoneHeader:
    """a pair of a generator index and a modulator index"""

    def __init__ (self : Object,
                  generatorIndex : Natural,
                  modulatorIndex : Natural,
                  generatorCount : Natural,
                  modulatorCount : Natural,):
        """Initializes <self> to values given by <generatorIndex>,
           <modulatorIndex>, <generatorCount> and <modulatorCount>"""

        Assertion.pre(generatorIndex is not None,
                      "generator index must be a natural")
        Assertion.pre(modulatorIndex is not None,
                      "modulator count must be a natural")
        Assertion.pre(generatorCount is not None,
                      "generator index must be a natural")
        Assertion.pre(modulatorCount is not None,
                      "modulator count must be a natural")
        Logging.trace(">>")

        self.generatorIndex = generatorIndex
        self.modulatorIndex = modulatorIndex
        self.generatorCount = generatorCount
        self.modulatorCount = modulatorCount

        Logging.trace("<<: %r", self)

    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns the string representation of <self>"""

        clsName = self.__class__.__name__
        template = ("%s("
                    + "generatorIndex = %d, modulatorIndex = %d,"
                    + "generatorCount = %d, modulatorCount = %d)")
        st = (template
              % (clsName,
                 self.generatorIndex, self.modulatorIndex,
                 self.generatorCount, self.modulatorCount))
        return st

    #--------------------
    # type conversion
    #--------------------

    def toSoundFontZone (self : Object,
                         zonedObject : Object,
                         generatorList : ObjectList,
                         modulatorList : ObjectList) -> SoundFontZone:
        """Converts a bag to SoundFont zone based on lists
           <generatorList> and <modulatorList>"""

        Logging.trace(">>: %s", self)

        getValue = \
            lambda list, i: (None if i == len(list) else list[i])

        # set up generators
        zoneGeneratorMap = {}
        index = self.generatorIndex

        for i in range(index, index + self.generatorCount):
            generator = getValue(generatorList, i)
            zoneGeneratorMap[generator.kind] = generator.amount

        # set up list of modulators
        zoneModulatorList = []
        index = self.modulatorIndex

        for i in range(index, index + self.modulatorCount):
            modulator = getValue(modulatorList, i)
            zoneModulatorList.append(modulator)

        isGlobalZone = \
            (SoundFontGeneratorKind.instrument not in zoneGeneratorMap
             and SoundFontGeneratorKind.sampleID not in zoneGeneratorMap)
        result = SoundFontZone(zonedObject, isGlobalZone,
                               zoneGeneratorMap, zoneModulatorList)
        
        Logging.trace("<<: %s", result)
        return result
    
#====================

class ChunkTreeNode:
    """Represents a chunk node in a tree, where a node has an
       attribute to value map and has a list of children"""

    # number of tree nodes so far
    _count = 0

    # object identification indexing kind to be used for the objects
    _objectIDIndexingKind = "nat"
    
    #--------------------
    # PRIVATE METHODS
    #--------------------

    def _generatorNodeToString (self : Object) -> String:
        """Returns simplified string representation for a generator
           node"""

        kind   = self.attributeToValueMap["generator"]
        amount = self.attributeToValueMap["amount"]

        if (kind not in _partnerGeneratorKindList
            or not _isObjectWithID(amount)):
            result = str(self)
        else:
            result = ("{'generator' : %s, 'amount' : '%s' }"
                      % (kind, amount.identification))

        return result
    
    #--------------------

    @classmethod
    def _objectIdentification (cls : Class,
                               nodeKind : NodeKind,
                               index : Natural,
                               naturalIndexIsForced : Boolean = False) \
                -> String:
        """Returns identification for <nodeKind> based on <index>
           depending on the <_objectIDIndexingKind> setting; if
           <naturalIndexIsForced> is set, the natural indexing is used
           in any case"""

        Logging.trace(">>: nodeKind = '%s', index = %d,"
                      + " naturalIndexIsForced = %s",
                      nodeKind, index, naturalIndexIsForced)

        if cls._objectIDIndexingKind == "nat" or naturalIndexIsForced:
            # return identification combined from node kind and an
            # index
            result = "%s%05d" % (nodeKind.upper(), index)
        else:
            # combine identification from node kind and a 48-bit
            # unique id
            result = "%s_%s" % (nodeKind, str(uuid4())[-12:]).upper()

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def _toByteListFromBagNode (self : Object) -> ByteList:
        """Converts bag node data to byte list"""

        Logging.trace(">>")

        generatorIndex = self.attributeValue("generatorIndex")
        modulatorIndex = self.attributeValue("modulatorIndex")

        result = (_ByteData.fromNatural(generatorIndex, 2)
                  + _ByteData.fromNatural(modulatorIndex, 2))
        
        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _toByteListFromGeneratorNode (self : Object) -> ByteList:
        """Converts generator node data to byte list"""

        Logging.trace(">>")

        generator = self.attributeValue("generator")
        amount    = self.attributeValue("amount")

        result = (_ByteData.fromNatural(generator, 2)
                  + _ByteData.fromNatural(amount, 2))

        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _toByteListFromInstrumentNode (self : Object) -> ByteList:
        """Converts instrument node data to byte list"""

        Logging.trace(">>")

        name     = self.attributeValue("name")
        bagIndex = self.attributeValue("bagIndex")

        result = (_ByteData.fromString(name, True, _soundFontNameLength)
                  + _ByteData.fromNatural(bagIndex, 2))

        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _toByteListFromModulatorNode (self : Object) -> ByteList:
        """Converts modulator node data to byte list"""

        Logging.trace(">>")

        sourceModulatorA     = self.attributeValue("sourceModulatorA")
        destinationGenerator = self.attributeValue("destinationGenerator")
        modulationAmount     = self.attributeValue("modulationAmount")
        sourceModulatorB     = self.attributeValue("sourceModulatorB")
        modulationTransform  = self.attributeValue("modulationTransform")

        result = (_ByteData.fromNatural(sourceModulatorA, 2)
                  + _ByteData.fromNatural(destinationGenerator, 2)
                  + _ByteData.fromInteger(modulationAmount, 2)
                  + _ByteData.fromNatural(sourceModulatorB, 2)
                  + _ByteData.fromNatural(modulationTransform, 2))

        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _toByteListFromPresetNode (self : Object) -> ByteList:
        """Converts preset node data to byte list"""

        Logging.trace(">>")

        name            = self.attributeValue("name")
        programNumber   = self.attributeValue("programNumber")
        bankNumber      = self.attributeValue("bankNumber")
        bagIndex        = self.attributeValue("bagIndex")
        libraryIndex    = self.attributeValue("libraryIndex")
        genreIndex      = self.attributeValue("genreIndex")
        morphologyIndex = self.attributeValue("morphologyIndex")

        result = (_ByteData.fromString(name, True, _soundFontNameLength)
                  + _ByteData.fromNatural(programNumber, 2)
                  + _ByteData.fromNatural(bankNumber, 2)
                  + _ByteData.fromNatural(bagIndex, 2)
                  + _ByteData.fromNatural(libraryIndex, 4)
                  + _ByteData.fromNatural(genreIndex, 4)
                  + _ByteData.fromNatural(morphologyIndex, 4))

        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _toByteListFromSampleNode (self : Object) -> ByteList:
        """Converts sample node data to byte list"""

        Logging.trace(">>")

        name                = self.attributeValue("name")
        sampleStartPosition = self.attributeValue("sampleStartPosition")
        sampleEndPosition   = self.attributeValue("sampleEndPosition")
        loopStartPosition   = self.attributeValue("loopStartPosition")
        loopEndPosition     = self.attributeValue("loopEndPosition")
        sampleRate          = self.attributeValue("sampleRate")
        originalPitch       = self.attributeValue("originalPitch")
        pitchCorrection     = self.attributeValue("pitchCorrection")
        sampleLinkIndex     = self.attributeValue("sampleLinkIndex")
        kind                = self.attributeValue("kind")

        result = (_ByteData.fromString (name, True, _soundFontNameLength)
                  + _ByteData.fromNatural(sampleStartPosition, 4)
                  + _ByteData.fromNatural(sampleEndPosition, 4)
                  + _ByteData.fromNatural(loopStartPosition, 4)
                  + _ByteData.fromNatural(loopEndPosition, 4)
                  + _ByteData.fromNatural(sampleRate, 4)
                  + _ByteData.fromNatural(originalPitch, 1)
                  + _ByteData.fromInteger(pitchCorrection, 1)
                  + _ByteData.fromNatural(sampleLinkIndex, 2)
                  + _ByteData.fromNatural(kind, 2))

        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _toByteListFromStringNode (self : Object) -> ByteList:
        """Converts string node data to byte list"""

        Logging.trace(">>")

        st = self.attributeValue("value")
        maxCount = 65536 if self.kind == "ICMT" else 256
        result = _ByteData.fromString(st, False, maxCount)

        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _toByteListFromVersionNode (self : Object) -> ByteList:
        """Converts version node data to byte list"""

        Logging.trace(">>")

        majorVersion = self.attributeValue("majorVersion")
        minorVersion = self.attributeValue("minorVersion")

        result = (_ByteData.fromNatural(majorVersion, 2)
                  + _ByteData.fromNatural(minorVersion, 2))

        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _toByteListFromWaveDataNode (self : Object) -> ByteList:
        """Converts wave node data to byte list"""

        Logging.trace(">>")
        result = self._waveData
        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def _updateMap (self : Object,
                    attributeToValueMap : StringMap):
        """Sets tree node map to <attributeToValueMap>"""
                
        Logging.trace(">>")
        self.attributeToValueMap |= attributeToValueMap
        Logging.trace("<<")
    
    #--------------------
    # EXPORTED METHODS
    #--------------------

    def __init__ (self : Object,
                  kind : String):
        """Initializes a tree node of <kind>"""

        Logging.trace(">>: kind = '%s'", kind)

        cls = self.__class__
        cls._count += 1

        self.identification      = "TND%05d" % cls._count
        self.kind                = kind
        self.attributeToValueMap = {}
        self.childrenList        = []

        Logging.trace("<<")

    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns string representation of <self>"""

        clsName = self.__class__.__name__
        childrenNodeIdentificationList = \
            [ child.identification for child in self.childrenList ]
        template = ("%s(identification = %s, kind = '%s',"
                    + " map = %s, children = %s)")
        st = (template
              % (clsName,
                 self.identification, self.kind,
                 self.attributeToValueMap, childrenNodeIdentificationList))
        return st

    #--------------------
    # configuration
    #--------------------

    @classmethod
    def setObjectIDIndexingKind (cls : Class,
                                 objectIDIndexingKind : String):
        """Sets identification indexing kind to <objectIDIndexingKind>"""

        Logging.trace(">>: %s", objectIDIndexingKind)
        cls.objectIDIndexingKind = objectIDIndexingKind
        Logging.trace("<<")
    
    #--------------------

    @classmethod
    def resetIdentificationCounter (cls : Class):
        """Resets identification counter to zero"""

        Logging.trace(">>")
        cls._count = 0
        Logging.trace("<<")

    #--------------------
    # property access
    #--------------------

    def attributeValue (self : Object,
                        attributeName : String) -> Object:
        """Returns value of node for <attributeName> converting access
           descriptor to associated value"""

        ## Logging.trace(">>: '%s'", attributeName)

        result = self.attributeToValueMap.get(attributeName)

        if isinstance(result, AccessDescriptor):
            result = result.value
        
        ## Logging.trace("<<: '%s'", result)
        return result
    
    #--------------------
    # change
    #--------------------

    def appendChild (self : Object,
                     child : Object):
        """Adds <child> as latest tree node child"""

        Logging.trace(">>")
        self.childrenList.append(child)
        Logging.trace("<<")
        
    #--------------------

    def fillBagNode (self : Object,
                     generatorIndex : NaturalOrAccessDescriptor,
                     modulatorIndex : NaturalOrAccessDescriptor):
        """Fills tree node with bag chunk data from <generatorIndex>
           and <modulatorIndex>"""

        Logging.trace(">>: generatorIndex = %s, modulatorIndex = %s",
                      generatorIndex, modulatorIndex)

        attributeToValueMap = {
            "generatorIndex" : generatorIndex,
            "modulatorIndex" : modulatorIndex
        }

        self._updateMap(attributeToValueMap)
        Logging.trace("<<: %s", self)

    #--------------------

    def fillBagNodeFromChunkData (self : Object,
                                  chunkData : _ByteListReader):
        """Fills tree node with bag chunk data from <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        generatorIndex = chunkData.readNatural(2)
        modulatorIndex = chunkData.readNatural(2)
        self.fillBagNode(generatorIndex, modulatorIndex)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillGeneratorNode (self : Object,
                           generator : NaturalOrAccessDescriptor,
                           amount : NaturalOrAccessDescriptor):
        """Fills tree node with generator chunk data from <generator>
           and <amount>"""

        amountAsString = (str(amount) if not _isObjectWithID(amount)
                          else amount.identification)
        
        Logging.trace(">>: generator = %s, amount = %s",
                      generator, amountAsString)

        attributeToValueMap = {
            "generator" : generator,
            "amount" : amount
        }

        self._updateMap(attributeToValueMap)

        Logging.trace("<<: %s", self._generatorNodeToString())

    #--------------------

    def fillGeneratorNodeFromChunkData (self : Object,
                                        chunkData : _ByteListReader):
        """Fills tree node with generator chunk data from
           <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        generator = chunkData.readNatural(2)
        amount    = chunkData.readNatural(2)

        self.fillGeneratorNode(generator, amount)

        Logging.trace("<<: %s", self._generatorNodeToString())

    #--------------------

    def fillInstrumentNode (self : Object,
                            name : StringOrAccessDescriptor,
                            bagIndex : NaturalOrAccessDescriptor):
        """Fills tree node with instrument chunk data from <name> and
           <bagIndex>"""

        Logging.trace(">>: name = %s, bagIndex = %s",
                      name, bagIndex)

        attributeToValueMap = {
            "name" : name,
            "bagIndex" : bagIndex
        }

        self._updateMap(attributeToValueMap)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillInstrumentNodeFromChunkData (self : Object,
                                         chunkData : _ByteListReader):
        """Fills tree node with instrument chunk data <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        name     = chunkData.readString(_soundFontNameLength)
        bagIndex = chunkData.readNatural(2)

        self.fillInstrumentNode(name, bagIndex)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillModulatorNode (self : Object,
                           sourceModulatorA : NaturalOrAccessDescriptor,
                           destinationGenerator : NaturalOrAccessDescriptor,
                           modulationAmount : NaturalOrAccessDescriptor,
                           sourceModulatorB : NaturalOrAccessDescriptor,
                           modulationTransform : NaturalOrAccessDescriptor):
        """Fills tree node with modulator chunk data from
           <sourceModulatorA>, <destinationGenerator>,
           <modulationAmount>, <sourceModulatorB>, and
           <modulationTransform>"""

        Logging.trace(">>: sourceModulatorA = %s, destinationGenerator = %s,"
                      + " modulationAmount = %s, sourceModulatorB = %s,"
                      + " modulationTransform = %s",
                      sourceModulatorA, destinationGenerator,
                      modulationAmount, sourceModulatorB,
                      modulationTransform)

        attributeToValueMap = {
            "sourceModulatorA"     : sourceModulatorA,
            "destinationGenerator" : destinationGenerator,
            "modulationAmount"     : modulationAmount,
            "sourceModulatorB"     : sourceModulatorB,
            "modulationTransform"  : modulationTransform
        }

        self._updateMap(attributeToValueMap)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillModulatorNodeFromChunkData (self : Object,
                                        chunkData : _ByteListReader):
        """Fills tree node with modulator chunk data <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        sourceModulatorA     = chunkData.readNatural(2)
        destinationGenerator = chunkData.readNatural(2)
        modulationAmount     = chunkData.readInteger(2)
        sourceModulatorB     = chunkData.readNatural(2)
        modulationTransform  = chunkData.readNatural(2)

        self.fillModulatorNode(sourceModulatorA,
                               destinationGenerator,
                               modulationAmount,
                               sourceModulatorB,
                               modulationTransform)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillPresetNode (self : Object,
                        name : StringOrAccessDescriptor,
                        programNumber : NaturalOrAccessDescriptor,
                        bankNumber : NaturalOrAccessDescriptor,
                        bagIndex : NaturalOrAccessDescriptor,
                        libraryIndex : NaturalOrAccessDescriptor,
                        genreIndex : NaturalOrAccessDescriptor,
                        morphologyIndex : NaturalOrAccessDescriptor):
        """Fills tree node with preset chunk data from <name>,
           <programNumber>, <bankNumber>, <bagIndex>, <libraryIndex>,
           <genreIndex>, and <morphologyIndex>"""

        Logging.trace(">>: name = %s, programNumber = %s,"
                      + " bankNumber = %s, bagIndex = %s,"
                      + " libraryIndex = %s, genreIndex = %s,"
                      + " morphologyIndex = %s",
                      name, programNumber, bankNumber, bagIndex,
                      libraryIndex, genreIndex, morphologyIndex)

        attributeToValueMap = {
            "name"            : name,
            "programNumber"   : programNumber,
            "bankNumber"      : bankNumber,
            "bagIndex"        : bagIndex,
            "libraryIndex"    : libraryIndex,
            "genreIndex"      : genreIndex,
            "morphologyIndex" : morphologyIndex
        }

        self._updateMap(attributeToValueMap)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillPresetNodeFromChunkData (self : Object,
                                     chunkData : _ByteListReader):
        """Fills tree node with preset chunk data <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        name            = chunkData.readString(_soundFontNameLength)
        programNumber   = chunkData.readNatural(2)
        bankNumber      = chunkData.readNatural(2)
        bagIndex        = chunkData.readNatural(2)
        libraryIndex    = chunkData.readNatural(4)
        genreIndex      = chunkData.readNatural(4)
        morphologyIndex = chunkData.readNatural(4)

        self.fillPresetNode(name, programNumber, bankNumber,
                            bagIndex, libraryIndex, genreIndex,
                            morphologyIndex)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillSampleNode (self : Object,
                        name : StringOrAccessDescriptor,
                        sampleStartPosition : NaturalOrAccessDescriptor,
                        sampleEndPosition : NaturalOrAccessDescriptor,
                        loopStartPosition : NaturalOrAccessDescriptor,
                        loopEndPosition : NaturalOrAccessDescriptor,
                        sampleRate : NaturalOrAccessDescriptor,
                        originalPitch : NaturalOrAccessDescriptor,
                        pitchCorrection : IntegerOrAccessDescriptor,
                        sampleLinkIndex : NaturalOrAccessDescriptor,
                        kind : NaturalOrAccessDescriptor):
        """Fills tree node with sample chunk data from <name>,
           <sampleStartPosition>, <sampleEndPosition>,
           <loopStartPosition>, <loopEndPosition>, <sampleRate>,
           <originalPitch>, <pitchCorrection>, <sampleLinkIndex>, and
           <kind>"""

        Logging.trace(">>: name = %s,"
                      + " sampleStartPosition = %s, sampleEndPosition = %s,"
                      + " loopStartPosition = %s, loopEndPosition = %s,"
                      + " sampleRate = %s, originalPitch = %s,"
                      + " pitchCorrection = %s, sampleLinkIndex = %s,"
                      + " kind = %s",
                      name, sampleStartPosition, sampleEndPosition,
                      loopStartPosition, loopEndPosition, sampleRate,
                      originalPitch, pitchCorrection, sampleLinkIndex,
                      kind)

        attributeToValueMap = {
            "name"                : name,
            "sampleStartPosition" : sampleStartPosition,
            "sampleEndPosition"   : sampleEndPosition,
            "loopStartPosition"   : loopStartPosition,
            "loopEndPosition"     : loopEndPosition,
            "sampleRate"          : sampleRate,
            "originalPitch"       : originalPitch,
            "pitchCorrection"     : pitchCorrection,
            "sampleLinkIndex"     : sampleLinkIndex,
            "kind"                : kind
        }

        self._updateMap(attributeToValueMap)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillSampleNodeFromChunkData (self : Object,
                                     chunkData : _ByteListReader):
        """Fills tree node with sample chunk data <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        name                = chunkData.readString(_soundFontNameLength)
        sampleStartPosition = chunkData.readNatural(4)
        sampleEndPosition   = chunkData.readNatural(4)
        loopStartPosition   = chunkData.readNatural(4)
        loopEndPosition     = chunkData.readNatural(4)
        sampleRate          = chunkData.readNatural(4)
        originalPitch       = chunkData.readNatural(1)
        pitchCorrection     = chunkData.readInteger(1)
        sampleLinkIndex     = chunkData.readNatural(2)
        kind                = chunkData.readNatural(2)

        self.fillSampleNode(name, sampleStartPosition, sampleEndPosition,
                            loopStartPosition, loopEndPosition, sampleRate,
                            originalPitch, pitchCorrection, sampleLinkIndex,
                            kind)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillStringNode (self : Object,
                        st : StringOrAccessDescriptor):
        """Fills tree node with string chunk data <st>"""

        Logging.trace(">>: st = %s", st)

        attributeToValueMap = { "value" : st }
        self._updateMap(attributeToValueMap)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillStringNodeFromChunkData (self : Object,
                                     chunkData : _ByteListReader):
        """Fills tree node with string chunk data <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        maxByteCount = chunkData.count()
        st = chunkData.readString(maxByteCount)

        self.fillStringNode(st)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillVersionNode (self : Object,
                         majorVersion : NaturalOrAccessDescriptor,
                         minorVersion : NaturalOrAccessDescriptor):
        """Fills tree node with version chunk data <majorVersion> and
           <minorVersion>"""

        Logging.trace(">>: majorVersion = %s, minorVersion = %s",
                      majorVersion, minorVersion)

        attributeToValueMap = { "majorVersion" : majorVersion,
                                "minorVersion" : minorVersion }
        self._updateMap(attributeToValueMap)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillVersionNodeFromChunkData (self : Object,
                                      chunkData : _ByteListReader):
        """Fills tree node with version chunk data <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        majorVersion = chunkData.readNatural(2)
        minorVersion = chunkData.readNatural(2)
        self.fillVersionNode(majorVersion, minorVersion)
        chunkData._position = chunkData._endPosition

        Logging.trace("<<: %s", self)

    #--------------------

    def fillWaveDataNode (self : Object,
                          byteCount : NaturalOrAccessDescriptor,
                          waveData : ByteListOrAccessDescriptor):
        """Fills tree node with wave chunk data from <byteCount> and
           <waveData>"""

        Logging.trace(">>: byteCount = %d", byteCount)

        attributeToValueMap = { "count" : byteCount }
        self._updateMap(attributeToValueMap)

        # do not store wave data in attribute map, but in hidden node
        # specific attribute
        self._waveData = waveData

        Logging.trace("<<: %s", self)

    #--------------------

    def fillWaveDataNodeFromChunkData (self : Object,
                                       chunkData : _ByteListReader):
        """Fills tree node with wave chunk data from <chunkData>"""

        Logging.trace(">>: kind = '%s', data = %s",
                      self.kind, chunkData)

        cls = self.__class__
        byteCount = chunkData.count()
        accessDescriptor = \
            chunkData._readBytesNOLOG(AccessDescriptor.Kind_bytes,
                                      byteCount)
        self.fillWaveDataNode(byteCount, accessDescriptor.value)
        chunkData._position = chunkData._endPosition

        Logging.trace("<<: %s", self)

    #--------------------
    # type conversion
    #--------------------

    def toByteList (self : Object) -> ByteList:
        """Serializes tree node and its children to byte list"""

        nodeKind = self.kind
        Logging.trace(">>: nodeKind = %s", nodeKind)

        fourCharStringToByteList = \
            lambda st: _ByteData.fromString(st, True, 4)
        isListNode           = nodeKind.startswith("LIST-")
        isPDTARootNode       = nodeKind.endswith(_pdtaRootNodeKindSuffix)
        isUnchunkedChildNode = nodeKind.startswith(_childNodeKindPrefix)

        if isUnchunkedChildNode:
            nodeKind = nodeKind[-4:]

        if isListNode:
            nodeData = fourCharStringToByteList(nodeKind[-4:])
        elif nodeKind == "RIFF":
            nodeData = fourCharStringToByteList("sfbk")
        elif nodeKind in NodeKind.listForHeader_string:
            nodeData = self._toByteListFromStringNode()
        elif nodeKind in NodeKind.listForHeader_version:
            nodeData = self._toByteListFromVersionNode()
        elif nodeKind in NodeKind.listForWaveData:
            nodeData = self._toByteListFromWaveDataNode()
        elif isPDTARootNode:
            # those are the formal root chunks for the lists within
            # the PDTA list
            nodeData = b''
        elif nodeKind == "phdr":
            nodeData = self._toByteListFromPresetNode()
        elif nodeKind == "inst":
            nodeData = self._toByteListFromInstrumentNode()
        elif nodeKind == "shdr":
            nodeData = self._toByteListFromSampleNode()
        elif nodeKind in NodeKind.listForGenerators:
            nodeData = self._toByteListFromGeneratorNode()
        elif nodeKind in NodeKind.listForModulators:
            nodeData = self._toByteListFromModulatorNode()
        elif nodeKind in NodeKind.listForBags:
            nodeData = self._toByteListFromBagNode()
        else:
            Logging.traceError("unknown node kind '%s'",
                               nodeKind)

        childrenData = bytes(0).join([ node.toByteList()
                                       for node in self.childrenList ])
        byteCount = len(nodeData) + len(childrenData)

        if isUnchunkedChildNode:
            prefix    = b''
            countData = b''
        else:
            prefix    = fourCharStringToByteList(nodeKind[:4])
            countData = _ByteData.fromNatural(byteCount, 4)

        Logging.trace("--: kind = '%s', byteCount = %s,"
                      + " prefixLength = %d, countLength = %d,"
                      + " nodeDataLength = %d, childrenDataLength = %d",
                      nodeKind, byteCount,
                      len(prefix), len(countData),
                      len(nodeData), len(childrenData))

        result = prefix + countData + nodeData + childrenData

        Logging.trace("<<: %d", len(result))
        return result
        
    #--------------------
    
    def toSoundFontGenerator (self : Object,
                              index : Natural) -> SoundFontGenerator:
        """Creates a SoundFont generator from node and returns it"""

        nodeKind = self.kind
        Assertion.check(nodeKind in NodeKind.listForGenerators,
                        "can only convert GENs, not %s" % nodeKind)
        Logging.trace(">>: nodeKind = %s", nodeKind)

        cls = self.__class__
        identification = cls._objectIdentification(nodeKind, index, True)

        kind               = self.attributeValue("generator")
        amount             = self.attributeValue("amount")
        parentIsInstrument = (nodeKind == "igen")

        result = SoundFontGenerator(identification,
                                    kind, amount, parentIsInstrument)

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def toSoundFontInstrument (self : Object,
                               index : Natural) -> SoundFontInstrument:
        """Creates a SoundFont instrument from node and returns it"""

        expectedNodeKind = "inst"
        nodeKind = self.kind
        Assertion.check(nodeKind == expectedNodeKind,
                        "expected '%s', not %s" % (expectedNodeKind,
                                                   nodeKind))
        Logging.trace(">>: nodeKind = %s", nodeKind)

        cls = self.__class__
        identification = cls._objectIdentification(nodeKind, index)

        name = self.attributeValue("name")
        result = SoundFontInstrument(identification)
        result.setName(name)
        
        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def toSoundFontModulator (self : Object,
                              index : Natural) -> SoundFontModulator:
        """Creates a SoundFont modulator from node and returns it"""

        nodeKind = self.kind
        Assertion.check(nodeKind in NodeKind.listForModulators,
                        "can only convert MODs, not %s" % nodeKind)
        Logging.trace(">>: nodeKind = %s", nodeKind)

        cls = self.__class__
        identification = cls._objectIdentification(nodeKind, index, True)

        sourceModulatorA     = self.attributeValue("sourceModulatorA")
        destinationGenerator = self.attributeValue("destinationGenerator")
        modulationAmount     = self.attributeValue("modulationAmount")
        sourceModulatorB     = self.attributeValue("sourceModulatorB")
        modulationTransform  = self.attributeValue("modulationTransform")

        result = \
            SoundFontModulator(identification,
                               sourceModulatorA, sourceModulatorB,
                               destinationGenerator, modulationAmount,
                               modulationTransform == 0)

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def toSoundFontPreset (self : Object,
                           index : Natural) -> SoundFontPreset:
        """Creates a SoundFont preset from node and returns it"""

        expectedNodeKind = "phdr"
        nodeKind = self.kind
        Assertion.check(nodeKind == expectedNodeKind,
                        "expected '%s', not %s" % (expectedNodeKind,
                                                   nodeKind))
        Logging.trace(">>: nodeKind = %s", nodeKind)

        cls = self.__class__
        identification = cls._objectIdentification(nodeKind, index)
        result = SoundFontPreset(identification)

        result.setName(self.attributeValue("name"))
        result.programNumber   = self.attributeValue("programNumber")
        result.bankNumber      = self.attributeValue("bankNumber")
        result.bagIndex        = self.attributeValue("bagIndex")
        result.libraryIndex    = self.attributeValue("libraryIndex")
        result.genreIndex      = self.attributeValue("genreIndex")
        result.morphologyIndex = self.attributeValue("morphologyIndex")

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def toSoundFontWaveData (self : Object) -> ByteList:
        """Creates a SoundFont wave byte list from node and
           returns it"""

        nodeKind = self.kind
        Assertion.check(nodeKind in NodeKind.listForWaveData,
                        "expected wave node, not %s" % nodeKind)
        Logging.trace(">>: nodeKind = %s", nodeKind)
        result = self._waveData
        
        Logging.trace("<<: %d", len(result))
        return result

    #--------------------

    def toSoundFontZoneHeader (self : Object,
                               successorNode : Object) -> _ZoneHeader:
        """Creates a zone header from current node and <successorNode>
           and returns it"""

        nodeKind          = self.kind
        successorNodeKind = successorNode.kind
        errorMessageTemplate = "can only convert BAGs, not %s"
        Assertion.check(nodeKind in NodeKind.listForBags,
                        errorMessageTemplate % nodeKind)
        Assertion.check(successorNodeKind in NodeKind.listForBags,
                        errorMessageTemplate % successorNodeKind)
        Logging.trace(">>: node = %s, successorNode = %s",
                      self, successorNode)

        generatorIndex = self.attributeValue("generatorIndex")
        modulatorIndex = self.attributeValue("modulatorIndex")
        otherGeneratorIndex = successorNode.attributeValue("generatorIndex")
        otherModulatorIndex = successorNode.attributeValue("modulatorIndex")
        generatorCount = otherGeneratorIndex - generatorIndex
        modulatorCount = otherModulatorIndex - modulatorIndex

        result = _ZoneHeader(generatorIndex, modulatorIndex,
                             generatorCount, modulatorCount)

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def updateSoundFontSample (self : Object,
                               sampleList : ObjectList,
                               index : Natural):
        """Updates SoundFont sample at <index> in <sampleList> from
           node"""

        expectedNodeKind = "shdr"
        nodeKind = self.kind
        Assertion.check(nodeKind == expectedNodeKind,
                        "expected '%s', not %s" % (expectedNodeKind,
                                                   nodeKind))
        Logging.trace(">>: nodeKind = %s", nodeKind)

        sample = sampleList[index]

        sample.setName(self.attributeValue("name"))
        sample.sampleStartPosition = \
            self.attributeValue("sampleStartPosition")
        sample.sampleEndPosition = \
            self.attributeValue("sampleEndPosition")
        sample.loopStartPosition = \
            self.attributeValue("loopStartPosition")
        sample.loopEndPosition = \
            self.attributeValue("loopEndPosition")
        sample.sampleRate = \
            self.attributeValue("sampleRate")
        sample.originalPitch = \
            self.attributeValue("originalPitch")
        sample.pitchCorrection = \
            self.attributeValue("pitchCorrection")

        sampleKind = SoundFontSampleKind(self.attributeValue("kind"))
        partnerIndex = self.attributeValue("sampleLinkIndex")
        hasNoPartner = (partnerIndex == 0
                        or sampleKind == SoundFontSampleKind.monoSample)
        sample.partner = None if hasNoPartner else sampleList[partnerIndex]
        sample.kind    = sampleKind

        Logging.trace("<<: %s", sample)

#====================

class ChunkTreeNodeList (list):
    """a list of chunk tree nodes with some additional operations"""

    def __init__ (self : Object):
        """Constructs a tree node list"""

        Logging.trace(">>")
        super().__init__()
        Logging.trace("<<: %s", self)
    
    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns string representation of <self>"""

        clsName = self.__class__.__name__
        template = "%s(elementCount = %d)"
        st = template % (clsName, len(self))
        return st
        
    #--------------------

    def flatten (self : Object):
        """Removes technical nodes from current list and flattens its
           structure"""

        Logging.trace(">>: %s", self)

        relevantNodeKindList = (
            # header
            NodeKind.listForHeader
            # sample wave data
            + NodeKind.listForWaveData
            # samples
            + NodeKind.listForSamples
            # instruments
            + NodeKind.listForInstruments
            # presets
            + NodeKind.listForPresets
        )

        flattenedNodeList = ChunkTreeNodeList()
        listStack = [ self ]

        while len(listStack) > 0:
            lengthProfile = [ len(element) for element in listStack ]
            Logging.trace("--: listStackLengthProfile = %s",
                          lengthProfile)
            currentList = listStack[-1]

            if len(currentList) == 0:
                listStack.pop()
            else:
                node = currentList[0]
                nodeKind = node.kind
                del currentList[0]
                childrenList = node.childrenList
                Logging.trace("--: node = %s, childrenCount = %d",
                              node, len(childrenList))

                if nodeKind not in relevantNodeKindList:
                    Logging.trace("--: skip node '%s'", nodeKind)
                else:
                    flattenedNodeList.append(node)
                    Logging.trace("--: append node '%s'", nodeKind)

                if len(childrenList) > 0:
                    listStack.append(childrenList)

        self.clear()
        self.extend(flattenedNodeList)
                        
        Logging.trace("<<: %s", self)

    #--------------------

    def update (self : Object,
                byteListReader : _ByteListReader):
        """Reads chunks via <byteListReader> and updates node list"""

        Logging.trace(">>: self = %s, byteListReader = %s",
                      self, byteListReader)

        while not byteListReader.isDone():
            chunkIdentification = byteListReader.readString(4).value
            chunkSize = byteListReader.readNatural(4).value

            if chunkIdentification in NodeKind.listForRIFFLists:
                # skip over list tag
                junk = byteListReader.readString(4)
                chunkSize -= 4

            # adapt size to even number
            chunkSize += chunkSize % 2
            chunkData = byteListReader.makeSlice(chunkSize)

            # traverse chunks identified by <chunkIdentification>
            # accessible via <chunkData> and update current node list
            # accordingly
            while not chunkData.isDone():
                Logging.trace("--: processing '%s'", chunkIdentification)
                treeNode = ChunkTreeNode(chunkIdentification)
                self.append(treeNode)

                if chunkIdentification == "RIFF":
                    break
                elif chunkIdentification in NodeKind.listForHeader_string:
                    treeNode.fillStringNodeFromChunkData(chunkData)
                elif chunkIdentification in NodeKind.listForHeader_version:
                    treeNode.fillVersionNodeFromChunkData(chunkData)
                elif chunkIdentification in NodeKind.listForWaveData:
                    treeNode.fillWaveDataNodeFromChunkData(chunkData)
                elif chunkIdentification == "shdr":
                    treeNode.fillSampleNodeFromChunkData(chunkData)
                elif chunkIdentification in NodeKind.listForBags:
                    treeNode.fillBagNodeFromChunkData(chunkData)
                elif chunkIdentification in NodeKind.listForGenerators:
                    treeNode.fillGeneratorNodeFromChunkData(chunkData)
                elif chunkIdentification in NodeKind.listForModulators:
                    treeNode.fillModulatorNodeFromChunkData(chunkData)
                elif chunkIdentification == "inst":
                    treeNode.fillInstrumentNodeFromChunkData(chunkData)
                elif chunkIdentification == "phdr":
                    treeNode.fillPresetNodeFromChunkData(chunkData)
                elif chunkIdentification != "LIST":
                    Logging.traceError("unknown chunk kind '%s'",
                                       chunkIdentification)
                    break
                else:
                    subList = ChunkTreeNodeList()
                    subList.update(chunkData)

                    for node in subList:
                        treeNode.appendChild(node)

            if chunkIdentification != "RIFF":
                byteListReader._position = chunkData._endPosition

        Logging.trace("<<: count = %d", len(self))

#====================

class SoundFontFileReader:
    """Represents a SoundFont file reader"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _collectElementLists (self : Object,
                              soundFont : SoundFont,
                              nodeList : ChunkTreeNodeList,
                              objectIDIndexingKind : String) -> Tuple:
        """Traverses nodes in <nodeList> and collects objects for
           presets and instruments; bag data is collected into
           <zoneHeaderListMap>, generators into <generatorListMap>,
           modulators into <modulatorListMap> and bag index intervals
           into <intervalListMap>; all those list maps are returned as
           well as the count of samples; <objectIDIndexingKind> tells
           how the identifiers indices are generated"""

        Logging.trace(">>")

        cls = self.__class__

        ChunkTreeNode.setObjectIDIndexingKind(objectIDIndexingKind)

        tempMap = { keyLetter : [] for keyLetter in _keyLetterList }
        generatorListMap  = deepcopy(tempMap)
        modulatorListMap  = deepcopy(tempMap)
        intervalListMap   = deepcopy(tempMap)
        zoneHeaderListMap = deepcopy(tempMap)

        previousNodeKind = ""
        previousBagIndex = 0
        previousNode = None
        count = 0

        for node in nodeList:
            nodeKind = node.kind
            groupHasChanged  = (nodeKind != previousNodeKind)
            isInstrumentNode = nodeKind in NodeKind.listForInstruments
            isPresetNode     = nodeKind in NodeKind.listForPresets
            count = 0 if groupHasChanged else count + 1

            if isInstrumentNode or isPresetNode:
                key = iif(isInstrumentNode,
                          _instrumentKeyLetter, _presetKeyLetter)

                if nodeKind in NodeKind.listForBags:
                    if count > 0:
                        zoneHeaderList = zoneHeaderListMap[key]
                        zoneHeaderList.append(previousNode
                                              .toSoundFontZoneHeader(node))
                elif nodeKind in NodeKind.listForGenerators:
                    generatorList = generatorListMap[key]
                    generator = node.toSoundFontGenerator(count)
                    generatorList.append(generator)
                elif nodeKind in NodeKind.listForModulators:
                    modulatorList = modulatorListMap[key]
                    modulator = node.toSoundFontModulator(count)
                    modulatorList.append(modulator)
                elif nodeKind not in ("inst", "phdr"):
                    Logging.traceError("unexpected node kind '%s'",
                                       nodeKind)
                else:
                    intervalList = intervalListMap[key]
                    currentBagIndex = node.attributeValue("bagIndex")
                    interval = (previousBagIndex, currentBagIndex)

                    if groupHasChanged:
                        intervalList.clear()
                    else:
                        Assertion.check(interval[0] is not None
                                        and interval[1] is not None,
                                        "bad interval in list of '%s'"
                                        % nodeKind)
                        intervalList.append(interval)

                    previousBagIndex = currentBagIndex

            previousNodeKind = nodeKind
            previousNode     = node

        # remove sentinel elements in generator and modulator lists
        for keyLetter in _keyLetterList:
            generatorListMap[keyLetter].pop()
            modulatorListMap[keyLetter].pop()
            
        # provide some final statistics
        statisticsMap = \
            self._makeStatisticsMap(generatorListMap, modulatorListMap,
                                    intervalListMap, zoneHeaderListMap)
        result = (generatorListMap, modulatorListMap,
                  intervalListMap, zoneHeaderListMap)

        Logging.trace("<<: statistics = %s", statisticsMap)
        return result

    #--------------------

    def _countSamples (self : Object,
                       nodeList : ChunkTreeNodeList) -> Natural:
        """Returns count of sample headers in <nodeList>"""

        Logging.trace(">>")

        sampleList = [ node for node in nodeList if node.kind == "shdr" ]

        # subtract one for sentinel header
        result = len(sampleList) - 1
        
        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def _fillSoundFont (self : Object,
                        soundFont : SoundFont,
                        nodeList : ChunkTreeNodeList,
                        objectIndexingKind : String):
        """Traverses nodes in <nodeList> and fills <soundFont>
           accordingly"""

        Logging.trace(">>: nodeListCount = %d", len(nodeList))

        cls = self.__class__

        # pass 1: update header information
        self._fillSoundFontHeader(soundFont.header, nodeList)

        # pass 2: find number of samples
        sampleCount = self._countSamples(nodeList)

        # pass 3: collect bags, generators, modulators and bag index
        # intervals into lists
        generatorListMap, modulatorListMap, intervalListMap, \
            zoneHeaderListMap = \
            self._collectElementLists(soundFont, nodeList,
                                      objectIndexingKind)

        # pass 4: generate list of sample headers and populate sample,
        # instrument and preset list and their associated bag
        # intervals
        soundFont.sampleList = [
            SoundFontSample(ChunkTreeNode._objectIdentification("shdr", i))
            for i in range(sampleCount)
        ]

        self._generateSoundFontElements(soundFont, nodeList,
                                        generatorListMap, modulatorListMap,
                                        intervalListMap, zoneHeaderListMap)

        # pass 5: relink non-global zones to appropriate partners
        self._relinkNonGlobalZones(soundFont)

        # pass 6: update wave data information in soundFont
        self._updateWaveData(soundFont, nodeList)

        Logging.trace("<<")

    #--------------------

    def _fillSoundFontHeader (self : Object,
                              soundFontHeader : SoundFontHeader,
                              nodeList : ChunkTreeNodeList):
        """Fills <soundFontHeader> by data from <node>"""

        Logging.trace(">>")

        for node in nodeList:
            nodeKind = node.kind
            Logging.trace("--: node kind '%s'", nodeKind)

            if nodeKind not in NodeKind.listForHeader:
                Logging.trace("--: break at first non-header node")
                break
            elif nodeKind in ("ifil", "iver"):
                majorVersion = node.attributeValue("majorVersion")
                minorVersion = node.attributeValue("minorVersion")

                if majorVersion is None or minorVersion is None:
                    Logging.traceError("bad versions in %s", nodeKind)
                else:
                    version = SoundFontVersion(majorVersion, minorVersion)

                    if nodeKind == "ifil":
                        soundFontHeader.specVersion = version
                    else:
                        soundFontHeader.romVersion  = version
            else:
                st = node.attributeValue("value")

                if nodeKind == "isng":
                    soundFontHeader.soundEngine = st
                elif nodeKind == "irom":
                    soundFontHeader.romName = st
                elif nodeKind == "INAM":
                    soundFontHeader.bankName = st
                elif nodeKind == "ICRD":
                    soundFontHeader.creationDate = st
                elif nodeKind == "IENG":
                    soundFontHeader.engineerNames = st
                elif nodeKind == "IPRD":
                    soundFontHeader.productName = st
                elif nodeKind == "ICOP":
                    soundFontHeader.copyright = st
                elif nodeKind == "ICMT":
                    soundFontHeader.comment = st
                elif nodeKind == "ISFT":
                    soundFontHeader.toolNames = st

        Logging.trace("<<: %s", soundFontHeader)

    #--------------------

    def _generateSoundFontElements (self : Object,
                                    soundFont : SoundFont,
                                    nodeList : ChunkTreeNodeList,
                                    generatorListMap : GeneratorListMap,
                                    modulatorListMap : ModulatorListMap,
                                    intervalListMap : IntervalListMap,
                                    zoneHeaderListMap : ZoneHeaderListMap):
        """Updates <soundFont> by collecting presets and instruments
           using bag data in <zoneHeaderListMap>, generators in
           <generatorListMap>, modulators in <modulatorListMap> and
           bag index intervals in <intervalListMap>"""

        Logging.trace(">>")

        Logging.trace("--: intervalListMap = %r", intervalListMap)
        previousNodeKind = ""
        count = 0
        sampleList = soundFont.sampleList
        sampleCount = len(sampleList)

        for node in nodeList:
            nodeKind = node.kind
            Logging.trace("--: node = %s", node)
            groupHasChanged = (nodeKind != previousNodeKind)
            count = iif(groupHasChanged, 0, count + 1)
            previousNodeKind = nodeKind
        
            if nodeKind == "shdr":
                if count == sampleCount:
                    Logging.trace("--: skipped sentinel node")
                else:
                    sample = sampleList[count]
                    node.updateSoundFontSample(sampleList, count)
            elif nodeKind in ("inst", "phdr"):
                isInstrument = (nodeKind == "inst")
                key = iif(isInstrument,
                          _instrumentKeyLetter, _presetKeyLetter)
                intervalList = intervalListMap[key]
                numberOfIntervals = len(intervalList)

                if count >= numberOfIntervals:
                    Logging.trace("--: skip sentinel node")
                else:
                    if isInstrument:
                        instrument = node.toSoundFontInstrument(count)
                        soundFont.instrumentList.append(instrument)
                        zonedObject = instrument
                    else:
                        preset = node.toSoundFontPreset(count)
                        soundFont.presetList.append(preset)
                        zonedObject = preset

                    # traverse all the bags and add them as zones to
                    # zoned object
                    instrumentList = soundFont.instrumentList
                    generatorList  = generatorListMap[key]
                    modulatorList  = modulatorListMap[key]

                    interval = intervalList[count]
                    zoneHeaderList = \
                        zoneHeaderListMap[key][interval[0]:interval[1]]

                    Logging.trace("--: sampleCount = %d,"
                                  + " instrumentCount = %d,"
                                  + " generatorCount = %d,"
                                  + " modulatorCount = %d,"
                                  + " interval = %r",
                                  len(sampleList), len(instrumentList),
                                  len(generatorList), len(modulatorList),
                                  interval)

                    for zoneHeader in zoneHeaderList:
                        zone = zoneHeader.toSoundFontZone(zonedObject,
                                                          generatorList,
                                                          modulatorList)

                        if zone.isGlobal:
                            zonedObject.globalZone = zone
                        else:
                            zonedObject.zoneList.append(zone)

        Logging.trace("<<")

    #--------------------

    def _makeStatisticsMap (self : Object,
                            generatorListMap : GeneratorListMap,
                            modulatorListMap : ModulatorListMap,
                            intervalListMap : IntervalListMap,
                            zoneHeaderListMap : ZoneHeaderListMap) -> Map:
        """Make a statistics summary from objects for presets and
           instruments using bag data from <zoneHeaderListMap>, generators
           from <generatorListMap>, modulators from <modulatorListMap>
           and zone index intervals from <intervalListMap>"""

        Logging.trace(">>")

        nameToDataMap = { "zoneHeaders" : zoneHeaderListMap,
                          "generators"  : generatorListMap,
                          "modulators"  : modulatorListMap,
                          "zones"       : intervalListMap }
        result = {}

        for key, dataMap in nameToDataMap.items():
            mapElement = {}
            result[key] = mapElement

            for letter in _keyLetterList:
                mapElement[letter] = len(dataMap[letter])

        Logging.trace("<<")
        return result

    #--------------------

    def _relinkNonGlobalZones (self : Object,
                               soundFont : SoundFont):
        """Changes linkage attributes 'sampleID' and 'instrument'
           in non-global zones to contain """

        Logging.trace(">>")

        sampleList      = soundFont.sampleList
        instrumentList  = soundFont.instrumentList
        zonedObjectList = instrumentList + soundFont.presetList

        for zonedObject in zonedObjectList:
            Logging.trace("--: process zones of '%s'", zonedObject.name)

            for i, zone in enumerate(zonedObject.zoneList):
                generatorMap = zone.generatorMap
                Logging.trace("--: process zone '%d', generators = %s",
                              i, generatorMap.keys())

                for kind in (SoundFontGeneratorKind.sampleID,
                             SoundFontGeneratorKind.instrument):
                    if kind not in generatorMap:
                        Logging.trace("--: %s not found", kind)
                    else:
                        kindIsSampleID = \
                            kind == SoundFontGeneratorKind.sampleID
                        generatorAmount = generatorMap[kind]
                        partnerIndex = (SoundFontGeneratorAmount
                                        .toPropertyData(generatorAmount,
                                                        kind, kindIsSampleID))
                        partnerList = (sampleList if kindIsSampleID
                                       else instrumentList)
                        referencedObject = partnerList[partnerIndex]
                        identification = referencedObject.identification
                        name = referencedObject.name.toShortString()
                        Logging.trace("--: %s found => update to %s-%s",
                                      kind, identification, name)
                        generatorMap[kind] = referencedObject

        Logging.trace("<<")

    #--------------------

    def _updateWaveData (self : Object,
                         soundFont : SoundFont,
                         nodeList : ChunkTreeNodeList):
        """Update wave data in <soundFont> from node in <nodeList>"""

        Logging.trace(">>")

        standardWaveData = ByteList([])
        extendedWaveData = ByteList([])

        for node in nodeList:
            if node.kind in NodeKind.listForWaveData:
                byteList = node.toSoundFontWaveData()

                if node.kind == "smpl":
                    standardWaveData = byteList
                else:
                    extendedWaveData = byteList

        waveData = SoundFontWaveData()
        waveData.fillFromByteListPair(standardWaveData, extendedWaveData)
        soundFont.waveData = waveData

        Logging.trace("<<")
    
    #--------------------
    # EXPORTED METHODS
    #--------------------

    def __init__ (self : Object,
                  fileName : String):
        """Initializes a SoundFont file reader for accessing
           <fileName>"""

        Logging.trace(">>: fileName = '%s'", fileName)
        self.fileName = fileName
        Logging.trace("<<")
        
    #--------------------

    def readChunks (self : Object) -> ChunkTreeNodeList:
        """Reads file and returns list of SoundFont chunks"""

        Logging.trace(">>")

        result = ChunkTreeNodeList()

        if not OperatingSystem.hasFile(self.fileName):
            Logging.traceError("cannot open file '%s'", self.fileName)
        else:
            with open(self.fileName, "rb") as soundFontFile:
                byteList = soundFontFile.read()

            byteListReader = _ByteListReader(byteList)
            result.update(byteListReader)
            result.flatten()

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def readSoundFont (self : Object,
                       objectIDIndexingKind : String = "nat") \
                       -> SoundFont:
        """Reads file and returns SoundFont object"""

        Logging.trace(">> objectIDIndexingKind = '%s'",
                      objectIDIndexingKind)

        # fill soundFont from node list
        result = SoundFont()
        treeNodeList = self.readChunks()
        self._fillSoundFont(result, treeNodeList, objectIDIndexingKind)

        Logging.trace("<<: %s", result)
        return result

#====================

class SoundFontFileWriter:
    """Represents a SoundFont file writer"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _appendHeaderStringNodeNOLOG (self : Object,
                                      nodeList : ChunkTreeNodeList,
                                      nodeKind : String,
                                      header : SoundFontHeader,
                                      attributeName : String):
        """Appends chunk tree node with <nodeKind> to <nodeList> using
           string data from <header> a attribute named <attributeName>
           (without logging)"""

        node = ChunkTreeNode(nodeKind)
        st = getattr(header, attributeName)
        node.fillStringNode(st)
        nodeList.append(node)
    
    #--------------------

    def _appendHeaderStringNode (self : Object,
                                 nodeList : ChunkTreeNodeList,
                                 nodeKind : String,
                                 header : SoundFontHeader,
                                 attributeName : String):
        """Appends chunk tree node with <nodeKind> to <nodeList> using
           string data from <header> a attribute named <attributeName>"""

        Logging.trace(">>: nodeKind = '%s', attributeName = '%s'",
                      nodeKind, attributeName)

        self._appendHeaderStringNodeNOLOG(nodeList, nodeKind,
                                          header, attributeName)

        Logging.trace("<<")
    
    #--------------------

    def _appendHeaderStringNodeConditionally (self : Object,
                                              nodeList : ChunkTreeNodeList,
                                              nodeKind : String,
                                              header : SoundFontHeader,
                                              attributeName : String):
        """Appends chunk tree node with <nodeKind> to <nodeList> using
           string data from <header> a attribute named <attributeName>
           when this value is not empty"""

        Logging.trace(">>: nodeKind = '%s', attributeName = '%s'",
                      nodeKind, attributeName)

        if getattr(header, attributeName) > "":
            self._appendHeaderStringNodeNOLOG(nodeList, nodeKind,
                                              header, attributeName)

        Logging.trace("<<")
    
    #--------------------

    def _appendHeaderVersionNode (self : Object,
                                  nodeList : ChunkTreeNodeList,
                                  nodeKind : String,
                                  header : SoundFontHeader,
                                  attributeName : String):
        """Appends chunk tree node with <nodeKind> to <nodeList> using
           version data from <header> a attribute named <attributeName>"""

        Logging.trace(">>: nodeKind = '%s', attributeName = '%s'",
                      nodeKind, attributeName)

        node = ChunkTreeNode(nodeKind)
        attribute = getattr(header, attributeName)
        majorVersion, minorVersion = attribute.toRawData()
        node.fillVersionNode(majorVersion, minorVersion)
        nodeList.append(node)

        Logging.trace("<<")
    
    #--------------------

    def _appendNodeListForBags (self : Object,
                                nodeList : ChunkTreeNodeList,
                                bagList : ObjectList,
                                parentIsPreset : Boolean):
        """Appends chunk tree nodes to <nodeList> for bags in
           <bagList>; <parentIsPreset> tells whether those
           are preset or instrument generators"""

        Logging.trace(">>: %d", len(bagList))

        # append the formal root node for bags
        nodeKind = iif(parentIsPreset, "pbag", "ibag")
        nodeList = self._makeFormalRootNode(nodeKind, nodeList)
        nodeKind = _childNodeKindPrefix + nodeKind

        for bag in bagList:
            node = ChunkTreeNode(nodeKind)
            node.fillBagNode(bag[0], bag[1])
            nodeList.append(node)

        Logging.trace("<<")
        
    #--------------------

    def _appendNodeListForGenerators (self : Object,
                                      nodeList : ChunkTreeNodeList,
                                      generatorList : ObjectList,
                                      identificationToIndexMap : StringMap,
                                      parentIsPreset : Boolean):
        """Appends chunk tree nodes to <nodeList> for generators in
           <generatorList>; <parentIsPreset> tells whether those
           are preset or instrument generators;
           <identificationToIndexMap> maps object identifications to
           natural numbers"""

        Logging.trace(">>: %d", len(generatorList))

        # append the formal root node for generators
        nodeKind = iif(parentIsPreset, "pgen", "igen")
        nodeList = self._makeFormalRootNode(nodeKind, nodeList)
        nodeKind = _childNodeKindPrefix + nodeKind

        for generator in generatorList:
            node = ChunkTreeNode(nodeKind)
            generatorKind, generatorAmount = generator

            if generatorKind in _partnerGeneratorKindList:
                partnerIdentification = generatorAmount.identification
                Logging.trace("--: kind = %s, partner = %s",
                              generatorKind.toShortString(),
                              partnerIdentification)
                naturalValue = \
                    identificationToIndexMap[partnerIdentification]
            else:
                Logging.trace("--: kind = %s, amount = %s",
                              generatorKind.toShortString(), generatorAmount)
                naturalValue = _SFGA.toNatural(generatorAmount,
                                               generatorKind,
                                               not parentIsPreset)

            node.fillGeneratorNode(int(generatorKind), naturalValue)
            nodeList.append(node)

        # append sentinel node
        node = ChunkTreeNode(nodeKind)
        node.fillGeneratorNode(0, 0)
        nodeList.append(node)

        Logging.trace("<<")
        
    #--------------------

    def _appendNodeListForHeader (self : Object,
                                  nodeList : ChunkTreeNodeList,
                                  soundFont : SoundFont):
        """Appends all chunk tree nodes for a header in <soundFont> to
           <nodeList>"""

        Logging.trace(">>")

        listNode = ChunkTreeNode("LIST-INFO")
        nodeList.append(listNode)
        nodeList = listNode.childrenList
        header = soundFont.header
        appndHVN  = self._appendHeaderVersionNode
        appndHSN  = self._appendHeaderStringNode
        appndHSNC = self._appendHeaderStringNodeConditionally

        # mandatory chunks
        appndHVN(nodeList, "ifil", header, "specVersion")
        appndHSN(nodeList, "isng", header, "soundEngine")
        appndHSN(nodeList, "INAM", header, "bankName")

        # optional chunks
        if header.romName > "":
            appndHSN(nodeList, "irom", header, "romName")
            appndHVN(nodeList, "iver", header, "romVersion")

        appndHSNC(nodeList, "ICRD", header, "creationDate")
        appndHSNC(nodeList, "IENG", header, "engineerNames")
        appndHSNC(nodeList, "IPRD", header, "productName")
        appndHSNC(nodeList, "ICOP", header, "copyright")
        appndHSNC(nodeList, "ICMT", header, "comment")
        appndHSNC(nodeList, "ISFT", header, "toolNames")
        
        Logging.trace("<<")
    
    #--------------------

    def _appendNodeListForModulators (self : Object,
                                      nodeList : ChunkTreeNodeList,
                                      modulatorList : ObjectList,
                                      parentIsPreset : Boolean):
        """Appends chunk tree nodes to <nodeList> for generators in
           <generatorList>; <parentIsPreset> tells whether those are
           preset or instrument modulators"""

        Logging.trace(">>: %d", len(modulatorList))

        # append the formal root node for modulators
        nodeKind = iif(parentIsPreset, "pmod", "imod")
        nodeList = self._makeFormalRootNode(nodeKind, nodeList)
        nodeKind = _childNodeKindPrefix + nodeKind

        for modulator in modulatorList:
            Logging.trace("--: modulator = %s", modulator)
            node = ChunkTreeNode(nodeKind)
            modulationTransform = iif(modulator.transformationIsLinear, 0, 2)
            node.fillModulatorNode(modulator.sourceModulatorA.toNatural(),
                                   int(modulator.destinationGeneratorKind),
                                   modulator.modulationAmount,
                                   modulator.sourceModulatorB.toNatural(),
                                   modulationTransform)
            nodeList.append(node)

        # append sentinel node
        node = ChunkTreeNode(nodeKind)
        node.fillModulatorNode(0, 0, 0, 0, 0)
        nodeList.append(node)
        
        Logging.trace("<<")

    #--------------------

    def _appendNodeListForObjects (self : Object,
                                   nodeList : ChunkTreeNodeList,
                                   soundFont : SoundFont):
        """Appends all chunk tree nodes for the sample, instrument and
           preset nodes in <soundFont> to <nodeList>"""

        Logging.trace(">>")

        listNode = ChunkTreeNode("LIST-pdta")
        nodeList.append(listNode)
        nodeList = listNode.childrenList

        # the canonical order by specification within the pdta chunk
        # is phdr, pbag, pmod, pgen, inst, ibag, imod, igen and shdr
        identificationToIndexMap = \
            self._collectIdentificationToIndexMap(soundFont)
        
        # presets
        self._appendNodeListForZonedElements(nodeList, soundFont,
                                             identificationToIndexMap,
                                             True)
        # instruments
        self._appendNodeListForZonedElements(nodeList, soundFont,
                                             identificationToIndexMap,
                                             False)
        # samples
        self._appendNodeListForSamples(nodeList, soundFont,
                                       identificationToIndexMap)

        Logging.trace("<<")

    #--------------------

    def _appendNodeListForSampleData (self : Object,
                                      nodeList : ChunkTreeNodeList,
                                      soundFont : SoundFont):
        """Appends all chunk tree nodes for the sample data points in
           <soundFont> to <nodeList>"""

        Logging.trace(">>")

        listNode = ChunkTreeNode("LIST-sdta")
        nodeList.append(listNode)
        nodeList = listNode.childrenList

        waveData = soundFont.waveData
        byteCount = waveData.byteCount()
        hasExtendedWaveData = waveData.bytesPerDataPoint() > 2
        nodeKindList = [ "smpl" ]
        nodeWaveDataList = waveData.toRawData()

        if hasExtendedWaveData:
            nodeKindList.append("sm24")

        for nodeKind, nodeWaveData in zip(nodeKindList, nodeWaveDataList):
            node = ChunkTreeNode(nodeKind)
            node.fillWaveDataNode(len(nodeWaveData), nodeWaveData)
            nodeList.append(node)
        
        Logging.trace("<<")

    #--------------------

    def _appendNodeListForSamples (self : Object,
                                   nodeList : ChunkTreeNodeList,
                                   soundFont : SoundFont,
                                   identificationToIndexMap : StringMap):
        """Appends all chunk tree nodes for the samples in <soundFont>
           to <nodeList>; <identificationToIndexMap> maps object
           identifications to natural numbers"""

        Logging.trace(">>")

        # append the formal root node for all samples
        nodeKind = "shdr"
        nodeList = self._makeFormalRootNode(nodeKind, nodeList)
        nodeKind = _childNodeKindPrefix + nodeKind

        for sample in soundFont.sampleList:
            node = ChunkTreeNode(nodeKind)
            partner = sample.partner
            partnerIndex = \
                (0 if partner is None
                 else identificationToIndexMap[partner.identification])
            node.fillSampleNode(str(sample.name),
                                sample.sampleStartPosition,
                                sample.sampleEndPosition,
                                sample.loopStartPosition,
                                sample.loopEndPosition,
                                sample.sampleRate,
                                sample.originalPitch,
                                sample.pitchCorrection,
                                partnerIndex,
                                sample.kind)
            nodeList.append(node)

        # append sentinel node
        node = ChunkTreeNode(nodeKind)
        node.fillSampleNode("EOS", 0, 0, 0, 0, 0, 0, 0, 0, 0)
        nodeList.append(node)
        
        Logging.trace("<<")

    #--------------------

    def _appendNodeListForZonedElementHeaders \
            (self : Object,
             nodeList : ChunkTreeNodeList,
             headerList : ObjectList,
             elementIDToBagMap : StringMap,
             elementsArePresets : Boolean):
        """Appends chunk tree nodes to <nodeList> for the
           zoned element headers in <headerList>; <elementsArePresets>
           tells whether those are presets or instruments;
           <elementIDToBagMap> maps object identifications to natural
           numbers as indices of the associated bag list"""

        Logging.trace(">>: %d", len(headerList))

        # append the formal root node for all zoned element headers
        nodeKind = iif(elementsArePresets, "phdr", "inst")
        nodeList = self._makeFormalRootNode(nodeKind, nodeList)
        nodeKind = _childNodeKindPrefix + nodeKind

        for header in headerList:
            node = ChunkTreeNode(nodeKind)
            bagIndex = elementIDToBagMap[header.identification]

            if not elementsArePresets:
                node.fillInstrumentNode(str(header.name), bagIndex)
            else:
                node.fillPresetNode(str(header.name),
                                    header.programNumber,
                                    header.bankNumber,
                                    bagIndex,
                                    header.libraryIndex,
                                    header.genreIndex,
                                    header.morphologyIndex)

            nodeList.append(node)

        # append sentinel node
        sentinelName = _sentinelName(elementsArePresets)
        node = ChunkTreeNode(nodeKind)
        nodeList.append(node)
        bagIndex = elementIDToBagMap[sentinelName]

        if not elementsArePresets:
            node.fillInstrumentNode(sentinelName, bagIndex)
        else:
            node.fillPresetNode(sentinelName, 0, 0, bagIndex, 0, 0, 0)
        
        Logging.trace("<<")

    #--------------------

    def _appendNodeListForZonedElements (self : Object,
                                         nodeList : ChunkTreeNodeList,
                                         soundFont : SoundFont,
                                         identificationToIndexMap : StringMap,
                                         isPresets : Boolean):
        """Appends all chunk tree nodes for zoned elements in
           <soundFont> to <nodeList>; <isPresets> tells whether the
           elements are presets or instruments;
           <identificationToIndexMap> maps object identifications to
           natural numbers"""

        Logging.trace(">>")

        elementList = (soundFont.presetList if isPresets
                       else soundFont.instrumentList)

        # order generator and modulator list by element and zones and
        # also set up mapping from element to bag list
        bagList = []
        generatorList = []
        modulatorList = []
        elementIDToBagMap = {}

        for element in elementList:
            bagIndex = len(bagList)
            elementIDToBagMap[element.identification] = bagIndex
            Logging.trace("--: bag index for '%s' = %d",
                          element.identification, bagIndex)
            elementZoneList = list(element.zoneList)

            if element.globalZone is None:
                # insert a dummy bag entry for an empty global zone
                bagList.append((len(generatorList), len(modulatorList)))
            else:
                elementZoneList.insert(0, element.globalZone)

            for i, zone in enumerate(elementZoneList):
                bagList.append((len(generatorList), len(modulatorList)))
                Logging.trace("--: new bag %r", bagList[-1])
                modulatorList.extend(zone.modulatorList)

                # reorder zone generator list by numerical order with
                # partner reference for non-global zones as last
                # generator
                keyProc = \
                    (lambda p:
                         -2 if p[0] == _SFGK.keyRange
                         else -1 if p[0] == _SFGK.velRange
                         else 999999 if p[0] in _partnerGeneratorKindList
                         else int(p[0]))
                zoneGeneratorList = list(zone.generatorMap.items())
                zoneGeneratorList.sort(key = keyProc)
                generatorList.extend(zoneGeneratorList)

        # append entry for sentinel record
        sentinelName = _sentinelName(isPresets)
        elementIDToBagMap[sentinelName] = len(bagList)
        bagList.append((len(generatorList), len(modulatorList)))

        # first append the zoned elements themselves
        self._appendNodeListForZonedElementHeaders(nodeList, elementList,
                                                   elementIDToBagMap,
                                                   isPresets)

        # construct nodes for the bags, modulators and generators
        self._appendNodeListForBags(nodeList, bagList, isPresets)
        self._appendNodeListForModulators(nodeList, modulatorList,
                                          isPresets)
        self._appendNodeListForGenerators(nodeList, generatorList,
                                          identificationToIndexMap,
                                          isPresets)

        Logging.trace("<<")

    #--------------------

    def _collectIdentificationToIndexMap (self : Object,
                                          soundFont : SoundFont) -> StringMap:
        """Traverses samples, instruments and presets for
           identifications, maps them to natural indices (in the
           order they are defined) and returns resulting map"""

        Logging.trace(">>")

        result = {}

        for elementList in (soundFont.sampleList, soundFont.instrumentList,
                            soundFont.presetList):
            for i, element in enumerate(elementList):
                result[element.identification] = i

        Logging.trace("<<: entryCount = %d", len(result.keys()))
        return result

    #--------------------

    def _makeChunkNodeTree (self : Object,
                            soundFont : SoundFont) -> ChunkTreeNode:
        """Constructs a tree of chunk tree nodes from <soundFont> and
           returns root tree node"""

        Logging.trace(">>")

        result = ChunkTreeNode("RIFF")
        nodeList = result.childrenList

        self._appendNodeListForHeader(nodeList, soundFont)
        self._appendNodeListForSampleData(nodeList, soundFont)
        self._appendNodeListForObjects(nodeList, soundFont)

        Logging.trace("<<: %s", result)
        return result
    
    #--------------------

    def _makeFormalRootNode (self : Object,
                             nodeKind : String,
                             nodeList : ChunkTreeNodeList) \
                -> ChunkTreeNodeList:
        """Appends new formal root node for <nodeKind> to
           <nodeList> and returns children list of that node"""

        Logging.trace(">>: '%s'", nodeKind)

        elementNode = ChunkTreeNode(nodeKind + _pdtaRootNodeKindSuffix)
        nodeList.append(elementNode)
        result = elementNode.childrenList

        Logging.trace("<<")
        return result

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object,
                  fileName : String):
        """Initializes a SoundFont file writer for accessing
           <fileName>"""

        Logging.trace(">>: fileName = '%s'", fileName)
        self.fileName = fileName
        Logging.trace("<<")
        
    #--------------------

    def writeSoundFont (self : Object,
                        soundFont : SoundFont):
        """Writes <soundFont> to file"""

        Logging.trace(">>")

        # make tree of nodes from soundFont
        ChunkTreeNode.resetIdentificationCounter()
        rootNode = self._makeChunkNodeTree(soundFont)

        # serialize tree of nodes to file
        byteList = rootNode.toByteList()

        # write file
        fileName = self.fileName
        directoryName = OperatingSystem.dirname(fileName)
        Assertion.check(OperatingSystem.hasDirectory(directoryName),
                        "cannot write to directory '%s'" % directoryName)

        with open(fileName, "wb") as destinationFile:
            destinationFile.write(byteList)
        
        Logging.trace("<<")
