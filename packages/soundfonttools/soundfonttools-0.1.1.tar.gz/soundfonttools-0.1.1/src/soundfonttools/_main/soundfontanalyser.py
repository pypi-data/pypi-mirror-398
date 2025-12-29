# soundFontAnalyser - scans SoundFont file for possible problems
#
# author: Dr. Thomas Tensi
# version: 2025-08

#====================
# IMPORTS
#====================

import argparse
from enum import StrEnum
import json
import math
import sys

from basemodules.configurationfile import ConfigurationFile
from basemodules.operatingsystem import OperatingSystem
from basemodules.simplelogging import Logging, Logging_Level
from basemodules.simpletypes import \
    Boolean, Class, Natural, Object, ObjectList, Real, String, \
    StringList, Tuple
from basemodules.stringutil import deserializeToList
from basemodules.ttbase import iif, iif3
from basemodules.validitychecker import ValidityChecker

from simplefunctions import \
    OneDimensionalFunctionFromIntervals, \
    OneDimensionalFunctionFromNumbers, \
    TwoDimensionalFunctionFromIntervals

from multimedia.midi.soundfontfile import SoundFontFileReader

from multimedia.midi.soundfont import \
    SoundFont, SoundFontGeneratorAmount, \
    SoundFontGeneratorKind, SoundFontObjectKind, \
    _SoundFontIdentifiedElement, SoundFontZonedElement

#====================
# Abbreviations
#====================

SFGA = SoundFontGeneratorAmount
SFGK = SoundFontGeneratorKind

#====================
# TYPES
#====================

GeneratorKindList         = ObjectList
SoundFontZonedElementList = ObjectList
SoundFontZoneList         = ObjectList
Pair                      = Tuple

#====================

_programName = "soundFontAnalyser"
_newline = "\n"

_partnerGeneratorKindList = (SoundFontGeneratorKind.sampleID,
                             SoundFontGeneratorKind.instrument)

#--------------------

# the name of all rule checks
_ruleNameList = (
    "instrumentGlobalZone", "instrumentModulators",
    "instrumentOverrides",
    "presetGlobalZone", "presetModulators",
    "sampleOverrides"
)

#--------------------

_modulatorGeneratorKindList = [
    SFGK.startAddrsOffset, SFGK.endAddrsOffset, SFGK.startLoopAddrsOffset,
    SFGK.endLoopAddrsOffset, SFGK.startAddrsCoarseOffset,
    SFGK.modLfoToPitch, SFGK.vibLfoToPitch, SFGK.modEnvToPitch,
    SFGK.initialFilterFc, SFGK.initialFilterQ, SFGK.modLfoToFilterFc,
    SFGK.modEnvToFilterFc, SFGK.endAddrsCoarseOffset, SFGK.modLfoToVolume,
    SFGK.chorusEffectsSend, SFGK.reverbEffectsSend, SFGK.pan,
    SFGK.delayModLFO, SFGK.freqModLFO, SFGK.delayVibLFO, SFGK.freqVibLFO,
    SFGK.delayModEnv, SFGK.attackModEnv, SFGK.holdModEnv, SFGK.decayModEnv,
    SFGK.sustainModEnv, SFGK.releaseModEnv,
    SFGK.keynumToModEnvHold, SFGK.keynumToModEnvDecay,
    SFGK.delayVolEnv, SFGK.attackVolEnv, SFGK.holdVolEnv,
    SFGK.decayVolEnv, SFGK.sustainVolEnv, SFGK.releaseVolEnv,
    SFGK.keynumToVolEnvHold, SFGK.keynumToVolEnvDecay,
    SFGK.keynum, SFGK.velocity, SFGK.initialAttenuation,
    SFGK.coarseTune, SFGK.fineTune, SFGK.sampleModes,
    SFGK.scaleTuning, SFGK.exclusiveClass, SFGK.overridingRootKey
]

#--------------------

# all generator kinds
_allGeneratorKindList = list(SoundFontGeneratorKind)

#--------------------

