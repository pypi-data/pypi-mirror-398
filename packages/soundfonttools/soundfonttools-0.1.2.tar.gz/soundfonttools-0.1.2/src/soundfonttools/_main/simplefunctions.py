# simplefunctions - module implementing functions from intervals to
#                   real values
#
# author: Dr. Thomas Tensi
# version: 2025-08

#====================
# IMPORTS
#====================

import dataclasses
from dataclasses import dataclass
from enum import Enum, IntEnum
import math
import statistics

from basemodules.simpleassertion import Assertion
from basemodules.simplelogging import Logging, Logging_Level
from basemodules.simpletypes import \
    Boolean, Callable, Class, Integer, Natural, Object, ObjectList, \
    Real, RealList, Set, String, Tuple
from basemodules.ttbase import iif, iif2, iif4

#====================

Interval     = Tuple
IntervalList = ObjectList
PairList     = ObjectList

#====================

_meanValue = lambda a, b: (a + b) / 2
_naturalMean = lambda a, b: (a + b) // 2

# value transformation procs (concave, convex, switch); note that
# those functions must be invertible
_concaveProc = \
    lambda x : _sign(x) * (1 - math.sqrt(1 - x ** 2))
_convexProc  = \
    lambda x : _sign(x) * math.sqrt(1 - (1 - abs(x)) ** 2)
_linearProc  = \
    lambda x : x

# replace non-invertible staircase function by a slowly ascending
# staircase
#_switchProc  = (lambda x, isUnipolar:
#                -1 if x < 0 else 0 if isUnipolar and x < 0.5 else 1)

_switchGradient = 1E-6
_switchProc  = \
    (lambda x, isUnipolar:
     1 - (1.0 - x) * _switchGradient if not isUnipolar and x >= 0
     else -1 + (1.0 + x) * _switchGradient if not isUnipolar
     else 2 * x * _switchGradient if x < 0.5
     else 1 - (2 - 2 * x) * _switchGradient)

#====================

def _sign (x : Real) -> Integer:
    """Returns the sign of <x>"""

    result = iif2(x > 0, +1,
                  x < 0, -1,
                  0)
    return result

#--------------------

def _intervalToNatural (interval : Interval) -> Natural:
    """Returns a natural value representing <interval>"""

    return interval[0] * 256 + interval[1]
    
#--------------------

def _makeContiguousSet (interval : Interval) -> Set:
    """Makes a contiguous integer set from integer pair <interval>"""

    return set(range(interval[0], interval[1] + 1))

#--------------------

def _transformXOntoRange (isUnipolar : Boolean,
                          isAscending : Boolean,
                          x : Natural) -> Real:
    """Transforms <x> onto -1..1 or 0..1 range taking into account the
       orientation of interpolation (when gradient is negative);
       ensure that the half-open intervals are correctly respected"""

    lastDomainValue = iif(isUnipolar, 127/128, 63/64)
    result = iif2(isAscending, x,
                  isUnipolar, lastDomainValue - x,
                  lastDomainValue - (x + 1))
    return result

#====================
# ENUMERATION TYPES
#====================

class ModulatorFunctionKind (IntEnum):
    """the direction kinds of a modulator functions"""

    linear  = 0
    concave = 1
    convex  = 2
    switch  = 3
    unknown = 4
    
    #--------------------
    # type conversion
    #--------------------

    __repr__ = lambda x: Enum.__str__(x).split(".")[-1]
    __str__ = __repr__

    #--------------------

    @classmethod
    def make (cls : Class,
              isLinear : Boolean,
              isConcave : Boolean,
              isConvex : Boolean,
              isSwitch : Boolean) -> Object:
        """Returns modulator function kind based on <isLinear>,
           <isConcave>, <isConvex> and <isSwitch>"""

        Logging.trace(">>: isLinear = %s, isConcave = %s,"
                      + " isConvex = %s, isSwitch = %s",
                      isLinear, isConcave, isConvex, isSwitch)

        result = iif4(isLinear, cls.linear, isConcave, cls.concave,
                      isConvex, cls.convex, isSwitch,  cls.switch,
                      cls.unknown)
        
        Logging.trace("<<: %s", result)
        return result

#====================

