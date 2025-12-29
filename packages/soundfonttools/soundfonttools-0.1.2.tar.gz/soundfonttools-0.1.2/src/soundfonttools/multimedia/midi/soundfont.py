# soundfont - the internal model for a SoundFont
#
# author: Dr. Thomas Tensi
# version: 2025-08

#====================
# IMPORTS
#====================

from enum import Enum, IntEnum, StrEnum
import math
import re

from basemodules.operatingsystem import OperatingSystem
from basemodules.simpleassertion import Assertion
from basemodules.simplelogging import Logging, Logging_Level
from basemodules.simpletypes import \
    Boolean, ByteList, Callable, Class, Integer, IntegerList, List, \
    Map, Natural, Object, ObjectList, Real, RealList, String, \
    StringList, StringMap, StringSet, Tuple
from basemodules.ttbase import iif, iif2, iif3

#====================

_ErrMsg_badValue = "bad value for %s: %s"
_ErrMsg_requiredAttrMissing = "required attribute '%s' not found"
_ErrMsg_unknownAttr = "unknown attribute '%s' found"

_ErrMsg_Generator_badAmount = "bad amount for %s - '%s'"
_ErrMsg_Generator_badKind = "unknown generator kind '%s'"

_ErrMsg_Header_badVersion = "bad %sVersion string: '%s'"

_ErrMsg_Sample_badPartner = "cannot find sample partner with id '%s'"
_ErrMsg_Sample_badPitch = "bad pitch value: %s"
_ErrMsg_Sample_badPitchCorrection = "bad pitch correction value: %s"
_ErrMsg_Sample_badPositions = ("implausible sample positions:"
                              + " start = %d, end = %d,"
                              + " loopStart = %d, loopEnd = %d")

_ErrMsg_Zone_badPartner = "cannot find zone partner with id '%s'"

#====================

_rCmp = re.compile

_expProc = lambda x: math.pow(2, x/1200.0)
_lnProc  = lambda x: round(1200 * math.log(x) / math.log(2))

_toPropertyMap = lambda x: None if x is None else x.toPropertyMap()
_zoneToPropertyMap = (lambda x, isInstrument:
                      None if x is None else x.toPropertyMap(isInstrument))

_undefinedPartnerIdentification = "---"
_partnerIdentification = (lambda x:
                          _undefinedPartnerIdentification if x is None
                          else x.identification)

#-------------------------
# type checking procedures
#-------------------------

_isBoolean = lambda x: isinstance(x, Boolean)
_isNatural = lambda x: isinstance(x, Natural)
_isInteger = lambda x: isinstance(x, Integer)
_isReal    = lambda x: isinstance(x, Real) or isinstance(x, Integer)
_isString  = lambda x: isinstance(x, String)
_isTuple   = lambda x: isinstance(x, Tuple)

#--------------------------
# range checking procedures
#--------------------------

_isNaturalInRange = lambda x, a, b: _isNatural(x) and a <= x <= b
_isIntegerInRange = lambda x, a, b: _isInteger(x) and a <= x <= b
_isRealInRange    = lambda x, a, b: _isReal(x)    and a <= x <= b

#====================

class ErrorHandler:
    """Represents error lists when transforming external
       representations to a soundfont"""

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object):
        """Sets up error handler"""

        Logging.trace(">>")

        self.context     = ""
        self.messageList = []

        Logging.trace("<<")

    #--------------------
    # change
    #--------------------

    def appendErrorMessage (self : Object,
                            errorMessage : String):
        """Appends <errorMessage> to error list"""

        Logging.trace(">>: '%s'", errorMessage)
        self.messageList.append("%s - %s" % (self.context, errorMessage))
        Logging.trace("<<")

    #--------------------

    def setErrorContext (self : Object,
                         context : String):
        """Sets current context to <context>"""

        Logging.trace(">>: '%s'", context)
        self.context = iif(context == "", "???", context)
        Logging.trace("<<")

    #--------------------
    # measurement
    #--------------------

    def hasErrors (self : Object) -> Boolean:
        """Tells whether some errors have occured"""

        Logging.trace(">>")
        result = len(self.messageList) > 0
        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # class methods
    #--------------------

    @classmethod
    def appendMessage (cls : Class,
                       errorHandler : Object,
                       errorMessage : String):
        """Appends <errorMessage> to <errorHandler> when the latter is
           not none"""

        if errorHandler is not None:
            errorHandler.appendErrorMessage(errorMessage)

    #--------------------

    @classmethod
    def setContext (cls : Class,
                    errorHandler : Object,
                    context : String):
        """Sets error message context <context> for <errorHandler>
           when the latter is not none"""

        if errorHandler is not None:
            errorHandler.setErrorContext(context)

#====================

def _checkForAttributes (propertyMap : StringMap,
                         mandatoryAttributeNameSet : StringSet,
                         attributeNameSet : StringSet,
                         errorHandler : ErrorHandler) -> Boolean:
    """Ensures that all attributes in <mandatoryAttributeNameSet> and
       only the attributes in <attributeNameSet> are keys of
       <propertyMap>; otherwise appends error messages to
       <errorHandler>"""

    # Logging.trace(">>: mandatory = %s, all = %s",
    #               mandatoryAttributeNameSet, attributeNameSet)

    isOkay = True
    
    for attributeName in propertyMap.keys():
        if attributeName not in attributeNameSet:
            isOkay = False
            ErrorHandler.appendMessage(errorHandler,
                                       (_ErrMsg_unknownAttr % attributeName))

    for attributeName in mandatoryAttributeNameSet:
        if attributeName not in propertyMap:
            isOkay = False
            ErrorHandler.appendMessage(errorHandler,
                                       (_ErrMsg_requiredAttrMissing
                                        % attributeName))

    # Logging.trace("<<: %s", isOkay)
    return isOkay

#--------------------

def _fromPropertyMapList (cls : Class,
                          identificationPrefix : String,
                          propertyMapList : ObjectList,
                          additionalPropertyMap : StringMap,
                          errorHandler : ErrorHandler = None) \
                          -> ObjectList:
    """Constructs list of objects of <cls> constructed from
       <propertyMapList> and returns it; if <additionalPropertyMap>
       is set, it contains settings for object attributes; error
       messages are appended to <errorHandler> (if set)"""

    clsName = cls.__name__
    Logging.trace(">>: class = '%s', identificationPrefix = '%s'",
                  clsName, identificationPrefix)

    result = []
    shortClassName = (clsName
                      .replace("_SoundFont", "")
                      .replace("SoundFont", "")
                      .lower())

    for i, propertyMap in enumerate(propertyMapList):
        if identificationPrefix is None:
            identification = None
            object = cls()
        else:
            defaultIdentification = "%s%05d" % (identificationPrefix, i)
            identification = propertyMap.get("identification",
                                             defaultIdentification)
            object = cls(identification)
            ErrorHandler.setContext(errorHandler,
                                    "%s '%s'" % (shortClassName,
                                                 identification))

        Logging.trace("--: %s object[%d], id = %s",
                      clsName, i, identification)

        object.fillFromPropertyMap(propertyMap, errorHandler)
        result.append(object)

        if additionalPropertyMap is not None:
            for attributeName, value in additionalPropertyMap.items():
                setattr(object, attributeName, value)
    
    Logging.trace("<<: objectCount = %d", len(result))
    return result
    
#--------------------

def _toPropertyMapList (objectList : ObjectList):
    """Returns a property record list for all elements in
       <objectList>"""

    Logging.trace(">>: objectCount = %s", len(objectList))
    result = [ element.toPropertyMap() for element in objectList ]
    Logging.trace("<<")
    return result

#====================
# ENUMERATION TYPES
#====================

class _SoundFontEnumeration (IntEnum):
    """the root class of all soundfont enumerations"""

    #--------------------
    # construction
    #--------------------

    @classmethod
    def fromNatural (cls : Class,
                     value : Natural) -> Object:
        """Constructs an enumeration value from <value>"""

        pass
    
    #--------------------
    # type conversion
    #--------------------

    __str__ = Enum.__str__

    #--------------------

    def toNatural (self : Object) -> Natural:
        """Returns the natural representation of <self>"""

        return self._value_

    #--------------------

    def toPropertyData (self : Object) -> Object:
        """Returns representation of <self> as data in a property map"""

        return "%02d - %s" % (self._value_, self.toShortString())

    #--------------------

    def toShortString (self : Object) -> String:
        """Returns string representation of <self> without number"""

        return str(self).split(".")[-1]
    
#====================

class SoundFontGeneratorAmountKind (_SoundFontEnumeration):
    """the kind of a generator amount in a SoundFont that can be a
       natural, an integer value or a pair of byte values"""

    signed   = 0
    unsigned = 1
    pair     = 2

    #--------------------

    def toPropertyData (self : Object) -> Object:
        """Returns representation of <self> as data in a property map"""

        return self.toShortString()

    #--------------------

    @classmethod
    def amountKindForGeneratorKind (cls : Class,
                                    generatorKind : Object) -> Object:
        """Returns the amount kind for <generatorKind>"""

        Logging.trace(">>: %s", generatorKind)

        if generatorKind in (SoundFontGeneratorKind.keyRange,
                             SoundFontGeneratorKind.velRange):
            # kind is a range generator => pair
            result = cls.pair
        elif generatorKind in (SoundFontGeneratorKind.instrument,
                               SoundFontGeneratorKind.keynum,
                               SoundFontGeneratorKind.velocity,
                               SoundFontGeneratorKind.sampleID):
            # kind is an index or substitution generator => positive
            # value
            result = cls.unsigned
        else:
            # signed value
            result = cls.signed

        Logging.trace("<<: %s", result)
        return result
    
#====================

