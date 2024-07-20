'''
ASN.1 Parser

This module parses ASN.1 grammars and creates an abstract syntax tree (AST)
'''

import os
import copy
import tempfile
import re
import xml.sax  
from distutils import spawn
from typing import  TypeVar, Type, Optional, Callable, Union, List, Dict, Tuple, Any  
from . import utility
from .asnAST import (
    AsnBasicNode, AsnEnumerated, AsnSequence, AsnChoice, AsnSequenceOf,
    AsnSet, AsnSetOf, AsnMetaMember, AsnMetaType, AsnInt, AsnReal, AsnNode,
    AsnComplexNode, AsnBool, AsnOctetString, AsnAsciiString
)

g_metatypes = {}

# MyPy type aliases
Typename = str
Filename = str
AST_Lookup = Dict[Typename, AsnNode]
AST_TypenamesOfFile = Dict[Filename, List[str]]  
AST_Leaftypes = Dict[Typename, str]
AST_TypesOfFile = Dict[Filename, List[AsnNode]]  
AST_Modules = Dict[str, List[Typename]]  

g_names = {}         # type: AST_Lookup 
g_typesOfFile = {}   # type: AST_TypenamesOfFile 
g_leafTypeDict = {}  # type: AST_Leaftypes
g_astOfFile = {}     # type: AST_TypesOfFile
g_modules = {}       # type: AST_Modules
g_modulesOfFile = {}       # type: AST_Modules


g_checkedSoFarForKeywords = {}  # type: Dict[str, int]

g_invalidKeywords = [
    "active", "adding", "all", "alternative", "and", "any", "as", "atleast", "axioms", "block", "call", "channel", "comment", "connect", "connection", "constant", "constants", "create", "dcl", "decision", "default", "else", "endalternative", "endblock", "endchannel", "endconnection", "enddecision", "endgenerator", "endmacro", "endnewtype", "endoperator", "endpackage", "endprocedure", "endprocess", "endrefinement", "endselect", "endservice", "endstate", "endsubstructure", "endsyntype", "endsystem", "env", "error", "export", "exported", "external", "fi", "finalized", "for", "fpar", "from", "gate", "generator", "if", "import", "imported", "in", "inherits", "input", "interface", "join", "literal", "literals", "macro", "macrodefinition", "macroid", "map", "mod", "nameclass", "newtype", "nextstate", "nodelay", "noequality", "none", "not", "now", "offspring", "operator", "operators", "or", "ordering", "out", "output", "package", "parent", "priority", "procedure", "process", "provided", "redefined", "referenced", "refinement", "rem", "remote", "reset", "return", "returns", "revealed", "reverse", "save", "select", "self", "sender", "service", "set", "signal", "signallist", "signalroute", "signalset", "spelling", "start", "state", "stop", "struct", "substructure", "synonym", "syntype", "system", "task", "then", "this", "to", "type", "use", "via", "view", "viewed", "virtual", "with", "xor", "end", "i", "j", "auto", "const",
    "abstract", "activate", "and", "assume", "automaton", "bool", "case", "char", "clock", "const", "default", "div", "do", "else", "elsif", "emit", "end", "enum", "every", "false", "fby", "final", "flatten", "fold", "foldi", "foldw", "foldwi", "function", "guarantee", "group", "if", "imported", "initial", "int", "is", "last", "let", "make", "map", "mapfold", "mapi", "mapw", "mapwi", "match", "merge", "mod", "node", "not", "numeric", "of", "onreset", "open", "or", "package", "parameter", "pre", "private", "probe", "public", "real", "restart", "resume", "returns", "reverse", "sensor", "sig", "specialize", "state", "synchro", "tel", "then", "times", "transpose", "true", "type", "unless", "until", "var", "when", "where", "with", "xor",
    "open", "close", "flag", "device", "range", "name"
]

