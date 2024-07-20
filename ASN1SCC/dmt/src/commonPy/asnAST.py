from typing import  Union, Dict, Any  

from . import utility

Lookup = Dict[str, 'AsnNode']
AsnSequenceOrSet = Union['AsnSequence', 'AsnSet']
AsnSequenceOrSetOf = Union['AsnSequenceOf', 'AsnSetOf']


class AsnNode:

    def __init__(self, asnFilename: str ) -> None:
        self._leafType = "unknown"
        self._asnFilename = asnFilename
        self._lineno = -1


    def Location(self) -> str:
        return "file %s, line %d" % (self._asnFilename, int(self._lineno))  

class AsnBasicNode(AsnNode):
    def __init__(self, asnFilename: str) -> None:
        AsnNode.__init__(self, asnFilename)


class AsnComplexNode(AsnNode):
    def __init__(self, asnFilename: str) -> None:
        AsnNode.__init__(self, asnFilename)

#########################################################
# Basic nodes: Bool, Int, Real, UTF8String, OctetString #
#########################################################

class AsnBool(AsnBasicNode):
    '''
This class stores the semantic content of an ASN.1 BOOLEAN.
Members:
    _name : the name of the type (or var)
    _bDefaultValue : one of True,False,None.
'''
    validOptions = ['bDefaultValue', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnBasicNode.__init__(self, args.get('asnFilename', ''))
        self._name = "BOOLEAN"  # default in case of SEQUENCE_OF BOOLEAN
        self._leafType = "BOOLEAN"
        self._lineno = args.get('lineno', None)
        self._bDefaultValue = args.get('bDefaultValue', None)
        for i in args:
            assert i in AsnBool.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._bDefaultValue is not None:
            result += ", default value " + self._bDefaultValue  
        return result


class AsnInt(AsnBasicNode):
    '''
This class stores the semantic content of an ASN.1 INTEGER.
Members:
    _name : the name of the type (or var)
    _range : a tuple containing the valid range for the integer or []
    _iDefaultValue : either None, or the default value for this integer
'''
    validOptions = ['range', 'iDefaultValue', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnBasicNode.__init__(self, args.get('asnFilename', ''))
        self._name = "INTEGER"  # default in case of SEQUENCE_OF INTEGER
        self._leafType = "INTEGER"
        self._lineno = args.get('lineno', None)
        self._range = args.get('range', [])
        self._iDefaultValue = args.get('iDefaultValue', None)
        for i in args:
            assert i in AsnInt.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._range:
            result += " within [%s,%s]" % (self._range[0], self._range[1])
        if self._iDefaultValue is not None:
            result += " with default value of %s" % self._iDefaultValue  
        return result


class AsnReal(AsnBasicNode):
    '''
This class stores the semantic content of an ASN.1 REAL.
Members:
    _name : the name of the type (or var)
    _range : a tuple containing the valid range for the integer or []
    _baseRange,
    _mantissaRange,
    _exponentRange  : single or double element tuples containing
                      the allowed ranges for respective values.
                      Or [].
    _dbDefaultValue : either None, or the default value for this real
'''
    validOptions = ['range', 'mantissa', 'base', 'exponent', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnBasicNode.__init__(self, args.get('asnFilename', ''))
        self._name = "REAL"  # default in case of SEQUENCE_OF REAL
        self._leafType = "REAL"
        self._lineno = args.get('lineno', None)
        self._range = args.get('range', [])
        self._mantissaRange = args.get('mantissa', None)
        self._baseRange = args.get('base', None)
        self._exponentRange = args.get('exponent', None)
        self._dbDefaultValue = args.get('defaultValue', None)
        for i in args:
            assert i in AsnReal.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._mantissaRange is not None:
            result += ", mantissa range is" 
            result += str(self._mantissaRange) 
        if self._baseRange is not None:
            result += ", base range is"  
            result += str(self._baseRange)  
        if self._exponentRange is not None:
            result += ", exponent range is"  
            result += str(self._exponentRange)  
        if self._dbDefaultValue is not None:
            result += ", default value of "  
            result += self._dbDefaultValue  
        if self._range:
            result += ", default range"
            result += " within [%s,%s]" % (self._range[0], self._range[1])
        return result

class AsnString(AsnBasicNode):
    '''
This class stores the semantic content of an ASN.1 String.
Members:
    _name : the name of the type (or var)
    _range : a tuple containing the allowed string size or []
'''
    validOptions = ['range', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnBasicNode.__init__(self, args.get('asnFilename', ''))
        self._leafType = "unknown"
        self._lineno = args.get('lineno', None)
        self._range = args.get('range', [])
        for i in args:
            assert i in AsnString.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._range:
            result += ", length within "
            result += str(self._range)
        return result

class AsnOctetString(AsnString):
    '''This class stores the semantic content of an ASN.1 OCTET STRING.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args)
        self._name = "OCTET STRING"  # default in case of SEQUENCE_OF OCTET STRING
        self._leafType = "OCTET STRING"


class AsnUTF8String(AsnString):
    '''This class stores the semantic content of an ASN.1 UTF8String.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args)  
        self._name = "UTF8String"  # default in case of SEQUENCE_OF UTF8String 
        self._leafType = "UTF8String"  


class AsnAsciiString(AsnString):
    '''This class stores the semantic content of an ASN.1 AsciiString.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args) 
        self._name = "AsciiString"  # default in case of SEQUENCE_OF AsciiString 
        self._leafType = "AsciiString"  


class AsnNumberString(AsnString):
    '''This class stores the semantic content of an ASN.1 NumberString.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args) 
        self._name = "NumberString"  # default in case of SEQUENCE_OF NumberString 
        self._leafType = "NumberString" 


class AsnVisibleString(AsnString):
    '''This class stores the semantic content of an ASN.1 VisibleString.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args) 
        self._name = "VisibleString"  # default in case of SEQUENCE_OF VisibleString 
        self._leafType = "VisibleString" 


class AsnPrintableString(AsnString):
    '''This class stores the semantic content of an ASN.1 PrintableString.'''

    def __init__(self, **args: Any) -> None:
        AsnString.__init__(self, **args) 
        self._name = "PrintableString"  # default in case of SEQUENCE_OF PrintableString 
        self._leafType = "PrintableString" 

###########################################################
# Complex nodes: Enumerated, Sequence, Choice, SequenceOf #
###########################################################


class AsnEnumerated(AsnComplexNode):
    '''
This class stores the semantic content of an ASN.1 enumeration.
Members:
    _name : the name of the type
    _members : a tuple of all the allowed values for the enumeration.
               Each value is itself a tuple, containing the name
               and the integer value associated with it (or None,
               if it is ommited)
    _default : if one of the values of the enumeration is the default,
               it is contained in this member
'''
    validOptions = ['members', 'default', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._name = "ENUMERATED"  # default in case of SEQUENCE_OF ENUMERATED
        self._leafType = "ENUMERATED"
        self._members = args.get('members', [])
        self._default = args.get('default', None)
        self._lineno = args.get('lineno', None)
        for i in args:
            assert i in AsnEnumerated.validOptions
        existing = {}  # type: Dict[str, int]
        for elem in self._members:
            if elem[0] in existing:
                utility.panic(
                    "member '%s' appears more than once in ENUMERATED %s" % ( 
                        elem[0],
                        ("defined in line %s" % self._lineno) if self._lineno is not None else "")) 
            else:
                existing[elem[0]] = 1

    def __repr__(self) -> str:
        result = self._leafType
        assert self._members != []
        for member in self._members:
            result += ", option "
            result += str(member)
        return result

class AsnSequence(AsnComplexNode):
    '''
This class stores the semantic content of an ASN.1 SEQUENCE.
Members:
    _name : the name of the type
    _members    : a tuple of all child elements. Each tuple contains
                  many elements: the name of the variable, the type itself
                  (as an AsnInt, AsnReal, ... or an AsnMetaMember),
                  an optionality boolean (true mean OPTIONAL),
                  and two more booleans to indicate alwaysAbsent
                  and alwaysPresent semantics. See comment at the
                  top diagram for more info.
'''
    validOptions = ['members', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._name = "SEQUENCE"
        self._leafType = "SEQUENCE"
        self._members = args.get('members', [])
        self._lineno = args.get('lineno', None)
        for i in args:
            assert i in AsnSequence.validOptions
        existing = {}  # type: Dict[str, int]
        for elem in self._members:
            if elem[0] in existing:
                utility.panic(
                    "member '%s' appears more than once in %s" % ( 
                        elem[0],
                        ("defined in line %s" % self._lineno) if self._lineno is not None else "")) 
            else:
                existing[elem[0]] = 1

    def __repr__(self) -> str:
        result = self._leafType
        assert self._members != []
        for member in self._members:
            result += ", member "
            result += str(member)
        return result

class AsnSet(AsnComplexNode):

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._name = "SET"
        self._leafType = "SET"
        self._members = args.get('members', [])
        self._lineno = args.get('lineno', None)
        for i in args:
            assert i in AsnSequence.validOptions
        existing = {}  # type: Dict[str, int]
        for elem in self._members:
            if elem[0] in existing:
                utility.panic(
                    "member '%s' appears more than once in %s" % ( 
                        elem[0],
                        ("defined in line %s" % self._lineno) if self._lineno is not None else "")) 
            else:
                existing[elem[0]] = 1

    def __repr__(self) -> str:
        result = self._leafType
        assert self._members != []
        for member in self._members:
            result += ", member "
            result += str(member)
        return result

class AsnChoice(AsnComplexNode):
    '''
This class stores the semantic content of an ASN.1 CHOICE.
Members:
    _name : the name of the type
    _members    : a tuple of all child elements. Each tuple contains
                  two elements: the name of the variable and the
                  type itself (as an AsnInt, AsnReal, ... or an AsnMetaMember).
'''
    validOptions = ['members', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._name = "CHOICE"  # default in case of SEQUENCE_OF CHOICE
        self._leafType = "CHOICE"
        self._members = args.get('members', [])
        self._lineno = args.get('lineno', None)
        for i in args:
            assert i in AsnChoice.validOptions
        existing = {}  # type: Dict[str, int]
        for elem in self._members:
            if elem[0] in existing:
                utility.panic(
                    "member '%s' appears more than once in CHOICE %s" % ( 
                        elem[0],
                        ("defined in line %s" % self._lineno) if self._lineno is not None else "")) 
            else:
                existing[elem[0]] = 1

    def __repr__(self) -> str:
        result = self._leafType
        assert self._members != []
        for member in self._members:
            result += ", member "
            result += str(member)
        return result

class AsnSequenceOf(AsnComplexNode):
    '''
This class stores the semantic content of an ASN.1 SEQUENCEOF.
Members:
    _name : the name of the type
    _containedType : the contained element (either a string or AsnNode)
    _range : [] or a tuple with the allowed size range.
'''
    validOptions = ['range', 'containedType', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._range = args.get('range', [])
        self._containedType = args.get('containedType', None)
        self._lineno = args.get('lineno', None)
        self._name = "unnamed"  # default in case of SEQUENCE_OF SEQUENCE_OF
        self._leafType = "SEQUENCEOF"
        for i in args:
            assert i in AsnSequenceOf.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._range:
            result += ", valid sizes in "
            result += str(self._range)
        assert self._containedType is not None
        result += ", contained type is "
        result += str(self._containedType)
        return result

class AsnSetOf(AsnComplexNode):

    def __init__(self, **args: Any) -> None:
        AsnComplexNode.__init__(self, args.get('asnFilename', ''))
        self._range = args.get('range', [])
        self._containedType = args.get('containedType', None)
        self._lineno = args.get('lineno', None)
        self._name = "unnamed"  # default in case of SEQUENCE_OF SEQUENCE_OF
        self._leafType = "SETOF"
        for i in args:
            assert i in AsnSequenceOf.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        if self._range:
            result += ", valid sizes in "
            result += str(self._range)
        assert self._containedType is not None
        result += ", contained type is "
        result += str(self._containedType)
        return result

class AsnMetaMember(AsnNode):
    '''
This class stores the semantic content of a member type of a
CHOICE or SEQUENCE.
Members:
    _containedType : the contained element as a string (type name)
'''
    validOptions = ['containedType', 'Min', 'Max', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnNode.__init__(self, args.get('asnFilename', ''))
        self._leafType = args.get('containedType', None)
        self._containedType = args.get('containedType', None)
        self._lineno = args.get('lineno', None)
        self._Min = args.get('Min', None)
        self._Max = args.get('Max', None)
        for i in args:
            assert i in AsnMetaMember.validOptions

    def __repr__(self) -> str:
        result = self._leafType
        assert self._leafType is not None
        result += ", contained member is "
        result += " of type "
        result += self._containedType
        return result


class AsnMetaType(AsnNode):
    '''
This class stores the semantic content of a type which is typedefed
to another type.
Members:
    _containedType : the contained type name
e.g.:
    MyNewType ::= MyOldType
    _name contains 'MyNewType'
    _containedType contains 'MyOldType'
'''
    validOptions = ['containedType', 'Min', 'Max', 'lineno', 'asnFilename']

    def __init__(self, **args: Any) -> None:
        AsnNode.__init__(self, args.get('asnFilename', ''))
        self._leafType = args.get('containedType', None)
        self._containedType = args.get('containedType', None)
        self._lineno = args.get('lineno', None)
        self._Min = args.get('Min', None)
        self._Max = args.get('Max', None)
        for i in args:
            assert i in AsnMetaType.validOptions

    def __repr__(self) -> str:
        result = "typedefed to " + self._leafType 
        if self._Min is not None:
            result += ", min=" + str(self._Min) 
        if self._Max is not None:
            result += ", max=" + str(self._Max) 
        assert self._leafType is not None  
        return result 