class SoundFontGeneratorKind (_SoundFontEnumeration):
    """a generator kind in a SoundFont"""
    
    startAddrsOffset           =  0
    endAddrsOffset             =  1
    startLoopAddrsOffset       =  2
    endLoopAddrsOffset         =  3
    startAddrsCoarseOffset     =  4
    modLfoToPitch              =  5
    vibLfoToPitch              =  6
    modEnvToPitch              =  7
    initialFilterFc            =  8
    initialFilterQ             =  9
    modLfoToFilterFc           = 10
    modEnvToFilterFc           = 11
    endAddrsCoarseOffset       = 12
    modLfoToVolume             = 13
    unused1                    = 14
    chorusEffectsSend          = 15
    reverbEffectsSend          = 16
    pan                        = 17
    unused2                    = 18
    unused3                    = 19
    unused4                    = 20
    delayModLFO                = 21
    freqModLFO                 = 22
    delayVibLFO                = 23
    freqVibLFO                 = 24
    delayModEnv                = 25
    attackModEnv               = 26
    holdModEnv                 = 27
    decayModEnv                = 28
    sustainModEnv              = 29
    releaseModEnv              = 30
    keynumToModEnvHold         = 31
    keynumToModEnvDecay        = 32
    delayVolEnv                = 33
    attackVolEnv               = 34
    holdVolEnv                 = 35
    decayVolEnv                = 36
    sustainVolEnv              = 37
    releaseVolEnv              = 38
    keynumToVolEnvHold         = 39
    keynumToVolEnvDecay        = 40
    instrument                 = 41
    reserved1                  = 42
    keyRange                   = 43
    velRange                   = 44
    startLoopAddrsCoarseOffset = 45
    keynum                     = 46
    velocity                   = 47
    initialAttenuation         = 48
    reserved2                  = 49
    endLoopAddrsCoarseOffset   = 50
    coarseTune                 = 51
    fineTune                   = 52
    sampleID                   = 53
    sampleModes                = 54
    reserved3                  = 55
    scaleTuning                = 56
    exclusiveClass             = 57
    overridingRootKey          = 58
    unused5                    = 59
    endOper                    = 60

    #--------------------

    @classmethod
    def adaptToPolyphoneOrder (cls : Class,
                               generatorKindList : ObjectList):
        """Brings <generatorKindList> to order as in the Polyphone
           SoundFont editor"""

        Logging.trace(">>")

        tempList = []
        listInPolyphoneOrder = cls.listInPolyphoneOrder()

        for kind in listInPolyphoneOrder:
            if kind in generatorKindList:
                tempList.append(kind)

        generatorKindList.clear()
        generatorKindList.extend(tempList)
        
        Logging.trace("<<")
    
    #--------------------

    def defaultValue (self : Object) -> Object:
        """Returns default value for given generator kind"""

        return SoundFontGeneratorAmount.defaultAmount(self)

    #--------------------

    @classmethod
    def fromNatural (cls : Class,
                     n : Natural) -> Object:
        """Converts natural <n> to generator kind"""

        result = None
        
        for generatorKind in cls:
            if generatorKind == n:
                result = generatorKind
                break

        return result

    #--------------------

    @classmethod
    def fromString (cls : Class,
                    st : String) -> Object:
        """Converts string <st> to generator kind"""

        result = None
        
        for generatorKind in cls:
            if generatorKind.toShortString() == st:
                result = generatorKind
                break

        return result

    #--------------------

    @classmethod
    def nameSet (cls : Class) -> StringSet:
        """Returns set of name strings for this enumeration"""

        return set([ value.toShortString() for value in cls ])
    
    #--------------------

    @classmethod
    def listInPolyphoneOrder (cls : Class) -> ObjectList:
        """Returns the generator kind list in the order of the
           polyphone tables"""
        
        result = [
            cls.instrument, cls.sampleID, cls.keyRange, cls.velRange,
            cls.initialAttenuation, cls.pan, cls.sampleModes,
            cls.overridingRootKey,
            cls.coarseTune, cls.fineTune, cls.scaleTuning,
            cls.initialFilterFc, cls.initialFilterQ,
            cls.delayVolEnv, cls.attackVolEnv, cls.holdVolEnv,
            cls.decayVolEnv, cls.sustainVolEnv, cls.releaseVolEnv,
            cls.keynumToVolEnvHold, cls.keynumToVolEnvDecay,
            cls.delayModEnv, cls.attackModEnv, cls.holdModEnv,
            cls.decayModEnv, cls.sustainModEnv, cls.releaseModEnv,
            cls.modEnvToPitch, cls.modEnvToFilterFc,
            cls.keynumToModEnvHold, cls.keynumToModEnvDecay,
            cls.delayModLFO, cls.freqModLFO, cls.modLfoToPitch,
            cls.modLfoToFilterFc, cls.modLfoToVolume,
            cls.delayVibLFO, cls.freqVibLFO, cls.vibLfoToPitch,
            cls.exclusiveClass,
            cls.chorusEffectsSend, cls.reverbEffectsSend,
            cls.keynum, cls.velocity,
            cls.startAddrsOffset, cls.startAddrsCoarseOffset,
            cls.endAddrsOffset, cls.endAddrsCoarseOffset,
            cls.startLoopAddrsOffset, cls.startLoopAddrsCoarseOffset,
            cls.endLoopAddrsOffset, cls.endLoopAddrsCoarseOffset,
            cls.endOper,
            cls.reserved1, cls.reserved2, cls.reserved3,
            cls.unused1, cls.unused2, cls.unused3, cls.unused4,
            cls.unused5
        ]
        
        return result

#====================

_SFGK = SoundFontGeneratorKind
    
#====================

class SoundFontObjectKind (StrEnum):

    sample     = "sample"
    instrument = "instrument"
    preset     = "preset"
    header     = "header"

#====================

class SoundFontSampleKind (_SoundFontEnumeration):
    """The kind of sample: mono, left, right or linked and provided or
       taken from ROM"""

    monoSample      = 0x0001
    rightSample     = 0x0002
    leftSample      = 0x0004
    linkedSample    = 0x0008
    romMonoSample   = 0x8001
    romRightSample  = 0x8002
    romLeftSample   = 0x8004
    romLinkedSample = 0x8008

    #--------------------
    # construction
    #--------------------

    @classmethod
    def fromNatural (cls : Class,
                     value : Natural) -> Object:
        """Constructs an enumeration value from <value>"""

        if value == 0x0001:
            result = cls.monoSample
        elif value == 0x0002:
            result = cls.rightSample
        elif value == 0x0004:
            result = cls.leftSample
        elif value == 0x0008:
            result = cls.linkedSample
        elif value == 0x8001:
            result = cls.romMonoSample
        elif value == 0x8002:
            result = cls.romRightSample
        elif value == 0x8004:
            result = cls.romLeftSample
        elif value == 0x8008:
            result = cls.romLinkedSample
        else:
            result = None

        return result
    
    #--------------------
    # type conversion
    #--------------------

    def toPropertyData (self : Object) -> Object:
        """Returns representation of <self> as data in a property map"""

        return "0x%04x - %s" % (self._value_, self.toShortString())

#====================

class SoundFontSampleLoopModeKind (_SoundFontEnumeration):
    """the kind of looping for a sample in a SoundFont instrument"""

    noLoop            = 0
    continousLoop     = 1
    unused            = 2
    loopWithRemainder = 3

    #--------------------

    @classmethod
    def fromExternalRepresentation (cls : Class,
                                    r : Object) -> Object:
        """Converts external representation to object"""

        Logging.trace(">>: %s", r)

        if _isNaturalInRange(r, 0, 3):
            pass
        elif not _isString(r):
            r = None
        else:
            match = re.match(r"(0*[0-3])", r)

            if match:
                r = int(match.group(1))
            else:
                r = None

        if r is None:
            result = None
        else:
            result = iif3(r == 0, cls.noLoop,
                          r == 1, cls.continousLoop,
                          r == 2, cls.unused,
                          cls.loopWithRemainder)

        Logging.trace("<<: %s", result)
        return result
    
#====================
# STRUCTURE TYPES
#====================

class _SoundFontElement:
    """ancestor of all SoundFont elements with an external
       representation"""

    # set of all attribute names for this class
    _attributeNameSet = frozenset()

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        return ""

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object):
        """Initializes <self> to default values"""

        Logging.trace(">>")
        pass
        Logging.trace("<<")

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; if <errorHandler> is
           not none, any error messages are appended to that list"""

        Logging.trace(">>: %s", propertyMap)
        pass
        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns string representation of <self>"""

        clsName = self.__class__.__name__
        template = "%s(%s)"
        st = template % (clsName, self._asRawString())
        return st

    #--------------------

    def toExternalString (self : Object) -> String:
        """Returns the external string representation of <self>
           without type indication"""

        return self._asRawString()

    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        """Returns a mapping from the attributes of <self> to their
           associated values (which may be numbers, strings, maps or
           lists)"""

        return {}

#====================

class _SoundFontIdentifiedElement (_SoundFontElement):
    """ancestor of all SoundFont elements with an identification"""

    # set of all attribute names for this class
    _attributeNameSet = \
        _SoundFontElement._attributeNameSet.union(set(["identification"]))

    # mapping from element identification to element
    _identificationToElementMap = {}

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        template = "identification = '%s'"
        result   = template % self.identification
        return result

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object,
                  identification : String):
        """Initializes <self> to default values"""

        Logging.trace(">>: '%s'", identification)

        super().__init__()
        self.identification = identification
        cls = self.__class__
        cls._identificationToElementMap[identification] = self

        Logging.trace("<<")

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; if <errorHandler> is
           not none, any error messages are appended to that list"""

        Logging.trace(">>: %s", propertyMap)

        super().fillFromPropertyMap(propertyMap, errorHandler)

        if "identification" in propertyMap:
            self.identification = propertyMap["identification"]

        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        return { "identification" : self.identification }

    #--------------------
    # lookup
    #--------------------

    @classmethod
    def getByIdentification (cls : Class,
                             identification : String) -> Object:
        """Returns element by identification (if found)"""

        return cls._identificationToElementMap.get(identification)

#====================

class _SoundFontNamedElement (_SoundFontIdentifiedElement):
    """ancestor of sample and zonedElement encapsulating the
       identification and a length-bounded name"""

    # set of all attribute names for this class
    _attributeNameSet = \
        (_SoundFontIdentifiedElement._attributeNameSet
         .union(set(["name"])))

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        template = "%s, name = '%s', elementKind = %s"
        result   = (template
                    % (super()._asRawString(), self.name, self.elementKind))
        return result

    #--------------------

    def _setNameNOLOG (self : Object,
                       name : String):
        """Sets name of <self> to <name>"""

        self.name.set(name)

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object,
                  identification : String,
                  elementKind : SoundFontObjectKind):
        """Initializes <self> to default values"""

        Logging.trace(">>: identification = '%s', elementKind = %s",
                      identification, elementKind)

        super().__init__(identification)
        self.name        = SoundFontName()
        self.elementKind = elementKind

        Logging.trace("<<")

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; if <errorHandler> is
           not none, any error messages are appended to that list"""

        Logging.trace(">>: %s", propertyMap)

        super().fillFromPropertyMap(propertyMap, errorHandler)

        if "name" in propertyMap:
            self._setNameNOLOG(propertyMap["name"])

        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        result = (super().toPropertyMap()
                  | { "name" : self.name._value })
        return result

    #--------------------
    # change
    #--------------------

    def setName (self : Object,
                 name : String):
        """Sets name of <self> to <name>"""

        Logging.trace(">>: '%s'", name)
        self._setNameNOLOG(name)
        Logging.trace("<<")

#====================

#--------------------------
# range checking procedures
#--------------------------

# _CheckProc_isAttenuation  = lambda x: _isRealInRange(x, 0.0, 144.0)
# _CheckProc_isFreqCent     = lambda x: _isRealInRange(x, -12000.0, 12000.0)
# _CheckProc_isModFreq      = lambda x: _isRealInRange(x, 0.0, 100.5)
# _CheckProc_isTimeCent_20  = lambda x: _isRealInRange(x, 0.0009, 20.5)
# _CheckProc_isTimeCent_100 = lambda x: _isRealInRange(x, 0.0009, 100.5)

# those ranges are typically based on the limits of the underlying
# WORD or CHAR format, not on musical considerations
_CheckProc_isAttenuation  = lambda x: _isRealInRange(x, 0.0, 144.0)
_CheckProc_isFreqCent     = _isReal
_CheckProc_isKeyNum       = lambda x: _isNaturalInRange(x, 0, 127)
_CheckProc_isKeyNumCent   = lambda x: _isRealInRange(x, -1200.0, 1200.0)
_CheckProc_isModFreq      = _isReal
_CheckProc_isNonNegative  = lambda x: _isNaturalInRange(x, 0, 9999999)
_CheckProc_isPair         = (lambda x:
                             _isTuple(x) and len(x) == 2
                             and all([ _isNatural(v) for v in x ])
                             and 0 <= x[0] <= x[1] <= 127)
_CheckProc_isPercentage   = lambda x: _isRealInRange(x, 0.0, 100.0)
_CheckProc_isTimeCent_20  = _isReal
_CheckProc_isVelocity     = lambda x: _isNaturalInRange(x, 1, 127)
_CheckProc_isTimeCent_100 = _isReal

#====================