tokens = (
    'DEFINITIONS', 'APPLICATION', 'AUTOMATIC', 'IMPLICIT', 'EXPLICIT', 'TAGS', 'BEGIN', 'IMPORTS', 'EXPORTS', 'FROM', 'ALL', 'CHOICE', 'SEQUENCE', 'SET', 'OF', 'END', 'OPTIONAL', 'INTEGER', 'REAL', 'OCTET', 'STRING', 'BOOLEAN', 'TRUE', 'FALSE', 'ASCIISTRING', 'NUMBERSTRING', 'VISIBLESTRING', 'PRINTABLESTRING', 'UTF8STRING', 'ENUMERATED', 'SEMI', 'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'BLOCK_END', 'BLOCK_BEGIN', 'DEF', 'NAME', 'COMMA', 'INTVALUE', 'REALVALUE', 'DEFAULT', 'SIZE', 'DOTDOT', 'DOTDOTDOT', 'WITH', 'COMPONENTS', 'MANTISSA', 'BASE', 'EXPONENT'  # 'BIT',
)

lotokens = [tkn.lower() for tkn in tokens]

reserved = {
    'DEFINITIONS': 'DEFINITIONS', 'APPLICATION': 'APPLICATION', 'TAGS': 'TAGS', 'BEGIN': 'BEGIN', 'CHOICE': 'CHOICE',
    'SEQUENCE': 'SEQUENCE', 'SET': 'SET', 'OF': 'OF', 'END': 'END', 'OPTIONAL': 'OPTIONAL', 'BOOLEAN': 'BOOLEAN', 'INTEGER': 'INTEGER',
    'REAL': 'REAL', 'OCTET': 'OCTET', 'STRING': 'STRING', 'UTF8String': 'UTF8STRING', 'AsciiString': 'ASCIISTRING',
    'NumberString': 'NUMBERSTRING', 'VisibleString': 'VISIBLESTRING', 'PrintableString': 'PRINTABLESTRING', 'ENUMERATED': 'ENUMERATED',
    'AUTOMATIC': 'AUTOMATIC', 'SIZE': 'SIZE', 'IMPLICIT': 'IMPLICIT', 'EXPLICIT': 'EXPLICIT', 'TRUE': 'TRUE', 'FALSE': 'FALSE',
    'DEFAULT': 'DEFAULT', 'mantissa': 'MANTISSA', 'base': 'BASE', 'exponent': 'EXPONENT', 'WITH': 'WITH', 'FROM': 'FROM',
    'IMPORTS': 'IMPORTS', 'EXPORTS': 'EXPORTS', 'ALL': 'ALL', 'COMPONENTS': 'COMPONENTS'
}


def KnownType(node: AsnNode, names: AST_Lookup) -> bool:
    retVal = True
    if isinstance(node, str):
        utility.panic("Referenced type (%s) does not exist!\n" % node)
    if isinstance(node, (AsnBasicNode, AsnEnumerated)):
        pass
    elif isinstance(node, (AsnSequence, AsnChoice, AsnSet)):
        for x in node._members:
            if not KnownType(x[1], names):
                return False
    elif isinstance(node, AsnMetaMember):
        retVal = KnownType(names.get(node._containedType, node._containedType), names)
    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        containedType = node._containedType
        while isinstance(containedType, str):
            containedType = names[containedType]
        retVal = KnownType(containedType, names)
    elif isinstance(node, AsnMetaType):
        retVal = KnownType(names.get(node._containedType, node._containedType), names)
    else:
        utility.panic("Unknown node type (%s)!\n" % str(node))
    return retVal


