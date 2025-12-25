"""
The system module contains low-level routines for I/O, timing, random
number generation etc. The Inoutput type is used to abstract both
formatted and unformatted(i.e. binary) I/O.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

Module system_module
Defined at System.fpp lines 137-2951
"""
from __future__ import print_function, absolute_import, division
import quippy._quippy
import f90wrap.runtime
import logging
import numpy
import warnings
import weakref

logger = logging.getLogger(__name__)
warnings.filterwarnings("error", category=numpy.exceptions.ComplexWarning)
_arrays = {}
_objs = {}

@f90wrap.runtime.register_class("quippy.Stack")
class Stack(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=stack)
    Defined at System.fpp lines 154-156
    """
    def __init__(self, value=None, handle=None):
        """
        self = Stack([value])
        Defined at System.fpp lines 2292-2302
        
        Parameters
        ----------
        value : int32
        
        Returns
        -------
        this : Stack
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_system_module__stack_initialise(value=value)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_system_module__stack_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def print(self, verbosity=None, out=None, interface_call=False):
        """
        Overloaded interface for printing. With the
        'this' parameter omitted output goes to the default mainlog('stdout'). The
        'verbosity' parameter controls whether the object is actually printed;
        if the verbosity is greater than that currently at the top of the
        verbosity stack then output is suppressed. Possible verbosity levels
        range from 'ERROR' through 'NORMAL', 'VERBOSE', 'NERD' and 'ANALYSIS'.
        Other user-defined types define the Print interface in the same way.
        
        print(self[, verbosity, out])
        Defined at System.fpp lines 2343-2351
        
        Parameters
        ----------
        this : Stack
        verbosity : int32
        out : Inoutput
        """
        quippy._quippy.f90wrap_system_module__stack_print(this=self._handle, verbosity=verbosity, out=None if out is None else \
            out._handle)
    
    def push(self, val, interface_call=False):
        """
        push(self, val)
        Defined at System.fpp lines 2308-2324
        
        Parameters
        ----------
        this : Stack
        val : int32
        """
        quippy._quippy.f90wrap_system_module__stack_push(this=self._handle, val=val)
    
    def pop(self, interface_call=False):
        """
        pop(self)
        Defined at System.fpp lines 2326-2332
        
        Parameters
        ----------
        this : Stack
        """
        quippy._quippy.f90wrap_system_module__stack_pop(this=self._handle)
    
    def value(self, interface_call=False):
        """
        stack_value = value(self)
        Defined at System.fpp lines 2334-2341
        
        Parameters
        ----------
        this : Stack
        
        Returns
        -------
        stack_value : int32
        """
        stack_value = quippy._quippy.f90wrap_system_module__stack_value(this=self._handle)
        return stack_value
    
    @property
    def pos(self):
        """
        Element pos ftype=integer pytype=int32
        Defined at System.fpp line 155
        """
        return quippy._quippy.f90wrap_stack__get__pos(self._handle)
    
    @pos.setter
    def pos(self, pos):
        quippy._quippy.f90wrap_stack__set__pos(self._handle, pos)
    
    @property
    def val(self):
        """
        Element val ftype=integer pytype=int array
        Defined at System.fpp line 156
        """
        array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_stack__array__val(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        val = self._arrays.get(array_hash)
        if val is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if val.ctypes.data != array_handle:
                val = None
        if val is None:
            try:
                val = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_stack__array__val)
            except TypeError:
                val = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = val
        return val
    
    @val.setter
    def val(self, val):
        self.val[...] = val
    
    def __str__(self):
        ret = ['<stack>{\n']
        ret.append('    pos : ')
        ret.append(repr(self.pos))
        ret.append(',\n    val : ')
        ret.append(repr(self.val))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