class SoundFontGeneratorAmount:
    """a generator amount in a SoundFont that can be a natural or
       integer value or a pair of byte values"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    _Unit_cent               =  1
    _Unit_constant           =  2
    _Unit_constantForInst    =  3
    _Unit_constantForPrst    =  4
    _Unit_decibel            =  5
    _Unit_decibelAttenuation =  6
    _Unit_hertz              =  7
    _Unit_pair               =  8
    _Unit_percent            =  9
    _Unit_sampleMode         = 10
    _Unit_second             = 11
    _Unit_semitone           = 12

    #--------------------

    _Unit_realUnitList    = (_Unit_decibel, _Unit_decibelAttenuation,
                             _Unit_hertz, _Unit_percent,
                             _Unit_second, _Unit_semitone)
    _Unit_integerUnitList = (_Unit_cent,)
    
    #--------------------

    # mapping from generator kind to amount unit
    _generatorKindToUnitMap = {
        _SFGK.startAddrsOffset           : _Unit_constantForInst,
        _SFGK.endAddrsOffset             : _Unit_constantForInst,
        _SFGK.startLoopAddrsOffset       : _Unit_constantForInst,
        _SFGK.endLoopAddrsOffset         : _Unit_constantForInst,
        _SFGK.startAddrsCoarseOffset     : _Unit_constantForInst,
        _SFGK.modLfoToPitch              : _Unit_cent,
        _SFGK.vibLfoToPitch              : _Unit_cent,
        _SFGK.modEnvToPitch              : _Unit_cent,
        _SFGK.initialFilterFc            : _Unit_hertz,
        _SFGK.initialFilterQ             : _Unit_decibel,
        _SFGK.modLfoToFilterFc           : _Unit_cent,
        _SFGK.modEnvToFilterFc           : _Unit_cent,
        _SFGK.endAddrsCoarseOffset       : _Unit_constantForInst,
        _SFGK.modLfoToVolume             : _Unit_decibel,
        _SFGK.chorusEffectsSend          : _Unit_percent,
        _SFGK.reverbEffectsSend          : _Unit_percent,
        _SFGK.pan                        : _Unit_percent,
        _SFGK.delayModLFO                : _Unit_second,
        _SFGK.freqModLFO                 : _Unit_hertz,
        _SFGK.delayVibLFO                : _Unit_second,
        _SFGK.freqVibLFO                 : _Unit_hertz,
        _SFGK.delayModEnv                : _Unit_second,
        _SFGK.attackModEnv               : _Unit_second,
        _SFGK.holdModEnv                 : _Unit_second,
        _SFGK.decayModEnv                : _Unit_second,
        _SFGK.sustainModEnv              : _Unit_percent,
        _SFGK.releaseModEnv              : _Unit_second,
        _SFGK.keynumToModEnvHold         : _Unit_cent,
        _SFGK.keynumToModEnvDecay        : _Unit_cent,
        _SFGK.instrument                 : _Unit_constantForPrst,
        _SFGK.delayVolEnv                : _Unit_second,
        _SFGK.attackVolEnv               : _Unit_second,
        _SFGK.holdVolEnv                 : _Unit_second,
        _SFGK.decayVolEnv                : _Unit_second,
        _SFGK.sustainVolEnv              : _Unit_decibel,
        _SFGK.releaseVolEnv              : _Unit_second,
        _SFGK.keynumToVolEnvHold         : _Unit_cent,
        _SFGK.keynumToVolEnvDecay        : _Unit_cent,
        _SFGK.keyRange                   : _Unit_pair,
        _SFGK.velRange                   : _Unit_pair,
        _SFGK.startLoopAddrsCoarseOffset : _Unit_constantForInst,
        _SFGK.keynum                     : _Unit_constantForInst,
        _SFGK.velocity                   : _Unit_constantForInst,
        _SFGK.initialAttenuation         : _Unit_decibelAttenuation,
        _SFGK.endLoopAddrsCoarseOffset   : _Unit_constantForInst,
        _SFGK.coarseTune                 : _Unit_semitone,
        _SFGK.fineTune                   : _Unit_cent,
        _SFGK.sampleID                   : _Unit_constantForInst,
        _SFGK.sampleModes                : _Unit_sampleMode,
        _SFGK.scaleTuning                : _Unit_constant,
        _SFGK.exclusiveClass             : _Unit_constantForInst,
        _SFGK.overridingRootKey          : _Unit_constantForInst
    }

    #--------------------

    # mapping from unit to format string to be applied to amount value
    # for external representation; %F stands for a float format with
    # either scientific notation for a small value or normal format
    # for values above that threshold
    _unitToFormatStringPairMap = {
        _Unit_cent               : ("%dct",)   * 2,
        _Unit_constant           : (None,)     * 2,
        _Unit_constantForInst    : (None,)     * 2,
        _Unit_constantForPrst    : (None,)     * 2,
        _Unit_decibel            : ("%FdB",)   * 2,
        _Unit_decibelAttenuation : ("%FdB",)   * 2,
        _Unit_hertz              : ("%FHz",    "%Fx"),
        _Unit_pair               : ("%d-%d",)  * 2,
        _Unit_percent            : ("%.1f%%",) * 2,
        _Unit_sampleMode         : ("%s",)     * 2,
        _Unit_second             : ("%Fs",     "%Fx"),
        _Unit_semitone           : ("%.2fst",) * 2
    }

    #--------------------

    _intNumberPattern  = r"([+-]?\d+)"
    _realNumberPattern = r"([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"

    _centRegExp     = re.compile(_intNumberPattern  + r"(?:ct)?$")
    _decibelRegExp  = re.compile(_realNumberPattern + r"(?:dB)?$")
    _hertzRegExp    = re.compile(_realNumberPattern + r"(?:Hz)?$")
    _pairRegExp     = re.compile(r"(\d+).(\d+)$")
    _percentRegExp  = re.compile(_realNumberPattern + r"%?$")
    _secondRegExp   = re.compile(_realNumberPattern + r"s?$")
    _semitoneRegExp = re.compile(_realNumberPattern + r"(?:st)?$")
    _timesRegExp    = re.compile(_realNumberPattern + r"x?$")

    # mapping from unit to regular expression to be applied to
    # external amount value
    _unitToRegExpPairMap = {
        _Unit_cent               : (_centRegExp,)     * 2,
        _Unit_constant           : (None,)            * 2,
        _Unit_constantForInst    : (None,)            * 2,
        _Unit_constantForPrst    : (None,)            * 2,
        _Unit_decibel            : (_decibelRegExp,)  * 2,
        _Unit_decibelAttenuation : (_decibelRegExp,)  * 2,
        _Unit_hertz              : (_hertzRegExp,     _timesRegExp),
        _Unit_pair               : (_pairRegExp,)     * 2,
        _Unit_percent            : (_percentRegExp,)  * 2,
        _Unit_sampleMode         : (None,)            * 2,
        _Unit_second             : (_secondRegExp,    _timesRegExp),
        _Unit_semitone           : (_semitoneRegExp,) * 2
    }

    #--------------------------
    # transformation procedures
    #--------------------------

    _divideBy10Proc           = lambda x: x / 10.0
    _divideBy25Proc           = lambda x: x / 25.0
    _divideBy100Proc          = lambda x: x / 100.0
    _expFrequencyProc         = lambda x: _expProc(x) * 8.176
    _identityProc             = lambda x: x
    _lnFrequencyProc          = lambda x: _lnProc(x / 8.176)
    _roundingProc             = lambda x: round(x)
    _toSampleModeLoopKindProc = lambda x: SoundFontSampleLoopModeKind(x)
    _times10Proc              = lambda x: round(x * 10.0)
    _times25Proc              = lambda x: round(x * 25.0)
    _times100Proc             = lambda x: round(x * 100.0)

    #--------------------

    # mapping from unit to transformation proc from word to real value
    _unitToRealConstructorPairMap = {
        _Unit_cent               : (None,)                     * 2,
        _Unit_constant           : (None,)                     * 2,
        _Unit_constantForInst    : (None,)                     * 2,
        _Unit_constantForPrst    : (None,)                     * 2,
        _Unit_decibel            : (_divideBy10Proc,)          * 2,
        _Unit_decibelAttenuation : (_divideBy25Proc,)          * 2,
        _Unit_hertz              : (_expFrequencyProc,         _expProc),
        _Unit_pair               : (None,)                     * 2,
        _Unit_percent            : (_divideBy10Proc,)          * 2,
        _Unit_sampleMode         : (_toSampleModeLoopKindProc, None),
        _Unit_second             : (_expProc,)                 * 2,
        _Unit_semitone           : (None,)                     * 2
    }

    # mapping from unit to transformation proc from real
    # value to word (reversing the above functions)
    _unitToRealConverterPairMap = {
        _Unit_cent               : (_roundingProc,)   * 2,
        _Unit_constant           : (_roundingProc,)   * 2,
        _Unit_constantForInst    : (_roundingProc,)   * 2,
        _Unit_constantForPrst    : (_roundingProc,)   * 2,
        _Unit_decibel            : (_times10Proc,)    * 2,
        _Unit_decibelAttenuation : (_times25Proc,)    * 2,
        _Unit_hertz              : (_lnFrequencyProc, _lnProc),
        _Unit_pair               : (_identityProc,)   * 2,
        _Unit_percent            : (_times10Proc,)    * 2,
        _Unit_sampleMode         : (_roundingProc,)   * 2,
        _Unit_second             : (_lnProc,)         * 2,
        _Unit_semitone           : (_roundingProc,)   * 2
    }

    #--------------------
    # check procedures
    #--------------------

    # mapping from unit and object kind (instrument/preset) to check
    # proc
    _unitToCheckProcPairMap = {
        _Unit_cent               : (_isReal,)           * 2,
        _Unit_constant           : (_isNatural,)        * 2,
        _Unit_constantForInst    : (None,)              * 2,
        _Unit_constantForPrst    : (None,)              * 2,
        _Unit_decibel            : (_isReal,)           * 2,
        _Unit_decibelAttenuation : (_isReal,)           * 2,
        _Unit_hertz              : (_isReal,)           * 2,
        _Unit_pair               : (_CheckProc_isPair,) * 2,
        _Unit_percent            : (_isReal,)        * 2,
        _Unit_second             : (_isReal,)           * 2,
        _Unit_semitone           : (_isReal,)           * 2,
    }    
    
    #--------------------
    # default values
    #--------------------

    # mapping from generator kind to default amount
    _generatorKindToDefaultAmountMap = {
        _SFGK.startAddrsOffset           : 0.0,
        _SFGK.endAddrsOffset             : 0.0,
        _SFGK.startLoopAddrsOffset       : 0.0,
        _SFGK.endLoopAddrsOffset         : 0.0,
        _SFGK.startAddrsCoarseOffset     : 0.0,
        _SFGK.modLfoToPitch              : 0.0,
        _SFGK.vibLfoToPitch              : 0.0,
        _SFGK.modEnvToPitch              : 0.0,
        _SFGK.initialFilterFc            : 13500.0,
        _SFGK.initialFilterQ             : 0.0,
        _SFGK.modLfoToFilterFc           : 0.0,
        _SFGK.modEnvToFilterFc           : 0.0,
        _SFGK.endAddrsCoarseOffset       : 0.0,
        _SFGK.modLfoToVolume             : 0.0,
        _SFGK.chorusEffectsSend          : 0.0,
        _SFGK.reverbEffectsSend          : 0.0,
        _SFGK.pan                        : 0.0,
        _SFGK.delayModLFO                : -120.0,
        _SFGK.freqModLFO                 : 0.0,
        _SFGK.delayVibLFO                : -120.0,
        _SFGK.freqVibLFO                 : 0.0,
        _SFGK.delayModEnv                : -120.0,
        _SFGK.attackModEnv               : -120.0,
        _SFGK.holdModEnv                 : -120.0,
        _SFGK.decayModEnv                : -120.0,
        _SFGK.sustainModEnv              : 0.0,
        _SFGK.releaseModEnv              : -120.0,
        _SFGK.keynumToModEnvHold         : 0.0,
        _SFGK.keynumToModEnvDecay        : 0.0,
        _SFGK.delayVolEnv                : -120.0,
        _SFGK.attackVolEnv               : -120.0,
        _SFGK.holdVolEnv                 : -120.0,
        _SFGK.decayVolEnv                : -120.0,
        _SFGK.sustainVolEnv              : 0.0,
        _SFGK.releaseVolEnv              : -120.0,
        _SFGK.keynumToVolEnvHold         : 0.0,
        _SFGK.keynumToVolEnvDecay        : 0.0,
        _SFGK.keyRange                   : (0, 127),
        _SFGK.velRange                   : (0, 127),
        _SFGK.startLoopAddrsCoarseOffset : 0.0,
        _SFGK.keynum                     : -1.0,
        _SFGK.velocity                   : -1.0,
        _SFGK.initialAttenuation         : 0.0,
        _SFGK.endLoopAddrsCoarseOffset   : 0.0,
        _SFGK.coarseTune                 : 0.0,
        _SFGK.fineTune                   : 0.0,
        _SFGK.sampleModes                : 0.0,
        _SFGK.scaleTuning                : 100.0,
        _SFGK.exclusiveClass             : 0.0,
        _SFGK.overridingRootKey          : -10.0
    }

    #--------------------
    #--------------------

    @classmethod
    def _formatStringForGeneratorKind (cls : Class,
                                       generatorKind : _SFGK,
                                       parentIsInstrument : Boolean) -> String:
        """Returns unit formatter string for <generatorKind> and
           <parentIsInstrument>"""

        Logging.trace(">>: generatorKind = '%s', parentIsInstrument = %s",
                      generatorKind.toShortString(), parentIsInstrument)

        result = cls._valueForUnitInMap(generatorKind, parentIsInstrument,
                                        cls._unitToFormatStringPairMap)

        Logging.trace("<<: %s", result)
        return result
    
    #--------------------

    @classmethod
    def _regExpForGeneratorKind (cls : Class,
                                 generatorKind : _SFGK,
                                 parentIsInstrument : Boolean) -> Object:
        """Returns regular expression for reading a value for
           <generatorKind> and <parentIsInstrument>"""

        Logging.trace(">>: generatorKind = '%s', parentIsInstrument = %s",
                      generatorKind.toShortString(), parentIsInstrument)

        result = cls._valueForUnitInMap(generatorKind, parentIsInstrument,
                                        cls._unitToRegExpPairMap)

        pattern = None if result is None else result.pattern
        Logging.trace("<<: %s", pattern)
        return result
    
    #--------------------

    @classmethod
    def _valueForUnitInMap (cls : Class,
                            generatorKind : _SFGK,
                            parentIsInstrument : Boolean,
                            unitToValuePairMap : Map) -> Object:
        """Returns check value for <generatorKind> and
           <parentIsInstrument> in <unitToValuePairMap>"""

        Logging.trace(">>: generatorKind = '%s', parentIsInstrument = %s",
                      generatorKind.toShortString(), parentIsInstrument)

        unit = cls._generatorKindToUnitMap.get(generatorKind)
        result = None

        if unit is not None:
            pair = unitToValuePairMap.get(unit)

            if pair is not None:
                index = iif(parentIsInstrument, 0, 1)
                result = pair[index]

        Logging.trace("<<: %s", result)
        return result
    
    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    @classmethod
    def fromNatural (cls : Class,
                     value : Natural,
                     generatorKind : SoundFontGeneratorKind,
                     parentIsInstrument : Boolean) -> Object:
        """Converts natural <value> to either pair or number depending
           on <generatorKind> and <parentIsInstrument>"""

        Logging.trace(">>: value = %d, kind = %s,"
                      + " parentIsInstrument = %s",
                      value, generatorKind, parentIsInstrument)

        amountKind = (SoundFontGeneratorAmountKind
                      .amountKindForGeneratorKind(generatorKind))
        
        if amountKind == SoundFontGeneratorAmountKind.pair:
            valueB, valueA = divmod(value, 256)
            result = (valueA, valueB)
        elif amountKind == SoundFontGeneratorAmountKind.unsigned:
            # kind is an index or substitution generator => positive
            # value
            result = value
        else:
            # signed value
            result = iif(value <= 32767, value, value - 65536)

        adaptationProc = \
            SoundFontGeneratorAmount.wordToRealProc(generatorKind,
                                                    parentIsInstrument)

        if adaptationProc is not None:
            originalValue = result
            newValue = adaptationProc(originalValue)
            Logging.trace("--: converted from %s to %s",
                          originalValue, newValue)
            result = newValue

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    @classmethod
    def fromPropertyData (cls : Class,
                          value : Object,
                          generatorKind : SoundFontGeneratorKind,
                          parentIsInstrument : Boolean) -> Object:
        """Converts <value> from property map to amount for
           <generatorKind> and <parentIsInstrument>"""

        Logging.trace(">>: value = %s, generatorKind = %s,"
                      + " parentIsInstrument = %s",
                      value, generatorKind.toShortString(),
                      parentIsInstrument)

        result = value

        if _isString(value):
            regExp = cls._regExpForGeneratorKind(generatorKind,
                                                 parentIsInstrument)

            if regExp is not None:
                match = regExp.match(value)

                if not match:
                    pass
                elif len(match.groups()) == 2:
                    # a pair
                    result = (int(match.group(1)), int(match.group(2)))
                else:
                    result = match.group(1)
                    unit = cls._generatorKindToUnitMap.get(generatorKind)

                    if unit is not None:
                        if unit in cls._Unit_integerUnitList:
                            result = int(result)
                        elif unit in cls._Unit_realUnitList:
                            result = float(result)

        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # type conversion
    #--------------------

    @classmethod
    def toNatural (cls : Class,
                   value : Object,
                   generatorKind : SoundFontGeneratorKind,
                   parentIsInstrument : Boolean) -> Natural:
        """Returns representation of <value> as natural value
           for <generatorKind> and <parentIsInstrument>"""

        Logging.trace(">>: value = %s, generatorKind = %s,"
                      + " parentIsInstrument = %s",
                      value, generatorKind.toShortString(),
                      parentIsInstrument)

        if isinstance(value, _SoundFontEnumeration):
            result = int(value)
        elif isinstance(value, Tuple):
            result = value[0] + value[1] * 256
        else:
            wordFromRealProc = cls.wordFromRealProc(generatorKind,
                                                    parentIsInstrument)
            result = wordFromRealProc(value)

            if result < 0:
                result += 65536

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    @classmethod
    def toPropertyData (cls : Class,
                        value : Object,
                        generatorKind : SoundFontGeneratorKind,
                        parentIsInstrument : Boolean) -> Object:
        """Returns representation of <value> as data in a property map
           for <generatorKind> and <parentIsInstrument>"""

        if isinstance(value, _SoundFontEnumeration):
            result = value.toPropertyData()
        else:
            template = cls._formatStringForGeneratorKind(generatorKind,
                                                         parentIsInstrument)

            if template is None:
                result = value
            else:
                # check for special float format
                specialFormat = "%F"

                if specialFormat in template and isinstance(value, Real):
                    realFormat = ("%.3f" if value == 0.0 or abs(value) >= 0.1
                                  else "%.3e")
                    template = template.replace(specialFormat, realFormat)
                    
                result = template % value

        return result

    #--------------------

    @classmethod
    def toShortRepresentation (cls : Class,
                               value : Object) -> String:
        """Returns the short string representation of <value>"""
        
        if value is None:
            result = None
        elif _isTuple(value):
            template = "%03d,%03d"
            result = template % value
        else:
            result = str(value)

        return result

    #--------------------

    @classmethod
    def fullPairRange (cls : Class) -> Object:
        """Returns a pair amount from 0 to 127"""

        return (0, 127)

    #--------------------
    # query
    #--------------------

    @classmethod
    def defaultAmount (cls : Class,
                       generatorKind : SoundFontGeneratorKind) -> Object:
        """Returns the default amount for <generatorKind>"""

        Logging.trace(">>: %s", generatorKind)
        result = cls._generatorKindToDefaultAmountMap.get(generatorKind)
        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # transformation
    #--------------------

    @classmethod
    def checkProcForGeneratorKind (cls : Class,
                                   generatorKind : SoundFontGeneratorKind,
                                   parentIsInstrument : Boolean) -> Callable:
        """Returns check routine for <generatorKind> and
           <parentIsInstrument>"""

        Logging.trace(">>: generatorKind = '%s', parentIsInstrument = %s",
                      generatorKind.toShortString(), parentIsInstrument)

        result = cls._valueForUnitInMap(generatorKind, parentIsInstrument,
                                        cls._unitToCheckProcPairMap)

        Logging.trace("<<")
        return result
    
    #--------------------

    @classmethod
    def wordFromRealProc (cls : Class,
                          generatorKind :  SoundFontGeneratorKind,
                          parentIsInstrument : Boolean) -> Callable:
        """Returns the mapping proc from real to word amount for
           <generatorKind> and <parentIsInstrument>"""

        Logging.trace(">>: generatorKind = '%s', parentIsInstrument = %s",
                      generatorKind.toShortString(), parentIsInstrument)

        result = cls._valueForUnitInMap(generatorKind, parentIsInstrument,
                                        cls._unitToRealConverterPairMap)

        Logging.trace("<<")
        return result

    #--------------------

    @classmethod
    def wordToRealProc (cls : Class,
                        generatorKind :  SoundFontGeneratorKind,
                        parentIsInstrument : Boolean) -> Callable:
        """Returns the mapping proc from amount real to word for
           <generatorKind> and <parentIsInstrument>"""

        Logging.trace(">>: generatorKind = '%s', parentIsInstrument = %s",
                      generatorKind.toShortString(), parentIsInstrument)

        result = cls._valueForUnitInMap(generatorKind, parentIsInstrument,
                                        cls._unitToRealConstructorPairMap)

        Logging.trace("<<")
        return result

#====================

class SoundFontGenerator (_SoundFontIdentifiedElement):
    """a generator in a SoundFont"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    # the maximum allowed amount value
    _maximumAmountValue = 65535

    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        template = "%s, kind = %s, amount = %s"
        st = (template
              % (super()._asRawString(), self.kind.toShortString(),
                 SoundFontGeneratorAmount.toShortRepresentation(self.amount)))
        return st

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object,
                  identification : String,
                  kind : Natural = 0,
                  amount : Natural = 0,
                  parentIsInstrument : Boolean = False):
        """Initializes a generator"""

        cls = self.__class__
        maxAmountValue = cls._maximumAmountValue
        Assertion.pre(amount in range(maxAmountValue + 1),
                      "amount %s must be in range [0..%d]"
                      % (amount, maxAmountValue))
        Logging.trace(">>: identification = '%s', kind = %2d,"
                      + " amount = %d, parentIsInstrument = %s",
                      identification, kind, amount, parentIsInstrument)

        super().__init__(identification)
        self.kind   = SoundFontGeneratorKind.fromNatural(kind)
        self.amount = \
            SoundFontGeneratorAmount.fromNatural(amount, self.kind,
                                                 parentIsInstrument)

        info = str(self)
        # Logging.trace("<<: %s", self)
        Logging.trace("<<: %s", info)

    #--------------------
    # type conversion
    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        result = (super().toPropertyMap()
                  | { "kind"   : self.kind.toPropertyData(),
                      "amount" : (SoundFontGeneratorAmount
                                  .toPropertyData(self.amount)) })
        return result