# mapping from isUnipolar and modulator kind to associated
# transformation proc
_kindToTransformationProcMap = {
    ModulatorFunctionKind.linear  : _linearProc,
    ModulatorFunctionKind.concave : _concaveProc,
    ModulatorFunctionKind.convex  : _convexProc,
    ModulatorFunctionKind.switch  : _switchProc
}

#====================
# CLASS TYPES
#====================

@dataclass(frozen=True)
class ApproximationResult:
    """Represents the result of an approximation of a function"""

    kind        : ModulatorFunctionKind = None
    distance    : Real                  = 0.0
    factor      : Real                  = 0.0
    offset      : Real                  = 0.0
    isUnipolar  : Boolean               = False
    isAbsolute  : Boolean               = False
    isAscending : Boolean               = False

    #--------------------

    def __repr__ (self : Object) -> String:
        """Returns string representation of <self>"""

        clsName = self.__class__.__name__
        template = \
            ("kind = %s, distance = %f, factor = %f, offset = %f,"
             + " isUnipolar = %s, isAbsolute = %s, isAscending = %s")
        st = "%s(%s)" % (clsName, template % self.asTuple())
        return st

    #--------------------

    def asTuple (self : Object) -> Tuple:
        """Returns tuple representation of <self>"""

        return dataclasses.astuple(self)

#====================

class _Function:
    """The base class for all functions with arbitrary hashable
       objects as arguments"""

    #--------------------
    # PROTECTED FEATURES
    #--------------------

    def _at (self : Object,
            domainValue : Object) -> Object:
        """Returns value at <domainValue> (without logging)"""

        return self._dataMap.get(domainValue)
    
    #--------------------

    def _setAt (self : Object,
                domainValue : Object,
                value : Real):
        """Sets value for a function at <domainValue> to
           some real <value> (without logging)"""

        self._domainValueSet.add(domainValue)
        self._dataMap[domainValue] = value

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object):
        """Sets up a function as a map"""

        Logging.trace(">>")
        self._domainValueSet = set()
        self._dataMap = {}
        Logging.trace("<<")

    #--------------------
    # type conversion
    #--------------------

    def __str__ (self : Object) -> String:
        """Returns string representation of <self>"""

        clsName = self.__class__.__name__
        st = "%s(data = %s)" % (clsName, self.asRawString())
        return st

    #--------------------

    def asRawString (self : Object) -> String:
        """Returns string representation of <self> without class
           information"""

        return "{}"

    #--------------------
    # access
    #--------------------

    def at (self : Object,
            domainValue : Object) -> Object:
        """Returns value at <domainValue>"""

        Logging.trace(">>: %s", domainValue)
        result = self._at(domainValue)
        Logging.trace("<<: %s", result)
        return result
    
    #--------------------
    # comparison
    #--------------------
 
    def isEqual (self : Object,
                 other : Object,
                 marginPercentage : Natural = 0) -> Boolean:
        """Tells whether current function and <other> have the same
           values (allowing for some margin given as percentage value
           <marginPercentage>)"""

        Logging.trace(">>: margin = %d%%", marginPercentage)

        dataMap = self._dataMap
        otherDataMap = other._dataMap
        result = True

        if len(dataMap) != len(otherDataMap):
            result = False
        else:
            factor = (1 - marginPercentage / 100.0, 
                           1 + marginPercentage / 100.0)

            for domainValue, value in dataMap.items():
                if domainValue not in otherDataMap:
                    Logging.trace("--: domain value not found for"
                                  + " partner: %s",
                                  domainValue)
                    result = False
                else:
                    otherValue = otherDataMap[domainValue]

                    if (otherValue > value * factor[1]
                        or otherValue < value * factor[0]):
                        Logging.trace("--: values for %s are too far"
                                      + " apart: %s, %s",
                                      domainValue, value, otherValue)
                        result = False

                if not result:
                    break

        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # measurement
    #--------------------

    def isEmpty (self : Object) -> Boolean:
        """Tells whether <self> is empty"""

        Logging.trace(">>")
        result = len(self._domainValueSet) == 0
        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def hasUnipolarData (self : Object) -> Boolean:
        """Tells whether <self> has neither a negative start or end"""

        domainValueSet = self._domainValueSet
        Assertion.pre(len(domainValueSet) > 0,
                      "function must be non-empty")
        Logging.trace(">>")

        domainValueList = list(sorted(self._domainValueSet))
        xFirst = domainValueList[0]
        xLast  = domainValueList[-1]
        yFirst = self._dataMap[xFirst]
        yLast  = self._dataMap[xLast]
        result = _sign(yFirst) != -1 and _sign(yLast) != -1

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def domainValueCount (self : Object) -> Natural:
        """Tells the number of values in the domain of <self>"""

        Logging.trace(">>")
        result = len(self._domainValueSet)
        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def domainValueList (self : Object) -> ObjectList:
        """Tells whether <self> is a constant function"""

        # Logging.trace(">>")
        result = list(sorted(self._domainValueSet))
        # Logging.trace("<<: %s", result)
        return result

    #--------------------

    def itemList (self : Object) -> PairList:
        """Returns the list of all values"""

        Logging.trace(">>")

        dataMap = self._dataMap
        domainValueList = list(sorted(self._domainValueSet))
        result = [ (domainValue, dataMap[domainValue])
                   for domainValue in domainValueList ]
        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def valueList (self : Object) -> RealList:
        """Returns the list of all values"""

        Logging.trace(">>")
        result = [ value for _, value in self._dataMap.items() ]
        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # change
    #--------------------

    def clear (self : Object):
        """Makes an empty function"""

        Logging.trace(">>")
        self._domainValueSet.clear()
        self._dataMap.clear()
        Logging.trace("<<")

    #--------------------

    def setAt (self : Object,
               domainValue : Object,
               value : Real):
        """Sets value for a function at <domainValue> to
           some real <value>"""

        # Logging.trace(">>: domainValue = %s, value = %s",
        #               domainValue, value)
        self._setAt(domainValue, value)
        # Logging.trace("<<")