def CleanNameForAST(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def VerifyAndFixAST() -> Dict[str, str]:
    '''Check that all types are defined and are not missing.
    It returns a map providing the leafType of each type.
    '''
    unknownTypes = {}  # type: Dict[str, int]
    knownTypes = {}    # type: Dict[str, str]
    equivalents = {}   # type: Dict[str, List[str]]
    while True:  # pylint: disable=too-many-nested-blocks
        lastUnknownTypes = copy.copy(unknownTypes)
        lastKnownTypes = copy.copy(knownTypes)
        lastEquivalents = copy.copy(equivalents)
        for nodeTypename in list(g_names.keys()):

            node = g_names[nodeTypename]  # type: AsnNode

            # AsnMetaMembers can only appear inside SEQUENCEs and CHOICEs,
            # not at the top level!
            assert not isinstance(node, AsnMetaMember)

            # Type level typedefs are stored in the equivalents dictionary
            if isinstance(node, AsnMetaType):
                # A ::= B
                # A and B are nodeTypename  and  node._containedType
                equivalents.setdefault(node._containedType, [])
                # Add A to the list of types that are equivalent to B
                equivalents[node._containedType].append(nodeTypename)
                # and if we know B's leafType, then we also know A's
                if node._containedType in knownTypes:
                    knownTypes[nodeTypename] = node._containedType
                else:
                    unknownTypes[nodeTypename] = 1
            # AsnBasicNode type assignments are also equivalents
            elif isinstance(node, AsnBasicNode):
                # node._leafType is one of BOOLEAN, OCTET STRING, INTEGER, etc
                equivalents.setdefault(node._leafType, [])
                equivalents[node._leafType].append(nodeTypename)
                knownTypes[nodeTypename] = node._leafType
            # AsnEnumerated types are known types - they don't have external refs
            elif isinstance(node, AsnEnumerated):
                # node._leafType is ENUMERATED
                knownTypes[nodeTypename] = node._leafType
            # SEQUENCEs and CHOICEs: check their children for unknown AsnMetaMembers
            elif isinstance(node, (AsnSequence, AsnChoice, AsnSet)):
                bFoundUnknown = False
                for x in node._members:
                    if isinstance(x[1], AsnMetaMember) and x[1]._containedType not in knownTypes:
                        bFoundUnknown = True
                        break
                if bFoundUnknown:
                    unknownTypes[nodeTypename] = 1
                else:
                    # node._leafType is SEQUENCE or CHOICE
                    knownTypes[nodeTypename] = node._leafType
            # SEQUENCE OFs: check their contained type
            elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
                if node._containedType in knownTypes or isinstance(node._containedType, AsnBasicNode):
                    knownTypes[nodeTypename] = node._leafType
                elif isinstance(node._containedType, AsnComplexNode):
                    knownTypes[nodeTypename] = node._leafType
                else:
                    unknownTypes[nodeTypename] = 1

        # We have completed a sweep over all AST entries.
        # now check the knownTypes and unknownTypes information
        # to see if we have figured out (leafType wise) all nodes
        for known in list(knownTypes.keys()):
            # for each of the nodes we know (leafType wise)

            # remove it from the unknownTypes dictionary
            if known in unknownTypes:
                del unknownTypes[known]

            # remove all it's equivalents, too (from the unknownTypes)
            if known in equivalents:
                for alsoKnown in equivalents[known]:
                    if alsoKnown in unknownTypes:
                        del unknownTypes[alsoKnown]

                    # Additionally, follow the chain to the last knownType
                    seed = known
                    while seed in knownTypes:
                        if seed != knownTypes[seed]:
                            seed = knownTypes[seed]
                        else:
                            break
                    # and update knownTypes dictionary to contain leafType
                    knownTypes[alsoKnown] = seed

        # If this pass has not changed the knownTypes and the unknownTypes and the equivalents, we are done
        if lastEquivalents == equivalents and lastKnownTypes == knownTypes and lastUnknownTypes == unknownTypes:
            break

    if unknownTypes:
        utility.panic('AsnParser: Types remain unknown after symbol fixup:\n%s\n' % list(unknownTypes.keys()))

    # Remove all AsnMetaTypes from the ast
    # by using the g_names lookup on their _containedType
    for nodeTypename in list(g_names.keys()):
        # Min, Max: to cope with ReferenceTypes that redefine their
        # constraints (for now, ASN1SCC provides only INTEGERs)
        Min = Max = None
        node = g_names[nodeTypename]
        if hasattr(node, "_Min") and Min is None:
            Min = node._Min  
        if hasattr(node, "_Max") and Max is None:
            Max = node._Max  
        originalNode = node
        while isinstance(node, AsnMetaType):
            g_metatypes[nodeTypename] = node._containedType
            node = g_names[node._containedType]
            if hasattr(node, "_Min") and Min is None:
                Min = node._Min  
            if hasattr(node, "_Max") and Max is None:
                Max = node._Max  
        # To cope with ReferenceTypes that redefine their
        # constraints (for now, ASN1SCC provides only INTEGERs)
        if isinstance(originalNode, AsnMetaType):
            target = copy.copy(node)  
            # we need to keep the _asnFilename
            target._asnFilename = originalNode._asnFilename
            if isinstance(node, AsnInt) and Min is not None and Max is not None:
                target._range = [Min, Max]  
        elif isinstance(node, AsnInt) and Min is not None and Max is not None:
            target = copy.copy(node)  # we need to keep the Min/Max
            target._range = [Min, Max]
        else:
            target = node
        g_names[nodeTypename] = target

    for name, node in list(g_names.items()):
        if not KnownType(node, g_names):
            utility.panic("Node %s not resolvable (%s)!\n" % (name, node.Location()))
        for i in ["_Min", "_Max"]:
            cast = float if isinstance(node, AsnReal) else int
            if hasattr(node, i) and getattr(node, i) is not None:
                setattr(node, i, cast(getattr(node, i)))

    knownTypes['INTEGER'] = 'INTEGER'
    knownTypes['REAL'] = 'REAL'
    knownTypes['BOOLEAN'] = 'BOOLEAN'
    knownTypes['OCTET STRING'] = 'OCTET STRING'
    knownTypes['AsciiString'] = 'OCTET STRING'
    knownTypes['NumberString'] = 'OCTET STRING'
    knownTypes['VisibleString'] = 'OCTET STRING'
    knownTypes['PrintableString'] = 'OCTET STRING'
    knownTypes['UTF8String'] = 'OCTET STRING'

    # Find all the SEQUENCE, CHOICE and SEQUENCE OFs
    # and if the contained type is not one of AsnBasicNode, AsnEnumerated, AsnMetaMember,
    # define a name and use it... (for SEQUENCEOFs/SETOFs, allow also 'str')
    internalNo = 1
    addedNewPseudoType = True
    while addedNewPseudoType:  
        addedNewPseudoType = False
        listOfTypenames = sorted(g_names.keys())
        for nodeTypename in listOfTypenames:
            node = g_names[nodeTypename]
            if isinstance(node, (AsnChoice, AsnSequence, AsnSet)):
                for child in node._members:
                    if not isinstance(child[1], AsnBasicNode) and \
                            not isinstance(child[1], AsnEnumerated) and \
                            not isinstance(child[1], AsnMetaMember):
                        # It will be an internal sequence, choice or sequenceof
                        assert isinstance(child[1], (AsnChoice, AsnSet, AsnSetOf, AsnSequence, AsnSequenceOf))
                        internalName = newname = nodeTypename + '_' + CleanNameForAST(child[0])
                        while internalName in g_names:
                            internalName = (newname + "_%d") % internalNo
                            internalNo += 1

                        g_leafTypeDict[internalName] = child[1]._leafType 
                        child[1] = AsnMetaMember(asnFilename=child[1]._asnFilename, containedType=internalName)
                        addedNewPseudoType = True
            elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
                if not isinstance(node._containedType, str) and \
                        not isinstance(node._containedType, AsnBasicNode) and \
                        not isinstance(node._containedType, AsnEnumerated):
                    internalName = newname = nodeTypename + "_elm"
                    while internalName in g_names:
                        internalName = (newname + "_%d") % internalNo
                        internalNo += 1
                    g_leafTypeDict[internalName] = node._containedType._leafType
                    node._containedType = internalName
                    addedNewPseudoType = True

    # return the leafType dictionary
    return knownTypes


def IsInvalidType(name: str) -> bool:
    return \
        (name.lower() in g_invalidKeywords) or \
        (name.lower() in lotokens) or \
        any([name.lower().endswith(x) for x in ["-buffer", "-buffer-max"]])


def CheckForInvalidKeywords(node_or_str: Union[str, AsnNode]) -> None:
    if isinstance(node_or_str, str):
        if IsInvalidType(node_or_str):
            utility.panic(
                "'%s' is not allowed" % node_or_str)
        node = g_names[node_or_str]  # type: AsnNode
    else:
        node = node_or_str
    if isinstance(node, (AsnBasicNode, AsnEnumerated)):
        pass
    elif isinstance(node, (AsnSequence, AsnChoice, AsnSet)):
        for child in node._members:
            if child[0].lower() in g_invalidKeywords or child[0].lower() in lotokens:
                utility.panic(
                    "Invalid field name '%s' used in type defined in %s" % (child[0], node.Location()))
            if isinstance(child[1], AsnMetaMember) and child[1]._containedType not in g_checkedSoFarForKeywords:
                if IsInvalidType(child[1]._containedType.lower()):
                    utility.panic(
                        "Invalid type name '%s' used in type defined in %s" % (child[1]._containedType, node.Location()))
                if child[1]._containedType not in g_checkedSoFarForKeywords:
                    g_checkedSoFarForKeywords[child[1]._containedType] = 1
                    CheckForInvalidKeywords(g_names[child[1]._containedType])

    elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
        if isinstance(node._containedType, str):
            if IsInvalidType(node._containedType):
                utility.panic(
                    "Invalid type name '%s' used in type defined in %s" % (node._containedType, node.Location()))
            if node._containedType not in g_checkedSoFarForKeywords:
                g_checkedSoFarForKeywords[node._containedType] = 1
                CheckForInvalidKeywords(g_names[node._containedType])
    

def ParseAsnFileList(listOfFilenames: List[str]) -> None: 

    (dummy, xmlAST) = tempfile.mkstemp()
    os.fdopen(dummy).close()
    asn1SccPath = spawn.find_executable('asn1scc')
    if asn1SccPath is None:
        utility.panic("ASN1SCC seems not installed on your system (asn1.exe not found in PATH).\n")
    asn1SccDir = os.path.dirname(os.path.abspath(asn1SccPath))
    print(asn1SccPath + " -customStg \"" + asn1SccDir + "/xml.stg::" + xmlAST + "\" -typePrefix asn1Scc -customStgAstVersion 4 \"" + "\" \"".join(listOfFilenames) + "\"")
    spawnResult = os.system(asn1SccPath + " -customStg \"" + asn1SccDir + "/xml.stg::" + xmlAST + "\" -typePrefix asn1Scc -customStgAstVersion 4 \"" + "\" \"".join(listOfFilenames) + "\"")


    if spawnResult != 0:
        utility.panic("ASN1SCC reported  errors. Aborting...")
          
    ParseASN1SCC_AST(xmlAST)
    os.unlink(xmlAST)
    g_names.update(g_names)
    g_leafTypeDict.update(g_leafTypeDict)
    g_checkedSoFarForKeywords.update(g_checkedSoFarForKeywords)
    g_typesOfFile.update(g_typesOfFile)




g_lineno = -1


class Element:
    def __init__(self, name: str, attrs: Dict[str, Any]) -> None:
        self._name = name
        self._attrs = attrs
        self._children = [] 
        
   

class InputFormatXMLHandler(xml.sax.ContentHandler):  
    def __init__(self, debug: bool = False) -> None:
        xml.sax.ContentHandler.__init__(self)  
        self._root = Element('root', {})
        self._roots = [self._root]

    def startElement(self, name: str, attrs: Dict[str, Any]) -> None: 
        newElement = Element(name, attrs)
        self._roots[-1]._children.append(newElement)
        self._roots.append(newElement)

    def endElement(self, _: Any) -> None:
        self._roots.pop()

Action = Callable[[Element], Any]

def VisitAll(node: Element, expectedType: str, action: Action) -> List[Any]:  # pylint: disable=invalid-sequence-index
    results = []  # type: List[Any]
    if node is not None:
        if node._name == expectedType:
            results = [action(node)]
        for child in node._children:
            results += VisitAll(child, expectedType, action)
    return results


def GetAttr(node: Element, attrName: str) -> Optional[Any]:
    if attrName not in list(node._attrs.keys()):
        return None
    else:
        return node._attrs[attrName]


def GetChild(node: Element, childName: str) -> Optional[Element]:
    for x in node._children:
        if x._name == childName:
            return x
    return None  


class Pretty:
    def __repr__(self) -> str:
        result = ""  
        for i in dir(self):  
            if i != "__repr__":  
                result += chr(27) + "[32m" + i + chr(27) + "[0m:"  
                result += repr(getattr(self, i))  
                result += "\n"  
        return result  


class Module(Pretty):
    _id = None                 # type: str
    _asnFilename = None        # type: str
    _exportedTypes = None      # type: List[str]
    _exportedVariables = None  # type: List[str]

    # (tuples of ModuleName, imported types, imported vars)
    _importedModules = None    # type: List[Tuple[str, List[str], List[str]]]
    # (tuples of Typename, AsnNode)
    _typeAssignments = None    # type: List[Tuple[str, AsnNode]]
    # (tuples of Typename, AsnNode)

def CreateBoolean(newModule: Module, lineNo: int, _: Any) -> AsnBool:
    return AsnBool(
        asnFilename=newModule._asnFilename,
        lineno=lineNo)


U = TypeVar('U', int, float)


def GetRange(newModule: Module, lineNo: int, nodeWithMinAndMax: Element, valueType: Type[U]) -> Tuple[U, U]:
    try:
        mmin = GetAttr(nodeWithMinAndMax, "Min")
        if mmin == "MIN":
            utility.panic("You missed a range specification, or used MIN/MAX (line %s)" % lineNo)  
        rangel = valueType(mmin)
        mmax = GetAttr(nodeWithMinAndMax, "Max")
        if mmax == "MAX":
            utility.panic("You missed a range specification, or used MIN/MAX (line %s)" % lineNo)  
        rangeh = valueType(mmax)
    except:  
        descr = {int: "integer", float: "floating point"}  
        utility.panic("Expecting %s value ranges (%s, %s)" %  
                      (descr[valueType], newModule._asnFilename, lineNo))  
    return (rangel, rangeh)


def CreateInteger(newModule: Module, lineNo: int, xmlIntegerNode: Element ) -> AsnInt:
    return AsnInt(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlIntegerNode, int))