#====================

class SoundFontHeader (_SoundFontElement):
    """Represents the header data of a SoundFont"""

    # list of local string-valued attribute names
    _stringAttributeNameList = \
         ("soundEngine", "bankName", "romName", "creationDate",
          "engineerNames", "productName", "copyright", "comment",
          "toolNames")
    
    # list of all local attribute names
    _attributeNameList = \
        ("specVersion", "romVersion") + _stringAttributeNameList
    
    # set of all attribute names for this class
    _attributeNameSet = \
        _SoundFontElement._attributeNameSet.union(set(_attributeNameList))

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        cls = self.__class__
        template = ", ".join([ "%s = '%%s'" % attributeName
                               for attributeName in cls._attributeNameList ])
        attributeValueList = [ getattr(self, attributeName)
                               for attributeName in cls._attributeNameList ]
        st = template % tuple(attributeValueList)
        return st

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object):
        """Initializes header structure in <self>"""

        Logging.trace(">>")

        cls = self.__class__

        for attributeName in cls._stringAttributeNameList:
            setattr(self, attributeName, "")

        self.kind          = SoundFontObjectKind.header
        self.specVersion   = SoundFontVersion()
        self.romVersion    = SoundFontVersion()

        Logging.trace("<<")

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap> and appends any errors to
           <errorHandler> (if set)"""

        Logging.trace(">>: %s", propertyMap)

        cls = self.__class__
        isOkay = _checkForAttributes(propertyMap, cls._attributeNameSet,
                                     cls._attributeNameSet, errorHandler)

        if not isOkay:
            Logging.traceError("bad property map for header %s",
                               propertyMap)

        super().fillFromPropertyMap(propertyMap, errorHandler)

        for attributeName in cls._stringAttributeNameList:
            setattr(self, attributeName,
                    propertyMap.get(attributeName, ""))

        versionList = []

        for prefix in ("spec", "rom"):
            st = propertyMap.get("%sVersion" % prefix, "0.0")
            version = SoundFontVersion.fromString(st)
            versionList.append(version)

            if version is None:
                isOkay = False
                ErrorHandler.appendMessage(errorHandler,
                                           (_ErrMsg_Header_badVersion
                                            % (prefix, st)))

        if isOkay:
            self.specVersion = versionList[0]
            self.romVersion  = versionList[1]

        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        cls = self.__class__
        propertyMap = {}

        for attributeName in cls._stringAttributeNameList:
            propertyMap[attributeName] = getattr(self, attributeName)

        propertyMap["specVersion"] = self.specVersion.toPropertyData()
        propertyMap["romVersion"]  = self.romVersion.toPropertyData()

        result = super().toPropertyMap() | propertyMap
        return result

#====================

class SoundFontZonedElement (_SoundFontNamedElement):
    """Ancestor of instrument and preset encapsulating the
       identification, the length-bounded name and the zones and
       modulators"""

    # set of mandatory attribute names for this class
    _mandatoryAttributeNameSet = \
        (_SoundFontNamedElement._attributeNameSet
         .union(set(["zoneList"])))

    # set of all attribute names for this class
    _attributeNameSet = \
        (_mandatoryAttributeNameSet.union(set(["globalZone"])))

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object,
                      st : String = "",
                      listsAreShown : Boolean = True) -> String:
        """Returns attributes as formatted string possibly inserting
           <st> between the identification/name and the zone and
           modulator data; if <listsAreShown> is not set, the zone
           lists are left out"""

        prefix = super()._asRawString()
        suffix = ""

        if listsAreShown:
            globalZone = self.globalZone
            zoneList   = self.zoneList
            
            if globalZone is not None and not globalZone.isEmpty():
                suffix = ", globalZone = %s" % globalZone

            if len(zoneList) > 0:
                suffix = ", zoneList = %s" % zoneList

        result = prefix + iif(st > "", ", ", "") + st + suffix
        return result

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object,
                  identification : String,
                  elementKind : SoundFontObjectKind):
        """Initializes <self> to default values"""

        Logging.trace(">>: identification = '%s', elementKind = %s",
                      identification, elementKind)

        super().__init__(identification, elementKind)
        self.globalZone = None
        self.zoneList   = []

        Logging.trace("<<")

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; if <errorHandler> is
           not none, any error messages are appended to that list"""

        Logging.trace(">>")

        super().fillFromPropertyMap(propertyMap, errorHandler)
        isInstrument = (self.elementKind == SoundFontObjectKind.instrument)
        ErrorHandler.setContext(errorHandler,
                                "%s '%s'" % (self.elementKind,
                                             self.identification))

        if "globalZone" in propertyMap:
            globalZone = SoundFontZone(True)
            globalZone.fillFromPropertyMap(isInstrument,
                                           propertyMap["globalZone"],
                                           errorHandler)
            globalZone.setParent(self)
            self.globalZone = globalZone

        if "zoneList" in propertyMap:
            propertyMapList = propertyMap["zoneList"]
            self.zoneList.clear()

            for propertyMap in propertyMapList:
                zone = SoundFontZone(False)
                zone.fillFromPropertyMap(isInstrument, propertyMap,
                                         errorHandler)
                zone.setParent(self)
                self.zoneList.append(zone)
            
        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def toPropertyMap (self : Object,
                       isInstrument : Boolean,
                       propertyMap : StringMap,
                       listsAreShown : Boolean = True) -> StringMap:
        """Returns a mapping from the attributes of <self> to their
           associated value strings possibly inserting <propertyMap>
           between the identification/name and the zone and modulator
           mappings; <isInstrument> tells whether this is an
           instrument (or a preset); if <listsAreShown> is not set,
           the zone lists are left out"""

        result = super().toPropertyMap() | propertyMap

        if listsAreShown:
            globalZone = self.globalZone
            zoneList   = self.zoneList
            
            if globalZone is not None and not globalZone.isEmpty():
                result["globalZone"] = \
                    globalZone.toPropertyMap(isInstrument)

            if len(zoneList) > 0:
                result["zoneList"] = [ zone.toPropertyMap(isInstrument)
                                       for zone in zoneList ]

        return result