#====================

class OneDimensionalFunctionFromNumbers (_Function):
    """A one dimensional function from one number variable to a real
       value"""

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object):
        """Sets up a one-dimensional function from intervals to some
           real value"""

        Logging.trace(">>")
        super().__init__()
        Logging.trace("<<")

    #--------------------

    @classmethod
    def make (cls : Class,
              domainValueList : RealList,
              factor : Real,
              offset : Real,
              kind : ModulatorFunctionKind,
              isAbsolute : Boolean,
              isAscending : Boolean) -> Object:
        """Makes a number function for <domainValueList> with
           <factor>, <offset> using characteristics <kind> and
           <isAbsolute> and <isAscending>"""

        Logging.trace(">>: domainValueList = %s,"
                      + " factor = %.3f, offset = %.3f,"
                      + " kind = %s, isAbsolute = %s, isAscending = %s",
                      domainValueList, factor, offset,
                      kind, isAbsolute, isAscending)

        result = cls()
        isUnipolar = domainValueList[0] >= 0.0

        for x in domainValueList:
            effectiveX = \
                _transformXOntoRange(isUnipolar, isAscending, x)

            if kind == ModulatorFunctionKind.linear:
                pass
            elif kind == ModulatorFunctionKind.concave:
                effectiveX = _concaveProc(effectiveX)
            elif kind == ModulatorFunctionKind.convex:
                effectiveX = _convexProc(effectiveX)
            elif kind == ModulatorFunctionKind.switch:
                effectiveX = _switchProc(effectiveX, isUnipolar)

            y = (abs(factor * effectiveX) + offset if isAbsolute
                 else factor * effectiveX + offset)
            result.setAt(x, y)

        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # type conversion
    #--------------------

    def asRawString (self : Object) -> String:
        """Returns string representation of <self> without class
           information"""

        st = ""

        for domainValue, value in self._dataMap.items():
            st += (iif(st == "", "", ", ")
                   + "%4.3f: %7.3f" % (domainValue, value))

        st = "{ %s }" % st
        return st

    #--------------------
    # measurement
    #--------------------

    def distance (self : Object,
                  other : Object) -> Real:
        """Returns root mean square error difference between <self>
           and <other>"""

        Logging.trace(">>")

        domainValueListA = self.domainValueList()
        domainValueListB = other.domainValueList()
        domainValuePairList = zip(domainValueListA, domainValueListB)
        domainValueCount = len(domainValueListA)

        valueDistance = lambda a, b: (a - b)**2
        meanSquareError = \
            (sum([ valueDistance(self._at(x1), other._at(x2))
                   for x1, x2 in domainValuePairList ])
             / domainValueCount)
        rootMeanSquareError = math.sqrt(meanSquareError)
        stdDev = statistics.stdev(self.valueList())
        stdDev = max(stdDev, 1.0E-10)
        result = rootMeanSquareError / stdDev
        
        Logging.trace("<<: result = %f (rmse = %f, stdDev = %f)",
                      result, rootMeanSquareError, stdDev)
        return result

    #--------------------
    # transformation
    #--------------------

    def makeMirroredPartner (self : Object) -> Tuple:
        """Returns bipolar partner function for <self> where the
           function is shifted down such that the function touches the
           x-axis for the mid value and then the left half is mirrored
           at the x-axis; returns tuple of function and vertical
           shift;if for some reason this cannot be done, none is
           returned"""

        Logging.trace(">>")

        result = (None, None)
        domainValueList = self.domainValueList()
        midX = 0.0

        if midX in domainValueList:
            yOffset = self.at(midX)
            partnerFunction = OneDimensionalFunctionFromNumbers()

            for x, y in self.itemList():
                y -= yOffset
                y = -y if x < midX else y
                partnerFunction.setAt(x, y)

            result = (partnerFunction, yOffset)

        Logging.trace("<<: function = %s, yOffset = %s",
                      result[0], result[1])
        return result
        