def CreateReal(newModule: Module, lineNo: int, xmlRealNode: Element) -> AsnReal:
    return AsnReal(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlRealNode, float))


def CreateEnumerated(newModule: Module, lineNo: int, xmlEnumeratedNode: Element) -> AsnEnumerated:
    return AsnEnumerated(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        members=VisitAll(
            xmlEnumeratedNode, "EnumValue",
            lambda x: [GetAttr(x, "StringValue"), GetAttr(x, "IntValue")]))

def CreateBitString(_, __, ___):  
    utility.panic("BitString type is not supported by the toolchain. "  
                  "Please use SEQUENCE OF BOOLEAN")  


def CreateOctetString(newModule: Module, lineNo: int, xmlOctetString: Element) -> AsnOctetString:
    return AsnOctetString(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlOctetString, int))


def CreateIA5String(newModule: Module, lineNo: int, xmlIA5StringNode: Element) -> AsnAsciiString:
    return AsnAsciiString(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlIA5StringNode, int))


def CreateNumericString(newModule: Module, lineNo: int, xmlNumericStringNode: Element) -> AsnOctetString:
    return CreateOctetString(newModule, lineNo, xmlNumericStringNode)  


def getIntOrFloatOrNone(d: str) -> Union[int, float, None]:
    i = f = None
    try:
        i = int(d)
        return i
    except:
        try:
            f = float(d)
            return f
        except:
            return None