# a mapping from rule name to generator kind list
_ruleNameToGeneratorKindListMap = {
    "instrumentGlobalZone" : _allGeneratorKindList,

    "instrumentModulators" : _modulatorGeneratorKindList,

    "instrumentOverrides" : [
        SFGK.keyRange, SFGK.velRange,
        SFGK.coarseTune, SFGK.fineTune, SFGK.scaleTuning,
        SFGK.chorusEffectsSend, SFGK.reverbEffectsSend
    ],

    "presetGlobalZone" : _allGeneratorKindList,

    "presetModulators" : _modulatorGeneratorKindList,
    
    "sampleOverrides" : [
        SFGK.overridingRootKey, SFGK.startAddrsOffset,
        SFGK.startLoopAddrsOffset
    ]
}

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

        ValidityChecker.isReadableFile(argumentList.soundFontFilePath,
                                       "soundFontFilePath")

        loggingFilePath       = argumentList.loggingFilePath
        configurationFilePath = argumentList.configurationFilePath

        if loggingFilePath is not None:
            ValidityChecker.isWritableFile(loggingFilePath,
                                           "loggingFilePath")

        if configurationFilePath is not None:
            ValidityChecker.isReadableFile(configurationFilePath,
                                           "configurationFilePath")

        Logging.trace("<<")

    #--------------------

    @classmethod
    def read (cls):
        """Reads commandline options and sets variables appropriately;
           returns tuple of variables read"""

        Logging.trace(">>")

        programDescription = \
            "Analyses SoundFont file and writes results to standard output"
        p = argparse.ArgumentParser(description=programDescription)

        p.add_argument("-c",
                       dest = "configurationFilePath",
                       help = ("defines the path of the (optional)"
                               + " configuration file"))
        p.add_argument("-l", "--logging_file",
                       dest = "loggingFilePath",
                       help = ("defines the path for the logging file;"
                              + " activates logging when given"))
        p.add_argument("-p", action = "store_true",
                       dest = "outputIsPrettyPrinted",
                       help = ("tells to format output in a" +
                               " pretty-printed style (human-readable)"))
        p.add_argument("soundFontFilePath",
                       help = ("defines the path of the SoundFont"
                               + " source file to be analysed"))

        result = p.parse_args()

        Logging.trace("<<: %s", result)
        return result

#====================

class _ConfigurationManager:
    """This module encapsulates the data from the configuration file."""

    # the set of excluded rule names (from configuration file)
    _excludedRuleNameSet = set()

    # mapping from rule name to excluded generator kind set
    _ruleNameToExcludedGeneratorKindSetMap = {}
    
    # setting for maximum accepted function distance when modulator
    # shall be recommended
    _maximumNormalizedRootMeanSquareError = 0.3

    # setting for maximum relative difference between two values when
    # projecting a two-dimensional generator function to one dimension
    _comparisonMarginForOneDFunctions = 0.2

    #--------------------
    #--------------------

    @classmethod
    def adaptGeneratorKindList (cls : Class,
                                ruleName : String,
                                generatorKindList : GeneratorKindList):
        """Strips generator kinds excluded in configuration file for
           rule named <ruleName> from <generatorKindList>"""

        Logging.trace(">>: ruleName = %s, generatorKindList = %s",
                      ruleName, generatorKindList)

        nameToExcludedGenKindSetMap = \
            cls._ruleNameToExcludedGeneratorKindSetMap

        if ruleName in nameToExcludedGenKindSetMap:
            excludedGeneratorKindSet = \
                nameToExcludedGenKindSetMap[ruleName]

            tempList = []

            for generatorKind in generatorKindList:
                if generatorKind not in excludedGeneratorKindSet:
                    tempList.append(generatorKind)

            generatorKindList.clear()
            generatorKindList.extend(tempList)

        Logging.trace("<<: %s", generatorKindList)

    #--------------------

    @classmethod
    def read (cls : Class,
              configurationFilePath : String):
        """Sets up manager with configuration file path
           <configurationFilePath>"""

        Logging.trace(">>: '%s'", configurationFilePath)

        configurationFile = ConfigurationFile(configurationFilePath)

        # process real bound variables
        def readRealProc (key : String, defaultValue : Real) -> Tuple:
            st = configurationFile.value(key, defaultValue)
            isOkay = ValidityChecker.isReal(st, key, False)

            if not isOkay:
                Logging.traceError("bad value %s for '%s' in configuration"
                                   + " file",
                                   st, key)

            return isOkay, st

        #-----

        isOkay, st = readRealProc("maximumNormalizedRootMeanSquareError", 0.1)

        if isOkay:
            cls._maximumNormalizedRootMeanSquareError = float(st)

        isOkay, st = readRealProc("comparisonMarginForOneDFunctions", 0.2)

        if isOkay:
            cls._comparisonMarginForOneDFunctions = float(st)

        # process rule variables
        nameToExcludedGenKindSetMap = \
            cls._ruleNameToExcludedGeneratorKindSetMap

        for ruleName in _ruleNameList:
            keyPrefix = "rule_%s_" % ruleName

            # check whether rule is active
            key = keyPrefix + "isActive"
            isActive = configurationFile.value(key, True)
            
            if not isActive:
                cls._excludedRuleNameSet.add(ruleName)

            # find list of excluded generator kinds
            key = keyPrefix + "excludedGeneratorKindList"
            kindListAsString = configurationFile.value(key, "[]")
            stringList = deserializeToList(kindListAsString)
            generatorKindSet = set()

            for st in stringList:
                generatorKind = SoundFontGeneratorKind.fromString(st)

                if generatorKind is not None:
                    generatorKindSet.add(generatorKind)

            nameToExcludedGenKindSetMap[ruleName] = generatorKindSet

        Logging.trace("--: _excludedRuleNameSet = %s,"
                      + " _ruleNameToExcludedGeneratorKindSetMap = %s",
                      cls._excludedRuleNameSet,
                      cls._ruleNameToExcludedGeneratorKindSetMap)

        Logging.trace("<<")

    #--------------------

    @classmethod
    def ruleIsChecked (cls : Class,
                       ruleName : String) -> Boolean:
        """Tells whether rule named <ruleName> is active in
           configuration file"""

        Logging.trace(">>: ruleName = %s", ruleName)
        result = ruleName not in cls._excludedRuleNameSet
        Logging.trace("<<: %s", result)
        return result