#====================

class SoundFontInstrument (SoundFontZonedElement):
    """a SoundFont instrument"""

    # set of mandatory attribute names for this class
    _mandatoryAttributeNameSet = \
        SoundFontZonedElement._mandatoryAttributeNameSet

    # set of all attribute names for this class
    _attributeNameSet = SoundFontZonedElement._attributeNameSet

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object,
                  identification : String):
        """Initializes <self> to default values"""

        Logging.trace(">>: '%s'", identification)
        super().__init__(identification, SoundFontObjectKind.instrument)
        Logging.trace("<<: %s", self)

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; if <errorHandler> is
           not none, any error messages are appended to that list"""

        Logging.trace(">>")

        cls = self.__class__
        isOkay = _checkForAttributes(propertyMap,
                                     cls._mandatoryAttributeNameSet,
                                     cls._attributeNameSet, errorHandler)
        if not isOkay:
            Logging.traceError("bad property map for instrument %s",
                               propertyMap)

        super().fillFromPropertyMap(propertyMap, errorHandler)

        Logging.trace("<<: %s", self)

    #--------------------
    # type conversion
    #--------------------

    def toExternalString (self : Object) -> String:
        """Returns the external string representation of <self>
           without type indication"""

        # leave out the zone lists
        return self._asRawString("", False)

    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        # leave out the zone lists
        Logging.trace(">>: name = '%s'", self.name)
        result = super().toPropertyMap(True, {}, True)
        Logging.trace("<<")
        return result

#====================

class SoundFontModulator (_SoundFontIdentifiedElement):
    """the modulator for a preset or instrument consisting of two
       sources, a destination generator kind, a modulation amount and
       a modulation transform"""

    _attributeNameList = ("sourceModulatorA", "destinationGeneratorKind",
                          "sourceModulatorB", "modulationAmount",
                          "transformationIsLinear")

    # set of mandatory attribute names for this class
    _mandatoryAttributeNameSet = frozenset(_attributeNameList)

    # set of attribute names for this class
    _attributeNameSet = (_SoundFontIdentifiedElement._attributeNameSet
                         .union(_mandatoryAttributeNameSet))

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        attributeNameList = self.__class__._attributeNameList
        template = ("%s,"
                    + ", ".join([ "%s = '%%s'" % attributeName
                               for attributeName in attributeNameList ]))
        attributeValueList = ([ super()._asRawString() ]
                              + [ getattr(self, attributeName)
                                  for attributeName in attributeNameList ])
        st = template % tuple(attributeValueList)
        return st

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object,
                  identification : String,
                  sourceModulatorValueA : Natural = 0,
                  sourceModulatorValueB : Natural = 0,
                  destinationGeneratorKind : SoundFontGeneratorKind =
                      SoundFontGeneratorKind.unused5,
                  modulationAmount : Natural = 0,
                  transformationIsLinear : Boolean = False):
        """Initializes a modulator from <sourceModulatorValueA>,
           <sourceModulatorValueB>, <destinationGeneratorKind>,
           <modulationAmount> and <transformationIsLinear>"""

        Logging.trace(">>:"
                      + " identification = '%s',"
                      + " sourceModulatorValueA = 0x%04x,"
                      + " sourceModulatorValueB = 0x%04x,"
                      + " destinationGeneratorKind = %s,"
                      + " modulationAmount = %d,"
                      + " transformationIsLinear = %s",
                      identification,
                      sourceModulatorValueA, sourceModulatorValueB,
                      destinationGeneratorKind, modulationAmount,
                      transformationIsLinear)

        super().__init__(identification)
        self.sourceModulatorA = \
            SoundFontModulatorSource(sourceModulatorValueA)
        self.sourceModulatorB = \
            SoundFontModulatorSource(sourceModulatorValueB)
        self.destinationGeneratorKind = \
            SoundFontGeneratorKind(destinationGeneratorKind)
        self.modulationAmount       = modulationAmount
        self.transformationIsLinear = transformationIsLinear

        Logging.trace("<<: %s", self)

    #--------------------

    def fillFromPropertyMap (self : Object,
                             parentIsInstrument : Boolean,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; if <errorHandler> is
           not none, any error messages are appended to that list"""

        Logging.trace(">>")

        super().fillFromPropertyMap(propertyMap, errorHandler)

        # check whether all attributes are set
        cls = self.__class__
        isOkay = _checkForAttributes(propertyMap,
                                     cls._mandatoryAttributeNameSet,
                                     cls._attributeNameSet, errorHandler)

        if not isOkay:
            Logging.traceError("bad property map for modulator %s",
                               propertyMap)

        for attributeName in ("sourceModulatorA", "sourceModulatorB"):
            modulatorSource = SoundFontModulatorSource()
            modulatorSource.fillFromPropertyMap(propertyMap[attributeName],
                                                errorHandler)
            setattr(self, attributeName, modulatorSource)

        transformerMap = {
            "destinationGeneratorKind" :
                lambda x: \
                    SoundFontGeneratorKind.fromString(x.split(" ")[-1]),
            "modulationAmount" :
                lambda x: (SoundFontGeneratorAmount
                           .fromPropertyData(x,
                                             self.destinationGeneratorKind,
                                             parentIsInstrument)),
            "transformationIsLinear" :
                lambda x: None if not _isBoolean(x) else x
        }

        for attributeName, transformationProc in transformerMap.items():
            value = propertyMap[attributeName]
            adaptedValue = transformationProc(value)

            if adaptedValue is not None:
                setattr(self, attributeName, adaptedValue)
            else:
                ErrorHandler.appendMessage(errorHandler,
                                           (_ErrMsg_badValue
                                            % (attributeName, value)))
 
        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        result = {
            "sourceModulatorA" : self.sourceModulatorA.toPropertyMap(),
            "destinationGeneratorKind" :
                self.destinationGeneratorKind.toPropertyData(),
            "sourceModulatorB" : self.sourceModulatorB.toPropertyMap(),
            "modulationAmount" : self.modulationAmount,
            "transformationIsLinear" : self.transformationIsLinear
        }

        return result

#====================