def CreateReference(newModule: Module, lineNo: int, xmlReferenceNode: Element) -> AsnMetaType:
    return AsnMetaType(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        containedType=GetAttr(xmlReferenceNode, "ReferencedTypeName"),
        Min=getIntOrFloatOrNone(GetAttr(xmlReferenceNode, "Min")),
        Max=getIntOrFloatOrNone(GetAttr(xmlReferenceNode, "Max")))


V = TypeVar('V', AsnSequenceOf, AsnSetOf)


def CommonSetSeqOf(newModule: Module, lineNo: int, xmlSequenceOfNode: Element, classToCreate: Type[V]) -> V:
    xmlType = GetChild(xmlSequenceOfNode, "Type")
    if xmlType is None:
        utility.panic("CommonSetSeqOf: No child under SequenceOfType (%s, %s)" %  
                      (newModule._asnFilename, lineNo))  
    if len(xmlType._children) == 0:  
        utility.panic("CommonSetSeqOf: No children for Type (%s, %s)" %  
                      (newModule._asnFilename, lineNo))  
    if xmlType._children[0]._name == "ReferenceType":
        contained = GetAttr(xmlType._children[0], "ReferencedTypeName")
    else:
        contained = GenericFactory(newModule, xmlType)
    return classToCreate(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        range=GetRange(newModule, lineNo, xmlSequenceOfNode, int),
        containedType=contained)


