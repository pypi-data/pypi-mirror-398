import inspect, weakref, types, collections, abc, ast, builtins, dis, enum, functools, importlib, keyword, itertools, linecache, os, re, sys, token, tokenize

def getClassAttributes(cls):
    return inspect.classify_class_attrs(cls)

def cleanDocumentation(doc):
    return inspect.cleandoc(doc)

def ismethodwrapper(obj):
    return isinstance(obj, types.MethodWrapperType)

def getCurrentFrame():
    return inspect.currentframe()

def findSource(obj):
    try:
        return inspect.findsource(obj)
    except Exception:
        return inspect.getsourcelines(obj)

def formatAnnotation(annotation, base_module=None):
    return inspect.formatannotation(annotation, base_module)

def formatAnnotationRelative(annotation, base_module=None):
    try:
        return inspect.formatannotationrelativeto(annotation, base_module)
    except Exception:
        return inspect.formatannotation(annotation, base_module)

def formatArguments(args, varargs, varkw, locals_dict):
    return inspect.formatargvalues(args, varargs, varkw, locals_dict)

def getAnnotations(obj, eval_str=False):
    return inspect.get_annotations(obj, eval_str=eval_str)

def getAbsoluteFile(obj):
    return inspect.getabsfile(obj)

def getArguments(func):
    try:
        return inspect.getargs(func)
    except Exception:
        return inspect.getfullargspec(func)

def getArgumentValues(frame):
    return inspect.getargvalues(frame)

def getAsyncGeneratorLocals(agen):
    try:
        return inspect.getasyncgenlocals(agen)
    except Exception:
        return {}

def getAsyncGeneratorState(agen):
    try:
        return inspect.getasyncgenstate(agen)
    except Exception:
        return None

def getStaticAttribute(obj, attr):
    return inspect.getattr_static(obj, attr)

def getCodeBlock(lines):
    return inspect.getblock(lines)

def getCallArguments(func, *args, **kwargs):
    return inspect.getcallargs(func, *args, **kwargs)

def getClassTree(classes, unique=False):
    return inspect.getclasstree(classes, unique=unique)

def getClosureVariables(func):
    return inspect.getclosurevars(func)

def getComments(obj):
    return inspect.getcomments(obj)

def getCoroutineLocals(coro):
    try:
        return inspect.getcoroutinelocals(coro)
    except Exception:
        return {}

def getCoroutineState(coro):
    try:
        return inspect.getcoroutinestate(coro)
    except Exception:
        return None

def getDocumentation(obj):
    return inspect.getdoc(obj)

def getFile(obj):
    return inspect.getfile(obj)

def getFrameInfo(frame, context=1):
    return inspect.getframeinfo(frame, context)

def getFullArgumentsSpec(func):
    return inspect.getfullargspec(func)

def getGeneratorLocals(gen):
    try:
        return inspect.getgeneratorlocals(gen)
    except Exception:
        return {}

def getGeneratorState(gen):
    try:
        return inspect.getgeneratorstate(gen)
    except Exception:
        return None

def getInnerFrames(tb, context=1):
    return inspect.getinnerframes(tb, context)

def getLineNumber(frame):
    return inspect.getlineno(frame)

def getMembers(obj, predicate=None):
    return inspect.getmembers(obj, predicate)

def getStaticMembers(obj):
    return inspect.getmembers_static(obj)

def getModule(obj):
    return inspect.getmodule(obj)

def getModuleName(path):
    return inspect.getmodulename(path)

def getMethodResolutionOrder(cls):
    return inspect.getmro(cls)

def getOuterFrames(frame, context=1):
    return inspect.getouterframes(frame, context)

def getSource(obj):
    return inspect.getsource(obj)

def getSourceFile(obj):
    return inspect.getsourcefile(obj)

def getSourceLines(obj):
    return inspect.getsourcelines(obj)

def getIndentSize(line):
    try:
        return inspect.indentsize(line)
    except Exception:
        return len(line) - len(line.lstrip())

checkIsAbstract = inspect.isabstract
checkIsAsyncGenerator = inspect.isasyncgen
checkIsAsyncGeneratorFunction = inspect.isasyncgenfunction
checkIsAwaitable = inspect.isawaitable
checkIsBuiltin = inspect.isbuiltin
checkIsClass = inspect.isclass
checkIsCode = inspect.iscode
checkIsCoroutine = inspect.iscoroutine
checkIsCoroutineFunction = inspect.iscoroutinefunction
checkIsDataDescriptor = inspect.isdatadescriptor
checkIsFrame = inspect.isframe
checkIsFunction = inspect.isfunction
checkIsGenerator = inspect.isgenerator
checkIsGeneratorFunction = inspect.isgeneratorfunction
checkIsGetSetDescriptor = inspect.isgetsetdescriptor
checkIsMemberDescriptor = inspect.ismemberdescriptor
checkIsMethod = inspect.ismethod
checkIsMethodDescriptor = inspect.ismethoddescriptor
checkIsMethodWrapper = ismethodwrapper
checkIsModule = inspect.ismodule
checkIsRoutine = inspect.isroutine
checkIsTraceback = inspect.istraceback