@f90wrap.runtime.register_class("quippy.InOutput")
class InOutput(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=inoutput)
    Defined at System.fpp lines 158-170
    """
    def rewind(self, interface_call=False):
        """
        Rewind to the start of this file. Works for both formatted and unformatted files.
        
        rewind(self)
        Defined at System.fpp lines 1637-1639
        
        Parameters
        ----------
        this : Inoutput
        """
        quippy._quippy.f90wrap_system_module__rewind(this=self._handle)
    
    def __init__(self, filename=None, action=None, isformatted=None, append=None, verbosity=None, verbosity_cascade=None, \
        master_only=None, unit=None, error=None, handle=None):
        """
        Open a file for reading or writing. The action optional parameter can
        be one of 'INPUT' (default), 'OUTPUT' or 'INOUT'.
        For unformatted output, the
        'isformatted' optional parameter must
        be set to false.
        
        self = Inoutput([filename, action, isformatted, append, verbosity, verbosity_cascade, master_only, unit, error])
        Defined at System.fpp lines 450-559
        
        Parameters
        ----------
        filename : str
        action : int32
        isformatted : bool
        append : bool
        verbosity : int32
        verbosity_cascade : int32
        master_only : bool
        unit : int32
        error : int32
        
        Returns
        -------
        this : Inoutput
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_system_module__inoutput_initialise(filename=filename, action=action, \
                isformatted=isformatted, append=append, verbosity=verbosity, verbosity_cascade=verbosity_cascade, \
                master_only=master_only, unit=unit, error=error)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_system_module__inoutput_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def activate(self, interface_call=False):
        """
        Activate an Inoutput object temporarily.
        
        activate(self)
        Defined at System.fpp lines 583-585
        
        Parameters
        ----------
        this : Inoutput
        """
        quippy._quippy.f90wrap_system_module__inoutput_activate(this=self._handle)
    
    def deactivate(self, interface_call=False):
        """
        Deactivate an Inoutput object temporarily.
        
        deactivate(self)
        Defined at System.fpp lines 578-580
        
        Parameters
        ----------
        this : Inoutput
        """
        quippy._quippy.f90wrap_system_module__inoutput_deactivate(this=self._handle)
    
    def mpi_all_inoutput(self, value=None, interface_call=False):
        """
        mpi_all_inoutput(self[, value])
        Defined at System.fpp lines 602-609
        
        Parameters
        ----------
        this : Inoutput
        value : bool
        """
        quippy._quippy.f90wrap_system_module__inoutput_mpi_all_inoutput(this=self._handle, value=value)
    
    def print_mpi_id(self, value=None, interface_call=False):
        """
        print_mpi_id(self[, value])
        Defined at System.fpp lines 611-618
        
        Parameters
        ----------
        this : Inoutput
        value : bool
        """
        quippy._quippy.f90wrap_system_module__inoutput_print_mpi_id(this=self._handle, value=value)
    
    def print_inoutput(self, interface_call=False):
        """
        Overloaded interface for printing. With the
        'this' parameter omitted output goes to the default mainlog('stdout'). The
        'verbosity' parameter controls whether the object is actually printed;
        if the verbosity is greater than that currently at the top of the
        verbosity stack then output is suppressed. Possible verbosity levels
        range from 'ERROR' through 'NORMAL', 'VERBOSE', 'NERD' and 'ANALYSIS'.
        Other user-defined types define the Print interface in the same way.
        
        print_inoutput(self)
        Defined at System.fpp lines 737-756
        
        Parameters
        ----------
        this : Inoutput
        """
        quippy._quippy.f90wrap_system_module__print_inoutput(this=self._handle)
    
    def read_line(self, status=None, interface_call=False):
        """
        Read a line of text from a file(up to a line break, or 1024 characters).
        This can then be parsed by the calling routine(using 'parse_line' for example)
        
        Optionally, a status is returned which is:
        
        \\begin{itemize}
        \\item $<0$ if the end of the file is reached
        \\item $=0$ if no problems were encountered
        \\item $>0$ if there was a read error
        \\end{itemize}
        
        The actual number returned is implementation specific
        
        inoutput_read_line = read_line(self[, status])
        Defined at System.fpp lines 802-814
        
        Parameters
        ----------
        this : Inoutput
        status : int32
        
        Returns
        -------
        inoutput_read_line : str
        """
        inoutput_read_line = quippy._quippy.f90wrap_system_module__inoutput_read_line(this=self._handle, status=status)
        return inoutput_read_line
    
    def parse_line(self, delimiters, fields, status=None, interface_call=False):
        """
        Call parse_string on the next line from a file
        
        num_fields = parse_line(self, delimiters, fields[, status])
        Defined at System.fpp lines 879-889
        
        Parameters
        ----------
        this : Inoutput
        delimiters : str
        fields : str array
        status : int32
        
        Returns
        -------
        num_fields : int32
        """
        num_fields = quippy._quippy.f90wrap_system_module__inoutput_parse_line(this=self._handle, delimiters=delimiters, \
            fields=fields, status=status)
        return num_fields
    
    def reada_real_dim1(self, da, status=None, interface_call=False):
        """
        Read scalar and array data from ascii files. These
        interfaces are not yet heavily overloaded to cater for all intrinsic and most
        derived types.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        
        reada_real_dim1(self, da[, status])
        Defined at System.fpp lines 1608-1620
        
        Parameters
        ----------
        this : Inoutput
        da : float array
        status : int32
        """
        quippy._quippy.f90wrap_system_module__reada_real_dim1(this=self._handle, da=da, status=status)
    
    def reada_int_dim1(self, ia, status=None, interface_call=False):
        """
        reada_int_dim1(self, ia[, status])
        Defined at System.fpp lines 1622-1634
        
        Parameters
        ----------
        this : Inoutput
        ia : int array
        status : int32
        """
        quippy._quippy.f90wrap_system_module__reada_int_dim1(this=self._handle, ia=ia, status=status)
    
    def read_ascii(*args, **kwargs):
        """
        read_ascii(*args, **kwargs)
        Defined at System.fpp lines 261-262
        
        Overloaded interface containing the following procedures:
          reada_real_dim1
          reada_int_dim1
        """
        for proc in [InOutput.reada_real_dim1, InOutput.reada_int_dim1]:
            exception=None
            try:
                return proc(*args, **kwargs, interface_call=True)
            except (TypeError, ValueError, AttributeError, IndexError, numpy.exceptions.ComplexWarning) as err:
                exception = "'%s: %s'" % (type(err).__name__, str(err))
                continue
        
        argTypes=[]
        for arg in args:
            try:
                argTypes.append("%s: dims '%s', type '%s',"
                " type code '%s'"
                %(str(type(arg)),arg.ndim, arg.dtype, arg.dtype.num))
            except AttributeError:
                argTypes.append(str(type(arg)))
        raise TypeError("Not able to call a version of "
            "read_ascii compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    @property
    def unit(self):
        """
        Element unit ftype=integer pytype=int32
        Defined at System.fpp line 159
        """
        return quippy._quippy.f90wrap_inoutput__get__unit(self._handle)
    
    @unit.setter
    def unit(self, unit):
        quippy._quippy.f90wrap_inoutput__set__unit(self._handle, unit)
    
    @property
    def filename(self):
        """
        Element filename ftype=character(256) pytype=str
        Defined at System.fpp line 160
        """
        return quippy._quippy.f90wrap_inoutput__get__filename(self._handle)
    
    @filename.setter
    def filename(self, filename):
        quippy._quippy.f90wrap_inoutput__set__filename(self._handle, filename)
    
    @property
    def prefix(self):
        """
        Element prefix ftype=character(256) pytype=str
        Defined at System.fpp line 161
        """
        return quippy._quippy.f90wrap_inoutput__get__prefix(self._handle)
    
    @prefix.setter
    def prefix(self, prefix):
        quippy._quippy.f90wrap_inoutput__set__prefix(self._handle, prefix)
    
    @property
    def postfix(self):
        """
        Element postfix ftype=character(256) pytype=str
        Defined at System.fpp line 161
        """
        return quippy._quippy.f90wrap_inoutput__get__postfix(self._handle)
    
    @postfix.setter
    def postfix(self, postfix):
        quippy._quippy.f90wrap_inoutput__set__postfix(self._handle, postfix)
    
    @property
    def default_real_precision(self):
        """
        Element default_real_precision ftype=integer pytype=int32
        Defined at System.fpp line 162
        """
        return quippy._quippy.f90wrap_inoutput__get__default_real_precision(self._handle)
    
    @default_real_precision.setter
    def default_real_precision(self, default_real_precision):
        quippy._quippy.f90wrap_inoutput__set__default_real_precision(self._handle, default_real_precision)
    
    @property
    def formatted(self):
        """
        Element formatted ftype=logical pytype=bool
        Defined at System.fpp line 163
        """
        return quippy._quippy.f90wrap_inoutput__get__formatted(self._handle)
    
    @formatted.setter
    def formatted(self, formatted):
        quippy._quippy.f90wrap_inoutput__set__formatted(self._handle, formatted)
    
    @property
    def append(self):
        """
        Element append ftype=logical pytype=bool
        Defined at System.fpp line 164
        """
        return quippy._quippy.f90wrap_inoutput__get__append(self._handle)
    
    @append.setter
    def append(self, append):
        quippy._quippy.f90wrap_inoutput__set__append(self._handle, append)
    
    @property
    def active(self):
        """
        Does it print?
        
        Element active ftype=logical pytype=bool
        Defined at System.fpp line 165
        """
        return quippy._quippy.f90wrap_inoutput__get__active(self._handle)
    
    @active.setter
    def active(self, active):
        quippy._quippy.f90wrap_inoutput__set__active(self._handle, active)
    
    @property
    def action(self):
        """
        Element action ftype=integer pytype=int32
        Defined at System.fpp line 166
        """
        return quippy._quippy.f90wrap_inoutput__get__action(self._handle)
    
    @action.setter
    def action(self, action):
        quippy._quippy.f90wrap_inoutput__set__action(self._handle, action)
    
    @property
    def mpi_all_inoutput_flag(self):
        """
        Element mpi_all_inoutput_flag ftype=logical pytype=bool
        Defined at System.fpp line 167
        """
        return quippy._quippy.f90wrap_inoutput__get__mpi_all_inoutput_flag(self._handle)
    
    @mpi_all_inoutput_flag.setter
    def mpi_all_inoutput_flag(self, mpi_all_inoutput_flag):
        quippy._quippy.f90wrap_inoutput__set__mpi_all_inoutput_flag(self._handle, mpi_all_inoutput_flag)
    
    @property
    def mpi_print_id(self):
        """
        Element mpi_print_id ftype=logical pytype=bool
        Defined at System.fpp line 168
        """
        return quippy._quippy.f90wrap_inoutput__get__mpi_print_id(self._handle)
    
    @mpi_print_id.setter
    def mpi_print_id(self, mpi_print_id):
        quippy._quippy.f90wrap_inoutput__set__mpi_print_id(self._handle, mpi_print_id)
    
    @property
    def verbosity_stack(self):
        """
        Element verbosity_stack ftype=type(stack) pytype=Stack
        Defined at System.fpp line 169
        """
        verbosity_stack_handle = quippy._quippy.f90wrap_inoutput__get__verbosity_stack(self._handle)
        if tuple(verbosity_stack_handle) in self._objs:
            verbosity_stack = self._objs[tuple(verbosity_stack_handle)]
        else:
            verbosity_stack = Stack.from_handle(verbosity_stack_handle)
            self._objs[tuple(verbosity_stack_handle)] = verbosity_stack
        return verbosity_stack
    
    @verbosity_stack.setter
    def verbosity_stack(self, verbosity_stack):
        verbosity_stack = verbosity_stack._handle
        quippy._quippy.f90wrap_inoutput__set__verbosity_stack(self._handle, verbosity_stack)
    
    @property
    def verbosity_cascade_stack(self):
        """
        Element verbosity_cascade_stack ftype=type(stack) pytype=Stack
        Defined at System.fpp line 169
        """
        verbosity_cascade_stack_handle = quippy._quippy.f90wrap_inoutput__get__verbosity_cascade_stack(self._handle)
        if tuple(verbosity_cascade_stack_handle) in self._objs:
            verbosity_cascade_stack = self._objs[tuple(verbosity_cascade_stack_handle)]
        else:
            verbosity_cascade_stack = Stack.from_handle(verbosity_cascade_stack_handle)
            self._objs[tuple(verbosity_cascade_stack_handle)] = verbosity_cascade_stack
        return verbosity_cascade_stack
    
    @verbosity_cascade_stack.setter
    def verbosity_cascade_stack(self, verbosity_cascade_stack):
        verbosity_cascade_stack = verbosity_cascade_stack._handle
        quippy._quippy.f90wrap_inoutput__set__verbosity_cascade_stack(self._handle, verbosity_cascade_stack)
    
    @property
    def initialised(self):
        """
        Element initialised ftype=logical pytype=bool
        Defined at System.fpp line 170
        """
        return quippy._quippy.f90wrap_inoutput__get__initialised(self._handle)
    
    @initialised.setter
    def initialised(self, initialised):
        quippy._quippy.f90wrap_inoutput__set__initialised(self._handle, initialised)
    
    def __str__(self):
        ret = ['<inoutput>{\n']
        ret.append('    unit : ')
        ret.append(repr(self.unit))
        ret.append(',\n    filename : ')
        ret.append(repr(self.filename))
        ret.append(',\n    prefix : ')
        ret.append(repr(self.prefix))
        ret.append(',\n    postfix : ')
        ret.append(repr(self.postfix))
        ret.append(',\n    default_real_precision : ')
        ret.append(repr(self.default_real_precision))
        ret.append(',\n    formatted : ')
        ret.append(repr(self.formatted))
        ret.append(',\n    append : ')
        ret.append(repr(self.append))
        ret.append(',\n    active : ')
        ret.append(repr(self.active))
        ret.append(',\n    action : ')
        ret.append(repr(self.action))
        ret.append(',\n    mpi_all_inoutput_flag : ')
        ret.append(repr(self.mpi_all_inoutput_flag))
        ret.append(',\n    mpi_print_id : ')
        ret.append(repr(self.mpi_print_id))
        ret.append(',\n    verbosity_stack : ')
        ret.append(repr(self.verbosity_stack))
        ret.append(',\n    verbosity_cascade_stack : ')
        ret.append(repr(self.verbosity_cascade_stack))
        ret.append(',\n    initialised : ')
        ret.append(repr(self.initialised))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

@f90wrap.runtime.register_class("quippy.allocatable_array_pointers")
class allocatable_array_pointers(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=allocatable_array_pointers)
    Defined at System.fpp lines 172-176
    """
    def __init__(self, handle=None):
        """
        Automatically generated constructor for allocatable_array_pointers
        
        self = Allocatable_Array_Pointers()
        Defined at System.fpp lines 172-176
        
        Returns
        -------
        this : Allocatable_Array_Pointers
            Object to be constructed
        
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_system_module__allocatable_array_pointers_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_system_module__allocatable_array_pointers_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    @property
    def i_a(self):
        """
        Element i_a ftype=integer pytype=int array
        Defined at System.fpp line 173
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_allocatable_array_pointers__array__i_a(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        i_a = self._arrays.get(array_hash)
        if i_a is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if i_a.ctypes.data != array_handle:
                i_a = None
        if i_a is None:
            try:
                i_a = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_allocatable_array_pointers__array__i_a)
            except TypeError:
                i_a = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = i_a
        return i_a
    
    @i_a.setter
    def i_a(self, i_a):
        self.i_a[...] = i_a
    
    @property
    def r_a(self):
        """
        Element r_a ftype=real(dp) pytype=float array
        Defined at System.fpp line 174
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_allocatable_array_pointers__array__r_a(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        r_a = self._arrays.get(array_hash)
        if r_a is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if r_a.ctypes.data != array_handle:
                r_a = None
        if r_a is None:
            try:
                r_a = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_allocatable_array_pointers__array__r_a)
            except TypeError:
                r_a = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = r_a
        return r_a
    
    @r_a.setter
    def r_a(self, r_a):
        self.r_a[...] = r_a
    
    @property
    def c_a(self):
        """
        Element c_a ftype=complex(dp) pytype=complex array
        Defined at System.fpp line 175
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_allocatable_array_pointers__array__c_a(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        c_a = self._arrays.get(array_hash)
        if c_a is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if c_a.ctypes.data != array_handle:
                c_a = None
        if c_a is None:
            try:
                c_a = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_allocatable_array_pointers__array__c_a)
            except TypeError:
                c_a = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = c_a
        return c_a
    
    @c_a.setter
    def c_a(self, c_a):
        self.c_a[...] = c_a
    
    @property
    def l_a(self):
        """
        Element l_a ftype=logical pytype=int32 array
        Defined at System.fpp line 176
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_allocatable_array_pointers__array__l_a(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        l_a = self._arrays.get(array_hash)
        if l_a is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if l_a.ctypes.data != array_handle:
                l_a = None
        if l_a is None:
            try:
                l_a = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_allocatable_array_pointers__array__l_a)
            except TypeError:
                l_a = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = l_a
        return l_a
    
    @l_a.setter
    def l_a(self, l_a):
        self.l_a[...] = l_a
    
    def __str__(self):
        ret = ['<allocatable_array_pointers>{\n']
        ret.append('    i_a : ')
        ret.append(repr(self.i_a))
        ret.append(',\n    r_a : ')
        ret.append(repr(self.r_a))
        ret.append(',\n    c_a : ')
        ret.append(repr(self.c_a))
        ret.append(',\n    l_a : ')
        ret.append(repr(self.l_a))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

def is_open(unit, interface_call=False):
    """
    OMIT
    
    is_open = is_open(unit)
    Defined at System.fpp lines 562-565
    
    Parameters
    ----------
    unit : int32
    
    Returns
    -------
    is_open : bool
    """
    is_open = quippy._quippy.f90wrap_system_module__is_open(unit=unit)
    return is_open

def print_title(title, verbosity=None, interface_call=False):
    """
    Print a centred title, like this:
    
    '==================================== Title ====================================='
    
    print_title(title[, verbosity])
    Defined at System.fpp lines 768-783
    
    Parameters
    ----------
    title : str
    verbosity : int32
    """
    quippy._quippy.f90wrap_system_module__print_title(title=title, verbosity=verbosity)

def split_string_simple(str, fields, separators, error=None, interface_call=False):
    """
    split a string into fields separated by possible separators
    no quoting, matching separators, just a simple split
    
    n_fields = split_string_simple(str, fields, separators[, error])
    Defined at System.fpp lines 893-923
    
    Parameters
    ----------
    str : str
        string to be split
    
    fields : str array
        on return, array of fields
    
    separators : str
        string of possible separators
    
    error : int32
    
    Returns
    -------
    n_fields : int32
        on return, number of fields
    
    """
    n_fields = quippy._quippy.f90wrap_system_module__split_string_simple(str=str, fields=fields, separators=separators, \
        error=error)
    return n_fields

def num_fields_in_string_simple(this, separators, interface_call=False):
    """
    num_fields_in_string_simple = num_fields_in_string_simple(this, separators)
    Defined at System.fpp lines 925-934
    
    Parameters
    ----------
    this : str
    separators : str
    
    Returns
    -------
    num_fields_in_string_simple : int32
    """
    num_fields_in_string_simple = quippy._quippy.f90wrap_system_module__num_fields_in_string_simple(this=this, \
        separators=separators)
    return num_fields_in_string_simple

def split_string(this, separators, quotes, fields, matching=None, interface_call=False):
    """
    split a string at separators, making sure not to break up bits that
    are in quotes(possibly matching opening and closing quotes), and
    also strip one level of quotes off, sort of like a shell would when
    tokenizing
    
    num_fields = split_string(this, separators, quotes, fields[, matching])
    Defined at System.fpp lines 940-1072
    
    Parameters
    ----------
    this : str
    separators : str
    quotes : str
    fields : str array
    matching : bool
    
    Returns
    -------
    num_fields : int32
    """
    num_fields = quippy._quippy.f90wrap_system_module__split_string(this=this, separators=separators, quotes=quotes, \
        fields=fields, matching=matching)
    return num_fields

def parse_string(this, delimiters, fields, matching=None, error=None, interface_call=False):
    """
    outdated - please use split_string
    Parse a string into fields delimited by certain characters. On exit
    the 'fields' array will contain one field per entry and 'num_fields'
    gives the total number of fields. 'status' will be given the error status
    (if present) and so can be used to tell if an end-of-file occurred.
    
    num_fields = parse_string(this, delimiters, fields[, matching, error])
    Defined at System.fpp lines 1098-1189
    
    Parameters
    ----------
    this : str
    delimiters : str
    fields : str array
    matching : bool
    error : int32
    
    Returns
    -------
    num_fields : int32
    """
    num_fields = quippy._quippy.f90wrap_system_module__parse_string(this=this, delimiters=delimiters, fields=fields, \
        matching=matching, error=error)
    return num_fields

def string_to_int(string_bn, error=None, interface_call=False):
    """
    Convert an input string into an integer.
    
    string_to_int = string_to_int(string_bn[, error])
    Defined at System.fpp lines 1282-1292
    
    Parameters
    ----------
    string_bn : str
    error : int32
    
    Returns
    -------
    string_to_int : int32
    """
    string_to_int = quippy._quippy.f90wrap_system_module__string_to_int(string_bn=string_bn, error=error)
    return string_to_int

def string_to_logical(string_bn, error=None, interface_call=False):
    """
    Convert an input string into a logical.
    
    string_to_logical = string_to_logical(string_bn[, error])
    Defined at System.fpp lines 1295-1307
    
    Parameters
    ----------
    string_bn : str
    error : int32
    
    Returns
    -------
    string_to_logical : bool
    """
    string_to_logical = quippy._quippy.f90wrap_system_module__string_to_logical(string_bn=string_bn, error=error)
    return string_to_logical

def string_to_real(string_bn, error=None, interface_call=False):
    """
    Convert an input string into a real.
    
    string_to_real = string_to_real(string_bn[, error])
    Defined at System.fpp lines 1310-1320
    
    Parameters
    ----------
    string_bn : str
    error : int32
    
    Returns
    -------
    string_to_real : float64
    """
    string_to_real = quippy._quippy.f90wrap_system_module__string_to_real(string_bn=string_bn, error=error)
    return string_to_real

def round(r, digits, interface_call=False):
    """
    Concatenation functions.
    Overloadings for the // operator to make strings from various other types.
    In each case, we need to work out the exact length of the resultant string
    in order to avoid printing excess spaces.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    Return a string which is the real number 'r' rounded to 'digits' decimal digits
    
    round = round(r, digits)
    Defined at System.fpp lines 1664-1676
    
    Parameters
    ----------
    r : float64
    digits : int32
    
    Returns
    -------
    round : str
    """
    round = quippy._quippy.f90wrap_system_module__round(r=r, digits=digits)
    return round

def get_mpi_size_rank(comm, interface_call=False):
    """
    Return the mpi size and rank for the communicator 'comm'.
    this routine aborts of _MPI is not defined
    
    nproc, rank_bn = get_mpi_size_rank(comm)
    Defined at System.fpp lines 1895-1901
    
    Parameters
    ----------
    comm : int32
        MPI communicator
    
    Returns
    -------
    nproc : int32
        Total number of processes
    
    rank_bn : int32
        Rank of this process
    
    """
    nproc, rank_bn = quippy._quippy.f90wrap_system_module__get_mpi_size_rank(comm=comm)
    return nproc, rank_bn

def system_initialise(verbosity=None, seed=None, mpi_all_inoutput=None, common_seed=None, enable_timing_in=None, \
    quippy_running=None, mainlog_file=None, mainlog_unit=None, interface_call=False):
    """
    Must be called at the start of all programs. Initialises MPI if present,
    set the random number seed sets up the default Inoutput objects
    logger and errorlog to point to stdout and stderr respectively. Calls
    Hello_World to do some of the work and print a friendly welcome. If we're
    using MPI, by default we set the same random seed for each process.
    This also attempts to read the executable name, the number of command
    arguments, and the arguments themselves.
    
    system_initialise([verbosity, seed, mpi_all_inoutput, common_seed, enable_timing_in, quippy_running, mainlog_file, \
        mainlog_unit])
    Defined at System.fpp lines 1911-1968
    
    Parameters
    ----------
    verbosity : int32
        mainlog output verbosity
    
    seed : int32
        Seed for the random number generator.
    
    mpi_all_inoutput : bool
        Print on all MPI nodes(false by default)
    
    common_seed : bool
    enable_timing_in : bool
        Enable system_timer() calls
    
    quippy_running : bool
        .true. if running under quippy(Python interface)
    
    mainlog_file : str
    mainlog_unit : int32
        If 'common_seed' is true(default), random seed will be the same for each
        MPI process.
    
    """
    quippy._quippy.f90wrap_system_module__system_initialise(verbosity=verbosity, seed=seed, \
        mpi_all_inoutput=mpi_all_inoutput, common_seed=common_seed, enable_timing_in=enable_timing_in, \
        quippy_running=quippy_running, mainlog_file=mainlog_file, mainlog_unit=mainlog_unit)

def cmd_arg_count(interface_call=False):
    """
    cmd_arg_count = cmd_arg_count()
    Defined at System.fpp lines 1981-1983
    
    Returns
    -------
    cmd_arg_count : int32
    """
    cmd_arg_count = quippy._quippy.f90wrap_system_module__cmd_arg_count()
    return cmd_arg_count

def get_cmd_arg(i, status=None, interface_call=False):
    """
    arg = get_cmd_arg(i[, status])
    Defined at System.fpp lines 1985-1989
    
    Parameters
    ----------
    i : int32
    status : int32
    
    Returns
    -------
    arg : str
    """
    arg = quippy._quippy.f90wrap_system_module__get_cmd_arg(i=i, status=status)
    return arg

def get_env_var(name, status=None, interface_call=False):
    """
    arg = get_env_var(name[, status])
    Defined at System.fpp lines 1991-1996
    
    Parameters
    ----------
    name : str
    status : int32
    
    Returns
    -------
    arg : str
    """
    arg = quippy._quippy.f90wrap_system_module__get_env_var(name=name, status=status)
    return arg

def system_finalise(interface_call=False):
    """
    Shut down gracefully, finalising system objects.
    
    system_finalise()
    Defined at System.fpp lines 1999-2014
    
    """
    quippy._quippy.f90wrap_system_module__system_finalise()

def print_warning(message, interface_call=False):
    """
    Backward compatible(replaced with print_message) routine to print a warning message to log
    
    print_warning(message)
    Defined at System.fpp lines 2017-2020
    
    Parameters
    ----------
    message : str
    """
    quippy._quippy.f90wrap_system_module__print_warning(message=message)

def print_message(message_type, message, verbosity=None, interface_call=False):
    """
    Print a message to log
    
    print_message(message_type, message[, verbosity])
    Defined at System.fpp lines 2023-2028
    
    Parameters
    ----------
    message_type : str
    message : str
    verbosity : int32
    """
    quippy._quippy.f90wrap_system_module__print_message(message_type=message_type, message=message, verbosity=verbosity)

def system_set_random_seeds(seed, interface_call=False):
    """
    system_set_random_seeds(seed)
    Defined at System.fpp lines 2044-2060
    
    Parameters
    ----------
    seed : int32
    """
    quippy._quippy.f90wrap_system_module__system_set_random_seeds(seed=seed)

def system_resync_rng(interface_call=False):
    """
    system_resync_rng()
    Defined at System.fpp lines 2113-2114
    
    """
    quippy._quippy.f90wrap_system_module__system_resync_rng()

def th(n, interface_call=False):
    """
    Return the correct ordinal ending(st,nd,rd,th) for the given integer
    
    th = th(n)
    Defined at System.fpp lines 2119-2138
    
    Parameters
    ----------
    n : int32
    
    Returns
    -------
    th : str
    """
    th = quippy._quippy.f90wrap_system_module__th(n=n)
    return th

def system_reseed_rng(new_seed, interface_call=False):
    """
    Reseed the random number generator. Useful when restarting from check files.
    
    system_reseed_rng(new_seed)
    Defined at System.fpp lines 2141-2144
    
    Parameters
    ----------
    new_seed : int32
    """
    quippy._quippy.f90wrap_system_module__system_reseed_rng(new_seed=new_seed)

def system_get_random_seed(interface_call=False):
    """
    Return the current random number seed.
    
    system_get_random_seed = system_get_random_seed()
    Defined at System.fpp lines 2147-2149
    
    Returns
    -------
    system_get_random_seed : int32
    """
    system_get_random_seed = quippy._quippy.f90wrap_system_module__system_get_random_seed()
    return system_get_random_seed

def ran(interface_call=False):
    """
    Return a random integer
    
    dran = ran()
    Defined at System.fpp lines 2152-2166
    
    Returns
    -------
    dran : float64
    """
    dran = quippy._quippy.f90wrap_system_module__ran()
    return dran

def ran_uniform(interface_call=False):
    """
    Return a random real number uniformly distributed in the range [0,1]
    
    ran_uniform = ran_uniform()
    Defined at System.fpp lines 2169-2178
    
    Returns
    -------
    ran_uniform : float64
    """
    ran_uniform = quippy._quippy.f90wrap_system_module__ran_uniform()
    return ran_uniform

def ran_normal(interface_call=False):
    """
    Return random real from Normal distribution with mean zero and standard deviation one.
    
    ran_normal = ran_normal()
    Defined at System.fpp lines 2181-2189
    
    Returns
    -------
    ran_normal : float64
    """
    ran_normal = quippy._quippy.f90wrap_system_module__ran_normal()
    return ran_normal

def current_times(cpu_t=None, wall_t=None, mpi_t=None, interface_call=False):
    """
    current_times([cpu_t, wall_t, mpi_t])
    Defined at System.fpp lines 2213-2221
    
    Parameters
    ----------
    cpu_t : float64
    wall_t : float64
    mpi_t : float64
    """
    quippy._quippy.f90wrap_system_module__current_times(cpu_t=cpu_t, wall_t=wall_t, mpi_t=mpi_t)

def system_timer(name, do_always=None, time_elapsed=None, do_print=None, interface_call=False):
    """
    Measure elapsed CPU and wall clock time between pairs of calls with
    matching 'name' parameter. Calls to 'system_timer' must be properly
    nested(i.e. start and stop from different pairs can't overlap), and
    maximum depth of calls is set by the 'TIMER_STACK' parameter.
    
    >   call system_timer(name)  start the clock
    >   ...                      do something
    >   call system_timer(name)  stop clock and print elapsed time
    >
    > If optional do_always argument is true, routine will do its thing even
    > if system_do_timing is false.
    
    system_timer(name[, do_always, time_elapsed, do_print])
    Defined at System.fpp lines 2235-2275
    
    Parameters
    ----------
    name : str
        Unique identifier for this timer
    
    do_always : bool
    time_elapsed : float64
    do_print : bool
    """
    quippy._quippy.f90wrap_system_module__system_timer(name=name, do_always=do_always, time_elapsed=time_elapsed, \
        do_print=do_print)

def is_file_readable(filename, interface_call=False):
    """
    Test if the file 'filename' can be accessed.
    
    is_file_readable = is_file_readable(filename)
    Defined at System.fpp lines 2278-2290
    
    Parameters
    ----------
    filename : str
    
    Returns
    -------
    is_file_readable : bool
    """
    is_file_readable = quippy._quippy.f90wrap_system_module__is_file_readable(filename=filename)
    return is_file_readable

def verbosity_to_str(val, interface_call=False):
    """
    Map from verbsoity codes to descriptive strings
    
    str = verbosity_to_str(val)
    Defined at System.fpp lines 2354-2370
    
    Parameters
    ----------
    val : int32
    
    Returns
    -------
    str : str
    """
    str = quippy._quippy.f90wrap_system_module__verbosity_to_str(val=val)
    return str

def verbosity_of_str(str, interface_call=False):
    """
    Map from descriptive verbosity names('NORMAL', 'VERBOSE' etc.) to numbers
    
    val = verbosity_of_str(str)
    Defined at System.fpp lines 2373-2390
    
    Parameters
    ----------
    str : str
    
    Returns
    -------
    val : int32
    """
    val = quippy._quippy.f90wrap_system_module__verbosity_of_str(str=str)
    return val

def verbosity_push(val, interface_call=False):
    """
    Push a value onto the verbosity stack
    Don't ever lower the verbosity if verbosity minimum is set,
    but always push _something_
    
    verbosity_push(val)
    Defined at System.fpp lines 2395-2403
    
    Parameters
    ----------
    val : int32
    """
    quippy._quippy.f90wrap_system_module__verbosity_push(val=val)

def verbosity_pop(interface_call=False):
    """
    pop the current verbosity value off the stack
    
    verbosity_pop()
    Defined at System.fpp lines 2406-2408
    
    """
    quippy._quippy.f90wrap_system_module__verbosity_pop()

def current_verbosity(interface_call=False):
    """
    return the current value of verbosity
    
    current_verbosity = current_verbosity()
    Defined at System.fpp lines 2411-2413
    
    Returns
    -------
    current_verbosity : int32
    """
    current_verbosity = quippy._quippy.f90wrap_system_module__current_verbosity()
    return current_verbosity

def verbosity_push_increment(n=None, interface_call=False):
    """
    push the current value + n onto the stack
    
    verbosity_push_increment([n])
    Defined at System.fpp lines 2416-2421
    
    Parameters
    ----------
    n : int32
    """
    quippy._quippy.f90wrap_system_module__verbosity_push_increment(n=n)

def verbosity_push_decrement(n=None, interface_call=False):
    """
    push the current value - n onto the stack
    
    verbosity_push_decrement([n])
    Defined at System.fpp lines 2424-2429
    
    Parameters
    ----------
    n : int32
    """
    quippy._quippy.f90wrap_system_module__verbosity_push_decrement(n=n)

def verbosity_set_minimum(verbosity, interface_call=False):
    """
    set the minimum verbosity value, by pushing value onto
    stack and pushing 1 on to verbosity_cascade_stack
    
    verbosity_set_minimum(verbosity)
    Defined at System.fpp lines 2433-2436
    
    Parameters
    ----------
    verbosity : int32
    """
    quippy._quippy.f90wrap_system_module__verbosity_set_minimum(verbosity=verbosity)

def verbosity_unset_minimum(interface_call=False):
    """
    unset the minimum verbosity value, by popping value from
    stack and popping from verbosity_cascade_stack
    
    verbosity_unset_minimum()
    Defined at System.fpp lines 2440-2442
    
    """
    quippy._quippy.f90wrap_system_module__verbosity_unset_minimum()

def enable_timing(interface_call=False):
    """
    enable_timing()
    Defined at System.fpp lines 2524-2525
    
    """
    quippy._quippy.f90wrap_system_module__enable_timing()

def get_quippy_running(interface_call=False):
    """
    get_quippy_running = get_quippy_running()
    Defined at System.fpp lines 2538-2540
    
    Returns
    -------
    get_quippy_running : bool
    """
    get_quippy_running = quippy._quippy.f90wrap_system_module__get_quippy_running()
    return get_quippy_running

def increase_stack(stack_size, interface_call=False):
    """
    increase_stack = increase_stack(stack_size)
    Defined at System.fpp lines 2542-2546
    
    Parameters
    ----------
    stack_size : int32
    
    Returns
    -------
    increase_stack : int32
    """
    increase_stack = quippy._quippy.f90wrap_system_module__increase_stack(stack_size=stack_size)
    return increase_stack

def abort_on_mpi_error(error_code, routine_name, interface_call=False):
    """
    Abort with a useful message if an MPI routine returned an error status
    
    abort_on_mpi_error(error_code, routine_name)
    Defined at System.fpp lines 2549-2554
    
    Parameters
    ----------
    error_code : int32
    routine_name : str
    """
    quippy._quippy.f90wrap_system_module__abort_on_mpi_error(error_code=error_code, routine_name=routine_name)

def parallel_print(lines, comm, verbosity=None, file=None, interface_call=False):
    """
    parallel_print(lines, comm[, verbosity, file])
    Defined at System.fpp lines 2556-2566
    
    Parameters
    ----------
    lines : str array
    comm : int32
    verbosity : int32
    file : Inoutput
    """
    quippy._quippy.f90wrap_system_module__parallel_print(lines=lines, comm=comm, verbosity=verbosity, file=None if file is \
        None else file._handle)

def alloc_trace(str, amt, interface_call=False):
    """
    alloc_trace(str, amt)
    Defined at System.fpp lines 2568-2574
    
    Parameters
    ----------
    str : str
    amt : int32
    """
    quippy._quippy.f90wrap_system_module__alloc_trace(str=str, amt=amt)

def dealloc_trace(str, amt, interface_call=False):
    """
    dealloc_trace(str, amt)
    Defined at System.fpp lines 2576-2582
    
    Parameters
    ----------
    str : str
    amt : int32
    """
    quippy._quippy.f90wrap_system_module__dealloc_trace(str=str, amt=amt)

def mpi_id(interface_call=False):
    """
    Return this processes' MPI ID
    
    id = mpi_id()
    Defined at System.fpp lines 2591-2593
    
    Returns
    -------
    id : int32
    """
    id = quippy._quippy.f90wrap_system_module__mpi_id()
    return id

def mpi_n_procs(interface_call=False):
    """
    Return the total number of MPI processes.
    
    n = mpi_n_procs()
    Defined at System.fpp lines 2596-2598
    
    Returns
    -------
    n : int32
    """
    n = quippy._quippy.f90wrap_system_module__mpi_n_procs()
    return n

def reference_true(interface_call=False):
    """
    reference_true = reference_true()
    Defined at System.fpp lines 2600-2602
    
    Returns
    -------
    reference_true : bool
    """
    reference_true = quippy._quippy.f90wrap_system_module__reference_true()
    return reference_true

def reference_false(interface_call=False):
    """
    reference_false = reference_false()
    Defined at System.fpp lines 2604-2606
    
    Returns
    -------
    reference_false : bool
    """
    reference_false = quippy._quippy.f90wrap_system_module__reference_false()
    return reference_false

def s2a(s, interface_call=False):
    """
    String to character array
    
    a = s2a(s)
    Defined at System.fpp lines 2609-2615
    
    Parameters
    ----------
    s : str
    
    Returns
    -------
    a : str array
    """
    a = quippy._quippy.f90wrap_system_module__s2a(s=s, f90wrap_n0=s.shape[0])
    return a

def a2s(a, interface_call=False):
    """
    Character array to string
    
    s = a2s(a)
    Defined at System.fpp lines 2618-2624
    
    Parameters
    ----------
    a : str array
    
    Returns
    -------
    s : str
    """
    s = quippy._quippy.f90wrap_system_module__a2s(a=a)
    return s

def pad(s, l, interface_call=False):
    """
    String to padded character array of length l
    
    a = pad(s, l)
    Defined at System.fpp lines 2627-2635
    
    Parameters
    ----------
    s : str
    l : int32
    
    Returns
    -------
    a : str array
    """
    a = quippy._quippy.f90wrap_system_module__pad(s=s, l=l, f90wrap_n0=l)
    return a

def make_run_directory(basename=None, force_run_dir_i=None, run_dir_i=None, error=None, interface_call=False):
    """
    dir = make_run_directory([basename, force_run_dir_i, run_dir_i, error])
    Defined at System.fpp lines 2637-2672
    
    Parameters
    ----------
    basename : str
    force_run_dir_i : int32
    run_dir_i : int32
    error : int32
    
    Returns
    -------
    dir : str
    """
    dir = quippy._quippy.f90wrap_system_module__make_run_directory(basename=basename, force_run_dir_i=force_run_dir_i, \
        run_dir_i=run_dir_i, error=error)
    return dir

def link_run_directory(sourcename, basename=None, run_dir_i=None, error=None, interface_call=False):
    """
    dir = link_run_directory(sourcename[, basename, run_dir_i, error])
    Defined at System.fpp lines 2674-2698
    
    Parameters
    ----------
    sourcename : str
    basename : str
    run_dir_i : int32
    error : int32
    
    Returns
    -------
    dir : str
    """
    dir = quippy._quippy.f90wrap_system_module__link_run_directory(sourcename=sourcename, basename=basename, \
        run_dir_i=run_dir_i, error=error)
    return dir

def linebreak_string(str, line_len, interface_call=False):
    """
    lb_str = linebreak_string(str, line_len)
    Defined at System.fpp lines 2710-2748
    
    Parameters
    ----------
    str : str
    line_len : int32
    
    Returns
    -------
    lb_str : str
    """
    lb_str = quippy._quippy.f90wrap_system_module__linebreak_string(str=str, line_len=line_len)
    return lb_str

def wait_for_file_to_exist(filename, max_wait_time, cycle_time=None, error=None, interface_call=False):
    """
    wait_for_file_to_exist(filename, max_wait_time[, cycle_time, error])
    Defined at System.fpp lines 2768-2788
    
    Parameters
    ----------
    filename : str
    max_wait_time : float64
    cycle_time : float64
    error : int32
    """
    quippy._quippy.f90wrap_system_module__wait_for_file_to_exist(filename=filename, max_wait_time=max_wait_time, \
        cycle_time=cycle_time, error=error)

def upper_case(word, interface_call=False):
    """
    Convert a word to upper case
    
    upper_case = upper_case(word)
    Defined at System.fpp lines 2791-2803
    
    Parameters
    ----------
    word : str
    
    Returns
    -------
    upper_case : str
    """
    upper_case = quippy._quippy.f90wrap_system_module__upper_case(word=word)
    return upper_case

def lower_case(word, interface_call=False):
    """
    Convert a word to lower case
    
    lower_case = lower_case(word)
    Defined at System.fpp lines 2806-2818
    
    Parameters
    ----------
    word : str
    
    Returns
    -------
    lower_case : str
    """
    lower_case = quippy._quippy.f90wrap_system_module__lower_case(word=word)
    return lower_case

def replace(string_bn, search, substitute, interface_call=False):
    """
    res = replace(string_bn, search, substitute)
    Defined at System.fpp lines 2820-2832
    
    Parameters
    ----------
    string_bn : str
    search : str
    substitute : str
    
    Returns
    -------
    res : str
    """
    res = quippy._quippy.f90wrap_system_module__replace(string_bn=string_bn, search=search, substitute=substitute)
    return res

def progress(total, current, name, interface_call=False):
    """
    Print a progress bar
    
    progress(total, current, name)
    Defined at System.fpp lines 2835-2851
    
    Parameters
    ----------
    total : int32
    current : int32
    name : str
    """
    quippy._quippy.f90wrap_system_module__progress(total=total, current=current, name=name)

def progress_timer(total, current, name, elapsed_seconds, interface_call=False):
    """
    Print a progress bar with an estimate of time to completion
    based on the elapsed time so far
    
    progress_timer(total, current, name, elapsed_seconds)
    Defined at System.fpp lines 2855-2899
    
    Parameters
    ----------
    total : int32
    current : int32
    name : str
    elapsed_seconds : float64
    """
    quippy._quippy.f90wrap_system_module__progress_timer(total=total, current=current, name=name, \
        elapsed_seconds=elapsed_seconds)

def increase_to_multiple(a, m, interface_call=False):
    """
    res = increase_to_multiple(a, m)
    Defined at System.fpp lines 2901-2905
    
    Parameters
    ----------
    a : int32
    m : int32
    
    Returns
    -------
    res : int32
    """
    res = quippy._quippy.f90wrap_system_module__increase_to_multiple(a=a, m=m)
    return res

def inoutput_print_string(string_bn, verbosity=None, file=None, nocr=None, do_flush=None, interface_call=False):
    """
    inoutput_print_string(string_bn[, verbosity, file, nocr, do_flush])
    Defined at System.fpp lines 625-672
    
    Parameters
    ----------
    string_bn : str
    verbosity : int32
    file : Inoutput
    nocr : bool
    do_flush : bool
    """
    quippy._quippy.f90wrap_system_module__inoutput_print_string(string_bn=string_bn, verbosity=verbosity, file=None if file \
        is None else file._handle, nocr=nocr, do_flush=do_flush)

def inoutput_print_integer(int_bn, verbosity=None, file=None, interface_call=False):
    """
    inoutput_print_integer(int_bn[, verbosity, file])
    Defined at System.fpp lines 701-706
    
    Parameters
    ----------
    int_bn : int32
    verbosity : int32
    file : Inoutput
    """
    quippy._quippy.f90wrap_system_module__inoutput_print_integer(int_bn=int_bn, verbosity=verbosity, file=None if file is \
        None else file._handle)

def inoutput_print_real(real, verbosity=None, file=None, precision=None, format=None, nocr=None, interface_call=False):
    """
    inoutput_print_real(real[, verbosity, file, precision, format, nocr])
    Defined at System.fpp lines 708-735
    
    Parameters
    ----------
    real : float64
    verbosity : int32
    file : Inoutput
    precision : int32
    format : str
    nocr : bool
    """
    quippy._quippy.f90wrap_system_module__inoutput_print_real(real=real, verbosity=verbosity, file=None if file is None else \
        file._handle, precision=precision, format=format, nocr=nocr)

def inoutput_print_logical(log, verbosity=None, file=None, interface_call=False):
    """
    inoutput_print_logical(log[, verbosity, file])
    Defined at System.fpp lines 694-699
    
    Parameters
    ----------
    log : bool
    verbosity : int32
    file : Inoutput
    """
    quippy._quippy.f90wrap_system_module__inoutput_print_logical(log=log, verbosity=verbosity, file=None if file is None \
        else file._handle)

def inoutput_print_char_array(char_a, verbosity=None, file=None, interface_call=False):
    """
    inoutput_print_char_array(char_a[, verbosity, file])
    Defined at System.fpp lines 683-692
    
    Parameters
    ----------
    char_a : str array
    verbosity : int32
    file : Inoutput
    """
    quippy._quippy.f90wrap_system_module__inoutput_print_char_array(char_a=char_a, verbosity=verbosity, file=None if file is \
        None else file._handle)

def print(*args, **kwargs):
    """
    Overloaded interface for printing. With the
    'this' parameter omitted output goes to the default mainlog('stdout'). The
    'verbosity' parameter controls whether the object is actually printed;
    if the verbosity is greater than that currently at the top of the
    verbosity stack then output is suppressed. Possible verbosity levels
    range from 'ERROR' through 'NORMAL', 'VERBOSE', 'NERD' and 'ANALYSIS'.
    Other user-defined types define the Print interface in the same way.
    
    print(*args, **kwargs)
    Defined at System.fpp lines 253-257
    
    Overloaded interface containing the following procedures:
      inoutput_print_string
      inoutput_print_integer
      inoutput_print_real
      inoutput_print_logical
      inoutput_print_char_array
    """
    for proc in [inoutput_print_char_array, inoutput_print_real, inoutput_print_string, inoutput_print_integer, \
        inoutput_print_logical]:
        exception=None
        try:
            return proc(*args, **kwargs, interface_call=True)
        except (TypeError, ValueError, AttributeError, IndexError, numpy.exceptions.ComplexWarning) as err:
            exception = "'%s: %s'" % (type(err).__name__, str(err))
            continue
    
    argTypes=[]
    for arg in args:
        try:
            argTypes.append("%s: dims '%s', type '%s',"
            " type code '%s'"
            %(str(type(arg)),arg.ndim, arg.dtype, arg.dtype.num))
        except AttributeError:
            argTypes.append(str(type(arg)))
    raise TypeError("Not able to call a version of "
        "print compatible with the provided args:"
        "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))

def mem_info_i(interface_call=False):
    """
    total_mem_i, free_mem_i = mem_info_i()
    Defined at System.fpp lines 2750-2755
    
    Returns
    -------
    total_mem_i : int64
    free_mem_i : int64
    """
    total_mem_i, free_mem_i = quippy._quippy.f90wrap_system_module__mem_info_i()
    return total_mem_i, free_mem_i

def mem_info_r(interface_call=False):
    """
    total_mem, free_mem = mem_info_r()
    Defined at System.fpp lines 2757-2759
    
    Returns
    -------
    total_mem : float64
    free_mem : float64
    """
    total_mem, free_mem = quippy._quippy.f90wrap_system_module__mem_info_r()
    return total_mem, free_mem

def mem_info(*args, **kwargs):
    """
    mem_info(*args, **kwargs)
    Defined at System.fpp lines 316-317
    
    Overloaded interface containing the following procedures:
      mem_info_i
      mem_info_r
    """
    for proc in [mem_info_i, mem_info_r]:
        exception=None
        try:
            return proc(*args, **kwargs, interface_call=True)
        except (TypeError, ValueError, AttributeError, IndexError, numpy.exceptions.ComplexWarning) as err:
            exception = "'%s: %s'" % (type(err).__name__, str(err))
            continue
    
    argTypes=[]
    for arg in args:
        try:
            argTypes.append("%s: dims '%s', type '%s',"
            " type code '%s'"
            %(str(type(arg)),arg.ndim, arg.dtype, arg.dtype.num))
        except AttributeError:
            argTypes.append(str(type(arg)))
    raise TypeError("Not able to call a version of "
        "mem_info compatible with the provided args:"
        "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))

def optional_default_l(def_, opt_val=None, interface_call=False):
    """
    optional_default_l = optional_default_l(def_[, opt_val])
    Defined at System.fpp lines 2444-2452
    
    Parameters
    ----------
    def_ : bool
    opt_val : bool
    
    Returns
    -------
    optional_default_l : bool
    """
    optional_default_l = quippy._quippy.f90wrap_system_module__optional_default_l(def_=def_, opt_val=opt_val)
    return optional_default_l

def optional_default_i(def_, opt_val=None, interface_call=False):
    """
    optional_default_i = optional_default_i(def_[, opt_val])
    Defined at System.fpp lines 2454-2462
    
    Parameters
    ----------
    def_ : int32
    opt_val : int32
    
    Returns
    -------
    optional_default_i : int32
    """
    optional_default_i = quippy._quippy.f90wrap_system_module__optional_default_i(def_=def_, opt_val=opt_val)
    return optional_default_i

def optional_default_r(def_, opt_val=None, interface_call=False):
    """
    optional_default_r = optional_default_r(def_[, opt_val])
    Defined at System.fpp lines 2474-2482
    
    Parameters
    ----------
    def_ : float64
    opt_val : float64
    
    Returns
    -------
    optional_default_r : float64
    """
    optional_default_r = quippy._quippy.f90wrap_system_module__optional_default_r(def_=def_, opt_val=opt_val)
    return optional_default_r

def optional_default_c(def_, opt_val=None, interface_call=False):
    """
    optional_default_c = optional_default_c(def_[, opt_val])
    Defined at System.fpp lines 2504-2512
    
    Parameters
    ----------
    def_ : str
    opt_val : str
    
    Returns
    -------
    optional_default_c : str
    """
    optional_default_c = quippy._quippy.f90wrap_system_module__optional_default_c(def_=def_, opt_val=opt_val)
    return optional_default_c

def optional_default_ca(def_, opt_val=None, interface_call=False):
    """
    optional_default_ca = optional_default_ca(def_[, opt_val])
    Defined at System.fpp lines 2514-2522
    
    Parameters
    ----------
    def_ : str array
    opt_val : str array
    
    Returns
    -------
    optional_default_ca : str array
    """
    optional_default_ca = quippy._quippy.f90wrap_system_module__optional_default_ca(def_=def_, opt_val=opt_val, \
        f90wrap_n2=def_.shape[0])
    return optional_default_ca

def optional_default_z(def_, interface_call=False):
    """
    optional_default_z = optional_default_z(def_)
    Defined at System.fpp lines 2494-2502
    
    Parameters
    ----------
    def_ : complex128
    
    Returns
    -------
    optional_default_z : complex128
    """
    optional_default_z = quippy._quippy.f90wrap_system_module__optional_default_z(def_=def_)
    return optional_default_z

def optional_default_ia(def_, opt_val=None, interface_call=False):
    """
    optional_default_ia = optional_default_ia(def_[, opt_val])
    Defined at System.fpp lines 2464-2472
    
    Parameters
    ----------
    def_ : int array
    opt_val : int array
    
    Returns
    -------
    optional_default_ia : int array
    """
    optional_default_ia = quippy._quippy.f90wrap_system_module__optional_default_ia(def_=def_, opt_val=opt_val, \
        f90wrap_n2=def_.shape[0])
    return optional_default_ia

def optional_default_ra(def_, opt_val=None, interface_call=False):
    """
    optional_default_ra = optional_default_ra(def_[, opt_val])
    Defined at System.fpp lines 2484-2492
    
    Parameters
    ----------
    def_ : float array
    opt_val : float array
    
    Returns
    -------
    optional_default_ra : float array
    """
    optional_default_ra = quippy._quippy.f90wrap_system_module__optional_default_ra(def_=def_, opt_val=opt_val, \
        f90wrap_n2=def_.shape[0])
    return optional_default_ra

def optional_default(*args, **kwargs):
    """
    takes as arguments a default value and an optional argument, and
    returns the optional argument value if it's present, otherwise
    the default value
    
    optional_default(*args, **kwargs)
    Defined at System.fpp lines 353-356
    
    Overloaded interface containing the following procedures:
      optional_default_l
      optional_default_i
      optional_default_r
      optional_default_c
      optional_default_ca
      optional_default_z
      optional_default_ia
      optional_default_ra
    """
    for proc in [optional_default_ca, optional_default_ia, optional_default_ra, optional_default_l, optional_default_i, \
        optional_default_r, optional_default_c, optional_default_z]:
        exception=None
        try:
            return proc(*args, **kwargs, interface_call=True)
        except (TypeError, ValueError, AttributeError, IndexError, numpy.exceptions.ComplexWarning) as err:
            exception = "'%s: %s'" % (type(err).__name__, str(err))
            continue
    
    argTypes=[]
    for arg in args:
        try:
            argTypes.append("%s: dims '%s', type '%s',"
            " type code '%s'"
            %(str(type(arg)),arg.ndim, arg.dtype, arg.dtype.num))
        except AttributeError:
            argTypes.append(str(type(arg)))
    raise TypeError("Not able to call a version of "
        "optional_default compatible with the provided args:"
        "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))

def string_to_real_sub(string_bn, error=None, interface_call=False):
    """
    real_number = string_to_real_sub(string_bn[, error])
    Defined at System.fpp lines 1322-1332
    
    Parameters
    ----------
    string_bn : str
    error : int32
    
    Returns
    -------
    real_number : float64
    """
    real_number = quippy._quippy.f90wrap_system_module__string_to_real_sub(string_bn=string_bn, error=error)
    return real_number

def string_to_integer_sub(string_bn, error=None, interface_call=False):
    """
    integer_number = string_to_integer_sub(string_bn[, error])
    Defined at System.fpp lines 1334-1344
    
    Parameters
    ----------
    string_bn : str
    error : int32
    
    Returns
    -------
    integer_number : int32
    """
    integer_number = quippy._quippy.f90wrap_system_module__string_to_integer_sub(string_bn=string_bn, error=error)
    return integer_number

def string_to_logical_sub(string_bn, error=None, interface_call=False):
    """
    logical_number = string_to_logical_sub(string_bn[, error])
    Defined at System.fpp lines 1346-1356
    
    Parameters
    ----------
    string_bn : str
    error : int32
    
    Returns
    -------
    logical_number : bool
    """
    logical_number = quippy._quippy.f90wrap_system_module__string_to_logical_sub(string_bn=string_bn, error=error)
    return logical_number

def string_to_real1d(string_bn, real1d, error=None, interface_call=False):
    """
    string_to_real1d(string_bn, real1d[, error])
    Defined at System.fpp lines 1358-1368
    
    Parameters
    ----------
    string_bn : str
    real1d : float array
    error : int32
    """
    quippy._quippy.f90wrap_system_module__string_to_real1d(string_bn=string_bn, real1d=real1d, error=error)

def string_to_integer1d(string_bn, integer1d, error=None, interface_call=False):
    """
    string_to_integer1d(string_bn, integer1d[, error])
    Defined at System.fpp lines 1370-1380
    
    Parameters
    ----------
    string_bn : str
    integer1d : int array
    error : int32
    """
    quippy._quippy.f90wrap_system_module__string_to_integer1d(string_bn=string_bn, integer1d=integer1d, error=error)

def string_to_logical1d(string_bn, logical1d, error=None, interface_call=False):
    """
    string_to_logical1d(string_bn, logical1d[, error])
    Defined at System.fpp lines 1382-1392
    
    Parameters
    ----------
    string_bn : str
    logical1d : int32 array
    error : int32
    """
    quippy._quippy.f90wrap_system_module__string_to_logical1d(string_bn=string_bn, logical1d=logical1d, error=error)

def string_to_numerical(*args, **kwargs):
    """
    string_to_numerical(*args, **kwargs)
    Defined at System.fpp lines 361-363
    
    Overloaded interface containing the following procedures:
      string_to_real_sub
      string_to_integer_sub
      string_to_logical_sub
      string_to_real1d
      string_to_integer1d
      string_to_logical1d
    """
    for proc in [string_to_real1d, string_to_integer1d, string_to_logical1d, string_to_real_sub, string_to_integer_sub, \
        string_to_logical_sub]:
        exception=None
        try:
            return proc(*args, **kwargs, interface_call=True)
        except (TypeError, ValueError, AttributeError, IndexError, numpy.exceptions.ComplexWarning) as err:
            exception = "'%s: %s'" % (type(err).__name__, str(err))
            continue
    
    argTypes=[]
    for arg in args:
        try:
            argTypes.append("%s: dims '%s', type '%s',"
            " type code '%s'"
            %(str(type(arg)),arg.ndim, arg.dtype, arg.dtype.num))
        except AttributeError:
            argTypes.append(str(type(arg)))
    raise TypeError("Not able to call a version of "
        "string_to_numerical compatible with the provided args:"
        "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))

def int_format_length_isp(i, interface_call=False):
    """
    len_bn = int_format_length_isp(i)
    Defined at System.fpp lines 1692-1695
    
    Parameters
    ----------
    i : int32
    
    Returns
    -------
    len_bn : int32
    """
    len_bn = quippy._quippy.f90wrap_system_module__int_format_length_isp(i=i)
    return len_bn

def int_format_length_idp(i, interface_call=False):
    """
    len_bn = int_format_length_idp(i)
    Defined at System.fpp lines 1697-1700
    
    Parameters
    ----------
    i : int64
    
    Returns
    -------
    len_bn : int32
    """
    len_bn = quippy._quippy.f90wrap_system_module__int_format_length_idp(i=i)
    return len_bn

def int_format_length(*args, **kwargs):
    """
    int_format_length(*args, **kwargs)
    Defined at System.fpp lines 366-367
    
    Overloaded interface containing the following procedures:
      int_format_length_isp
      int_format_length_idp
    """
    for proc in [int_format_length_isp, int_format_length_idp]:
        exception=None
        try:
            return proc(*args, **kwargs, interface_call=True)
        except (TypeError, ValueError, AttributeError, IndexError, numpy.exceptions.ComplexWarning) as err:
            exception = "'%s: %s'" % (type(err).__name__, str(err))
            continue
    
    argTypes=[]
    for arg in args:
        try:
            argTypes.append("%s: dims '%s', type '%s',"
            " type code '%s'"
            %(str(type(arg)),arg.ndim, arg.dtype, arg.dtype.num))
        except AttributeError:
            argTypes.append(str(type(arg)))
    raise TypeError("Not able to call a version of "
        "int_format_length compatible with the provided args:"
        "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))

def get_system_always_flush():
    """
    Element system_always_flush ftype=logical pytype=bool
    Defined at System.fpp line 143
    """
    return quippy._quippy.f90wrap_system_module__get__system_always_flush()

def set_system_always_flush(system_always_flush):
    quippy._quippy.f90wrap_system_module__set__system_always_flush(system_always_flush)

def get_system_use_fortran_random():
    """
    Element system_use_fortran_random ftype=logical pytype=bool
    Defined at System.fpp line 144
    """
    return quippy._quippy.f90wrap_system_module__get__system_use_fortran_random()

def set_system_use_fortran_random(system_use_fortran_random):
    quippy._quippy.f90wrap_system_module__set__system_use_fortran_random(system_use_fortran_random)

def get_quip_new_line():
    """
    Element quip_new_line ftype=character pytype=str
    Defined at System.fpp line 146
    """
    return quippy._quippy.f90wrap_system_module__get__quip_new_line()

def set_quip_new_line(quip_new_line):
    quippy._quippy.f90wrap_system_module__set__quip_new_line(quip_new_line)

def get_integer_size():
    """
    Element integer_size ftype=integer pytype=int32
    Defined at System.fpp line 147
    """
    return quippy._quippy.f90wrap_system_module__get__integer_size()

INTEGER_SIZE = get_integer_size()

def get_real_size():
    """
    Element real_size ftype=integer pytype=int32
    Defined at System.fpp line 148
    """
    return quippy._quippy.f90wrap_system_module__get__real_size()

REAL_SIZE = get_real_size()

def get_complex_size():
    """
    Element complex_size ftype=integer pytype=int32
    Defined at System.fpp line 149
    """
    return quippy._quippy.f90wrap_system_module__get__complex_size()

COMPLEX_SIZE = get_complex_size()

def get_trace_memory():
    """
    Element trace_memory ftype=logical pytype=bool
    Defined at System.fpp line 150
    """
    return quippy._quippy.f90wrap_system_module__get__trace_memory()

def set_trace_memory(trace_memory):
    quippy._quippy.f90wrap_system_module__set__trace_memory(trace_memory)

def get_traced_memory():
    """
    Element traced_memory ftype=integer pytype=int32
    Defined at System.fpp line 151
    """
    return quippy._quippy.f90wrap_system_module__get__traced_memory()

def set_traced_memory(traced_memory):
    quippy._quippy.f90wrap_system_module__set__traced_memory(traced_memory)

def get_line():
    """
    Element line ftype=character(system_string_length_long) pytype=str
    Defined at System.fpp line 183
    """
    return quippy._quippy.f90wrap_system_module__get__line()

def set_line(line):
    quippy._quippy.f90wrap_system_module__set__line(line)

def get_mainlog():
    """
    main output, connected to 'stdout' by default
    
    Element mainlog ftype=type(inoutput) pytype=Inoutput
    Defined at System.fpp line 185
    """
    global mainlog
    mainlog_handle = quippy._quippy.f90wrap_system_module__get__mainlog()
    if tuple(mainlog_handle) in _objs:
        mainlog = _objs[tuple(mainlog_handle)]
    else:
        mainlog = InOutput.from_handle(mainlog_handle)
        _objs[tuple(mainlog_handle)] = mainlog
    return mainlog

def set_mainlog(mainlog):
    mainlog = mainlog._handle
    quippy._quippy.f90wrap_system_module__set__mainlog(mainlog)

def get_errorlog():
    """
    error output, connected to 'stderr' by default
    
    Element errorlog ftype=type(inoutput) pytype=Inoutput
    Defined at System.fpp line 186
    """
    global errorlog
    errorlog_handle = quippy._quippy.f90wrap_system_module__get__errorlog()
    if tuple(errorlog_handle) in _objs:
        errorlog = _objs[tuple(errorlog_handle)]
    else:
        errorlog = InOutput.from_handle(errorlog_handle)
        _objs[tuple(errorlog_handle)] = errorlog
    return errorlog

def set_errorlog(errorlog):
    errorlog = errorlog._handle
    quippy._quippy.f90wrap_system_module__set__errorlog(errorlog)

def get_mpilog():
    """
    MPI output, written to by each mpi process
    
    Element mpilog ftype=type(inoutput) pytype=Inoutput
    Defined at System.fpp line 187
    """
    global mpilog
    mpilog_handle = quippy._quippy.f90wrap_system_module__get__mpilog()
    if tuple(mpilog_handle) in _objs:
        mpilog = _objs[tuple(mpilog_handle)]
    else:
        mpilog = InOutput.from_handle(mpilog_handle)
        _objs[tuple(mpilog_handle)] = mpilog
    return mpilog

def set_mpilog(mpilog):
    mpilog = mpilog._handle
    quippy._quippy.f90wrap_system_module__set__mpilog(mpilog)

def get_numerical_zero():
    """
    Element numerical_zero ftype=real(dp) pytype=float64
    Defined at System.fpp line 190
    """
    return quippy._quippy.f90wrap_system_module__get__numerical_zero()

NUMERICAL_ZERO = get_numerical_zero()

def get_ran_max():
    """
    Element ran_max ftype=integer pytype=int32
    Defined at System.fpp line 192
    """
    return quippy._quippy.f90wrap_system_module__get__ran_max()

def set_ran_max(ran_max):
    quippy._quippy.f90wrap_system_module__set__ran_max(ran_max)

def get_print_always():
    """
    Element print_always ftype=integer pytype=int32
    Defined at System.fpp line 194
    """
    return quippy._quippy.f90wrap_system_module__get__print_always()

PRINT_ALWAYS = get_print_always()

def get_print_silent():
    """
    Element print_silent ftype=integer pytype=int32
    Defined at System.fpp line 195
    """
    return quippy._quippy.f90wrap_system_module__get__print_silent()

PRINT_SILENT = get_print_silent()

def get_print_normal():
    """
    Element print_normal ftype=integer pytype=int32
    Defined at System.fpp line 196
    """
    return quippy._quippy.f90wrap_system_module__get__print_normal()

PRINT_NORMAL = get_print_normal()

def get_print_verbose():
    """
    Element print_verbose ftype=integer pytype=int32
    Defined at System.fpp line 197
    """
    return quippy._quippy.f90wrap_system_module__get__print_verbose()

PRINT_VERBOSE = get_print_verbose()

def get_print_nerd():
    """
    Element print_nerd ftype=integer pytype=int32
    Defined at System.fpp line 198
    """
    return quippy._quippy.f90wrap_system_module__get__print_nerd()

PRINT_NERD = get_print_nerd()

def get_print_analysis():
    """
    Element print_analysis ftype=integer pytype=int32
    Defined at System.fpp line 199
    """
    return quippy._quippy.f90wrap_system_module__get__print_analysis()

PRINT_ANALYSIS = get_print_analysis()

def get_input():
    """
    Element input ftype=integer pytype=int32
    Defined at System.fpp line 200
    """
    return quippy._quippy.f90wrap_system_module__get__input()

INPUT = get_input()

def get_output():
    """
    Element output ftype=integer pytype=int32
    Defined at System.fpp line 201
    """
    return quippy._quippy.f90wrap_system_module__get__output()

OUTPUT = get_output()

def get_inout():
    """
    Element inout ftype=integer pytype=int32
    Defined at System.fpp line 202
    """
    return quippy._quippy.f90wrap_system_module__get__inout()

INOUT = get_inout()

def get_ran_a():
    """
    Element ran_a ftype=integer pytype=int32
    Defined at System.fpp line 204
    """
    return quippy._quippy.f90wrap_system_module__get__ran_a()

ran_A = get_ran_a()

def get_ran_m():
    """
    Element ran_m ftype=integer pytype=int32
    Defined at System.fpp line 205
    """
    return quippy._quippy.f90wrap_system_module__get__ran_m()

ran_M = get_ran_m()

def get_ran_q():
    """
    Element ran_q ftype=integer pytype=int32
    Defined at System.fpp line 206
    """
    return quippy._quippy.f90wrap_system_module__get__ran_q()

ran_Q = get_ran_q()

def get_ran_r():
    """
    Element ran_r ftype=integer pytype=int32
    Defined at System.fpp line 207
    """
    return quippy._quippy.f90wrap_system_module__get__ran_r()

ran_R = get_ran_r()

def get_timer_stack():
    """
    Element timer_stack ftype=integer pytype=int32
    Defined at System.fpp line 209
    """
    return quippy._quippy.f90wrap_system_module__get__timer_stack()

TIMER_STACK = get_timer_stack()

def get_num_command_args():
    """
    The number of arguments on the command line
    
    Element num_command_args ftype=integer pytype=int32
    Defined at System.fpp line 211
    """
    return quippy._quippy.f90wrap_system_module__get__num_command_args()

def set_num_command_args(num_command_args):
    quippy._quippy.f90wrap_system_module__set__num_command_args(num_command_args)

def get_max_readable_args():
    """
    The maximum number of arguments that will be read
    
    Element max_readable_args ftype=integer pytype=int32
    Defined at System.fpp line 212
    """
    return quippy._quippy.f90wrap_system_module__get__max_readable_args()

MAX_READABLE_ARGS = get_max_readable_args()

def get_exec_name():
    """
    The name of the executable
    
    Element exec_name ftype=character(255) pytype=str
    Defined at System.fpp line 213
    """
    return quippy._quippy.f90wrap_system_module__get__exec_name()

def set_exec_name(exec_name):
    quippy._quippy.f90wrap_system_module__set__exec_name(exec_name)

def get_array_command_arg():
    """
    The first 'MAX_READABLE_ARGS' command arguments
    
    Element command_arg ftype=character(2550) pytype=str array
    Defined at System.fpp line 214
    """
    global command_arg
    array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_system_module__array__command_arg()
    if array_handle == 0:
        command_arg = None
    else:
        array_shape = list(array_shape[:array_ndim])
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        if array_hash in _arrays:
            command_arg = _arrays[array_hash]
        else:
            command_arg = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            _arrays[array_hash] = command_arg
    return command_arg

def set_array_command_arg(command_arg):
    globals()['command_arg'][...] = command_arg


_array_initialisers = [get_array_command_arg]
_dt_array_initialisers = []


try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module "system_module".')

for func in _dt_array_initialisers:
    func()
