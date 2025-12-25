"""
A Dictionary object contains a list of keys(strings) and corresponding entries.
Entries are a variable type, containing one of:
'integer', 'real(dp)', 'complex(dp)', 'logical', extendable_str
or a 1-D array of any of those. 2-D arrays of integers and reals are also supported.

Module dictionary_module
Defined at Dictionary.fpp lines 127-2663
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

@f90wrap.runtime.register_class("quippy.DictData")
class DictData(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=dictdata)
    Defined at Dictionary.fpp lines 153-154
    """
    def __init__(self, handle=None):
        """
        Automatically generated constructor for dictdata
        
        self = Dictdata()
        Defined at Dictionary.fpp lines 153-154
        
        Returns
        -------
        this : Dictdata
            Object to be constructed
        
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_dictionary_module__dictdata_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_dictionary_module__dictdata_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    @property
    def d(self):
        """
        Element d ftype=integer pytype=int array
        Defined at Dictionary.fpp line 154
        """
        array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_dictdata__array__d(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        d = self._arrays.get(array_hash)
        if d is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if d.ctypes.data != array_handle:
                d = None
        if d is None:
            try:
                d = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_dictdata__array__d)
            except TypeError:
                d = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = d
        return d
    
    @d.setter
    def d(self, d):
        self.d[...] = d
    
    def __str__(self):
        ret = ['<dictdata>{\n']
        ret.append('    d : ')
        ret.append(repr(self.d))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

@f90wrap.runtime.register_class("quippy.DictEntry")
class DictEntry(f90wrap.runtime.FortranDerivedType):
    """
    OMIT
    
    Type(name=dictentry)
    Defined at Dictionary.fpp lines 157-175
    """
    def print(self, key, verbosity=None, file=None, interface_call=False):
        """
        Print a DictEntry or a Dictionary
        
        print(self, key[, verbosity, file])
        Defined at Dictionary.fpp lines 336-394
        
        Parameters
        ----------
        this : Dictentry
        key : str
        verbosity : int32
        file : Inoutput
        """
        quippy._quippy.f90wrap_dictionary_module__dictentry_print(this=self._handle, key=key, verbosity=verbosity, file=None if \
            file is None else file._handle)
    
    def __init__(self, handle=None):
        """
        Automatically generated constructor for dictentry
        
        self = Dictentry()
        Defined at Dictionary.fpp lines 157-175
        
        Returns
        -------
        this : Dictentry
            Object to be constructed
        
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_dictionary_module__dictentry_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_dictionary_module__dictentry_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    @property
    def type_bn(self):
        """
        Element type_bn ftype=integer  pytype=int32
        Defined at Dictionary.fpp line 159
        """
        return quippy._quippy.f90wrap_dictentry__get__type_bn(self._handle)
    
    @type_bn.setter
    def type_bn(self, type_bn):
        quippy._quippy.f90wrap_dictentry__set__type_bn(self._handle, type_bn)
    
    @property
    def len_bn(self):
        """
        Element len_bn ftype=integer  pytype=int32
        Defined at Dictionary.fpp line 160
        """
        return quippy._quippy.f90wrap_dictentry__get__len_bn(self._handle)
    
    @len_bn.setter
    def len_bn(self, len_bn):
        quippy._quippy.f90wrap_dictentry__set__len_bn(self._handle, len_bn)
    
    @property
    def len2(self):
        """
        Element len2 ftype=integer  pytype=int array
        Defined at Dictionary.fpp line 161
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dictentry__array__len2(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        len2 = self._arrays.get(array_hash)
        if len2 is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if len2.ctypes.data != array_handle:
                len2 = None
        if len2 is None:
            try:
                len2 = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_dictentry__array__len2)
            except TypeError:
                len2 = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = len2
        return len2
    
    @len2.setter
    def len2(self, len2):
        self.len2[...] = len2
    
    @property
    def own_data(self):
        """
        True if we own the data and should free it in finalise()
        
        Element own_data ftype=logical pytype=bool
        Defined at Dictionary.fpp line 162
        """
        return quippy._quippy.f90wrap_dictentry__get__own_data(self._handle)
    
    @own_data.setter
    def own_data(self, own_data):
        quippy._quippy.f90wrap_dictentry__set__own_data(self._handle, own_data)
    
    @property
    def i(self):
        """
        Element i ftype=integer  pytype=int32
        Defined at Dictionary.fpp line 163
        """
        return quippy._quippy.f90wrap_dictentry__get__i(self._handle)
    
    @i.setter
    def i(self, i):
        quippy._quippy.f90wrap_dictentry__set__i(self._handle, i)
    
    @property
    def r(self):
        """
        Element r ftype=real(dp) pytype=float64
        Defined at Dictionary.fpp line 164
        """
        return quippy._quippy.f90wrap_dictentry__get__r(self._handle)
    
    @r.setter
    def r(self, r):
        quippy._quippy.f90wrap_dictentry__set__r(self._handle, r)
    
    @property
    def c(self):
        """
        Element c ftype=complex(dp) pytype=complex128
        Defined at Dictionary.fpp line 165
        """
        return quippy._quippy.f90wrap_dictentry__get__c(self._handle)
    
    @c.setter
    def c(self, c):
        quippy._quippy.f90wrap_dictentry__set__c(self._handle, c)
    
    @property
    def l(self):
        """
        Element l ftype=logical pytype=bool
        Defined at Dictionary.fpp line 166
        """
        return quippy._quippy.f90wrap_dictentry__get__l(self._handle)
    
    @l.setter
    def l(self, l):
        quippy._quippy.f90wrap_dictentry__set__l(self._handle, l)
    
    @property
    def i_a(self):
        """
        Element i_a ftype=integer pytype=int array
        Defined at Dictionary.fpp line 168
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dictentry__array__i_a(self._handle)
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
                                        quippy._quippy.f90wrap_dictentry__array__i_a)
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
        Defined at Dictionary.fpp line 169
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dictentry__array__r_a(self._handle)
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
                                        quippy._quippy.f90wrap_dictentry__array__r_a)
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
        Defined at Dictionary.fpp line 170
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dictentry__array__c_a(self._handle)
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
                                        quippy._quippy.f90wrap_dictentry__array__c_a)
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
        Defined at Dictionary.fpp line 171
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dictentry__array__l_a(self._handle)
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
                                        quippy._quippy.f90wrap_dictentry__array__l_a)
            except TypeError:
                l_a = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = l_a
        return l_a
    
    @l_a.setter
    def l_a(self, l_a):
        self.l_a[...] = l_a
    
    @property
    def s_a(self):
        """
        Element s_a ftype=character(len=1) pytype=str array
        Defined at Dictionary.fpp line 172
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dictentry__array__s_a(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        s_a = self._arrays.get(array_hash)
        if s_a is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if s_a.ctypes.data != array_handle:
                s_a = None
        if s_a is None:
            try:
                s_a = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_dictentry__array__s_a)
            except TypeError:
                s_a = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = s_a
        return s_a
    
    @s_a.setter
    def s_a(self, s_a):
        self.s_a[...] = s_a
    
    @property
    def i_a2(self):
        """
        Element i_a2 ftype=integer pytype=int array
        Defined at Dictionary.fpp line 173
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dictentry__array__i_a2(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        i_a2 = self._arrays.get(array_hash)
        if i_a2 is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if i_a2.ctypes.data != array_handle:
                i_a2 = None
        if i_a2 is None:
            try:
                i_a2 = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_dictentry__array__i_a2)
            except TypeError:
                i_a2 = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = i_a2
        return i_a2
    
    @i_a2.setter
    def i_a2(self, i_a2):
        self.i_a2[...] = i_a2
    
    @property
    def r_a2(self):
        """
        Element r_a2 ftype=real(dp) pytype=float array
        Defined at Dictionary.fpp line 174
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dictentry__array__r_a2(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        r_a2 = self._arrays.get(array_hash)
        if r_a2 is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if r_a2.ctypes.data != array_handle:
                r_a2 = None
        if r_a2 is None:
            try:
                r_a2 = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_dictentry__array__r_a2)
            except TypeError:
                r_a2 = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = r_a2
        return r_a2
    
    @r_a2.setter
    def r_a2(self, r_a2):
        self.r_a2[...] = r_a2
    
    @property
    def d(self):
        """
        Element d ftype=type(dictdata) pytype=Dictdata
        Defined at Dictionary.fpp line 175
        """
        d_handle = quippy._quippy.f90wrap_dictentry__get__d(self._handle)
        if tuple(d_handle) in self._objs:
            d = self._objs[tuple(d_handle)]
        else:
            d = DictData.from_handle(d_handle)
            self._objs[tuple(d_handle)] = d
        return d
    
    @d.setter
    def d(self, d):
        d = d._handle
        quippy._quippy.f90wrap_dictentry__set__d(self._handle, d)
    
    def __str__(self):
        ret = ['<dictentry>{\n']
        ret.append('    type_bn : ')
        ret.append(repr(self.type_bn))
        ret.append(',\n    len_bn : ')
        ret.append(repr(self.len_bn))
        ret.append(',\n    len2 : ')
        ret.append(repr(self.len2))
        ret.append(',\n    own_data : ')
        ret.append(repr(self.own_data))
        ret.append(',\n    i : ')
        ret.append(repr(self.i))
        ret.append(',\n    r : ')
        ret.append(repr(self.r))
        ret.append(',\n    c : ')
        ret.append(repr(self.c))
        ret.append(',\n    l : ')
        ret.append(repr(self.l))
        ret.append(',\n    i_a : ')
        ret.append(repr(self.i_a))
        ret.append(',\n    r_a : ')
        ret.append(repr(self.r_a))
        ret.append(',\n    c_a : ')
        ret.append(repr(self.c_a))
        ret.append(',\n    l_a : ')
        ret.append(repr(self.l_a))
        ret.append(',\n    s_a : ')
        ret.append(repr(self.s_a))
        ret.append(',\n    i_a2 : ')
        ret.append(repr(self.i_a2))
        ret.append(',\n    r_a2 : ')
        ret.append(repr(self.r_a2))
        ret.append(',\n    d : ')
        ret.append(repr(self.d))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

@f90wrap.runtime.register_class("quippy.Dictionary")
class Dictionary(f90wrap.runtime.FortranDerivedType):
    """
    Fortran implementation of a dictionary to store key/value pairs of the following types:
    
    - Integer
    - Real
    - String
    - Complex
    - Logical
    - 1D integer array
    - 1D real array
    - 1D complex array
    - 1D logical array
    - 2D integer array
    - 2D real array
    - Arbitrary data, via Fortran ``transform()`` intrinsic
    
    Type(name=dictionary)
    Defined at Dictionary.fpp lines 179-198
    """
    def get_key(self, i, error=None, interface_call=False):
        """
        key = get_key(self, i[, error])
        Defined at Dictionary.fpp lines 479-488
        
        Parameters
        ----------
        this : Dictionary
        i : int32
        error : int32
        
        Returns
        -------
        key : str
        """
        key = quippy._quippy.f90wrap_dictionary_module__dictionary_get_key(this=self._handle, i=i, error=error)
        return key
    
    def get_type_and_size(self, key, thesize2, error=None, interface_call=False):
        """
        type_bn, thesize = get_type_and_size(self, key, thesize2[, error])
        Defined at Dictionary.fpp lines 490-503
        
        Parameters
        ----------
        this : Dictionary
        key : str
        thesize2 : int array
        error : int32
        
        Returns
        -------
        type_bn : int32
        thesize : int32
        """
        type_bn, thesize = quippy._quippy.f90wrap_dictionary_module__dictionary_get_type_and_size(this=self._handle, key=key, \
            thesize2=thesize2, error=error)
        return type_bn, thesize
    
    def lookup_entry_i(self, key, case_sensitive=None, interface_call=False):
        """
        OMIT
        
        lookup_entry_i = lookup_entry_i(self, key[, case_sensitive])
        Defined at Dictionary.fpp lines 2219-2240
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        
        Returns
        -------
        lookup_entry_i : int32
        """
        lookup_entry_i = quippy._quippy.f90wrap_dictionary_module__lookup_entry_i(this=self._handle, key=key, \
            case_sensitive=case_sensitive)
        return lookup_entry_i
    
    def _array__(self, key, interface_call=False):
        """
        nd, dtype, dshape, dloc = _array__(self, key)
        Defined at Dictionary.fpp lines 2608-2662
        
        Parameters
        ----------
        this : Dictionary
        key : str
        
        Returns
        -------
        nd : int32
        dtype : int32
        dshape : int array
        dloc : int64
        """
        nd, dtype, dshape, dloc = quippy._quippy.f90wrap_dictionary_module__dictionary__array__(this=self._handle, key=key)
        return nd, dtype, dshape, dloc
    
    def __init__(self, handle=None):
        """
        Initialise a new empty dictionary
        
        self = Dictionary()
        Defined at Dictionary.fpp lines 428-433
        
        Returns
        -------
        this : Dictionary
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_dictionary_module__dictionary_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_dictionary_module__dictionary_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def print(self, verbosity=None, file=None, interface_call=False):
        """
        Print a DictEntry or a Dictionary
        
        print(self[, verbosity, file])
        Defined at Dictionary.fpp lines 413-421
        
        Parameters
        ----------
        this : Dictionary
        verbosity : int32
        file : Inoutput
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_print(this=self._handle, verbosity=verbosity, file=None if file is \
            None else file._handle)
    
    def print_keys(self, verbosity=None, file=None, interface_call=False):
        """
        print_keys(self[, verbosity, file])
        Defined at Dictionary.fpp lines 396-411
        
        Parameters
        ----------
        this : Dictionary
        verbosity : int32
        file : Inoutput
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_print_keys(this=self._handle, verbosity=verbosity, file=None if \
            file is None else file._handle)
    
    def remove_value(self, key, interface_call=False):
        """
        Remove an entry from a Dictionary
        
        remove_value(self, key)
        Defined at Dictionary.fpp lines 1803-1812
        
        Parameters
        ----------
        this : Dictionary
        key : str
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_remove_value(this=self._handle, key=key)
    
    def write_string(self, real_format=None, entry_sep=None, char_a_sep=None, quote_char=None, error=None, \
        interface_call=False):
        """
        Write a string representation of this dictionary
        
        dictionary_write_string = write_string(self[, real_format, entry_sep, char_a_sep, quote_char, error])
        Defined at Dictionary.fpp lines 2044-2122
        
        Parameters
        ----------
        this : Dictionary
        real_format : str
            Output format for reals, default is 'f9.3'
        
        entry_sep : str
            Entry seperator, default is single space
        
        char_a_sep : str
            Output separator for character arrays, default is ','
        
        quote_char : str
            Character to use to quote output fields containing whitespace, default is '"'
        
        error : int32
        
        Returns
        -------
        dictionary_write_string : str
        """
        dictionary_write_string = quippy._quippy.f90wrap_dictionary_module__dictionary_write_string(this=self._handle, \
            real_format=real_format, entry_sep=entry_sep, char_a_sep=char_a_sep, quote_char=quote_char, error=error)
        return dictionary_write_string
    
    def read_string(self, str, append=None, error=None, interface_call=False):
        """
        Read into this dictionary from a string
        
        read_string(self, str[, append, error])
        Defined at Dictionary.fpp lines 1814-1849
        
        Parameters
        ----------
        this : Dictionary
        str : str
        append : bool
            If true, append to dictionary(default false)
        
        error : int32
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_read_string(this=self._handle, str=str, append=append, error=error)
    
    def subset(self, keys, out, case_sensitive=None, out_no_initialise=None, error=None, interface_call=False):
        """
        subset(self, keys, out[, case_sensitive, out_no_initialise, error])
        Defined at Dictionary.fpp lines 2250-2269
        
        Parameters
        ----------
        this : Dictionary
        keys : str array
        out : Dictionary
        case_sensitive : bool
        out_no_initialise : bool
        error : int32
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_subset(this=self._handle, keys=keys, out=out._handle, \
            case_sensitive=case_sensitive, out_no_initialise=out_no_initialise, error=error)
    
    def swap(self, key1, key2, case_sensitive=None, error=None, interface_call=False):
        """
        Swap the positions of two entries in the dictionary. Arrays are not moved in memory.
        
        swap(self, key1, key2[, case_sensitive, error])
        Defined at Dictionary.fpp lines 2372-2399
        
        Parameters
        ----------
        this : Dictionary
        key1 : str
        key2 : str
        case_sensitive : bool
        error : int32
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_swap(this=self._handle, key1=key1, key2=key2, \
            case_sensitive=case_sensitive, error=error)
    
    def has_key(self, key, case_sensitive=None, interface_call=False):
        """
        Return true if 'key' is in Dictionary or false if not
        
        dictionary_has_key = has_key(self, key[, case_sensitive])
        Defined at Dictionary.fpp lines 2243-2248
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        
        Returns
        -------
        dictionary_has_key : bool
        """
        dictionary_has_key = quippy._quippy.f90wrap_dictionary_module__dictionary_has_key(this=self._handle, key=key, \
            case_sensitive=case_sensitive)
        return dictionary_has_key
    
    def deepcopy(self, from_, error=None, interface_call=False):
        """
        Make a deep copy of 'from' in 'this', allocating new memory for array components
        
        deepcopy(self, from_[, error])
        Defined at Dictionary.fpp lines 2594-2600
        
        Parameters
        ----------
        this : Dictionary
        from_ : Dictionary
        error : int32
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_deepcopy(this=self._handle, from_=from_._handle, error=error)
    
    def set_value_none(self, key, interface_call=False):
        """
        set_value_none(self, key)
        Defined at Dictionary.fpp lines 510-519
        
        Parameters
        ----------
        this : Dictionary
        key : str
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_none(this=self._handle, key=key)
    
    def set_value_i(self, key, value, interface_call=False):
        """
        set_value_i(self, key, value)
        Defined at Dictionary.fpp lines 521-532
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int32
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_i(this=self._handle, key=key, value=value)
    
    def set_value_r(self, key, value, interface_call=False):
        """
        set_value_r(self, key, value)
        Defined at Dictionary.fpp lines 534-545
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : float64
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_r(this=self._handle, key=key, value=value)
    
    def set_value_c(self, key, value, interface_call=False):
        """
        set_value_c(self, key, value)
        Defined at Dictionary.fpp lines 547-558
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : complex128
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_c(this=self._handle, key=key, value=value)
    
    def set_value_l(self, key, value, interface_call=False):
        """
        set_value_l(self, key, value)
        Defined at Dictionary.fpp lines 560-571
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_l(this=self._handle, key=key, value=value)
    
    def set_value_i_a(self, key, value, interface_call=False):
        """
        set_value_i_a(self, key, value)
        Defined at Dictionary.fpp lines 600-617
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_i_a(this=self._handle, key=key, value=value)
    
    def set_value_r_a(self, key, value, interface_call=False):
        """
        set_value_r_a(self, key, value)
        Defined at Dictionary.fpp lines 619-636
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : float array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_r_a(this=self._handle, key=key, value=value)
    
    def set_value_c_a(self, key, value, interface_call=False):
        """
        set_value_c_a(self, key, value)
        Defined at Dictionary.fpp lines 678-695
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : complex array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_c_a(this=self._handle, key=key, value=value)
    
    def set_value_l_a(self, key, value, interface_call=False):
        """
        set_value_l_a(self, key, value)
        Defined at Dictionary.fpp lines 697-714
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int32 array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_l_a(this=self._handle, key=key, value=value)
    
    def set_value_s(self, key, value, interface_call=False):
        """
        set_value_s(self, key, value)
        Defined at Dictionary.fpp lines 573-585
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : str
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_s(this=self._handle, key=key, value=value)
    
    def set_value_s_a2(self, key, value, interface_call=False):
        """
        set_value_s_a2(self, key, value)
        Defined at Dictionary.fpp lines 740-758
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : str array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_s_a2(this=self._handle, key=key, value=value)
    
    def set_value_s_a(self, key, value, interface_call=False):
        """
        set_value_s_a(self, key, value)
        Defined at Dictionary.fpp lines 716-738
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : str array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_s_a(this=self._handle, key=key, value=value)
    
    def set_value_d(self, key, value, interface_call=False):
        """
        set_value_d(self, key, value)
        Defined at Dictionary.fpp lines 760-772
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : Dictdata
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_d(this=self._handle, key=key, value=value._handle)
    
    def set_value_i_a2(self, key, value, interface_call=False):
        """
        set_value_i_a2(self, key, value)
        Defined at Dictionary.fpp lines 638-656
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_i_a2(this=self._handle, key=key, value=value)
    
    def set_value_r_a2(self, key, value, interface_call=False):
        """
        set_value_r_a2(self, key, value)
        Defined at Dictionary.fpp lines 658-676
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : float array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_r_a2(this=self._handle, key=key, value=value)
    
    def set_value_dict(self, key, value, interface_call=False):
        """
        set_value_dict(self, key, value)
        Defined at Dictionary.fpp lines 774-787
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : Dictionary
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_dict(this=self._handle, key=key, value=value._handle)
    
    def set_value(*args, **kwargs):
        """
        Set a value in a Dictionary
        
        set_value(*args, **kwargs)
        Defined at Dictionary.fpp lines 225-234
        
        Overloaded interface containing the following procedures:
          set_value_none
          set_value_i
          set_value_r
          set_value_c
          set_value_l
          set_value_i_a
          set_value_r_a
          set_value_c_a
          set_value_l_a
          set_value_s
          set_value_s_a2
          set_value_s_a
          set_value_d
          set_value_i_a2
          set_value_r_a2
          set_value_dict
        """
        for proc in [Dictionary.set_value_i_a, Dictionary.set_value_r_a, Dictionary.set_value_c_a, Dictionary.set_value_l_a, \
            Dictionary.set_value_s_a2, Dictionary.set_value_s_a, Dictionary.set_value_i_a2, Dictionary.set_value_r_a2, \
            Dictionary.set_value_i, Dictionary.set_value_r, Dictionary.set_value_c, Dictionary.set_value_l, \
            Dictionary.set_value_s, Dictionary.set_value_d, Dictionary.set_value_dict, Dictionary.set_value_none]:
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
            "set_value compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def set_value_pointer_i(self, key, ptr, interface_call=False):
        """
        set_value_pointer_i(self, key, ptr)
        Defined at Dictionary.fpp lines 1336-1350
        
        Parameters
        ----------
        this : Dictionary
        key : str
        ptr : int array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_pointer_i(this=self._handle, key=key, ptr=ptr)
    
    def set_value_pointer_r(self, key, ptr, interface_call=False):
        """
        set_value_pointer_r(self, key, ptr)
        Defined at Dictionary.fpp lines 1352-1366
        
        Parameters
        ----------
        this : Dictionary
        key : str
        ptr : float array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_pointer_r(this=self._handle, key=key, ptr=ptr)
    
    def set_value_pointer_c(self, key, ptr, interface_call=False):
        """
        set_value_pointer_c(self, key, ptr)
        Defined at Dictionary.fpp lines 1368-1382
        
        Parameters
        ----------
        this : Dictionary
        key : str
        ptr : complex array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_pointer_c(this=self._handle, key=key, ptr=ptr)
    
    def set_value_pointer_l(self, key, ptr, interface_call=False):
        """
        set_value_pointer_l(self, key, ptr)
        Defined at Dictionary.fpp lines 1384-1398
        
        Parameters
        ----------
        this : Dictionary
        key : str
        ptr : int32 array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_pointer_l(this=self._handle, key=key, ptr=ptr)
    
    def set_value_pointer_s(self, key, ptr, interface_call=False):
        """
        set_value_pointer_s(self, key, ptr)
        Defined at Dictionary.fpp lines 1400-1415
        
        Parameters
        ----------
        this : Dictionary
        key : str
        ptr : str array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_pointer_s(this=self._handle, key=key, ptr=ptr)
    
    def set_value_pointer_i2(self, key, ptr, interface_call=False):
        """
        set_value_pointer_i2(self, key, ptr)
        Defined at Dictionary.fpp lines 1417-1432
        
        Parameters
        ----------
        this : Dictionary
        key : str
        ptr : int array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_pointer_i2(this=self._handle, key=key, ptr=ptr)
    
    def set_value_pointer_r2(self, key, ptr, interface_call=False):
        """
        set_value_pointer_r2(self, key, ptr)
        Defined at Dictionary.fpp lines 1434-1449
        
        Parameters
        ----------
        this : Dictionary
        key : str
        ptr : float array
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_set_value_pointer_r2(this=self._handle, key=key, ptr=ptr)
    
    def set_value_pointer(*args, **kwargs):
        """
        set_value_pointer(*args, **kwargs)
        Defined at Dictionary.fpp lines 237-244
        
        Overloaded interface containing the following procedures:
          set_value_pointer_i
          set_value_pointer_r
          set_value_pointer_c
          set_value_pointer_l
          set_value_pointer_s
          set_value_pointer_i2
          set_value_pointer_r2
        """
        for proc in [Dictionary.set_value_pointer_i, Dictionary.set_value_pointer_r, Dictionary.set_value_pointer_c, \
            Dictionary.set_value_pointer_l, Dictionary.set_value_pointer_s, Dictionary.set_value_pointer_i2, \
            Dictionary.set_value_pointer_r2]:
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
            "set_value_pointer compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def get_value_i(self, key, case_sensitive=None, i=None, interface_call=False):
        """
        v, dictionary_get_value_i = get_value_i(self, key[, case_sensitive, i])
        Defined at Dictionary.fpp lines 794-813
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        v : int32
        dictionary_get_value_i : bool
        """
        v, dictionary_get_value_i = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_i(this=self._handle, key=key, \
            case_sensitive=case_sensitive, i=i)
        return v, dictionary_get_value_i
    
    def get_value_r(self, key, case_sensitive=None, i=None, interface_call=False):
        """
        v, dictionary_get_value_r = get_value_r(self, key[, case_sensitive, i])
        Defined at Dictionary.fpp lines 815-834
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        v : float64
        dictionary_get_value_r : bool
        """
        v, dictionary_get_value_r = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_r(this=self._handle, key=key, \
            case_sensitive=case_sensitive, i=i)
        return v, dictionary_get_value_r
    
    def get_value_c(self, key, case_sensitive=None, i=None, interface_call=False):
        """
        v, dictionary_get_value_c = get_value_c(self, key[, case_sensitive, i])
        Defined at Dictionary.fpp lines 836-855
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        v : complex128
        dictionary_get_value_c : bool
        """
        v, dictionary_get_value_c = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_c(this=self._handle, key=key, \
            case_sensitive=case_sensitive, i=i)
        return v, dictionary_get_value_c
    
    def get_value_l(self, key, case_sensitive=None, i=None, interface_call=False):
        """
        v, dictionary_get_value_l = get_value_l(self, key[, case_sensitive, i])
        Defined at Dictionary.fpp lines 857-876
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        v : bool
        dictionary_get_value_l : bool
        """
        v, dictionary_get_value_l = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_l(this=self._handle, key=key, \
            case_sensitive=case_sensitive, i=i)
        return v, dictionary_get_value_l
    
    def get_value_i_a(self, key, v, case_sensitive=None, i=None, interface_call=False):
        """
        dictionary_get_value_i_a = get_value_i_a(self, key, v[, case_sensitive, i])
        Defined at Dictionary.fpp lines 921-944
        
        Parameters
        ----------
        this : Dictionary
        key : str
        v : int array
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        dictionary_get_value_i_a : bool
        """
        dictionary_get_value_i_a = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_i_a(this=self._handle, \
            key=key, v=v, case_sensitive=case_sensitive, i=i)
        return dictionary_get_value_i_a
    
    def get_value_r_a(self, key, v, case_sensitive=None, i=None, interface_call=False):
        """
        dictionary_get_value_r_a = get_value_r_a(self, key, v[, case_sensitive, i])
        Defined at Dictionary.fpp lines 946-969
        
        Parameters
        ----------
        this : Dictionary
        key : str
        v : float array
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        dictionary_get_value_r_a : bool
        """
        dictionary_get_value_r_a = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_r_a(this=self._handle, \
            key=key, v=v, case_sensitive=case_sensitive, i=i)
        return dictionary_get_value_r_a
    
    def get_value_c_a(self, key, v, case_sensitive=None, i=None, interface_call=False):
        """
        dictionary_get_value_c_a = get_value_c_a(self, key, v[, case_sensitive, i])
        Defined at Dictionary.fpp lines 1023-1046
        
        Parameters
        ----------
        this : Dictionary
        key : str
        v : complex array
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        dictionary_get_value_c_a : bool
        """
        dictionary_get_value_c_a = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_c_a(this=self._handle, \
            key=key, v=v, case_sensitive=case_sensitive, i=i)
        return dictionary_get_value_c_a
    
    def get_value_l_a(self, key, v, case_sensitive=None, i=None, interface_call=False):
        """
        dictionary_get_value_l_a = get_value_l_a(self, key, v[, case_sensitive, i])
        Defined at Dictionary.fpp lines 1048-1071
        
        Parameters
        ----------
        this : Dictionary
        key : str
        v : int32 array
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        dictionary_get_value_l_a : bool
        """
        dictionary_get_value_l_a = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_l_a(this=self._handle, \
            key=key, v=v, case_sensitive=case_sensitive, i=i)
        return dictionary_get_value_l_a
    
    def get_value_s(self, key, case_sensitive=None, i=None, interface_call=False):
        """
        v, dictionary_get_value_s = get_value_s(self, key[, case_sensitive, i])
        Defined at Dictionary.fpp lines 878-898
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        v : str
        dictionary_get_value_s : bool
        """
        v, dictionary_get_value_s = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_s(this=self._handle, key=key, \
            case_sensitive=case_sensitive, i=i)
        return v, dictionary_get_value_s
    
    def get_value_s_a(self, key, v, case_sensitive=None, i=None, interface_call=False):
        """
        dictionary_get_value_s_a = get_value_s_a(self, key, v[, case_sensitive, i])
        Defined at Dictionary.fpp lines 1073-1100
        
        Parameters
        ----------
        this : Dictionary
        key : str
        v : str array
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        dictionary_get_value_s_a : bool
        """
        dictionary_get_value_s_a = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_s_a(this=self._handle, \
            key=key, v=v, case_sensitive=case_sensitive, i=i)
        return dictionary_get_value_s_a
    
    def get_value_s_a2(self, key, v, case_sensitive=None, i=None, interface_call=False):
        """
        dictionary_get_value_s_a2 = get_value_s_a2(self, key, v[, case_sensitive, i])
        Defined at Dictionary.fpp lines 1102-1125
        
        Parameters
        ----------
        this : Dictionary
        key : str
        v : str array
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        dictionary_get_value_s_a2 : bool
        """
        dictionary_get_value_s_a2 = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_s_a2(this=self._handle, \
            key=key, v=v, case_sensitive=case_sensitive, i=i)
        return dictionary_get_value_s_a2
    
    def get_value_d(self, key, case_sensitive=None, i=None, interface_call=False):
        """
        v, dictionary_get_value_d = get_value_d(self, key[, case_sensitive, i])
        Defined at Dictionary.fpp lines 1127-1146
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        v : Dictdata
        dictionary_get_value_d : bool
        """
        v, dictionary_get_value_d = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_d(this=self._handle, key=key, \
            case_sensitive=case_sensitive, i=i)
        v = f90wrap.runtime.lookup_class("quippy.DictData").from_handle(v, alloc=True)
        v._setup_finalizer()
        return v, dictionary_get_value_d
    
    def get_value_i_a2(self, key, v, case_sensitive=None, i=None, interface_call=False):
        """
        dictionary_get_value_i_a2 = get_value_i_a2(self, key, v[, case_sensitive, i])
        Defined at Dictionary.fpp lines 971-995
        
        Parameters
        ----------
        this : Dictionary
        key : str
        v : int array
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        dictionary_get_value_i_a2 : bool
        """
        dictionary_get_value_i_a2 = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_i_a2(this=self._handle, \
            key=key, v=v, case_sensitive=case_sensitive, i=i)
        return dictionary_get_value_i_a2
    
    def get_value_r_a2(self, key, v, case_sensitive=None, i=None, interface_call=False):
        """
        dictionary_get_value_r_a2 = get_value_r_a2(self, key, v[, case_sensitive, i])
        Defined at Dictionary.fpp lines 997-1021
        
        Parameters
        ----------
        this : Dictionary
        key : str
        v : float array
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        dictionary_get_value_r_a2 : bool
        """
        dictionary_get_value_r_a2 = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_r_a2(this=self._handle, \
            key=key, v=v, case_sensitive=case_sensitive, i=i)
        return dictionary_get_value_r_a2
    
    def get_value_dict(self, key, case_sensitive=None, i=None, interface_call=False):
        """
        v, dictionary_get_value_dict = get_value_dict(self, key[, case_sensitive, i])
        Defined at Dictionary.fpp lines 1148-1172
        
        Parameters
        ----------
        this : Dictionary
        key : str
        case_sensitive : bool
        i : int32
        
        Returns
        -------
        v : Dictionary
        dictionary_get_value_dict : bool
        """
        v, dictionary_get_value_dict = quippy._quippy.f90wrap_dictionary_module__dictionary_get_value_dict(this=self._handle, \
            key=key, case_sensitive=case_sensitive, i=i)
        v = f90wrap.runtime.lookup_class("quippy.Dictionary").from_handle(v, alloc=True)
        v._setup_finalizer()
        return v, dictionary_get_value_dict
    
    def get_value(*args, **kwargs):
        """
        Get a value from a Dictionary
        
        get_value(*args, **kwargs)
        Defined at Dictionary.fpp lines 248-255
        
        Overloaded interface containing the following procedures:
          get_value_i
          get_value_r
          get_value_c
          get_value_l
          get_value_i_a
          get_value_r_a
          get_value_c_a
          get_value_l_a
          get_value_s
          get_value_s_a
          get_value_s_a2
          get_value_d
          get_value_i_a2
          get_value_r_a2
          get_value_dict
        """
        for proc in [Dictionary.get_value_i_a, Dictionary.get_value_r_a, Dictionary.get_value_c_a, Dictionary.get_value_l_a, \
            Dictionary.get_value_s_a, Dictionary.get_value_s_a2, Dictionary.get_value_i_a2, Dictionary.get_value_r_a2, \
            Dictionary.get_value_i, Dictionary.get_value_r, Dictionary.get_value_c, Dictionary.get_value_l, \
            Dictionary.get_value_s, Dictionary.get_value_d, Dictionary.get_value_dict]:
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
            "get_value compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def add_array_i(self, key, value, len_bn, overwrite=None, interface_call=False):
        """
        add_array_i(self, key, value, len_bn[, overwrite])
        Defined at Dictionary.fpp lines 1456-1478
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int32
        len_bn : int32
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_i(this=self._handle, key=key, value=value, len_bn=len_bn, \
            overwrite=overwrite)
    
    def add_array_r(self, key, value, len_bn, overwrite=None, interface_call=False):
        """
        add_array_r(self, key, value, len_bn[, overwrite])
        Defined at Dictionary.fpp lines 1480-1502
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : float64
        len_bn : int32
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_r(this=self._handle, key=key, value=value, len_bn=len_bn, \
            overwrite=overwrite)
    
    def add_array_c(self, key, value, len_bn, overwrite=None, interface_call=False):
        """
        add_array_c(self, key, value, len_bn[, overwrite])
        Defined at Dictionary.fpp lines 1504-1526
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : complex128
        len_bn : int32
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_c(this=self._handle, key=key, value=value, len_bn=len_bn, \
            overwrite=overwrite)
    
    def add_array_l(self, key, value, len_bn, overwrite=None, interface_call=False):
        """
        add_array_l(self, key, value, len_bn[, overwrite])
        Defined at Dictionary.fpp lines 1528-1550
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : bool
        len_bn : int32
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_l(this=self._handle, key=key, value=value, len_bn=len_bn, \
            overwrite=overwrite)
    
    def add_array_s(self, key, value, len2, overwrite=None, interface_call=False):
        """
        add_array_s(self, key, value, len2[, overwrite])
        Defined at Dictionary.fpp lines 1552-1575
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : str
        len2 : int array
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_s(this=self._handle, key=key, value=value, len2=len2, \
            overwrite=overwrite)
    
    def add_array_i2(self, key, value, len2, overwrite=None, interface_call=False):
        """
        add_array_i2(self, key, value, len2[, overwrite])
        Defined at Dictionary.fpp lines 1577-1600
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int32
        len2 : int array
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_i2(this=self._handle, key=key, value=value, len2=len2, \
            overwrite=overwrite)
    
    def add_array_r2(self, key, value, len2, overwrite=None, interface_call=False):
        """
        add_array_r2(self, key, value, len2[, overwrite])
        Defined at Dictionary.fpp lines 1602-1625
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : float64
        len2 : int array
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_r2(this=self._handle, key=key, value=value, len2=len2, \
            overwrite=overwrite)
    
    def add_array_i_a(self, key, value, len_bn, overwrite=None, interface_call=False):
        """
        add_array_i_a(self, key, value, len_bn[, overwrite])
        Defined at Dictionary.fpp lines 1627-1649
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int array
        len_bn : int32
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_i_a(this=self._handle, key=key, value=value, \
            len_bn=len_bn, overwrite=overwrite)
    
    def add_array_r_a(self, key, value, len_bn, overwrite=None, interface_call=False):
        """
        add_array_r_a(self, key, value, len_bn[, overwrite])
        Defined at Dictionary.fpp lines 1651-1673
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : float array
        len_bn : int32
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_r_a(this=self._handle, key=key, value=value, \
            len_bn=len_bn, overwrite=overwrite)
    
    def add_array_c_a(self, key, value, len_bn, overwrite=None, interface_call=False):
        """
        add_array_c_a(self, key, value, len_bn[, overwrite])
        Defined at Dictionary.fpp lines 1675-1697
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : complex array
        len_bn : int32
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_c_a(this=self._handle, key=key, value=value, \
            len_bn=len_bn, overwrite=overwrite)
    
    def add_array_l_a(self, key, value, len_bn, overwrite=None, interface_call=False):
        """
        add_array_l_a(self, key, value, len_bn[, overwrite])
        Defined at Dictionary.fpp lines 1699-1721
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int32 array
        len_bn : int32
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_l_a(this=self._handle, key=key, value=value, \
            len_bn=len_bn, overwrite=overwrite)
    
    def add_array_s_a(self, key, value, len2, overwrite=None, interface_call=False):
        """
        add_array_s_a(self, key, value, len2[, overwrite])
        Defined at Dictionary.fpp lines 1723-1746
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : str array
        len2 : int array
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_s_a(this=self._handle, key=key, value=value, len2=len2, \
            overwrite=overwrite)
    
    def add_array_i2_a(self, key, value, len2, overwrite=None, interface_call=False):
        """
        add_array_i2_a(self, key, value, len2[, overwrite])
        Defined at Dictionary.fpp lines 1748-1771
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : int array
        len2 : int array
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_i2_a(this=self._handle, key=key, value=value, len2=len2, \
            overwrite=overwrite)
    
    def add_array_r2_a(self, key, value, len2, overwrite=None, interface_call=False):
        """
        add_array_r2_a(self, key, value, len2[, overwrite])
        Defined at Dictionary.fpp lines 1773-1796
        
        Parameters
        ----------
        this : Dictionary
        key : str
        value : float array
        len2 : int array
        overwrite : bool
        """
        quippy._quippy.f90wrap_dictionary_module__dictionary_add_array_r2_a(this=self._handle, key=key, value=value, len2=len2, \
            overwrite=overwrite)
    
    def add_array(*args, **kwargs):
        """
        add_array(*args, **kwargs)
        Defined at Dictionary.fpp lines 269-283
        
        Overloaded interface containing the following procedures:
          add_array_i
          add_array_r
          add_array_c
          add_array_l
          add_array_s
          add_array_i2
          add_array_r2
          add_array_i_a
          add_array_r_a
          add_array_c_a
          add_array_l_a
          add_array_s_a
          add_array_i2_a
          add_array_r2_a
        """
        for proc in [Dictionary.add_array_s_a, Dictionary.add_array_i2_a, Dictionary.add_array_r2_a, Dictionary.add_array_s, \
            Dictionary.add_array_i2, Dictionary.add_array_r2, Dictionary.add_array_i_a, Dictionary.add_array_r_a, \
            Dictionary.add_array_c_a, Dictionary.add_array_l_a, Dictionary.add_array_i, Dictionary.add_array_r, \
            Dictionary.add_array_c, Dictionary.add_array_l]:
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
            "add_array compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    @property
    def n(self):
        """
        number of entries in use
        
        Element n ftype=integer  pytype=int32
        Defined at Dictionary.fpp line 194
        """
        return quippy._quippy.f90wrap_dictionary__get__n(self._handle)
    
    @n.setter
    def n(self, n):
        quippy._quippy.f90wrap_dictionary__set__n(self._handle, n)
    
    def init_array_entries(self):
        self.entries = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            quippy._quippy.f90wrap_dictionary__array_getitem__entries,
                                            quippy._quippy.f90wrap_dictionary__array_setitem__entries,
                                            quippy._quippy.f90wrap_dictionary__array_len__entries,
                                            """
        array of entries
        
        Element entries ftype=type(dictentry) pytype=Dictentry array
        Defined at Dictionary.fpp line 196
        """, DictEntry,
                                            module_level=False)
        return self.entries
    
    @property
    def cache_invalid(self):
        """
        non-zero on exit from set_value(), set_value_pointer(), add_array(), remove_entry() if any array memory locations \
            changed
        
        Element cache_invalid ftype=integer  pytype=int32
        Defined at Dictionary.fpp line 197
        """
        return quippy._quippy.f90wrap_dictionary__get__cache_invalid(self._handle)
    
    @cache_invalid.setter
    def cache_invalid(self, cache_invalid):
        quippy._quippy.f90wrap_dictionary__set__cache_invalid(self._handle, cache_invalid)
    
    @property
    def key_cache_invalid(self):
        """
        non-zero on exit from set_value(), set_value_pointer(), add_array(), remove_entry() if any keys changed
        
        Element key_cache_invalid ftype=integer  pytype=int32
        Defined at Dictionary.fpp line 198
        """
        return quippy._quippy.f90wrap_dictionary__get__key_cache_invalid(self._handle)
    
    @key_cache_invalid.setter
    def key_cache_invalid(self, key_cache_invalid):
        quippy._quippy.f90wrap_dictionary__set__key_cache_invalid(self._handle, key_cache_invalid)
    
    def __str__(self):
        ret = ['<dictionary>{\n']
        ret.append('    n : ')
        ret.append(repr(self.n))
        ret.append(',\n    cache_invalid : ')
        ret.append(repr(self.cache_invalid))
        ret.append(',\n    key_cache_invalid : ')
        ret.append(repr(self.key_cache_invalid))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = [init_array_entries]
    

@f90wrap.runtime.register_class("quippy.c_dictionary_ptr_type")
class c_dictionary_ptr_type(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=c_dictionary_ptr_type)
    Defined at Dictionary.fpp lines 201-202
    """
    def __init__(self, handle=None):
        """
        Automatically generated constructor for c_dictionary_ptr_type
        
        self = C_Dictionary_Ptr_Type()
        Defined at Dictionary.fpp lines 201-202
        
        Returns
        -------
        this : C_Dictionary_Ptr_Type
            Object to be constructed
        
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_dictionary_module__c_dictionary_ptr_type_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_dictionary_module__c_dictionary_ptr_type_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    @property
    def p(self):
        """
        Element p ftype=type(dictionary) pytype=Dictionary
        Defined at Dictionary.fpp line 202
        """
        p_handle = quippy._quippy.f90wrap_c_dictionary_ptr_type__get__p(self._handle)
        if tuple(p_handle) in self._objs:
            p = self._objs[tuple(p_handle)]
        else:
            p = Dictionary.from_handle(p_handle)
            self._objs[tuple(p_handle)] = p
        return p
    
    @p.setter
    def p(self, p):
        p = p._handle
        quippy._quippy.f90wrap_c_dictionary_ptr_type__set__p(self._handle, p)
    
    def __str__(self):
        ret = ['<c_dictionary_ptr_type>{\n']
        ret.append('    p : ')
        ret.append(repr(self.p))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

def get_t_none():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_none ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_none()

T_NONE = get_t_none()

def get_t_integer():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_integer ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_integer()

T_INTEGER = get_t_integer()

def get_t_real():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_real ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_real()

T_REAL = get_t_real()

def get_t_complex():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_complex ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_complex()

T_COMPLEX = get_t_complex()

def get_t_logical():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_logical ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_logical()

T_LOGICAL = get_t_logical()

def get_t_integer_a():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_integer_a ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_integer_a()

T_INTEGER_A = get_t_integer_a()

def get_t_real_a():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_real_a ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_real_a()

T_REAL_A = get_t_real_a()

def get_t_complex_a():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_complex_a ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_complex_a()

T_COMPLEX_A = get_t_complex_a()

def get_t_logical_a():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_logical_a ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_logical_a()

T_LOGICAL_A = get_t_logical_a()

def get_t_char():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_char ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_char()

T_CHAR = get_t_char()

def get_t_char_a():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_char_a ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_char_a()

T_CHAR_A = get_t_char_a()

def get_t_data():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_data ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_data()

T_DATA = get_t_data()

def get_t_integer_a2():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_integer_a2 ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_integer_a2()

T_INTEGER_A2 = get_t_integer_a2()

def get_t_real_a2():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_real_a2 ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_real_a2()

T_REAL_A2 = get_t_real_a2()

def get_t_dict():
    """
    OMITMaintained for backwards compatibility with old NetCDF files using type attribute
    
    Element t_dict ftype=integer pytype=int32
    Defined at Dictionary.fpp line 142
    """
    return quippy._quippy.f90wrap_dictionary_module__get__t_dict()

T_DICT = get_t_dict()

def get_property_int():
    """
    Element property_int ftype=integer pytype=int32
    Defined at Dictionary.fpp line 146
    """
    return quippy._quippy.f90wrap_dictionary_module__get__property_int()

PROPERTY_INT = get_property_int()

def get_property_real():
    """
    Element property_real ftype=integer pytype=int32
    Defined at Dictionary.fpp line 146
    """
    return quippy._quippy.f90wrap_dictionary_module__get__property_real()

PROPERTY_REAL = get_property_real()

def get_property_str():
    """
    Element property_str ftype=integer pytype=int32
    Defined at Dictionary.fpp line 146
    """
    return quippy._quippy.f90wrap_dictionary_module__get__property_str()

PROPERTY_STR = get_property_str()

def get_property_logical():
    """
    Element property_logical ftype=integer pytype=int32
    Defined at Dictionary.fpp line 146
    """
    return quippy._quippy.f90wrap_dictionary_module__get__property_logical()

PROPERTY_LOGICAL = get_property_logical()

def get_c_key_len():
    """
    Element c_key_len ftype=integer pytype=int32
    Defined at Dictionary.fpp line 148
    """
    return quippy._quippy.f90wrap_dictionary_module__get__c_key_len()

C_KEY_LEN = get_c_key_len()

def get_string_length():
    """
    Maximum string length
    
    Element string_length ftype=integer pytype=int32
    Defined at Dictionary.fpp line 149
    """
    return quippy._quippy.f90wrap_dictionary_module__get__string_length()

STRING_LENGTH = get_string_length()

def get_string_length_short():
    """
    a shorter string length, for when there are LOTS of strings
    
    Element string_length_short ftype=integer pytype=int32
    Defined at Dictionary.fpp line 150
    """
    return quippy._quippy.f90wrap_dictionary_module__get__string_length_short()

STRING_LENGTH_SHORT = get_string_length_short()

def get_dict_n_fields():
    """
    Maximum number of fields during parsing
    
    Element dict_n_fields ftype=integer pytype=int32
    Defined at Dictionary.fpp line 151
    """
    return quippy._quippy.f90wrap_dictionary_module__get__dict_n_fields()

DICT_N_FIELDS = get_dict_n_fields()


_array_initialisers = []
_dt_array_initialisers = []


try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module "dictionary_module".')

for func in _dt_array_initialisers:
    func()