#====================

class _SoundFontAnalyser:
    """Provides the checking of all rules for a SoundFont analysis"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    def _addMessage (self : Object,
                     objectKind : SoundFontObjectKind,
                     objectName : String,
                     message : String):
        """Adds analysis message <message> for SoundFont object with
           <objectKind> and name <objectName> to internal data"""

        Logging.trace(">>: objectKind = '%s', objectName = '%s',"
                      + " message = '%s'",
                      objectKind, objectName, message)

        key = (objectKind, objectName)
        nameToMessageListMap = self._nameToMessageListMap

        if key not in nameToMessageListMap:
            nameToMessageListMap[key] = []

        nameToMessageListMap[key].append(message)

        Logging.trace("<<")
    
    #--------------------

    def _analyse1DFunctionForModulator \
            (self : Object,
             objectKind : SoundFontObjectKind,
             objectName : String,
             controllingParameter : String,
             generatorKind : SoundFontGeneratorKind,
             intervalFunction : OneDimensionalFunctionFromIntervals):
        """Checks whether <intervalFunction> for generator of kind
           <generatorKind> from interval to real for <objectKind> and
           <objectName> can be implemented by a modulator controlled
           by <controllingParameter>"""

        generatorKindString = generatorKind.toShortString()
        Logging.trace(">>: objectKind = %s, objectName = '%s',"
                      " generatorKind = %s, controllingParameter = '%s'"
                      + " function = %s",
                      objectKind, objectName, generatorKindString,
                      controllingParameter, intervalFunction)

        approximationResult = \
            OneDimensionalFunctionFromIntervals.approximate(intervalFunction)
        curveKind, functionDistance, factor, offset, isUnipolar, \
            isAbsolute, isAscending = approximationResult.asTuple()
        evaluationMessage = None
        maximumFunctionDistance = \
            _ConfigurationManager._maximumNormalizedRootMeanSquareError

        if curveKind is None:
            evaluationMessage = ("%s: no approximation found for %s"
                                 % (objectName, generatorKindString))
        elif functionDistance > maximumFunctionDistance:
            evaluationMessage = \
                (("%s: skipped approximation for %s because"
                  + " function distance %.3f is greater than %.3f")
                 % (objectName, generatorKindString,
                    functionDistance, maximumFunctionDistance))
        else:
            isInstrument = objectKind == SoundFontObjectKind.instrument
            factorAdaptationProc = \
                SFGA.wordFromRealProc(generatorKind, isInstrument)

            try:
                adaptedFactor = factorAdaptationProc(factor)
            except Exception as exception:
                evaluationMessage = \
                    (("%s: adaptation of factor %s for %s"
                      + " was not possible")
                     % (objectName, factor, generatorKindString))
                adaptedFactor = None

            if adaptedFactor is None or adaptedFactor <= 0:
                evaluationMessage = ("%s: cannot use adapted factor %s for %s"
                                     % (objectName,
                                        adaptedFactor, generatorKindString))
            else:
                messageTemplate = \
                    ("data for generator kind '%s' can be provided by"
                     + " a global modulator"
                     + " (controllerKind = '%s',"
                     + " isUnipolar = %s, isAscending = %s, curveKind = %s,"
                     + " factor = %.3f (=> %s), isAbsolute = %s)"
                     + " and offset = %.3f; with an overall function"
                     + " distance of %.4f, new function = %s")
                ODFFI = OneDimensionalFunctionFromIntervals
                newFunction = \
                    ODFFI.make(intervalFunction.domainValueList(),
                               factor, offset,
                               isUnipolar, isAscending, curveKind, isAbsolute)
                newFunctionAsString = \
                    self._makeComparativeString(newFunction, intervalFunction)

                message = (messageTemplate
                           % (generatorKindString,
                              controllingParameter,
                              isUnipolar, isAscending, curveKind,
                              factor, adaptedFactor, isAbsolute,
                              offset,
                              functionDistance, newFunctionAsString))
                self._addMessage(objectKind, objectName, message)
                evaluationMessage = message

        if evaluationMessage is not None:
            Logging.trace("--: EVALUATION - %s", evaluationMessage)

        Logging.trace("<<")

    #--------------------

    def _analyse2DFunctionForModulator \
            (self : Object,
             objectKind : SoundFontObjectKind,
             objectName : String,
             generatorKind : SoundFontGeneratorKind,
             function : TwoDimensionalFunctionFromIntervals):
        """Checks whether <function> from key range and velocity range
           to value can be implemented by a modulator"""

        generatorKindString = generatorKind.toShortString()
        Logging.trace(">>: objectName = '%s', generatorKind = %s,"
                      + " function = %s",
                      objectName, generatorKindString, function)

        relevantFunction = None
        comparisonMarginForOneDFunctions = \
            int(100 * _ConfigurationManager._comparisonMarginForOneDFunctions)

        if function.isOneDimensional(comparisonMarginForOneDFunctions):
            relevantFunction = function
            parameter = "velocity"
        else:
            otherFunction = function.flip()

            if otherFunction.isOneDimensional(comparisonMarginForOneDFunctions):
                relevantFunction = otherFunction
                parameter = "key"

        if relevantFunction is not None:
            firstInterval = relevantFunction.domainValueList()[0]
            oneDimensionalFunction = relevantFunction.at(firstInterval)
            Logging.trace("--: function ('%s', %s)  only depends"
                          + " on %s: %s",
                          objectName, generatorKindString, parameter,
                          oneDimensionalFunction)

            self._analyse1DFunctionForModulator(objectKind,
                                                objectName,
                                                parameter,
                                                generatorKind,
                                                oneDimensionalFunction)

        Logging.trace("<<")

    #--------------------

    def _checkForPossibleGlobalZoneOverrides \
                        (self : Object,
                         objectKind : SoundFontObjectKind,
                         zonedObjectList : SoundFontZonedElementList):
        """Checks whether there are identical settings in the
           non-global zones of some object in <zonedObjectList> that
           can be generalized to the global zone"""

        Logging.trace(">>: objectKind = '%s', listCount = %d",
                      objectKind, len(zonedObjectList))

        messageTemplate = "data for '%s' can be moved to global zone"
        ruleName = "%sGlobalZone" % objectKind
        valueGeneratorKindList = \
            _ruleNameToGeneratorKindListMap[ruleName]
        _ConfigurationManager \
            .adaptGeneratorKindList(ruleName, valueGeneratorKindList)

        for zonedObject in zonedObjectList:
            objectName = zonedObject.name
            Logging.trace("--: analyzing %s '%s'",
                          objectKind, objectName)

            if len(zonedObject.zoneList) < 2:
                Logging.trace("--: skipped, because there are less"
                              + " than two non-global zones")
                continue

            for generatorKind in valueGeneratorKindList:
                if generatorKind in _partnerGeneratorKindList:
                    # those kinds identify a non-global zone and
                    # must not be consolidated
                    continue

                valueList = \
                    self._collectZoneValuesAsList(zonedObject,
                                                  generatorKind)

                if len(valueList) == 0:
                    continue

                firstValue = valueList[0]
                hasIdenticalValues = \
                    all([ value == firstValue for value in valueList ])

                Logging.trace("--: valueList = %s, isEqual = %s",
                              valueList, hasIdenticalValues)

                if hasIdenticalValues:
                    message = \
                        messageTemplate % generatorKind.toShortString()
                    self._addMessage(objectKind, objectName, message)

        Logging.trace("<<")

    #--------------------

    def _checkForPossibleZoneModulations \
            (self : Object,
             objectKind : SoundFontObjectKind,
             zonedObjectList : SoundFontZonedElementList):
        """Checks whether there are settings in the non-global zones
           of some object in <zonedObjectList> that can be generalized
           via a modulator"""

        Logging.trace(">>: objectKind = '%s', listCount = %d",
                      objectKind, len(zonedObjectList))

        ruleName = "%sModulators" % objectKind
        valueGeneratorKindList = \
            _ruleNameToGeneratorKindListMap[ruleName]
        _ConfigurationManager \
            .adaptGeneratorKindList(ruleName, valueGeneratorKindList)

        for zonedObject in zonedObjectList:
            objectName = zonedObject.name
            Logging.trace("--: analyzing %s '%s'", objectKind, objectName)

            if len(zonedObject.zoneList) < 4:
                Logging.trace("--: skipped, because there are less than"
                              + " four non-global zones")
                continue

            for generatorKind in valueGeneratorKindList:
                function = \
                    self._collectZoneValuesAs2DFunction(zonedObject,
                                                        generatorKind)

                if (function.isEmpty()
                    or function.isConstant()
                    or not function.isConsistent()):
                    Logging.trace("--: function is empty, constant"
                                  + " or inconsistent")
                else:
                    self._analyse2DFunctionForModulator(objectKind,
                                                        objectName,
                                                        generatorKind,
                                                        function)

        Logging.trace("<<")

    #--------------------

    def _collectZoneValuesAsList \
            (self : Object,
             zonedObject : SoundFontZonedElement,
             valueGeneratorKind : SoundFontGeneratorKind) -> ObjectList:
        """Collects values for <generatorKind> from non-global zones
           for <zonedObject> into object list and returns it"""

        Logging.trace(">>: zonedObject = '%s', valueGeneratorKind = '%s'",
                      zonedObject.name, valueGeneratorKind)

        globalZone = zonedObject.globalZone
        zoneList   = zonedObject.zoneList

        getValue = lambda x, kind: x.generatorMap.get(kind)
        globalValue = (None if globalZone is None
                       else getValue(globalZone, valueGeneratorKind))
        valueList = [ getValue(zone, valueGeneratorKind)
                      for zone in zoneList ]
        hasValues = any([ value is not None for value in valueList])

        if not hasValues:
            Logging.trace("--: no values in zones")
            result = []
        else:
            Logging.trace("--: original values = %s", valueList)
            update = lambda x: x if x is not None else globalValue
            result = list(map(update, valueList))

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def _collectZoneValuesAs2DFunction \
            (self : Object,
             zonedObject : SoundFontZonedElement,
             valueGeneratorKind : SoundFontGeneratorKind) \
             -> TwoDimensionalFunctionFromIntervals:
        """Collects values for <generatorKind> from non-global zones
           for <zonedObject> into a 2D function object and returns it"""

        Logging.trace(">>: zonedObject = '%s', valueGeneratorKind = '%s'",
                      zonedObject.name, valueGeneratorKind)

        getValue   = lambda x, kind: x.generatorMap.get(kind)
        adaptValue = (lambda x, default:
                      default if x is None else x)

        globalZone = zonedObject.globalZone
        zoneList   = zonedObject.zoneList

        keyRangeKind      = SoundFontGeneratorKind.keyRange
        velocityRangeKind = SoundFontGeneratorKind.velRange
        fullRange = (0, 127)

        globalKeyRange = \
            adaptValue((None if globalZone is None
                        else getValue(globalZone, keyRangeKind)),
                       fullRange)
        globalVelocityRange = \
            adaptValue((None if globalZone is None
                        else getValue(globalZone, velocityRangeKind)),
                       fullRange)
        globalValue = \
            adaptValue(getValue(globalZone, valueGeneratorKind), None)

        result = TwoDimensionalFunctionFromIntervals()

        for zone in zoneList:
            keyRange = \
                adaptValue(getValue(zone, keyRangeKind), globalKeyRange)
            velocityRange = \
                adaptValue(getValue(zone, velocityRangeKind),
                           globalVelocityRange)
            value = \
                adaptValue(getValue(zone, valueGeneratorKind), globalValue)

            if value is not None:
                result.setAt(keyRange, velocityRange, value)
            else:
                result.clear()
                break

        result.consolidate()

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def _combinedZoneList (self : Object,
                           isPresetList : Boolean) -> SoundFontZoneList:
        """Returns list of all zones either for presets or instruments
           (depending on <isPresetList>"""

        Logging.trace(">>: isPresetList = %s", isPresetList)

        zonedElementList = iif(isPresetList,
                               self._soundFont.presetList,
                               self._soundFont.instrumentList)
        result = []

        for zonedElement in zonedElementList:
            result.extend(zonedElement.zoneList)

        Logging.trace("<<: count = %d", len(result))
        return result

    #--------------------

    def _makeComparativeString \
            (self : Object,
             functionA : OneDimensionalFunctionFromIntervals,
             functionB : OneDimensionalFunctionFromIntervals) -> String:
        """Returns a string with values of <functionA> and <functionB>
           combined for a comparison; assumes that the domain of both
           functions is identical"""

        Logging.trace(">>")

        result = ""

        for domainValue in functionA.domainValueList():
            result += ("%s%d..%d : %.3f (for %.3f)"
                       % (iif(result == "", "", ", "),
                          domainValue[0], domainValue[1],
                          functionA.at(domainValue),
                          functionB.at(domainValue)))

        result = "{ %s }" % result
       
        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def _scanForRedundantValues (self : Object,
                                 objectKind : SoundFontObjectKind,
                                 zoneList : SoundFontZoneList,
                                 partnerGeneratorKind : SoundFontGeneratorKind,
                                 valueGeneratorKind : SoundFontGeneratorKind):
        """Analyses zones in <zoneList> for identical values for
           <valueGeneratorKind> referencing underlying elements
           characterized by <partnerGeneratorKind> and reports any
           redundancies"""

        Logging.trace(">>: objectKind = '%s', zoneCount = %d,"
                      + " partnerGeneratorKind = %s,"
                      + " valueGeneratorKind = %s",
                      objectKind, len(zoneList),
                      partnerGeneratorKind, valueGeneratorKind)

        # collect value set for value generator kind grouped by
        # partner
        identificationToValueSetMap = {}
        identificationToUsageCountMap = {}
        idSeparator = " "
        undefinedValue = -1E10
        defaultValue = valueGeneratorKind.defaultValue()

        for zone in zoneList:
            associatedGlobalZone = zone.parent.globalZone
            generatorMap = zone.generatorMap
            value = generatorMap.get(valueGeneratorKind, defaultValue)

            if value is not None:
                partner = generatorMap.get(partnerGeneratorKind)

                if partner is None:
                    continue

                identification = partner.identification

                if identification in identificationToValueSetMap:
                    identificationToUsageCountMap[identification] += 1
                else:
                    identificationToValueSetMap[identification] = set()
                    identificationToUsageCountMap[identification] = 1

                valueSet = identificationToValueSetMap[identification]

                if (associatedGlobalZone is not None
                    and associatedGlobalZone.generatorMap is not None):
                    globalGeneratorMap = associatedGlobalZone.generatorMap
                    globalValue = globalGeneratorMap.get(valueGeneratorKind)

                    if globalValue is not None and globalValue != value:
                        # value overrides global value, hence generate
                        # some dummy value for the value set
                        Logging.trace("--: override of global value")
                        value = undefinedValue
                
                valueSet.add(value)

        Logging.trace("--: identificationToValueSetMap = %s",
                      identificationToValueSetMap)

        # check for single valued sets that may be transferred to
        # underlying partner
        messageTemplate = ("all %d usage(s) have identical values"
                           + " for '%s' - %r")
        messageCount = 0

        for identification, valueSet in identificationToValueSetMap.items():
            if len(valueSet) == 1:
                value = list(valueSet)[0]

                if value not in (undefinedValue, defaultValue):
                    usageCount = identificationToUsageCountMap[identification]
                    partner = (_SoundFontIdentifiedElement
                               .getByIdentification(identification))
                    message = (messageTemplate
                            % (usageCount,
                               valueGeneratorKind.toShortString(), value))
                    self._addMessage(partner.elementKind, partner.name,
                                     message)
                    messageCount += 1

        Logging.trace("<<: number of messages = %d", messageCount)

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object,
                  soundFont : SoundFont):
        """Initializes analyser <self> for <soundFont>"""

        Logging.trace(">>")

        self._soundFont = soundFont
        self._nameToMessageListMap = {}

        Logging.trace("<<")

    #--------------------
    # access
    #--------------------

    def getResults (self : Object,
                    outputIsPrettyPrinted : Boolean) -> StringList:
        """Returns line list with analysis results"""

        Logging.trace(">>: outputIsPrettyPrinted = %s",
                      outputIsPrettyPrinted)

        result = []

        kindToPosition = lambda x: iif3(x == "header", 0,
                                        x == "sample", 1,
                                        x == "instrument", 2, 3)
        keyToPosition = lambda x: (kindToPosition(x[0]), str(x[1]))
        keyList = sorted(self._nameToMessageListMap.keys(),
                         key = keyToPosition)

        previousObjectKind = ""
        indentation = " " * 4

        for key in keyList:
            objectKind, objectName = key
            messageList = self._nameToMessageListMap[key]

            if outputIsPrettyPrinted:
                if previousObjectKind != objectKind:
                    previousObjectKind = objectKind

                    line = ("=== %s%s ==="
                            % (objectKind.upper(),
                               "S" if objectKind != "header" else ""))
                    result.append(line)

                result.append("%s%s" % (indentation, objectName))

            for message in messageList:
                if not outputIsPrettyPrinted:
                    line = "%s '%s': %s" % (objectKind, objectName, message)
                else:
                    line = indentation * 2 + message

                result.append(line)
                    
        Logging.trace("<<")
        return result
    
    #--------------------
    # rule checkers
    #--------------------

    def checkInstrumentGlobalZone (self : Object):
        """Checks whether there are identical settings in the voice
           zones of an instrument that can be generalized to the
           global zone"""

        Logging.trace(">>")

        ruleName = "instrumentGlobalZone"

        if _ConfigurationManager.ruleIsChecked(ruleName):
            instrumentList = self._soundFont.instrumentList
            self._checkForPossibleGlobalZoneOverrides \
                (SoundFontObjectKind.instrument, instrumentList)

        Logging.trace("<<")

    #--------------------

    def checkInstrumentModulations (self : Object):
        """Checks whether there are settings in the voice zones of an
           instrument that can be generalized via a modulator"""

        Logging.trace(">>")

        ruleName = "instrumentModulators"

        if _ConfigurationManager.ruleIsChecked(ruleName):
            instrumentList = self._soundFont.instrumentList
            self._checkForPossibleZoneModulations \
                (SoundFontObjectKind.instrument, instrumentList)

        Logging.trace("<<")

    #--------------------

    def checkInstrumentOverrideParameters (self : Object):
        """Checks whether there are identical settings in the voice
           zones of a preset that can be applied to the
           underlying instrument"""

        Logging.trace(">>")

        ruleName = "instrumentOverrides"

        if _ConfigurationManager.ruleIsChecked(ruleName):
            presetZoneList = self._combinedZoneList(True)
            partnerGeneratorKind = SFGK.instrument
            valueGeneratorKindList = \
                _ruleNameToGeneratorKindListMap[ruleName]
            _ConfigurationManager \
                .adaptGeneratorKindList(ruleName, valueGeneratorKindList)

            for valueGeneratorKind in valueGeneratorKindList:
                self._scanForRedundantValues(SoundFontObjectKind.instrument,
                                             presetZoneList,
                                             partnerGeneratorKind,
                                             valueGeneratorKind)

        Logging.trace("<<")

    #--------------------

    def checkPresetGlobalZone (self : Object):
        """Checks whether there are identical settings in the voice
           zones of a preset that can be generalized to the global
           zone"""

        Logging.trace(">>")

        ruleName = "presetGlobalZone"
        
        if _ConfigurationManager.ruleIsChecked(ruleName):
            presetList = self._soundFont.presetList
            objectKind = SoundFontObjectKind.preset
            self._checkForPossibleGlobalZoneOverrides(objectKind,
                                                      presetList)

        Logging.trace("<<")

    #--------------------

    def checkPresetModulations (self : Object):
        """Checks whether there are settings in the voice zones of a
           preset that can be generalized via a modulator"""

        Logging.trace(">>")

        ruleName = "presetModulators"

        if _ConfigurationManager.ruleIsChecked(ruleName):
            presetList = self._soundFont.presetList
            self._checkForPossibleZoneModulations \
                (SoundFontObjectKind.preset, presetList)

        Logging.trace("<<")

    #--------------------

    def checkSampleOverrideParameters (self : Object):
        """Checks whether there are identical settings in the voice
           zones of an instrument that can be applied to the
           underlying sample"""

        Logging.trace(">>")

        ruleName = "sampleOverrides"
        
        if _ConfigurationManager.ruleIsChecked(ruleName):
            SFGK = SoundFontGeneratorKind
            instrumentZoneList = self._combinedZoneList(False)
            partnerGeneratorKind = SFGK.sampleID
            valueGeneratorKindList = \
                _ruleNameToGeneratorKindListMap[ruleName]

            _ConfigurationManager \
                .adaptGeneratorKindList(ruleName, valueGeneratorKindList)

            for valueGeneratorKind in valueGeneratorKindList:
                self._scanForRedundantValues("sample",
                                             instrumentZoneList,
                                             partnerGeneratorKind,
                                             valueGeneratorKind)

        Logging.trace("<<")

#====================

def _analyseSoundFont (soundFont : SoundFont,
                       outputIsPrettyPrinted : Boolean) -> StringList:
    """Collects analysis information about <soundFont> in a line list
       and returns it"""

    Logging.trace(">>: outputIsPrettyPrinted = %s",
                  outputIsPrettyPrinted)

    soundFontAnalyser = _SoundFontAnalyser(soundFont)

    soundFontAnalyser.checkSampleOverrideParameters()
    soundFontAnalyser.checkInstrumentGlobalZone()
    soundFontAnalyser.checkInstrumentModulations()
    soundFontAnalyser.checkInstrumentOverrideParameters()
    soundFontAnalyser.checkPresetGlobalZone()

    result = soundFontAnalyser.getResults(outputIsPrettyPrinted)
    
    Logging.trace("<<: lineCount = %d", len(result))
    return result

#--------------------

def _process (soundFontFilePath : String,
              configurationFilePath : String,
              loggingFilePath : String,
              outputIsPrettyPrinted : Boolean):
    """Processes SoundFont file named <soundFontFilePath> and writes
       analysis results to standard output; <loggingFilePath> gives
       the path to the optional logging file, <outputIsPrettyPrinted>
       tells to output in human readable form and
       <configurationFilePath> gives the path of an optional
       configuration file"""

    global _ruleNameToGeneratorKindListMap

    if loggingFilePath is None:
        Logging.setLevel(Logging_Level.noLogging)
    else:
        Logging.setFileName(loggingFilePath)
        Logging.setLevel(Logging_Level.verbose)

    Logging.trace(">>: soundFontFilePath = '%s',"
                  + " configurationFilePath = '%s',"
                  + " loggingFilePath = '%s',"
                  + " outputIsPrettyPrinted = %s",
                  soundFontFilePath, configurationFilePath,
                  loggingFilePath, outputIsPrettyPrinted)

    # read soundfont
    Logging.setLevel(Logging_Level.noLogging)
    soundFontFileReader = SoundFontFileReader(soundFontFilePath)
    soundFont = soundFontFileReader.readSoundFont()
    Logging.setLevel(Logging_Level.verbose)

    # read configuration file (if any)
    if configurationFilePath is not None:
        _ConfigurationManager.read(configurationFilePath)

    # bring all lists in Polyphone order
    for _, value in _ruleNameToGeneratorKindListMap.items():
        SFGK.adaptToPolyphoneOrder(value)
        
    # analyse soundfont
    lineList = _analyseSoundFont(soundFont, outputIsPrettyPrinted)

    # write lines to stdout
    sys.stdout.write(_newline.join(lineList) + _newline)

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

def main ():
    """The main program"""

    _initialize()
    argumentList = _CommandLineOptions.read()
    _CommandLineOptions.checkArguments(argumentList)

    _process(argumentList.soundFontFilePath,
             argumentList.configurationFilePath,
             argumentList.loggingFilePath,
             argumentList.outputIsPrettyPrinted)

    _finalize()

#--------------------
#--------------------

if __name__ == "__main__":
    main()