class SoundFontModulatorSource:
    """the modulator source"""

    # list of externally visible attribute names
    _attributeNameList = ("sourceController", "hasDescendingDirection",
                          "isUnipolar", "typeName")

    # set of mandatory attribute names
    _attributeNameSet = set(_attributeNameList)

    # mapping from source controller number to text
    _sourceControllerIndexToNameMap = {
          0 : "No Controller",
          2 : "Note-On Velocity",
          3 : "Note-On Key Number",
         10 : "Poly Pressure",
         13 : "Channel Pressure",
         14 : "Pitch Wheel",
         16 : "Pitch Wheel Sensitivity",
        127 : "Link"
    }

    # mapping from source controller name to number
    _sourceControllerNameToIndexMap = {
        value : key for key, value in _sourceControllerIndexToNameMap.items()
    }

    # mapping from type number to name
    _typeIndexToNameMap = {
        0 : "Linear", 1 : "Concave", 2 : "Convex", 3 : "Switch"
    }

    # mapping from type name to number
    _typeNameToIndexMap = {
        value : key for key, value in _typeIndexToNameMap.items()
    }

    #--------------------

    def _controllerAndTypeName (self : Object) -> Tuple:
        """Returns pair of controller name and type name"""

        cls = self.__class__
        return (cls._sourceControllerName(self.isMidiController,
                                          self.sourceIndex),
                cls._typeName(self.typeIndex))

    #--------------------

    @classmethod
    def _sourceControllerIndex (cls : Class,
                                name : String) -> Tuple:
        """Returns tuple of number and isMidiController for modulator
           source characterized by <name>"""

        match = re.match(r"MidiCC(\d+)", name)

        if match:
            isMidiController = True
            number = int(match.group(1))
        else:
            isMidiController = False
            number = cls._sourceControllerNameToIndexMap.get(name)

        result = (number, isMidiController)
        return result

    #--------------------

    @classmethod
    def _sourceControllerName (cls : Class,
                               isMidiController : Boolean,
                               value : Natural) -> String:
        """Returns name of modulator source characterized by
           <isMidiController> and <value>"""

        result = \
            ("MidiCC%03d" % value if isMidiController
             else cls._sourceControllerIndexToNameMap.get(value,
                                                          "???%03d" % value))
        return result

    #--------------------

    @classmethod
    def _typeIndex (cls : Class,
                    name : String) -> Natural:
        """Returns index of type characterized by <name>"""

        result = cls._typeNameToIndexMap.get(name)
        return result

    #--------------------

    @classmethod
    def _typeName (cls : Class,
                   typeIndex : Natural) -> String:
        """Returns name of type characterized by <value>"""

        result = \
            cls._typeIndexToNameMap.get(typeIndex, "???%03d" % typeIndex)
        return result

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object,
                  value : Natural = 0):
        """Initializes <self> to <value>"""

        Logging.trace(">>: 0x%04x", value)

        self.sourceIndex            = (value & 0x007F)
        self.isMidiController       = (value & 0x0080) != 0
        self.hasDescendingDirection = (value & 0x0100) != 0
        self.isUnipolar             = (value & 0x0200) != 0
        self.typeIndex              = (value >> 10) & 0x3F

        Logging.trace("<<: %s", self)

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; if <errorHandler> is
           not none, any error messages are appended to that list"""

        Logging.trace(">>")

        cls = self.__class__
        isOkay = _checkForAttributes(propertyMap, cls._attributeNameSet,
                                     cls._attributeNameSet, errorHandler)

        if not isOkay:
            Logging.traceError("bad property map for modulator source %s",
                               propertyMap)
        else:
            attributeName = "sourceController"
            value         = propertyMap[attributeName]
            sourceIndex, isMidiController = cls._sourceControllerIndex(value)
            isOkay = sourceIndex is not None

            if isOkay:
                self.sourceIndex      = sourceIndex
                self.isMidiController = isMidiController

            for attributeName in ("hasDescendingDirection", "isUnipolar"):
                if isOkay:
                    value = propertyMap[attributeName]
                    isOkay = _isBoolean(value)

                    if isOkay:
                        setattr(self, attributeName, value)

            if isOkay:
                attributeName = "typeName"
                value         = propertyMap[attributeName]
                typeIndex = cls._typeNameToIndexMap[value]
                isOkay = typeIndex is not None

                if isOkay:
                    self.typeIndex = typeIndex

            if not isOkay:
                # report first error encountered
                errorMessage = _ErrMsg_badValue % (attributeName, value)
                ErrorHandler.appendMessage(errorHandler, errorMessage)

        Logging.trace("<<: %s", self)

    #--------------------
    # type conversion
    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns the string representation of <self>"""

        clsName = self.__class__.__name__
        template = ("%s("
                    + "source = %s:%d ('%s'),"
                    + " hasDescendingDirection = %s, isUnipolar = %s,"
                    + " type = %d ('%s'))")
        sourceControllerName, typeName = self._controllerAndTypeName()
        st = (template
              % (clsName,
                 iif(self.isMidiController, "MIDICC", "INTERNAL"),
                 self.sourceIndex,
                 sourceControllerName,
                 self.hasDescendingDirection, self.isUnipolar,
                 self.typeIndex, typeName))
        return st

    #--------------------

    def toNatural (self : Object) -> Natural:
        """Returns natural representation of <self>"""

        Logging.trace(">>: %s", self)
        boolToInt = lambda x: 1 if x else 0

        result = (  (self.sourceIndex & 0x007F)            <<  0
                  | boolToInt(self.isMidiController)       <<  7
                  | boolToInt(self.hasDescendingDirection) <<  8
                  | boolToInt(self.isUnipolar)             <<  9
                  | (self.typeIndex & 0x003F)              << 10)

        Logging.trace("<<: 0x%04x", result)
        return result

    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        sourceControllerName, typeName = self._controllerAndTypeName()
        result = {
            "sourceController"       : sourceControllerName,
            "hasDescendingDirection" : self.hasDescendingDirection,
            "isUnipolar"             : self.isUnipolar,
            "typeName"               : typeName
        }

        return result

#====================

class SoundFontName:
    """length bounded name for samples, instruments and presets"""

    # maximum length of a SoundFont name
    _maximumLength = 20

    #--------------------

    def __init__ (self : Object,
                  value : String = ""):
        """Initializes <self> to <value>"""

        Logging.trace(">>: '%s'", value)
        self._value = None
        self.set(value)
        Logging.trace("<<: %s", self)

    #--------------------
    # type conversion
    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns the string representation of <self>"""

        clsName = self.__class__.__name__
        template = "%s('%s')"
        st = template % (clsName, self._value)
        return st

    #--------------------

    def __str__ (self : Object) -> String:
        """Returns the string representation of <self>"""

        return self.toShortString()

    #--------------------

    def toPropertyData (self : Object) -> Object:
        """Returns representation of <self> as data in a property map"""

        return self.toShortString()

    #--------------------

    def toShortString (self : Object) -> Object:
        """Returns short string representation of <self>"""

        return self._value

    #--------------------
    # change
    #--------------------

    def set (self : Object,
             value : String = ""):
        """Sets <self> to <value>"""

        Logging.trace(">>: '%s'", value)
        cls = self.__class__
        self._value = value[:cls._maximumLength]
        Logging.trace("<<: %s", SoundFontName.__repr__(self))

#====================

class SoundFontPreset (SoundFontZonedElement):
    """a SoundFont preset"""

    # list of local attribute names being mandatory
    _mandatoryAttributeNameList = ("programNumber", "bankNumber")

    # list of local attribute names
    _attributeNameList = (_mandatoryAttributeNameList
                          + ("libraryIndex", "genreIndex",
                            "morphologyIndex"))

    # set of all attribute names for this class
    _attributeNameSet = \
        (SoundFontZonedElement._attributeNameSet
         .union(set(_attributeNameList)))

    # set of mandatory attribute names for this class
    _mandatoryAttributeNameSet = \
        (SoundFontZonedElement._mandatoryAttributeNameSet
         .union(set(_mandatoryAttributeNameList)))

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object,
                      listsAreShown : Boolean = False) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        template = ("preset = %03d:%03d,"
                    + " libraryIndex = %d, genreIndex = %d,"
                    + " morphologyIndex = %d")
        st = (template
              % (self.bankNumber, self.programNumber,
                 self.libraryIndex, self.genreIndex, self.morphologyIndex))
        result = super()._asRawString(st, listsAreShown)
        return result

    #--------------------
    
    def _validate (self : Object,
                   errorHandler : ErrorHandler):
        """Checks <self> for implausible values"""

        Logging.trace(">>")

        cls = self.__class__
        isValidNumber = lambda x: _isNaturalInRange(x, 0, 65535)

        for attributeName in cls._mandatoryAttributeNameList:
            value = getattr(self, attributeName)

            if not isValidNumber(value):
                ErrorHandler.appendMessage(errorHandler,
                                           (_ErrMsg_badValue
                                            % (attributeName, value)))

        Logging.trace("<<")
    
    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object,
                  identification : String):
        """Initializes <self> to default values"""

        Logging.trace(">>: '%s'", identification)

        cls = self.__class__
        super().__init__(identification, SoundFontObjectKind.preset)

        for attributeName in cls._attributeNameList:
            setattr(self, attributeName, 0)

        Logging.trace("<<: %s", self)

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap> and appends any errors to
           <errorHandler> (if set)"""

        Logging.trace(">>")

        cls = self.__class__
        isOkay = _checkForAttributes(propertyMap,
                                     cls._mandatoryAttributeNameSet,
                                     cls._attributeNameSet, errorHandler)

        if not isOkay:
            Logging.traceError("bad property map for preset %s",
                               propertyMap)

        super().fillFromPropertyMap(propertyMap, errorHandler)

        for attributeName in cls._attributeNameList:
            setattr(self, attributeName, propertyMap.get(attributeName, 0))

        self._validate(errorHandler)

        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def toExternalString (self : Object) -> String:
        """Returns the external string representation of <self>
           without type indication"""

        # leave out the zone lists
        return self._asRawString(False)

    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        Logging.trace(">>: name = '%s'", self.name)

        cls = self.__class__
        propertyMap = {}

        for attributeName in cls._attributeNameList:
            propertyMap[attributeName] = getattr(self, attributeName)

        # leave out the zone lists
        result = super().toPropertyMap(False, propertyMap, True)

        Logging.trace("<<")
        return result

#====================

class SoundFontSample (_SoundFontNamedElement):
    """the SoundFont sample header"""

    # list of local string-valued attribute names
    _stringAttributeNameList = ("partner", "kind")
    
    # list of local integer-valued attribute names
    _integerAttributeNameList = (
        "sampleStartPosition", "sampleEndPosition",
        "loopStartPosition", "loopEndPosition",
        "sampleRate", "originalPitch", "pitchCorrection"
    )
    
    # set of all attribute names for this class
    _attributeNameSet = \
        (_SoundFontNamedElement._attributeNameSet
         .union(set(_stringAttributeNameList + _integerAttributeNameList)))

    # global setting for the export of sample headers: when
    # <_waveReferencesAreNormalized> is set, the wave data in sample
    # objects is normalized for referencing external wave files
    _waveReferencesAreNormalized = False

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        cls = self.__class__
        template = ("%s, "
                    + ", ".join([ attributeName + " = %d"
                                  for attributeName in
                                  cls._integerAttributeNameList ])
                    + ", "
                    + ", ".join([ attributeName + " = '%s'"
                                  for attributeName in
                                  cls._stringAttributeNameList ]))
        partner = self.partner
        partnerIdentification = \
            (partner if partner is None or _isString(partner)
             else _partnerIdentification(partner))
        st = (template
              % (super()._asRawString(),
                 self.sampleStartPosition, self.sampleEndPosition,
                 self.loopStartPosition, self.loopEndPosition,
                 self.sampleRate, self.originalPitch,
                 self.pitchCorrection, partnerIdentification,
                 self.kind))
        return st

    #--------------------
    
    def _validate (self : Object,
                   errorHandler : ErrorHandler):
        """Checks <self> for implausible values"""

        Logging.trace(">>")

        # positions
        isOkay = self.sampleStartPosition < self.sampleEndPosition

        if self.loopStartPosition > 0 or self.loopEndPosition > 0:
            isOkay = \
                (isOkay
                 and self.loopStartPosition < self.loopEndPosition
                 and self.sampleStartPosition <= self.loopStartPosition
                 and self.loopEndPosition <= self.sampleEndPosition)

        if not isOkay:
            errorMessage = (_ErrMsg_Sample_badPositions
                            % (self.sampleStartPosition,
                               self.sampleEndPosition,
                               self.loopStartPosition,
                               self.loopEndPosition))
            ErrorHandler.appendMessage(errorHandler, errorMessage)

        # pitch
        pitch = self.originalPitch
        isOkay = _isNaturalInRange(pitch, 0, 127)

        if not isOkay:
            ErrorHandler.appendMessage(errorHandler,
                                       _ErrMsg_Sample_badPitch % pitch)
            
        # pitch correction
        pitchCorrection = self.pitchCorrection
        isOkay = _isIntegerInRange(pitchCorrection, -128, 127)

        if not isOkay:
            ErrorHandler.appendMessage(errorHandler,
                                       _ErrMsg_Sample_badPitchCorrection
                                       % pitchCorrection)

        Logging.trace("<<")
    
    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object,
                  identification : String):
        """Initializes <self> to default values"""

        Logging.trace(">>: '%s'", identification)

        cls = self.__class__
        super().__init__(identification, SoundFontObjectKind.sample)

        for attributeName in cls._integerAttributeNameList:
            setattr(self, attributeName, 0)

        self.partner = None
        self.kind    = SoundFontSampleKind.romLinkedSample

        Logging.trace("<<: %s", self)

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap> and appends any errors to
           <errorHandler> (if set)"""

        Logging.trace(">>: %s", propertyMap)

        cls = self.__class__
        erroneousDataPair = None
        isOkay = _checkForAttributes(propertyMap, cls._attributeNameSet,
                                     cls._attributeNameSet, errorHandler)

        if not isOkay:
            Logging.traceError("bad property map for preset %s",
                               propertyMap)

        super().fillFromPropertyMap(propertyMap, errorHandler)
        attributeName = "partner"
        value = propertyMap[attributeName]
        isOkay = (_isString(value)
                  and (value == _undefinedPartnerIdentification
                       or re.match(r"SHDR\[0-9A-Fa-f]+", value)))

        if not isOkay:
            erroneousDataPair = (attributeName, value)
        else:
            # set partner preliminarily to its identification string
            # (unless it is undefined)
            self.partner = iif(value == _undefinedPartnerIdentification,
                               None, value)

        if isOkay:
            attributeName = "kind"
            value = propertyMap[attributeName]
            isOkay = (_isString(value) and re.match(r"0x\d+", value))

            if isOkay:
                match = re.match(r"(0x\d+)", value)
                value = int(match.group(1), 0)
                kind = SoundFontSampleKind.fromNatural(value)
                isOkay = kind is not None

                if isOkay:
                    self.kind = kind

        if not isOkay and erroneousDataPair is None:
            erroneousDataPair = (attributeName, value)
        else:
            for attributeName in cls._integerAttributeNameList:
                value = propertyMap.get(attributeName)

                if _isInteger(value):
                    setattr(self, attributeName, value)
                else:
                    erroneousDataPair = (attributeName, value)
                    isOkay = False

        if not isOkay and erroneousDataPair is not None:
            # report first error encountered
            errorMessage = _ErrMsg_badValue % erroneousDataPair
            ErrorHandler.appendMessage(errorHandler, errorMessage)

        self._validate(errorHandler)

        Logging.trace("<<: %s", self)

    #--------------------
    # type conversion
    #--------------------

    @classmethod
    def enableNormalizedWaveReferences (cls : Class,
                                        isNormalized : Boolean):
        """Sets or resets the normalization of wave references for
           exporting to a property map"""

        Logging.trace(">>: %s", isNormalized)
        cls._waveReferencesAreNormalized = isNormalized
        Logging.trace("<<")

    #--------------------
   
    def toPropertyMap (self : Object) -> StringMap:
        """Returns a property map for sample <self>"""

        Logging.trace(">>: name = '%s'", self.name)

        # adjust sample positions depending on setting of
        # <cls._waveReferencesAreNormalized>
        cls = self.__class__
        offset = iif(cls._waveReferencesAreNormalized,
                     self.sampleStartPosition, 0)
        sampleStartPosition = self.sampleStartPosition - offset
        sampleEndPosition   = self.sampleEndPosition   - offset
        loopStartPosition   = self.loopStartPosition   - offset
        loopEndPosition     = self.loopEndPosition     - offset

        partnerIdentification = \
            _partnerIdentification(self.partner)
        propertyMap = {
            "sampleStartPosition" : sampleStartPosition,
            "sampleEndPosition"   : sampleEndPosition,
            "loopStartPosition"   : loopStartPosition,
            "loopEndPosition"     : loopEndPosition,
            "sampleRate"          : self.sampleRate,
            "originalPitch"       : self.originalPitch,
            "pitchCorrection"     : self.pitchCorrection,
            "partner"             : partnerIdentification,
            "kind"                : self.kind.toPropertyData()
        }

        result = super().toPropertyMap() | propertyMap
        Logging.trace("<<: %s", result)
        return result

#====================

class SoundFontVersion:
    """SoundFont version as a pair of naturals"""

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object,
                  majorVersion : Natural = 0,
                  minorVersion : Natural = 0):
        """Sets up a SoundFont version"""

        Logging.trace(">>: (%d, %d)", majorVersion, minorVersion)
        self.major = majorVersion
        self.minor = minorVersion
        Logging.trace("<<: %s", self)

    #--------------------

    @classmethod
    def fromString (cls : Class,
                    st : String) -> Object:
        """Makes a soundfont version from a string"""

        Logging.trace(">>: '%s'", st)

        match = re.match(r"(\d+).(\d+)", st)

        if not match:
            Logging.traceError("bad version string '%s'", st)
            result = cls(0, 0)
        else:
            majorVersion = int(match.group(1))
            minorVersion = int(match.group(2))
            Logging.trace("--: %d.%d", majorVersion, minorVersion)
            result = cls(majorVersion, minorVersion)
        
        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # type conversion
    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns the string representation of <self>"""

        clsName = self.__class__.__name__
        template = "%s(major = %d, minor = %d)"
        st = template % (clsName, self.major, self.minor)
        return st

    #--------------------

    def toPropertyData (self : Object) -> Object:
        """Returns representation of <self> as data in a property map"""

        return "%d.%02d" % (self.major, self.minor)

    #--------------------

    def toRawData (self : Object) -> Tuple:
        """Returns representation of <self> as pair of naturals"""

        return (self.major, self.minor)