isCoroutineFunction = inspect.iscoroutinefunction
createNamedTuple = collections.namedtuple
getSignature = inspect.signature
getStack = inspect.stack
getTrace = inspect.trace
unwrapFunction = inspect.unwrap

ArgInfo = inspect.ArgInfo
Arguments = inspect.Arguments
Attribute = inspect.Attribute
BlockFinder = inspect.BlockFinder
BoundArguments = inspect.BoundArguments

class BufferFlags:
    SIMPLE = 0
    WRITABLE = 0x0001
    FORMAT = 0x0004
    ND = 0x0008
    STRIDES = 0x0010
    C_CONTIGUOUS = 0x0020
    F_CONTIGUOUS = 0x0040
    ANY_CONTIGUOUS = 0x0080
    INDIRECT = 0x0100
    FULL = ND | STRIDES | WRITABLE | FORMAT
    FULL_RO = ND | STRIDES | FORMAT

ClosureVars = inspect.ClosureVars
EndOfBlock = inspect.EndOfBlock
FrameInfo = inspect.FrameInfo
FullArgSpec = inspect.FullArgSpec
OrderedDict = collections.OrderedDict
Parameter = inspect.Parameter
Signature = inspect.Signature
Traceback = inspect.Traceback

attrgetter = inspect.attrgetter
makeWeakReference = weakref.ref

try:
    AGENCLOSED = inspect.AGEN_CLOSED
except Exception:
    AGENCLOSED = None
try:
    AGENCREATED = inspect.AGEN_CREATED
except Exception:
    AGENCREATED = None
try:
    AGENRUNNING = inspect.AGEN_RUNNING
except Exception:
    AGENRUNNING = None
try:
    AGENSUSPENDED = inspect.AGEN_SUSPENDED
except Exception:
    AGENSUSPENDED = None
try:
    COROCLOSED = inspect.CORO_CLOSED
except Exception:
    COROCLOSED = None
try:
    COROCREATED = inspect.CORO_CREATED
except Exception:
    COROCREATED = None
try:
    CORORUNNING = inspect.CORO_RUNNING
except Exception:
    CORORUNNING = None
try:
    COROSUSPENDED = inspect.CORO_SUSPENDED
except Exception:
    COROSUSPENDED = None
try:
    COASYNCGENERATOR = inspect.CO_ASYNC_GENERATOR
except Exception:
    COASYNCGENERATOR = None
try:
    COCOROUTINE = inspect.CO_COROUTINE
except Exception:
    COCOROUTINE = None
try:
    COGENERATOR = inspect.CO_GENERATOR
except Exception:
    COGENERATOR = None
try:
    COITERABLE_COROUTINE = inspect.CO_ITERABLE_COROUTINE
except Exception:
    COITERABLE_COROUTINE = None
try:
    CONESTED = inspect.CO_NESTED
except Exception:
    CONESTED = None
try:
    CONEWLOCALS = inspect.CO_NEWLOCALS
except Exception:
    CONEWLOCALS = None
try:
    CONOFREE = inspect.CO_NOFREE
except Exception:
    CONOFREE = None
try:
    COOPTIMIZED = inspect.CO_OPTIMIZED
except Exception:
    COOPTIMIZED = None
try:
    COVARARGS = inspect.CO_VARARGS
except Exception:
    COVARARGS = None
try:
    COVARKEYWORDS = inspect.CO_VARKEYWORDS
except Exception:
    COVARKEYWORDS = None
try:
    GENCLOSED = inspect.GEN_CLOSED
except Exception:
    GENCLOSED = None
try:
    GENCREATED = inspect.GEN_CREATED
except Exception:
    GENCREATED = None
try:
    GENRUNNING = inspect.GEN_RUNNING
except Exception:
    GENRUNNING = None
try:
    GENSUSPENDED = inspect.GEN_SUSPENDED
except Exception:
    GENSUSPENDED = None
try:
    TPFLAGSISABSTRACT = inspect.TPFLAGS_IS_ABSTRACT
except Exception:
    TPFLAGSISABSTRACT = None

inspectabc = inspect.abc
inspectbuiltins = inspect.builtins
inspectcollections = inspect.collections
inspectdis = inspect.dis
inspectenum = inspect.enum
inspectfunctools = inspect.functools
inspectimportlib = inspect.importlib
def inspectiskeyword(string): return keyword.iskeyword(string)
inspectitertools = inspect.itertools
inspectlinecache = inspect.linecache
inspectos = inspect.os
inspectre = inspect.re
inspectsys = inspect.sys
inspecttoken = inspect.token
inspecttokenize = inspect.tokenize
inspecttypes = inspect.types