def CreateSequenceOf(newModule: Module, lineNo: int, xmlSequenceOfNode: Element) -> AsnSequenceOf:
    return CommonSetSeqOf(newModule, lineNo, xmlSequenceOfNode, AsnSequenceOf)


def CreateSetOf(newModule: Module, lineNo: int, xmlSetOfNode: Element) -> AsnSetOf:
    return CommonSetSeqOf(newModule, lineNo, xmlSetOfNode, AsnSetOf)


W = TypeVar('W', AsnSequence, AsnSet, AsnChoice)


def CommonSeqSetChoice(
        newModule: Module,
        lineNo: int,
        xmlSequenceNode: Element,
        classToCreate: Type[W],
        childTypeName: str) -> W:

    myMembers = []

    for x in xmlSequenceNode._children:
        if x._name == childTypeName:
            opti = GetAttr(x, "Optional")
            bAlwaysPresent = GetAttr(x, "bAlwaysPresent")
            bAlwaysAbsent = GetAttr(x, "bAlwaysAbsent")
            if opti and opti == "True":
                utility.warn("OPTIONAL attribute ignored by mapper (for field contained in %s,%s)" % (newModule._asnFilename, lineNo))
            enumID = GetAttr(x, "EnumID")
            myMembers.append([GetAttr(x, "VarName"), GenericFactory(newModule, GetChild(x, "Type"))])
            myMembers[-1].append(enumID)
            for flag in [opti, bAlwaysPresent, bAlwaysAbsent]:
                myMembers[-1].append(flag == "True")
           
    for tup in myMembers:
        if isinstance(tup[1], AsnMetaType):
            asnMetaMember = AsnMetaMember(
                asnFilename=tup[1]._asnFilename,
                containedType=tup[1]._containedType,
                lineno=tup[1]._lineno,
                Min=tup[1]._Min,
                Max=tup[1]._Max)
            tup[1] = asnMetaMember
                              
    return classToCreate(
        asnFilename=newModule._asnFilename,
        lineno=lineNo,
        members=myMembers)