#====================

class SoundFontZone (_SoundFontElement):
    """the SoundFont zone definition for either a preset or
       instrument; a zone consists of a map from generator kind to
       generator value and a list of modulators"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _adaptToPolyphoneOrder (self : Object):
        """Brings generator map keys to order as in the Polyphone
           SoundFont editor"""

        Logging.trace(">>")

        generatorMap = self.generatorMap
        keyList = generatorMap.keys()
        tempMap = {}
        listInPolyphoneOrder = _SFGK.listInPolyphoneOrder()

        for kind in listInPolyphoneOrder:
            if kind in keyList:
                tempMap[kind] = generatorMap[kind]

        generatorMap.clear()
        generatorMap |= tempMap
        
        Logging.trace("<<")
    
    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        template = ("parent = '%s', isGlobal = %s,"
                    + " generatorMap = %s, modulatorList = %s")
        st = (template
              % (_partnerIdentification(self.parent), self.isGlobal,
                 self.generatorMap, self.modulatorList))
        return st
                    
    #--------------------

    def _fillFromGeneratorPropertyMap (self : Object,
                                       parentIsInstrument : Boolean,
                                       generatorPropertyMap : StringMap,
                                       errorHandler : ErrorHandler = None):
        """Fills <self> from <generatorPropertyMap>; if
           <errorHandler> is not none, any error messages are
           appended to that list"""

        Logging.trace(">>: parentIsInstrument = %s", parentIsInstrument)

        self.generatorMap  = {}
        isOkay = _checkForAttributes(generatorPropertyMap, set(),
                                     _SFGK.nameSet(), errorHandler)

        if not isOkay:
            Logging.traceError("bad property map for generator map %s",
                               generatorPropertyMap)

        for key, value in generatorPropertyMap.items():
            generatorKind = SoundFontGeneratorKind.fromString(key)
            isOkay = True

            if generatorKind is not None:
                amount = \
                    (SoundFontGeneratorAmount
                     .fromPropertyData(value, generatorKind,
                                       parentIsInstrument))
            else:
                isOkay = False
                amount = None
                ErrorHandler.appendMessage(errorHandler,
                                           _ErrMsg_Generator_badKind % key)

            if amount is not None and generatorKind == _SFGK.sampleModes:
                amount = (SoundFontSampleLoopModeKind
                          .fromExternalRepresentation(amount))

            if amount is None:
                isOkay = False
                ErrorHandler.appendMessage(errorHandler,
                                           _ErrMsg_Generator_badAmount
                                           % (key, value))

            if isOkay:
                checkProc = \
                    (SoundFontGeneratorAmount
                     .checkProcForGeneratorKind(generatorKind,
                                                parentIsInstrument))

                if checkProc is None:
                    Logging.trace("generatorKind %s without checkProc",
                                  generatorKind)
                else:
                    isOkay = checkProc(amount)

                    if not isOkay:
                        ErrorHandler.appendMessage(errorHandler,
                                                   _ErrMsg_Generator_badAmount
                                                   % (key, value))
                        Logging.trace("--: value for %s not accepted: %s -> %s",
                                      key, value, amount)

            if isOkay:
                Logging.trace("--: generatorMap[%s] = %s",
                              generatorKind.toShortString(), amount)
                self.generatorMap[generatorKind] = amount

        Logging.trace("<<: %s", self)

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object,
                  parent : _SoundFontIdentifiedElement = None,
                  isGlobalZone : Boolean = False,
                  generatorMap : Map = {},
                  modulatorList : List = []):
        """Initializes <self> to <generatorMap> and <modulatorList>"""

        Logging.trace(">>: isGlobalZone = %s,"
                      + " generatorMap = %s, modulatorList = %s",
                      isGlobalZone, generatorMap, modulatorList)

        self.parent        = parent
        self.isGlobal      = isGlobalZone
        self.generatorMap  = generatorMap
        self.modulatorList = modulatorList

        self._adaptToPolyphoneOrder()
        
        Logging.trace("<<: %s", self)

    #--------------------

    def fillFromPropertyMap (self : Object,
                             parentIsInstrument : Boolean,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; <parentIsInstrument> tells
           whether zoned element is an instrumentif <errorHandler> is
           not none, any error messages are appended to that list"""

        Logging.trace(">>: parentIsInstrument = %s",
                      parentIsInstrument)

        self.generatorMap  = {}
        self.modulatorList = []

        for attributeName in ("generatorMap", "modulatorList"):
            if attributeName in propertyMap:
                if attributeName == "generatorMap":
                    generatorMap = propertyMap[attributeName]
                    self._fillFromGeneratorPropertyMap(parentIsInstrument,
                                                       generatorMap,
                                                       errorHandler)
                else:
                    propertyMapList = propertyMap[attributeName]
                    identificationPrefix = "MODL"

                    for i, propertyMap in enumerate(propertyMapList):
                        defaultIdentification = ("%s%05d"
                                                 % (identificationPrefix, i))
                        identification = propertyMap.get("identification",
                                                         defaultIdentification)
                        modulator = SoundFontModulator(identification)
                        modulator.fillFromPropertyMap(parentIsInstrument,
                                                       propertyMap,
                                                       errorHandler)
                        self.modulatorList.append(modulator)

        self._adaptToPolyphoneOrder()

        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def toPropertyMap (self : Object,
                       parentIsInstrument : Boolean) -> StringMap:
        result = super().toPropertyMap()

        if len(self.generatorMap) > 0:
            toPropertyData = \
                (lambda kind, x:
                 x if _isString(x)
                 else x.identification
                     if isinstance(x, _SoundFontIdentifiedElement)
                 else (SoundFontGeneratorAmount
                       .toPropertyData(x, kind, parentIsInstrument)))
            generatorPropertyMap = {
                key.toShortString() : toPropertyData(key, value)
                for key, value in self.generatorMap.items()
            }

            result["generatorMap"] = generatorPropertyMap

        if len(self.modulatorList) > 0:
            result["modulatorList"] = _toPropertyMapList(self.modulatorList)

        return result

    #--------------------
    # property change
    #--------------------

    def setParent (self : Object,
                   parent : _SoundFontIdentifiedElement):
        """Sets parent of <self> to <parent>"""

        Logging.trace(">>: '%s'", _partnerIdentification(parent))
        self.parent = parent
        Logging.trace("<<")

    #--------------------
    # measurement
    #--------------------

    def isEmpty (self : Object) -> Boolean:
        """Tells whether zone has neither generators or modulators"""

        return (len(self.generatorMap) == 0
                and len(self.modulatorList) == 0)

#====================