#====================

class _Regression:
    """Does a linear, concave, convex or switch regression on a
       numerical function"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    @classmethod
    def _fitLinear (cls : Class,
                    function : OneDimensionalFunctionFromNumbers) -> Tuple:
        """Does a linear fit on function and returns tuple of
           parameters factor, offset and isAscending; factor
           is none, when no fit can be done"""

        Logging.trace(">>")

        domainValueList = function.domainValueList()
        valueList       = function.valueList()
        factor, offset, isAscending = None, None, None

        n = len(domainValueList)

        if n < 2:
            Logging.trace("--: no fit possible for function %s", function)
        else:
            xBar = sum(domainValueList) / n
            yBar = sum(valueList) / n

            itemList = function.itemList()
            partialProduct = sum([(y - yBar) * (x - xBar)
                                  for x, y in itemList ])
            squaredSum = sum([ (x - xBar)**2 for x in domainValueList ])
            factor = partialProduct / squaredSum
            Logging.trace("--: xBar = %f, yBar = %f,"
                          + " partialProduct = %f, squaredSum = %f,"
                          + " factor = %f",
                          xBar, yBar, partialProduct, squaredSum, factor)

            isAscending = factor >= 0.0
            factor = abs(factor)
            offset = yBar - xBar * factor

        result = (factor, offset, isAscending)

        Logging.trace("<<: factor = %s, offset = %s, isAscending = %s",
                      factor, offset, isAscending)
        return result

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    @classmethod
    def fit (cls : Class,
             function : OneDimensionalFunctionFromNumbers,
             transformationProc : Callable) -> Tuple:
        """Does a fit on function with x-values transformed by
           <transformationProc>; returns tuple of parameters factor,
           offset, and isAscending; factor is none, when no fit can be
           done"""

        Logging.trace(">>")

        newFunction = OneDimensionalFunctionFromNumbers()
        tempMap = {}

        for x, y in function.itemList():
            transformedX = transformationProc(x)
            tempMap[x] = transformedX
            newFunction.setAt(transformedX, y)

        Logging.trace("--: TRANSFORM = %r", tempMap)
        result = cls._fitLinear(newFunction)
        factor, offset, isAscending = result

        Logging.trace("<<: factor = %s, offset = %s, isAscending = %s",
                      factor, offset, isAscending)
        return result

#====================

_ODFFN = OneDimensionalFunctionFromNumbers

#====================

class OneDimensionalFunctionFromIntervals (_Function):
    """A one dimensional function from one interval variable to a real
       value"""

    #--------------------
    # PRIVATE FEATURES
    #--------------------

    @classmethod
    def _findBestApproximationResult \
            (cls : Class,
             approximationResultList : ObjectList) -> ApproximationResult:
        """Returns best approximation match by scanning
           <approximationResultList> returning a tuple of (factor,
           offset, isAscending, kind, isAbsolute); sets factor to None
           when approximation fails"""

        Logging.trace(">>: %r", approximationResultList)

        # store the bipolar approximations for linear and switch just
        # in case some corresponding unipolar version is identified as
        # the best fit; then the version with a positive offset is
        # used (if required)
        ambiguousKindList = (ModulatorFunctionKind.linear,
                             ModulatorFunctionKind.switch)
        isBipolarApproximation = \
            lambda a: (not a.isUnipolar
                       and not a.isAbsolute
                       and a.kind in ambiguousKindList)
        firstResult = lambda x: None if len(x) == 0 else x[0]
        bipolarApproximationList = list(filter(isBipolarApproximation,
                                               approximationResultList))
        bipolarApproximationMap = { bpa.kind : bpa
                                    for bpa in bipolarApproximationList }

        if len(approximationResultList) == 0:
            result = ApproximationResult()
        else:
            result = min(approximationResultList,
                         key = lambda a: a.distance)

            # check whether this is an unipolar result for a switch or
            # linear approximation with negative offset and possibly
            # replace it with corresponding bipolar result
            if result.isUnipolar and result.offset < 0:
                partnerResult = bipolarApproximationMap.get(result.kind)

                if partnerResult is None:
                    Logging.trace("--: no partner for unipolar"
                                  + " approximation")
                elif partnerResult.offset <= result.offset:
                    Logging.trace("--: partner also has negative"
                                  + " offset: %s",
                                  partnerResult)
                else:
                    Logging.trace("--: unipolar approximation replaced"
                                  + " by bipolar version: %s", result)
                    result = partnerResult

        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object):
        """Sets up a one-dimensional function from intervals to some
           real value"""

        Logging.trace(">>")
        super().__init__()
        Logging.trace("<<")

    #--------------------

    @classmethod
    def make (cls : Class,
              intervalList : IntervalList,
              factor : Real,
              offset : Real,
              isUnipolar : Boolean,
              isAscending : Boolean,
              kind : ModulatorFunctionKind,
              isAbsolute : Boolean) -> Object:
        """Makes a interval function from <intervalList> containing
           pairs of non-negative byte values with <factor>, <offset>
           using characteristics <isUnipolar>, <isAscending>, <kind>
           and <isAbsolute>"""

        Logging.trace(">>: intervalList = %s,"
                      + " factor = %.3f, offset = %.3f,"
                      + " isUnipolar = %s, isAscending = %s, kind = %s,"
                      + " isAbsolute = %s",
                      intervalList, factor, offset,
                      isUnipolar, isAscending, kind, isAbsolute)

        result = cls()
        MFK = ModulatorFunctionKind

        for interval in intervalList:
            x = _naturalMean(interval[0], interval[1])
            x /= 128
            originalX = x
            x = iif(isUnipolar, x, 2 * x - 1)
            x = _transformXOntoRange(isUnipolar, isAscending, x)

            if kind == MFK.linear:
                pass
            elif kind == MFK.concave:
                x = _concaveProc(x)
            elif kind == MFK.convex:
                x = _convexProc(x)
            elif kind == MFK.switch:
                x = _switchProc(x, isUnipolar)

            y = offset + iif(isAbsolute, abs(factor * x), factor * x)
                 
            Logging.trace("--: originalX = %f, x = %f, y = %f",
                          originalX, x, y)
            result.setAt(interval, y)
        
        Logging.trace("<<: %s", result)
        return result
        
    #--------------------
    # type conversion
    #--------------------

    def asRawString (self : Object) -> String:
        """Returns string representation of <self> without class
           information"""

        st = ""

        for interval, value in self._dataMap.items():
            valueAsString = ("%.3f" % value if isinstance(value, float)
                             else str(value))
            st += (iif(st == "", "", ", ")
                   + "%03d..%03d: " % interval
                   + valueAsString)

        st = "{ %s }" % st
        return st

    #--------------------

    def toNumberFunction (self : Object,
                          isUnipolar : Boolean = True) \
            -> OneDimensionalFunctionFromNumbers:
        """Returns function from [0..1) or [-1..1) to real using the
           intervals in the domain"""

        Logging.trace(">>: %s, isUnipolar = %s", self, isUnipolar)

        result = OneDimensionalFunctionFromNumbers()

        for interval, y in self._dataMap.items():
            for domainValue in range(interval[0], interval[1] + 1):
                x = iif(isUnipolar, domainValue / 128, domainValue / 64 - 1)
                result._setAt(x, y)

        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # measurement
    #--------------------

    @classmethod
    def approximate (cls : Class,
                     intervalFunction : Object) -> ApproximationResult:
        """Approximate <intervalFunction> by soundfont modulator
           settings returning a tuple of (factor, offset, isAscending,
           kind, isAbsolute); sets all entries of result to None when
           approximation fails"""

        Logging.trace(">>")

        unipolarFunction = intervalFunction.toNumberFunction(True)
        bipolarFunction  = intervalFunction.toNumberFunction(False)
        partnerFunction, bpOffset = bipolarFunction.makeMirroredPartner()

        functionList = [ unipolarFunction, bipolarFunction ]

        if partnerFunction is not None:
            functionList.append(partnerFunction)

        approximationResultList = []

        for i, function in enumerate(functionList):
            hasUnipolarDomain = (i == 0)
            isPartnerFunction = (i == 2)
            Logging.trace("--: approximation for %spolar %s function",
                          iif(hasUnipolarDomain, "uni", "bi"),
                          iif(isPartnerFunction, "partner", "normal"))
            domainValueList = function.domainValueList()

            for kind, transformationProc \
                    in _kindToTransformationProcMap.items():
                Logging.trace("--: approximate for kind %s", kind)

                if kind == ModulatorFunctionKind.switch:
                    if isPartnerFunction:
                        # switch does not work for absolute value
                        # transformation
                        continue
                    else:
                        transformationProc = \
                            lambda x: _switchProc(x, hasUnipolarDomain)

                factor, offset, isAscending = \
                    _Regression.fit(function, transformationProc)

                if factor is None:
                    Logging.trace("--: no fit for kind %s", kind)
                else:
                    Logging.trace("--: fit for kind %s", kind)
                    isAbsolute = isPartnerFunction
                    offset = iif(isPartnerFunction, bpOffset, offset)
                    calculatedFunction = \
                        _ODFFN.make(domainValueList, factor, offset,
                                    kind, isAbsolute, isAscending)
                    distance = unipolarFunction.distance(calculatedFunction)

                    if distance is not None:
                        approximationResult = \
                            ApproximationResult(kind, distance, factor,
                                                offset, hasUnipolarDomain,
                                                isAbsolute, isAscending)
                        approximationResultList.append(approximationResult)

        result = cls._findBestApproximationResult(approximationResultList)

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def isConstant (self : Object) -> Boolean:
        """Tells whether <self> is a constant function"""

        Logging.trace(">>")

        valueList = self.valueList()

        if len(valueList) == 0:
            result = True
        else:
            firstValue = valueList[0]
            result = \
                all([ value == firstValue for value in valueList ])

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def isConsistent (self : Object) -> Boolean:
        """Tells whether <self> is a consistent function without
           overlaps"""

        Logging.trace(">>")

        isOkay = True
        xValueSet = set()
        
        for interval, value in self._dataMap.items():
            Logging.trace("--: interval = %s", interval)
            rangeSet = _makeContiguousSet(interval)

            if not rangeSet.isdisjoint(xValueSet):
                Logging.trace("--: overlapping data")
                isOkay = False
                break
            else:
                xValueSet.update(rangeSet)

        Logging.trace("<<: %s", isOkay)
        return isOkay

    #--------------------
    # change
    #--------------------

    def consolidate (self : Object):
        """Orders x-intervals in <self>"""

        Logging.trace(">>")

        dataMap = self._dataMap
        tempMap = {}

        xIntervalList = sorted(dataMap.keys(), key = _intervalToNatural)

        for interval in xIntervalList:
            tempMap[interval] = dataMap[interval]

        self._dataMap = tempMap

        Logging.trace("<<")

#====================

class TwoDimensionalFunctionFromIntervals (_Function):
    """A two dimensional function from two interval variables to a
       real value"""

    #--------------------
    # EXPORTED FEATURES
    #--------------------

    def __init__ (self : Object):
        """Sets up a two-dimensional function from one interval to
           a function from an interval to some real value"""

        Logging.trace(">>")
        super().__init__()
        Logging.trace("<<")

    #--------------------

    def asRawString (self : Object) -> String:
        """Returns string representation of <self> without class
           information"""

        st = ""

        for interval, function in self._dataMap.items():
            st += (iif(st == "", "", ", ")
                   + "%03d..%03d: " % interval
                   + function.asRawString())

        st = "{ %s }" % st
        return st

    #--------------------
    # measurement
    #--------------------

    def isConstant (self : Object) -> Boolean:
        """Tells whether <self> is a constant function"""

        Logging.trace(">>")

        valueList = []

        for _, function in self._dataMap.items():
            valueList.extend(function.valueList())

        if len(valueList) == 0:
            result = True
        else:
            firstValue = valueList[0]
            result = \
                all([ value == firstValue for value in valueList ])

        Logging.trace("<<: %s", result)
        return result

    #--------------------

    def isConsistent (self : Object) -> Boolean:
        """Tells whether <self> is a consistent function without
           overlaps"""

        Logging.trace(">>")

        isOkay = True
        xValueSet = set()

        for interval, function in self._dataMap.items():
            Logging.trace("--: interval = %s", interval)
            rangeSet = _makeContiguousSet(interval)

            if not rangeSet.isdisjoint(xValueSet):
                Logging.trace("--: overlapping data")
                isOkay = False
                break
            else:
                xValueSet.update(rangeSet)

                if not function.isConsistent():
                    isOkay = False
                    break

        Logging.trace("<<: %s", isOkay)
        return isOkay

    #--------------------

    def isOneDimensional (self : Object,
                          marginPercentage : Natural = 0) -> Boolean:
        """Tells whether <self> is a function that does not depend on
           its first argument (allowing for some margin given as
           percentage value <marginPercentage>)"""

        Logging.trace(">>: margin = %d%%", marginPercentage)

        dataMap = self._dataMap
        result = True

        if len(dataMap) > 1:
            intervalList = list(dataMap.keys())
            firstInterval = intervalList[0]
            referenceFunction = dataMap[firstInterval].toNumberFunction()

            for interval in intervalList[1:]:
                function = dataMap[interval].toNumberFunction()

                if not function.isEqual(referenceFunction,
                                        marginPercentage):
                    Logging.trace("--: different functions for %s and %s",
                                  firstInterval, interval)
                    result = False
                    break

        Logging.trace("<<: %s", result)
        return result

    #--------------------
    # change
    #--------------------

    def consolidate (self : Object):
        """Orders x-intervals in <self> and the subfunctions"""

        Logging.trace(">>")

        dataMap = self._dataMap
        tempMap = {}

        xIntervalList = sorted(dataMap.keys(), key = _intervalToNatural)

        for interval in xIntervalList:
            function = dataMap[interval]
            function.consolidate()
            tempMap[interval] = function

        self._dataMap = tempMap

        Logging.trace("<<")
    
    #--------------------

    def setAt (self : Object,
               intervalA : Interval,
               intervalB : Interval,
               value : Real):
        """Sets value for a two-dimensional function at <intervalA>
           and <intervalB> to some real <value>"""

        # Logging.trace(">>: intervalA = %s, intervalB = %s, value = %s",
        #               intervalA, intervalB, value)

        dataMap = self._dataMap

        if intervalA in dataMap:
            subFunction = self._at(intervalA)
        else:
            subFunction = OneDimensionalFunctionFromIntervals()
            self._setAt(intervalA, subFunction)

        subFunction.setAt(intervalB, value)

        # Logging.trace("<<")

    #--------------------
    # transformation
    #--------------------

    def flip (self : Object) -> Object:
        """Returns a function with x- and y-coordinate exchanged"""

        Logging.trace(">>")
        result = TwoDimensionalFunctionFromIntervals()

        for intervalA, function in self._dataMap.items():
            for intervalB, value in function._dataMap.items():
                result.setAt(intervalB, intervalA, value)
        
        Logging.trace("<<: %s", result)
        return result