def CreateSequence(newModule: Module, lineNo: int, xmlSequenceNode: Element) -> AsnSequence:
    return CommonSeqSetChoice(
        newModule, lineNo, xmlSequenceNode,
        AsnSequence,"SequenceOrSetChild")


def CreateSet(newModule: Module, lineNo: int, xmlSetNode: Element) -> AsnSet:
    return CommonSeqSetChoice(
        newModule, lineNo, xmlSetNode,
        AsnSet, "SequenceOrSetChild")


def CreateChoice(newModule: Module, lineNo: int, xmlChoiceNode: Element) -> AsnChoice:
    return CommonSeqSetChoice(
        newModule, lineNo, xmlChoiceNode,
        AsnChoice,"ChoiceChild")


def GenericFactory(newModule: Module, xmlType: Element) -> AsnNode:
    Factories = {
        "BooleanType": CreateBoolean,
        "IntegerType": CreateInteger,
        "RealType": CreateReal,
        "EnumeratedType": CreateEnumerated,
        "BitStringType": CreateBitString,
        "OctetStringType": CreateOctetString,
        "IA5StringType": CreateIA5String,
        "NumericStringType": CreateNumericString,
        "ReferenceType": CreateReference,
        "SequenceOfType": CreateSequenceOf,
        "SetOfType": CreateSetOf,
        "SequenceType": CreateSequence,
        "SetType": CreateSet,
        "ChoiceType": CreateChoice
    }  # type: Dict[str, Callable[[Module, int, Element], AsnNode]]
    lineNo = GetAttr(xmlType, "Line")
    global g_lineno
    g_lineno = lineNo
    if len(xmlType._children) == 0:  
        utility.panic("GenericFactory: No children for Type (%s, %s)" %  
                      (newModule._asnFilename, lineNo))  
    xmlContainedType = xmlType._children[0]
    if xmlContainedType._name not in list(Factories.keys()):
        utility.panic("Unsupported XML type node: '%s' (%s, %s)" %  
                      (xmlContainedType._name, newModule._asnFilename, lineNo))  
    maker = Factories[xmlContainedType._name]
    return maker(newModule, lineNo, xmlContainedType)