class SoundFontWaveData:
    """Represents the 16- or 24-bit sample data points in a SoundFont"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _clearNOLOG (self : Object,
                     bytesPerDataPoint : Natural):
        """Clears wave data object (without logging)"""

        self._standardWaveData  = ByteList(0)
        self._extendedWaveData  = ByteList(0)
        self._bytesPerDataPoint = bytesPerDataPoint
        self._waveData          = []

    #--------------------

    def _synthesizeFragmentsFromWaveData (self : Object):
        """Synthesizes fragments from combined wave data"""

        Logging.trace(">>")

        bytesPerDataPoint = self._bytesPerDataPoint
        waveData          = self._waveData

        dataPointCount    = len(waveData)
        hasExtendedData   = (bytesPerDataPoint > 2)
        extendedByteCount = dataPointCount if hasExtendedData else 0
        scalingFactor     = float(2 << (bytesPerDataPoint * 8 - 1))
        integerList = [ int(scalingFactor * value) for value in waveData ]

        self._standardWaveData  = ByteList(dataPointCount * 2)
        self._extendedWaveData  = ByteList(extendedByteCount)
        j = 0

        if not hasExtendedData:
            for value in integerList:
                byteList = value.to_bytes(bytesPerDataPoint, 'little',
                                          signed = True)
                self._standardWaveData[j:j+2] = byteList
                j += 2
        else:
            for i, value in enumerate(integerList):
                byteList = value.to_bytes(bytesPerDataPoint, 'little',
                                          signed = True)
                self._extendedWaveData[i]     = byteList[0]
                self._standardWaveData[j:j+2] = byteList[1:2]
                j += 2
        
        Logging.trace("<<: %s", self)

    #--------------------

    def _synthesizeWaveDataFromFragments (self : Object):
        """Synthesizes combined wave data from fragments"""

        Logging.trace(">>")

        cls = self.__class__
        standardWaveData = self._standardWaveData
        extendedWaveData = self._extendedWaveData

        hasExtendedData   = (len(extendedWaveData) != 0)
        sampleCount       = len(standardWaveData) // 2
        bytesPerDataPoint = self._bytesPerDataPoint

        Logging.trace("--: hasExtendedData = %s, sampleCount = %d,"
                      + " bytesPerDataPoint = %d",
                      hasExtendedData, sampleCount, bytesPerDataPoint)

        if not hasExtendedData:
            Logging.trace("--: packing standard wave data")
            waveData = cls._unpackWaveData(bytesPerDataPoint,
                                           bytes(standardWaveData))
            maxSampleValue = float(2 << 15)
        else:            
            Logging.trace("--: combining standard and extended wave data")
            sampleByteList = ByteList(bytesPerDataPoint * sampleCount)
            i = 0
            k = 0

            for j in range(sampleCount):
                if hasExtendedData:
                    sampleByteList[k + 0] = extendedWaveData[j]

                sampleByteList[k + 1] = standardWaveData[i + 0]
                sampleByteList[k + 2] = standardWaveData[i + 1]

                k += self._bytesPerDataPoint
                i += 2

            waveData = cls._unpackWaveData(bytesPerDataPoint, sampleByteList)
            maxSampleValue = float(2 << 23)

        Logging.trace("--: converting to unit interval")
        factor = 1.0 / maxSampleValue
        self._waveData = [ value * factor for value in waveData ]

        Logging.trace("<<: %s", self)

    #--------------------

    @classmethod
    def _unpackWaveData (cls : Class,
                         bytesPerDataPoint : Natural,
                         byteList : ByteList) -> IntegerList:
        """Unpacks wave data in <byteList> with <bytesPerDataPoint> in
           little endian order"""

        byteCount = len(byteList)
        Logging.trace(">>: bytesPerDataPoint = %d, byteCount = %d",
                      bytesPerDataPoint, byteCount)

        convertByteSlice = \
            lambda i: int.from_bytes(byteList[i : i + bytesPerDataPoint],
                                     byteorder = 'little', signed = True)
        result = [ convertByteSlice(i)
                   for i in range(0, byteCount, bytesPerDataPoint) ]
        
        Logging.trace("<<: count = %d", len(result))
        return result

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object):
        """Initializes wave data object to be empty"""

        Logging.trace(">>")
        self._clearNOLOG(4)
        Logging.trace("<<: %s", self)

    #--------------------

    def fillFromByteListPair (self : Object,
                              standardWaveData : ByteList,
                              extendedWaveData : ByteList):
        """Fills wave data object with byte lists <standardWaveData> and
           <extendedWaveData>"""

        Logging.trace(">>: standardWaveDataCount = %d,"
                      + " extendedWaveDataCount = %d",
                      len(standardWaveData), len(extendedWaveData))

        bytesPerDataPoint  = iif(len(extendedWaveData) > 0, 4, 2)
        self._clearNOLOG(bytesPerDataPoint)

        self._standardWaveData  = standardWaveData
        self._extendedWaveData  = extendedWaveData

        Logging.trace("<<: %s", self)

    #--------------------

    def fillFromRealList (self : Object,
                          hasExtendedData : Boolean,
                          waveData : RealList):
        """Fills wave data object with real list <waveData>; if
           <hasExtendedData> is set, there are three bytes per sample
           data point"""

        Logging.trace(">>: hasExtendedData = %s, waveDataCount = %d",
                      hasExtendedData, len(waveData))

        bytesPerDataPoint = iif(hasExtendedData, 3, 2)
        self._clearNOLOG(bytesPerDataPoint)
        self._waveData = waveData

        Logging.trace("<<: %s", self)

    #--------------------
    # type conversion
    #--------------------

    def __str__ (self : Object) -> String:
        """Returns the string representation of <self>"""

        return self.toShortString()

    #--------------------

    def toShortString (self : Object) -> Object:
        """Returns short string representation of <self>"""

        clsName = self.__class__.__name__
        template = ("%s(bytesPerDataPoint = %d, standardWaveDataCount = %d,"
                    + " extendedWaveDataCount = %d, waveDataCount = %d)")
        st = (template
              % (clsName, self._bytesPerDataPoint,
                 len(self._standardWaveData), len(self._extendedWaveData),
                 len(self._waveData)))
        return st

    #--------------------

    def toRawData (self : Object) -> List:
        """Returns representation of <self> as a list of byte lists"""

        if len(self._standardWaveData) == 0 and len(self._waveData) > 0:
            self._synthesizeFragmentsFromWaveData()
        
        if self._bytesPerDataPoint == 2:
            result = (self._standardWaveData,)
        else:
            result = (self._standardWaveData, self._extendedWaveData)

        return result

    #--------------------
    # access
    #--------------------

    def byteCount (self : Object) -> Natural:
        """Returns the number of bytes in wave data byte lists"""

        return len(self._standardWaveData) + len(self._extendedWaveData)

    #--------------------

    def bytesPerDataPoint (self : Object) -> Natural:
        """Returns the number of bytes per sample data point"""

        return self._bytesPerDataPoint
        
    #--------------------

    def dataPointCount (self : Object) -> Natural:
        """Returns the number of data points in real wave data list"""

        return len(self._waveData)

    #--------------------
    
    def slice (self : Object,
               startPosition : Natural,
               endPosition   : Natural) -> RealList:
        """Returns slice of wave data from <startPosition> to
           <endPosition>"""

        Logging.trace(">>: startPosition = %d, endPosition = %d",
                      startPosition, endPosition)

        if len(self._waveData) == 0:
            self._synthesizeWaveDataFromFragments()

        result = self._waveData[startPosition:endPosition]
        
        Logging.trace("<<: sampleCount = %d", len(result))
        return result

    #--------------------
    # change
    #--------------------

    def clear (self : Object,
               hasExtendedData : Boolean):
        """Clears all wave data and sets bytes per sample to either
           two or three depending on <hasExtendedData>"""

        Logging.trace(">>: %s", hasExtendedData)
        bytesPerDataPoint = iif(hasExtendedData, 3, 2)
        self._clearNOLOG(bytesPerDataPoint)
        Logging.trace("<<: %s", self)
        
    #--------------------

    def extendByRealList (self : Object,
                          otherWaveData : RealList):
        """Extends wave data object with <otherWaveData>"""

        Logging.trace(">>: waveDataCount = %d", len(otherWaveData))

        self._standardWaveData = ByteList(0)
        self._extendedWaveData = ByteList(0)
        self._waveData.extend(otherWaveData)

        Logging.trace("<<: %s", self)
        
    #--------------------

    def extendByByteListPair (self : Object,
                              standardWaveData : ByteList,
                              extendedWaveData : ByteList):
        """Extends wave data object with <standardWaveData> and
           <extendedWaveData>"""

        Logging.trace(">>: standardWaveDataCount = %d,"
                      + " extendedWaveDataCount = %d",
                      len(standardWaveData), len(extendedWaveData))

        self._standardWaveData.extend(standardWaveData)
        self._extendedWaveData.extend(extendedWaveData)
        self._waveData = []

        Logging.trace("<<")

#====================

class SoundFont (_SoundFontElement):
    """Represents the complete SoundFont"""

    # list of attribute names for this class
    _attributeNameList = ("header", "sampleList", "instrumentList",
                          "presetList")

    # set of attribute names for this class
    _attributeNameSet = (_SoundFontElement._attributeNameSet
                         .union(set(_attributeNameList)))

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _asRawString (self : Object) -> String:
        """Returns the raw string representation of <self> with just
           the attribute data"""

        template = ("header = %s, sampleCount = %d,"
                    + " instrumentCount = %d, presetCount = %d,"
                    + " waveData = %s")
        st = (template
              % (self.header, len(self.sampleList),
                 len(self.instrumentList), len(self.presetList),
                 self.waveData))
        return st

    #--------------------

    def _replaceIdentificationsByLinks (self : Object,
                                        errorHandler : ErrorHandler):
        """Traverses all objects in soundfont and replaces
           identifications by object links; error messages are
           appended to <errorHandler>"""

        Logging.trace(">>")

        getByIdentification = \
            lambda x: _SoundFontIdentifiedElement.getByIdentification(x)

        for sample in self.sampleList:
            partnerIdentification = sample.partner
            Logging.trace("--: sample = '%s', partner = '%s'",
                          sample.identification, partnerIdentification)

            if partnerIdentification is not None:
                Logging.trace("--: partnerIdentification = %s",
                              partnerIdentification)
                partner = getByIdentification(partnerIdentification)

                if partner is None:
                    ErrorHandler.appendMessage(errorHandler,
                                               (_ErrMsg_Sample_badPartner
                                                % partnerIdentification))
                else:
                    Logging.trace("--: found partner sample")
                    sample.partner = partner

        zonedElementList = self.instrumentList + self.presetList

        for zonedElement in zonedElementList:
            Logging.trace("--: zonedElement = '%s'",
                          zonedElement.identification)

            for i, zone in enumerate(zonedElement.zoneList):
                generatorMap = zone.generatorMap

                for generatorKind in (SoundFontGeneratorKind.instrument,
                                      SoundFontGeneratorKind.sampleID):
                    if generatorKind in generatorMap:
                        partnerIdentification = generatorMap[generatorKind]
                        Logging.trace("--: zone[%d].%s = '%s'",
                                      i, generatorKind.toShortString(),
                                      partnerIdentification)
                        partner = getByIdentification(partnerIdentification)

                        if partner is None:
                            errorMessage = (_ErrMsg_Zone_badPartner
                                            % partnerIdentification)
                            ErrorHandler.appendMessage(errorHandler,
                                                       errorMessage)
                        else:
                            Logging.trace("--: found partner")
                            generatorMap[generatorKind] = partner
        
        Logging.trace("<<")
    
    #--------------------
    # EXPORTED FEATURES
    #--------------------

    #--------------------
    # construction
    #--------------------

    def __init__ (self : Object):
        """Initializes SoundFont structure in <self>"""

        Logging.trace(">>")

        self.header         = SoundFontHeader()
        self.sampleList     = []
        self.instrumentList = []
        self.presetList     = []
        self.waveData       = SoundFontWaveData()

        Logging.trace("<<")

    #--------------------

    def fillFromPropertyMap (self : Object,
                             propertyMap : StringMap,
                             errorHandler : ErrorHandler = None):
        """Fills <self> from <propertyMap>; error messages are appended
           to <errorHandler> (if set)"""

        Logging.trace(">>")

        cls = self.__class__
        isOkay = _checkForAttributes(propertyMap, cls._attributeNameSet,
                                     cls._attributeNameSet, errorHandler)

        if not isOkay:
            Logging.traceError("bad property map for SoundFont %s",
                               propertyMap)

        for attributeName in cls._attributeNameList:
            data = propertyMap[attributeName]

            if attributeName == "header":
                header = SoundFontHeader()
                ErrorHandler.setContext(errorHandler, "header")
                header.fillFromPropertyMap(data, errorHandler)
                self.header = header
            elif attributeName == "sampleList":
                self.sampleList = \
                    _fromPropertyMapList(SoundFontSample,
                                         "SHDR", data, None,
                                         errorHandler)
            elif attributeName == "instrumentList":
                self.instrumentList = \
                    _fromPropertyMapList(SoundFontInstrument,
                                         "INST", data, None,
                                         errorHandler)
            else:
                # attributeName == "presetList"
                self.presetList = \
                    _fromPropertyMapList(SoundFontPreset,
                                         "PHDR", data, None,
                                         errorHandler)

        self._replaceIdentificationsByLinks(errorHandler)
       
        Logging.trace("<<")
    
    #--------------------
    # type conversion
    #--------------------

    def toPropertyMap (self : Object) -> StringMap:
        """Returns property map"""

        Logging.trace(">>")

        propertyMap = {
            "header"         : self.header.toPropertyMap(),
            "sampleList"     : _toPropertyMapList(self.sampleList),
            "instrumentList" : _toPropertyMapList(self.instrumentList),
            "presetList"     : _toPropertyMapList(self.presetList)
        }

        result = super().toPropertyMap() | propertyMap

        Logging.trace("<<")
        return result