def VisitTypeAssignment(newModule: Module, xmlTypeAssignment: Element) -> Tuple[str, AsnNode]:
    xmlType = GetChild(xmlTypeAssignment, "Type")
    name = GetAttr(xmlTypeAssignment, "Name")
               
    if xmlType is None:
        utility.panic("VisitTypeAssignment: No child under TypeAssignment")  
    newNode = GenericFactory(newModule, xmlType)
    return (name, newNode)


def VisitAsn1Module(xmlAsn1File: Element, xmlModule: Element, modules: List[Module]) -> None:  
    newModule = Module()
    newModule._id = GetAttr(xmlModule, "ID")
    newModule._asnFilename = GetAttr(xmlAsn1File, "FileName")
    newModule._exportedTypes = VisitAll(
        GetChild(xmlModule, "ExportedTypes"), "ExportedType",
        lambda x: GetAttr(x, "Name"))

    newModule._exportedVariables = VisitAll(
        GetChild(xmlModule, "ExportedVariables"), "ExportedVariable",
        lambda x: GetAttr(x, "Name"))

    newModule._importedModules = VisitAll(
        GetChild(xmlModule, "ImportedModules"), "ImportedModule",
        lambda x: (
            GetAttr(x, "ID"),
            VisitAll(GetChild(x, "ImportedTypes"), "ImportedType",
                     lambda y: GetAttr(y, "Name")),
            VisitAll(GetChild(x, "ImportedVariables"), "ImportedVariable",
                     lambda y: GetAttr(y, "Name")),
        )
    )

    newModule._typeAssignments = VisitAll(
        GetChild(xmlModule, "TypeAssignments"), "TypeAssignment",
        lambda x: VisitTypeAssignment(newModule, x)) 

    g_typesOfFile.setdefault(newModule._asnFilename, [])
    g_typesOfFile[newModule._asnFilename].extend(
        [x for x, _ in newModule._typeAssignments])

    g_astOfFile.setdefault(newModule._asnFilename, [])
    g_astOfFile[newModule._asnFilename].extend(
        [y for _, y in newModule._typeAssignments])

    modules.append(newModule)


def ParseASN1SCC_AST(filename: str) -> None:
    parser = xml.sax.make_parser([])
    handler = InputFormatXMLHandler()
    parser.setContentHandler(handler)
    parser.parse(filename)
    if len(handler._root._children) != 1 or handler._root._children[0]._name != "ASN1AST":
        utility.panic("You must use an XML file that contains one ASN1AST node")  


    modules = []  # type: List[Module]
    VisitAll(
        handler._root._children[0], "Asn1File",
        lambda x: VisitAll(x, "Asn1Module",
                           lambda y: VisitAsn1Module(x, y, modules)))

    g_names.clear()
    g_checkedSoFarForKeywords.clear()
    g_leafTypeDict.clear()
    for m in modules:
        if len(m._typeAssignments) != 0:
         g_modulesOfFile.setdefault(m._asnFilename, []).append(m._id)
        for typeName, typeData in m._typeAssignments:
            g_names[typeName] = typeData
            g_modules.setdefault(m._id, []).append(typeName)
    g_leafTypeDict.update(VerifyAndFixAST())

    for nodeTypename in list(g_names.keys()):
        if nodeTypename not in g_checkedSoFarForKeywords:
            g_checkedSoFarForKeywords[nodeTypename] = 1
            CheckForInvalidKeywords(nodeTypename)

