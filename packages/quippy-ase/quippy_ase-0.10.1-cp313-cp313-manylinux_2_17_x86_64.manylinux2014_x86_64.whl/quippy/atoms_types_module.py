"""
Module atoms_types_module
Defined at Atoms_types.fpp lines 133-1518
"""
from __future__ import print_function, absolute_import, division
import quippy._quippy
import f90wrap.runtime
import logging
import numpy
import warnings
import weakref
from quippy.dictionary_module import Dictionary

logger = logging.getLogger(__name__)
warnings.filterwarnings("error", category=numpy.exceptions.ComplexWarning)
_arrays = {}
_objs = {}

@f90wrap.runtime.register_class("quippy.Table_pointer")
class Table_pointer(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=table_pointer)
    Defined at Atoms_types.fpp lines 152-153
    """
    def __init__(self, handle=None):
        """
        Automatically generated constructor for table_pointer
        
        self = Table_Pointer()
        Defined at Atoms_types.fpp lines 152-153
        
        Returns
        -------
        this : Table_Pointer
            Object to be constructed
        
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_atoms_types_module__table_pointer_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_atoms_types_module__table_pointer_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    _dt_array_initialisers = []
    

@f90wrap.runtime.register_class("quippy.Connection")
class Connection(f90wrap.runtime.FortranDerivedType):
    """
    The Connection type stores the topology of a set of Atoms
    
    We do not use a minimum image convention, rather, collect all the images of a neigbouring atoms
    that fall within the neighbour cutoff. The different images are made distinct in the connection list
    by having different 'shift' vectors associated with them.
    
    To save storage, the 'neighbour1' table contains all information about the connection
    but is only filled in for $i <= j$. 'neighbour2' is just a list of those of $i$'s neighbours
    with $i > j$ together with an index into the 'neighbour1' table of atom $j$.
    
    In normal use(i.e. outside this module) you don\\'t need direct access to the tables
    so you should use the interface functions 'atoms_n_neighbours' and 'atoms_neighbour' which
    hide the distiction between the cases $i <= j$ and $i > j$.
    
    :class:`Table` :attr:`neighbour1` (i): $i \\le j$ for all $j$ in table, ``intsize=4``, ``realsize=1``
    
    'connect%neighbour1(i)%int'
    
    > +----------+----------+----------+----------+
    > |    1     |    2     |    3     |    4     |
    > +----------+----------+----------+----------+
    > |    j     | shift_a  | shift_b  | shift_c  |
    > +----------+----------+----------+----------+
    
    'connect%neighbour1(i)%real'
    
    > +----------+
    > |    1     |
    > +----------+
    > |  r_ij    |
    > +----------+
    
    :class:`Table` :attr:`neighbour2` (i): $i > j$ for all $j$ in table, ``intsize =2``, ``realsize=0``
    
    'connect%neighbour2(i)%int'
    
    > +----------+----------+
    > |    1     |    2     |
    > +----------+----------+
    > |    j     |    n     |
    > +----------+----------+
    
    :class:`Table` :attr:`cell` (i,j,k) with ``intsize = 1``, ``realsize = 0``
    
    'connect%cell(i,j,k)2%int'
    
    > +----------+
    > |    1     |
    > +----------+
    > |  atom    |
    > +----------+
    
    N.B. If $i$ and $j$ are neighbours with shift 'shift', then
    'norm(atoms%pos(j) - atoms%pos(i) + shift)' is a minimum.
    Mnemonic: 'shift' is added to $j$ to get closer to $i$.
    
    Type(name=connection)
    Defined at Atoms_types.fpp lines 156-228
    """
    def __init__(self, handle=None):
        """
        Automatically generated constructor for connection
        
        self = Connection()
        Defined at Atoms_types.fpp lines 156-228
        
        Returns
        -------
        this : Connection
            Object to be constructed
        
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_atoms_types_module__connection_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_atoms_types_module__connection_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    @property
    def initialised(self):
        """
        Element initialised ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 212
        """
        return quippy._quippy.f90wrap_connection__get__initialised(self._handle)
    
    @initialised.setter
    def initialised(self, initialised):
        quippy._quippy.f90wrap_connection__set__initialised(self._handle, initialised)
    
    @property
    def cells_initialised(self):
        """
        Element cells_initialised ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 213
        """
        return quippy._quippy.f90wrap_connection__get__cells_initialised(self._handle)
    
    @cells_initialised.setter
    def cells_initialised(self, cells_initialised):
        quippy._quippy.f90wrap_connection__set__cells_initialised(self._handle, cells_initialised)
    
    @property
    def too_few_cells_warning_issued(self):
        """
        Element too_few_cells_warning_issued ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 214
        """
        return quippy._quippy.f90wrap_connection__get__too_few_cells_warning_issued(self._handle)
    
    @too_few_cells_warning_issued.setter
    def too_few_cells_warning_issued(self, too_few_cells_warning_issued):
        quippy._quippy.f90wrap_connection__set__too_few_cells_warning_issued(self._handle, too_few_cells_warning_issued)
    
    @property
    def cellsna(self):
        """
        no. of cells in the lattice directions
        
        Element cellsna ftype=integer                                     pytype=int32
        Defined at Atoms_types.fpp line 215
        """
        return quippy._quippy.f90wrap_connection__get__cellsna(self._handle)
    
    @cellsna.setter
    def cellsna(self, cellsna):
        quippy._quippy.f90wrap_connection__set__cellsna(self._handle, cellsna)
    
    @property
    def cellsnb(self):
        """
        Element cellsnb ftype=integer                                     pytype=int32
        Defined at Atoms_types.fpp line 216
        """
        return quippy._quippy.f90wrap_connection__get__cellsnb(self._handle)
    
    @cellsnb.setter
    def cellsnb(self, cellsnb):
        quippy._quippy.f90wrap_connection__set__cellsnb(self._handle, cellsnb)
    
    @property
    def cellsnc(self):
        """
        Element cellsnc ftype=integer                                     pytype=int32
        Defined at Atoms_types.fpp line 216
        """
        return quippy._quippy.f90wrap_connection__get__cellsnc(self._handle)
    
    @cellsnc.setter
    def cellsnc(self, cellsnc):
        quippy._quippy.f90wrap_connection__set__cellsnc(self._handle, cellsnc)
    
    @property
    def n(self):
        """
        no. of atoms at last calc_connect
        
        Element n ftype=integer                                     pytype=int32
        Defined at Atoms_types.fpp line 217
        """
        return quippy._quippy.f90wrap_connection__get__n(self._handle)
    
    @n.setter
    def n(self, n):
        quippy._quippy.f90wrap_connection__set__n(self._handle, n)
    
    def init_array_neighbour1(self):
        self.neighbour1 = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            quippy._quippy.f90wrap_connection__array_getitem__neighbour1,
                                            quippy._quippy.f90wrap_connection__array_setitem__neighbour1,
                                            quippy._quippy.f90wrap_connection__array_len__neighbour1,
                                            """
        Neighbour information for pairs $i <= j$.
        Contains full details of $j$, $r_{ij}$ and shift.
        
        Element neighbour1 ftype=type(table_pointer) pytype=Table_Pointer array
        Defined at Atoms_types.fpp line 218
        """, Table_pointer,
                                            module_level=False)
        return self.neighbour1
    
    def init_array_neighbour2(self):
        self.neighbour2 = f90wrap.runtime.FortranDerivedTypeArray(self,
                                            quippy._quippy.f90wrap_connection__array_getitem__neighbour2,
                                            quippy._quippy.f90wrap_connection__array_setitem__neighbour2,
                                            quippy._quippy.f90wrap_connection__array_len__neighbour2,
                                            """
        Neighbour information for pairs $i > j$.
        Simply contains $j$ and a reference to $j$'s
        'neighbour1' table.
        
        Element neighbour2 ftype=type(table_pointer) pytype=Table_Pointer array
        Defined at Atoms_types.fpp line 220
        """, Table_pointer,
                                            module_level=False)
        return self.neighbour2
    
    @property
    def cell_heads(self):
        """
        First entry in cell atoms structure
        
        Element cell_heads ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 223
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_connection__array__cell_heads(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        cell_heads = self._arrays.get(array_hash)
        if cell_heads is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if cell_heads.ctypes.data != array_handle:
                cell_heads = None
        if cell_heads is None:
            try:
                cell_heads = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_connection__array__cell_heads)
            except TypeError:
                cell_heads = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = cell_heads
        return cell_heads
    
    @cell_heads.setter
    def cell_heads(self, cell_heads):
        self.cell_heads[...] = cell_heads
    
    @property
    def next_atom_in_cell(self):
        """
        List of atoms, terminated by zero
        
        Element next_atom_in_cell ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 224
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_connection__array__next_atom_in_cell(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        next_atom_in_cell = self._arrays.get(array_hash)
        if next_atom_in_cell is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if next_atom_in_cell.ctypes.data != array_handle:
                next_atom_in_cell = None
        if next_atom_in_cell is None:
            try:
                next_atom_in_cell = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_connection__array__next_atom_in_cell)
            except TypeError:
                next_atom_in_cell = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = next_atom_in_cell
        return next_atom_in_cell
    
    @next_atom_in_cell.setter
    def next_atom_in_cell(self, next_atom_in_cell):
        self.next_atom_in_cell[...] = next_atom_in_cell
    
    @property
    def is_min_image(self):
        """
        True if i is a minimum image
        
        Element is_min_image ftype=logical pytype=int32 array
        Defined at Atoms_types.fpp line 225
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_connection__array__is_min_image(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        is_min_image = self._arrays.get(array_hash)
        if is_min_image is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if is_min_image.ctypes.data != array_handle:
                is_min_image = None
        if is_min_image is None:
            try:
                is_min_image = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_connection__array__is_min_image)
            except TypeError:
                is_min_image = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = is_min_image
        return is_min_image
    
    @is_min_image.setter
    def is_min_image(self, is_min_image):
        self.is_min_image[...] = is_min_image
    
    @property
    def last_connect_cutoff(self):
        """
        Value of cutoff used last time connectivity was updated
        
        Element last_connect_cutoff ftype=real(dp) pytype=float64
        Defined at Atoms_types.fpp line 226
        """
        return quippy._quippy.f90wrap_connection__get__last_connect_cutoff(self._handle)
    
    @last_connect_cutoff.setter
    def last_connect_cutoff(self, last_connect_cutoff):
        quippy._quippy.f90wrap_connection__set__last_connect_cutoff(self._handle, last_connect_cutoff)
    
    @property
    def last_connect_pos(self):
        """
        Positions of atoms last time connnectivity was updated
        
        Element last_connect_pos ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 227
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_connection__array__last_connect_pos(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        last_connect_pos = self._arrays.get(array_hash)
        if last_connect_pos is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if last_connect_pos.ctypes.data != array_handle:
                last_connect_pos = None
        if last_connect_pos is None:
            try:
                last_connect_pos = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_connection__array__last_connect_pos)
            except TypeError:
                last_connect_pos = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = last_connect_pos
        return last_connect_pos
    
    @last_connect_pos.setter
    def last_connect_pos(self, last_connect_pos):
        self.last_connect_pos[...] = last_connect_pos
    
    @property
    def last_connect_lattice(self):
        """
        Lattice last time connectivity was updated
        
        Element last_connect_lattice ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 228
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_connection__array__last_connect_lattice(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        last_connect_lattice = self._arrays.get(array_hash)
        if last_connect_lattice is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if last_connect_lattice.ctypes.data != array_handle:
                last_connect_lattice = None
        if last_connect_lattice is None:
            try:
                last_connect_lattice = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_connection__array__last_connect_lattice)
            except TypeError:
                last_connect_lattice = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = last_connect_lattice
        return last_connect_lattice
    
    @last_connect_lattice.setter
    def last_connect_lattice(self, last_connect_lattice):
        self.last_connect_lattice[...] = last_connect_lattice
    
    def __str__(self):
        ret = ['<connection>{\n']
        ret.append('    initialised : ')
        ret.append(repr(self.initialised))
        ret.append(',\n    cells_initialised : ')
        ret.append(repr(self.cells_initialised))
        ret.append(',\n    too_few_cells_warning_issued : ')
        ret.append(repr(self.too_few_cells_warning_issued))
        ret.append(',\n    cellsna : ')
        ret.append(repr(self.cellsna))
        ret.append(',\n    cellsnb : ')
        ret.append(repr(self.cellsnb))
        ret.append(',\n    cellsnc : ')
        ret.append(repr(self.cellsnc))
        ret.append(',\n    n : ')
        ret.append(repr(self.n))
        ret.append(',\n    cell_heads : ')
        ret.append(repr(self.cell_heads))
        ret.append(',\n    next_atom_in_cell : ')
        ret.append(repr(self.next_atom_in_cell))
        ret.append(',\n    is_min_image : ')
        ret.append(repr(self.is_min_image))
        ret.append(',\n    last_connect_cutoff : ')
        ret.append(repr(self.last_connect_cutoff))
        ret.append(',\n    last_connect_pos : ')
        ret.append(repr(self.last_connect_pos))
        ret.append(',\n    last_connect_lattice : ')
        ret.append(repr(self.last_connect_lattice))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = [init_array_neighbour1, init_array_neighbour2]
    

@f90wrap.runtime.register_class("quippy.DomainDecomposition")
class DomainDecomposition(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=domaindecomposition)
    Defined at Atoms_types.fpp lines 231-275
    """
    def __init__(self, handle=None):
        """
        Automatically generated constructor for domaindecomposition
        
        self = Domaindecomposition()
        Defined at Atoms_types.fpp lines 231-275
        
        Returns
        -------
        this : Domaindecomposition
            Object to be constructed
        
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_atoms_types_module__domaindecomposition_initialise()
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_atoms_types_module__domaindecomposition_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    @property
    def ntotal(self):
        """
        Number of total particles in this simulation
        
        Element ntotal ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 232
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__ntotal(self._handle)
    
    @ntotal.setter
    def ntotal(self, ntotal):
        quippy._quippy.f90wrap_domaindecomposition__set__ntotal(self._handle, ntotal)
    
    @property
    def local_to_global(self):
        """
        Local index to global index
        
        Element local_to_global ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 233
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__local_to_global(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        local_to_global = self._arrays.get(array_hash)
        if local_to_global is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if local_to_global.ctypes.data != array_handle:
                local_to_global = None
        if local_to_global is None:
            try:
                local_to_global = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__local_to_global)
            except TypeError:
                local_to_global = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = local_to_global
        return local_to_global
    
    @local_to_global.setter
    def local_to_global(self, local_to_global):
        self.local_to_global[...] = local_to_global
    
    @property
    def global_to_local(self):
        """
        Global index to local index
        
        Element global_to_local ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 234
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__global_to_local(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        global_to_local = self._arrays.get(array_hash)
        if global_to_local is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if global_to_local.ctypes.data != array_handle:
                global_to_local = None
        if global_to_local is None:
            try:
                global_to_local = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__global_to_local)
            except TypeError:
                global_to_local = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = global_to_local
        return global_to_local
    
    @global_to_local.setter
    def global_to_local(self, global_to_local):
        self.global_to_local[...] = global_to_local
    
    @property
    def decomposition(self):
        """
        Type of decomposition
        
        Element decomposition ftype=integer                     pytype=int array
        Defined at Atoms_types.fpp line 235
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__decomposition(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        decomposition = self._arrays.get(array_hash)
        if decomposition is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if decomposition.ctypes.data != array_handle:
                decomposition = None
        if decomposition is None:
            try:
                decomposition = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__decomposition)
            except TypeError:
                decomposition = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = decomposition
        return decomposition
    
    @decomposition.setter
    def decomposition(self, decomposition):
        self.decomposition[...] = decomposition
    
    @property
    def mode(self):
        """
        Element mode ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 236
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__mode(self._handle)
    
    @mode.setter
    def mode(self, mode):
        quippy._quippy.f90wrap_domaindecomposition__set__mode(self._handle, mode)
    
    @property
    def decomposed(self):
        """
        True if domain decomposition is active
        
        Element decomposed ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 237
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__decomposed(self._handle)
    
    @decomposed.setter
    def decomposed(self, decomposed):
        quippy._quippy.f90wrap_domaindecomposition__set__decomposed(self._handle, decomposed)
    
    @property
    def requested_border(self):
        """
        Element requested_border ftype=real(dp) pytype=float64
        Defined at Atoms_types.fpp line 238
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__requested_border(self._handle)
    
    @requested_border.setter
    def requested_border(self, requested_border):
        quippy._quippy.f90wrap_domaindecomposition__set__requested_border(self._handle, requested_border)
    
    @property
    def border(self):
        """
        Element border ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 239
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__border(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        border = self._arrays.get(array_hash)
        if border is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if border.ctypes.data != array_handle:
                border = None
        if border is None:
            try:
                border = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__border)
            except TypeError:
                border = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = border
        return border
    
    @border.setter
    def border(self, border):
        self.border[...] = border
    
    @property
    def verlet_shell(self):
        """
        Element verlet_shell ftype=real(dp) pytype=float64
        Defined at Atoms_types.fpp line 240
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__verlet_shell(self._handle)
    
    @verlet_shell.setter
    def verlet_shell(self, verlet_shell):
        quippy._quippy.f90wrap_domaindecomposition__set__verlet_shell(self._handle, verlet_shell)
    
    @property
    def communicate_forces(self):
        """
        Element communicate_forces ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 241
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__communicate_forces(self._handle)
    
    @communicate_forces.setter
    def communicate_forces(self, communicate_forces):
        quippy._quippy.f90wrap_domaindecomposition__set__communicate_forces(self._handle, communicate_forces)
    
    @property
    def lower(self):
        """
        Lower domain boundary, in fraction of the total cell
        
        Element lower ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 242
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__lower(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        lower = self._arrays.get(array_hash)
        if lower is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if lower.ctypes.data != array_handle:
                lower = None
        if lower is None:
            try:
                lower = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__lower)
            except TypeError:
                lower = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = lower
        return lower
    
    @lower.setter
    def lower(self, lower):
        self.lower[...] = lower
    
    @property
    def upper(self):
        """
        Upper domain boundary, in fraction of the total cell
        
        Element upper ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 243
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__upper(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        upper = self._arrays.get(array_hash)
        if upper is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if upper.ctypes.data != array_handle:
                upper = None
        if upper is None:
            try:
                upper = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__upper)
            except TypeError:
                upper = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = upper
        return upper
    
    @upper.setter
    def upper(self, upper):
        self.upper[...] = upper
    
    @property
    def center(self):
        """
        Center of the domain
        
        Element center ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 244
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__center(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        center = self._arrays.get(array_hash)
        if center is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if center.ctypes.data != array_handle:
                center = None
        if center is None:
            try:
                center = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__center)
            except TypeError:
                center = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = center
        return center
    
    @center.setter
    def center(self, center):
        self.center[...] = center
    
    @property
    def lower_with_border(self):
        """
        Lower domain boundary, including border
        
        Element lower_with_border ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 245
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__lower_with_border(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        lower_with_border = self._arrays.get(array_hash)
        if lower_with_border is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if lower_with_border.ctypes.data != array_handle:
                lower_with_border = None
        if lower_with_border is None:
            try:
                lower_with_border = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__lower_with_border)
            except TypeError:
                lower_with_border = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = lower_with_border
        return lower_with_border
    
    @lower_with_border.setter
    def lower_with_border(self, lower_with_border):
        self.lower_with_border[...] = lower_with_border
    
    @property
    def upper_with_border(self):
        """
        Upper domain boundary, including border
        
        Element upper_with_border ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 246
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__upper_with_border(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        upper_with_border = self._arrays.get(array_hash)
        if upper_with_border is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if upper_with_border.ctypes.data != array_handle:
                upper_with_border = None
        if upper_with_border is None:
            try:
                upper_with_border = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__upper_with_border)
            except TypeError:
                upper_with_border = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = upper_with_border
        return upper_with_border
    
    @upper_with_border.setter
    def upper_with_border(self, upper_with_border):
        self.upper_with_border[...] = upper_with_border
    
    @property
    def periodic(self):
        """
        Periodicity for domain decomposition
        
        Element periodic ftype=logical pytype=int32 array
        Defined at Atoms_types.fpp line 248
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__periodic(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        periodic = self._arrays.get(array_hash)
        if periodic is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if periodic.ctypes.data != array_handle:
                periodic = None
        if periodic is None:
            try:
                periodic = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__periodic)
            except TypeError:
                periodic = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = periodic
        return periodic
    
    @periodic.setter
    def periodic(self, periodic):
        self.periodic[...] = periodic
    
    @property
    def l(self):
        """
        Ranks of left domains in x-, y- and z-direction
        
        Element l ftype=integer                     pytype=int array
        Defined at Atoms_types.fpp line 249
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_domaindecomposition__array__l(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        l = self._arrays.get(array_hash)
        if l is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if l.ctypes.data != array_handle:
                l = None
        if l is None:
            try:
                l = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__l)
            except TypeError:
                l = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = l
        return l
    
    @l.setter
    def l(self, l):
        self.l[...] = l
    
    @property
    def r(self):
        """
        Ranks of right domains in x-, y- and z-direction
        
        Element r ftype=integer                     pytype=int array
        Defined at Atoms_types.fpp line 250
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_domaindecomposition__array__r(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        r = self._arrays.get(array_hash)
        if r is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if r.ctypes.data != array_handle:
                r = None
        if r is None:
            try:
                r = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__r)
            except TypeError:
                r = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = r
        return r
    
    @r.setter
    def r(self, r):
        self.r[...] = r
    
    @property
    def off_l(self):
        """
        Distance vector to left domain
        
        Element off_l ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 251
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__off_l(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        off_l = self._arrays.get(array_hash)
        if off_l is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if off_l.ctypes.data != array_handle:
                off_l = None
        if off_l is None:
            try:
                off_l = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__off_l)
            except TypeError:
                off_l = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = off_l
        return off_l
    
    @off_l.setter
    def off_l(self, off_l):
        self.off_l[...] = off_l
    
    @property
    def off_r(self):
        """
        Distance vector to right domain
        
        Element off_r ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 252
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__off_r(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        off_r = self._arrays.get(array_hash)
        if off_r is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if off_r.ctypes.data != array_handle:
                off_r = None
        if off_r is None:
            try:
                off_r = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__off_r)
            except TypeError:
                off_r = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = off_r
        return off_r
    
    @off_r.setter
    def off_r(self, off_r):
        self.off_r[...] = off_r
    
    @property
    def atoms_properties(self):
        """
        Fields to communicate if for particles
        
        Element atoms_properties ftype=type(dictionary) pytype=Dictionary
        Defined at Atoms_types.fpp line 253
        """
        atoms_properties_handle = quippy._quippy.f90wrap_domaindecomposition__get__atoms_properties(self._handle)
        if tuple(atoms_properties_handle) in self._objs:
            atoms_properties = self._objs[tuple(atoms_properties_handle)]
        else:
            atoms_properties = Dictionary.from_handle(atoms_properties_handle)
            self._objs[tuple(atoms_properties_handle)] = atoms_properties
        return atoms_properties
    
    @atoms_properties.setter
    def atoms_properties(self, atoms_properties):
        atoms_properties = atoms_properties._handle
        quippy._quippy.f90wrap_domaindecomposition__set__atoms_properties(self._handle, atoms_properties)
    
    @property
    def ghost_properties(self):
        """
        Fields to communicate for ghosts
        
        Element ghost_properties ftype=type(dictionary) pytype=Dictionary
        Defined at Atoms_types.fpp line 254
        """
        ghost_properties_handle = quippy._quippy.f90wrap_domaindecomposition__get__ghost_properties(self._handle)
        if tuple(ghost_properties_handle) in self._objs:
            ghost_properties = self._objs[tuple(ghost_properties_handle)]
        else:
            ghost_properties = Dictionary.from_handle(ghost_properties_handle)
            self._objs[tuple(ghost_properties_handle)] = ghost_properties
        return ghost_properties
    
    @ghost_properties.setter
    def ghost_properties(self, ghost_properties):
        ghost_properties = ghost_properties._handle
        quippy._quippy.f90wrap_domaindecomposition__set__ghost_properties(self._handle, ghost_properties)
    
    @property
    def reverse_properties(self):
        """
        Back-communication after force computations
        
        Element reverse_properties ftype=type(dictionary) pytype=Dictionary
        Defined at Atoms_types.fpp line 255
        """
        reverse_properties_handle = quippy._quippy.f90wrap_domaindecomposition__get__reverse_properties(self._handle)
        if tuple(reverse_properties_handle) in self._objs:
            reverse_properties = self._objs[tuple(reverse_properties_handle)]
        else:
            reverse_properties = Dictionary.from_handle(reverse_properties_handle)
            self._objs[tuple(reverse_properties_handle)] = reverse_properties
        return reverse_properties
    
    @reverse_properties.setter
    def reverse_properties(self, reverse_properties):
        reverse_properties = reverse_properties._handle
        quippy._quippy.f90wrap_domaindecomposition__set__reverse_properties(self._handle, reverse_properties)
    
    @property
    def atoms_mask(self):
        """
        Element atoms_mask ftype=logical pytype=int32 array
        Defined at Atoms_types.fpp line 256
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__atoms_mask(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        atoms_mask = self._arrays.get(array_hash)
        if atoms_mask is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if atoms_mask.ctypes.data != array_handle:
                atoms_mask = None
        if atoms_mask is None:
            try:
                atoms_mask = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__atoms_mask)
            except TypeError:
                atoms_mask = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = atoms_mask
        return atoms_mask
    
    @atoms_mask.setter
    def atoms_mask(self, atoms_mask):
        self.atoms_mask[...] = atoms_mask
    
    @property
    def ghost_mask(self):
        """
        Element ghost_mask ftype=logical pytype=int32 array
        Defined at Atoms_types.fpp line 257
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__ghost_mask(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        ghost_mask = self._arrays.get(array_hash)
        if ghost_mask is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if ghost_mask.ctypes.data != array_handle:
                ghost_mask = None
        if ghost_mask is None:
            try:
                ghost_mask = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__ghost_mask)
            except TypeError:
                ghost_mask = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = ghost_mask
        return ghost_mask
    
    @ghost_mask.setter
    def ghost_mask(self, ghost_mask):
        self.ghost_mask[...] = ghost_mask
    
    @property
    def reverse_mask(self):
        """
        Element reverse_mask ftype=logical pytype=int32 array
        Defined at Atoms_types.fpp line 258
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__reverse_mask(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        reverse_mask = self._arrays.get(array_hash)
        if reverse_mask is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if reverse_mask.ctypes.data != array_handle:
                reverse_mask = None
        if reverse_mask is None:
            try:
                reverse_mask = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__reverse_mask)
            except TypeError:
                reverse_mask = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = reverse_mask
        return reverse_mask
    
    @reverse_mask.setter
    def reverse_mask(self, reverse_mask):
        self.reverse_mask[...] = reverse_mask
    
    @property
    def atoms_buffer_size(self):
        """
        Element atoms_buffer_size ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 259
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__atoms_buffer_size(self._handle)
    
    @atoms_buffer_size.setter
    def atoms_buffer_size(self, atoms_buffer_size):
        quippy._quippy.f90wrap_domaindecomposition__set__atoms_buffer_size(self._handle, atoms_buffer_size)
    
    @property
    def ghost_buffer_size(self):
        """
        Element ghost_buffer_size ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 260
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__ghost_buffer_size(self._handle)
    
    @ghost_buffer_size.setter
    def ghost_buffer_size(self, ghost_buffer_size):
        quippy._quippy.f90wrap_domaindecomposition__set__ghost_buffer_size(self._handle, ghost_buffer_size)
    
    @property
    def reverse_buffer_size(self):
        """
        Element reverse_buffer_size ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 261
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__reverse_buffer_size(self._handle)
    
    @reverse_buffer_size.setter
    def reverse_buffer_size(self, reverse_buffer_size):
        quippy._quippy.f90wrap_domaindecomposition__set__reverse_buffer_size(self._handle, reverse_buffer_size)
    
    @property
    def send_l(self):
        """
        buffer for sending to the left
        
        Element send_l ftype=character(1) pytype=str array
        Defined at Atoms_types.fpp line 262
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__send_l(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        send_l = self._arrays.get(array_hash)
        if send_l is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if send_l.ctypes.data != array_handle:
                send_l = None
        if send_l is None:
            try:
                send_l = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__send_l)
            except TypeError:
                send_l = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = send_l
        return send_l
    
    @send_l.setter
    def send_l(self, send_l):
        self.send_l[...] = send_l
    
    @property
    def send_r(self):
        """
        buffer for sending to the right
        
        Element send_r ftype=character(1) pytype=str array
        Defined at Atoms_types.fpp line 263
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__send_r(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        send_r = self._arrays.get(array_hash)
        if send_r is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if send_r.ctypes.data != array_handle:
                send_r = None
        if send_r is None:
            try:
                send_r = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__send_r)
            except TypeError:
                send_r = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = send_r
        return send_r
    
    @send_r.setter
    def send_r(self, send_r):
        self.send_r[...] = send_r
    
    @property
    def recv_l(self):
        """
        buffer for receiving from the left
        
        Element recv_l ftype=character(1) pytype=str array
        Defined at Atoms_types.fpp line 264
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__recv_l(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        recv_l = self._arrays.get(array_hash)
        if recv_l is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if recv_l.ctypes.data != array_handle:
                recv_l = None
        if recv_l is None:
            try:
                recv_l = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__recv_l)
            except TypeError:
                recv_l = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = recv_l
        return recv_l
    
    @recv_l.setter
    def recv_l(self, recv_l):
        self.recv_l[...] = recv_l
    
    @property
    def recv_r(self):
        """
        buffer for receiving from the right
        
        Element recv_r ftype=character(1) pytype=str array
        Defined at Atoms_types.fpp line 265
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__recv_r(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        recv_r = self._arrays.get(array_hash)
        if recv_r is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if recv_r.ctypes.data != array_handle:
                recv_r = None
        if recv_r is None:
            try:
                recv_r = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__recv_r)
            except TypeError:
                recv_r = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = recv_r
        return recv_r
    
    @recv_r.setter
    def recv_r(self, recv_r):
        self.recv_r[...] = recv_r
    
    @property
    def n_ghosts_r(self):
        """
        length of the ghost particle lists(right)
        
        Element n_ghosts_r ftype=integer                     pytype=int array
        Defined at Atoms_types.fpp line 266
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__n_ghosts_r(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        n_ghosts_r = self._arrays.get(array_hash)
        if n_ghosts_r is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if n_ghosts_r.ctypes.data != array_handle:
                n_ghosts_r = None
        if n_ghosts_r is None:
            try:
                n_ghosts_r = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__n_ghosts_r)
            except TypeError:
                n_ghosts_r = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = n_ghosts_r
        return n_ghosts_r
    
    @n_ghosts_r.setter
    def n_ghosts_r(self, n_ghosts_r):
        self.n_ghosts_r[...] = n_ghosts_r
    
    @property
    def n_ghosts_l(self):
        """
        length of the ghost particle lists(left)
        
        Element n_ghosts_l ftype=integer                     pytype=int array
        Defined at Atoms_types.fpp line 267
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__n_ghosts_l(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        n_ghosts_l = self._arrays.get(array_hash)
        if n_ghosts_l is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if n_ghosts_l.ctypes.data != array_handle:
                n_ghosts_l = None
        if n_ghosts_l is None:
            try:
                n_ghosts_l = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__n_ghosts_l)
            except TypeError:
                n_ghosts_l = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = n_ghosts_l
        return n_ghosts_l
    
    @n_ghosts_l.setter
    def n_ghosts_l(self, n_ghosts_l):
        self.n_ghosts_l[...] = n_ghosts_l
    
    @property
    def ghosts_r(self):
        """
        particles send to the right(where they become ghosts)
        
        Element ghosts_r ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 268
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__ghosts_r(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        ghosts_r = self._arrays.get(array_hash)
        if ghosts_r is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if ghosts_r.ctypes.data != array_handle:
                ghosts_r = None
        if ghosts_r is None:
            try:
                ghosts_r = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__ghosts_r)
            except TypeError:
                ghosts_r = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = ghosts_r
        return ghosts_r
    
    @ghosts_r.setter
    def ghosts_r(self, ghosts_r):
        self.ghosts_r[...] = ghosts_r
    
    @property
    def ghosts_l(self):
        """
        particles send to the left(where they become ghosts)
        
        Element ghosts_l ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 269
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_domaindecomposition__array__ghosts_l(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        ghosts_l = self._arrays.get(array_hash)
        if ghosts_l is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if ghosts_l.ctypes.data != array_handle:
                ghosts_l = None
        if ghosts_l is None:
            try:
                ghosts_l = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_domaindecomposition__array__ghosts_l)
            except TypeError:
                ghosts_l = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = ghosts_l
        return ghosts_l
    
    @ghosts_l.setter
    def ghosts_l(self, ghosts_l):
        self.ghosts_l[...] = ghosts_l
    
    @property
    def n_send_p_tot(self):
        """
        Statistics: Number of total particles send
        
        Element n_send_p_tot ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 270
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__n_send_p_tot(self._handle)
    
    @n_send_p_tot.setter
    def n_send_p_tot(self, n_send_p_tot):
        quippy._quippy.f90wrap_domaindecomposition__set__n_send_p_tot(self._handle, n_send_p_tot)
    
    @property
    def n_recv_p_tot(self):
        """
        Statistics: Number of total particles received
        
        Element n_recv_p_tot ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 271
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__n_recv_p_tot(self._handle)
    
    @n_recv_p_tot.setter
    def n_recv_p_tot(self, n_recv_p_tot):
        quippy._quippy.f90wrap_domaindecomposition__set__n_recv_p_tot(self._handle, n_recv_p_tot)
    
    @property
    def n_send_g_tot(self):
        """
        Statistics: Number of total ghosts send
        
        Element n_send_g_tot ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 272
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__n_send_g_tot(self._handle)
    
    @n_send_g_tot.setter
    def n_send_g_tot(self, n_send_g_tot):
        quippy._quippy.f90wrap_domaindecomposition__set__n_send_g_tot(self._handle, n_send_g_tot)
    
    @property
    def n_recv_g_tot(self):
        """
        Statistics: Number of total ghosts received
        
        Element n_recv_g_tot ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 273
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__n_recv_g_tot(self._handle)
    
    @n_recv_g_tot.setter
    def n_recv_g_tot(self, n_recv_g_tot):
        quippy._quippy.f90wrap_domaindecomposition__set__n_recv_g_tot(self._handle, n_recv_g_tot)
    
    @property
    def nit_p(self):
        """
        Statistics: Number of particle send events
        
        Element nit_p ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 274
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__nit_p(self._handle)
    
    @nit_p.setter
    def nit_p(self, nit_p):
        quippy._quippy.f90wrap_domaindecomposition__set__nit_p(self._handle, nit_p)
    
    @property
    def nit_g(self):
        """
        Statistics: Number of ghost send events
        
        Element nit_g ftype=integer                     pytype=int32
        Defined at Atoms_types.fpp line 275
        """
        return quippy._quippy.f90wrap_domaindecomposition__get__nit_g(self._handle)
    
    @nit_g.setter
    def nit_g(self, nit_g):
        quippy._quippy.f90wrap_domaindecomposition__set__nit_g(self._handle, nit_g)
    
    def __str__(self):
        ret = ['<domaindecomposition>{\n']
        ret.append('    ntotal : ')
        ret.append(repr(self.ntotal))
        ret.append(',\n    local_to_global : ')
        ret.append(repr(self.local_to_global))
        ret.append(',\n    global_to_local : ')
        ret.append(repr(self.global_to_local))
        ret.append(',\n    decomposition : ')
        ret.append(repr(self.decomposition))
        ret.append(',\n    mode : ')
        ret.append(repr(self.mode))
        ret.append(',\n    decomposed : ')
        ret.append(repr(self.decomposed))
        ret.append(',\n    requested_border : ')
        ret.append(repr(self.requested_border))
        ret.append(',\n    border : ')
        ret.append(repr(self.border))
        ret.append(',\n    verlet_shell : ')
        ret.append(repr(self.verlet_shell))
        ret.append(',\n    communicate_forces : ')
        ret.append(repr(self.communicate_forces))
        ret.append(',\n    lower : ')
        ret.append(repr(self.lower))
        ret.append(',\n    upper : ')
        ret.append(repr(self.upper))
        ret.append(',\n    center : ')
        ret.append(repr(self.center))
        ret.append(',\n    lower_with_border : ')
        ret.append(repr(self.lower_with_border))
        ret.append(',\n    upper_with_border : ')
        ret.append(repr(self.upper_with_border))
        ret.append(',\n    periodic : ')
        ret.append(repr(self.periodic))
        ret.append(',\n    l : ')
        ret.append(repr(self.l))
        ret.append(',\n    r : ')
        ret.append(repr(self.r))
        ret.append(',\n    off_l : ')
        ret.append(repr(self.off_l))
        ret.append(',\n    off_r : ')
        ret.append(repr(self.off_r))
        ret.append(',\n    atoms_properties : ')
        ret.append(repr(self.atoms_properties))
        ret.append(',\n    ghost_properties : ')
        ret.append(repr(self.ghost_properties))
        ret.append(',\n    reverse_properties : ')
        ret.append(repr(self.reverse_properties))
        ret.append(',\n    atoms_mask : ')
        ret.append(repr(self.atoms_mask))
        ret.append(',\n    ghost_mask : ')
        ret.append(repr(self.ghost_mask))
        ret.append(',\n    reverse_mask : ')
        ret.append(repr(self.reverse_mask))
        ret.append(',\n    atoms_buffer_size : ')
        ret.append(repr(self.atoms_buffer_size))
        ret.append(',\n    ghost_buffer_size : ')
        ret.append(repr(self.ghost_buffer_size))
        ret.append(',\n    reverse_buffer_size : ')
        ret.append(repr(self.reverse_buffer_size))
        ret.append(',\n    send_l : ')
        ret.append(repr(self.send_l))
        ret.append(',\n    send_r : ')
        ret.append(repr(self.send_r))
        ret.append(',\n    recv_l : ')
        ret.append(repr(self.recv_l))
        ret.append(',\n    recv_r : ')
        ret.append(repr(self.recv_r))
        ret.append(',\n    n_ghosts_r : ')
        ret.append(repr(self.n_ghosts_r))
        ret.append(',\n    n_ghosts_l : ')
        ret.append(repr(self.n_ghosts_l))
        ret.append(',\n    ghosts_r : ')
        ret.append(repr(self.ghosts_r))
        ret.append(',\n    ghosts_l : ')
        ret.append(repr(self.ghosts_l))
        ret.append(',\n    n_send_p_tot : ')
        ret.append(repr(self.n_send_p_tot))
        ret.append(',\n    n_recv_p_tot : ')
        ret.append(repr(self.n_recv_p_tot))
        ret.append(',\n    n_send_g_tot : ')
        ret.append(repr(self.n_send_g_tot))
        ret.append(',\n    n_recv_g_tot : ')
        ret.append(repr(self.n_recv_g_tot))
        ret.append(',\n    nit_p : ')
        ret.append(repr(self.nit_p))
        ret.append(',\n    nit_g : ')
        ret.append(repr(self.nit_g))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

@f90wrap.runtime.register_class("quippy.Atoms")
class Atoms(f90wrap.runtime.FortranDerivedType):
    """
    Representation of an atomic configuration and its associated properties
    
    An atoms object contains atomic numbers, all dynamical variables
    and connectivity information for all the atoms in the simulation cell.
    It is initialised like this:
    >           call initialise(MyAtoms,N,lattice)
    where 'N' is the number of atoms to allocate space for and 'lattice' is a $3\\times3$
    matrix of lattice vectors given as column vectors, so that 'lattice(:,i)' is the i-th lattice vector.
    
    Atoms also contains a Connection object, which stores distance information about
    the atom neghbours after 'calc_connect' has been called. Rather than using a minimum
    image convention, all neighbours are stored up to a radius of 'cutoff', including imagesSelf-deallocating object
    
    Type(name=atoms)
    Defined at Atoms_types.fpp lines 278-383
    """
    def repoint(self, interface_call=False):
        """
        OMITInitialise pointers for convenient access to special columns of this%properties
        
        repoint(self)
        Defined at Atoms_types.fpp lines 468-596
        
        Parameters
        ----------
        this : Atoms
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_repoint(this=self._handle)
    
    def sort(self, prop1, prop2=None, prop3=None, error=None, interface_call=False):
        """
        sort atoms by one or more(max 2 now) integer or real properties
        
        sort(self, prop1[, prop2, prop3, error])
        Defined at Atoms_types.fpp lines 1260-1302
        
        Parameters
        ----------
        this : Atoms
        prop1 : str
        prop2 : str
        prop3 : str
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_sort(this=self._handle, prop1=prop1, prop2=prop2, prop3=prop3, \
            error=error)
    
    def diff(self, i, j, shift, interface_call=False):
        """
        Difference vector between atoms $i$ and $j$ if they are separated by a shift of 'shift'
        \\begin{displaymath}
        \\mathbf{u}_{ij} = \\mathbf{r}_j - \\mathbf{r}_i + \\mathbf{R} \\cdot  \\mathbf{s}
        \\end{displaymath}
        where $\\mathbf{R}$ is the 'lattice' matrix and $\\mathbf{s}$ the shift
        
        diff = diff(self, i, j, shift)
        Defined at Atoms_types.fpp lines 1364-1369
        
        Parameters
        ----------
        this : Atoms
        i : int32
        j : int32
        shift : int array
        
        Returns
        -------
        diff : float array
        """
        diff = quippy._quippy.f90wrap_atoms_types_module__diff(this=self._handle, i=i, j=j, shift=shift)
        return diff
    
    def realpos(self, i, interface_call=False):
        """
        Return the real position of atom 'i', taking into account the
        stored travel across the periodic boundary \
            conditions.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        
        realpos = realpos(self, i)
        Defined at Atoms_types.fpp lines 1429-1437
        
        Parameters
        ----------
        this : Atoms
        i : int32
        
        Returns
        -------
        realpos : float array
        """
        realpos = quippy._quippy.f90wrap_atoms_types_module__realpos(this=self._handle, i=i)
        return realpos
    
    def distance(self, i, j, shift, interface_call=False):
        """
        Return distance between atoms 'i' and 'j' if they are separated by a shift
        of 'shift'.
        
        \\begin{displaymath}
        r_{ij} = \\left| \\mathbf{r}_j - \\mathbf{r}_i + \\mathbf{R} \\cdot  \\mathbf{s} \\right|
        \\end{displaymath}
        where $\\mathbf{R}$ is the 'lattice' matrix and $\\mathbf{s}$ the shift.
        
        distance = distance(self, i, j, shift)
        Defined at Atoms_types.fpp lines 1446-1450
        
        Parameters
        ----------
        this : Atoms
        i : int32
        j : int32
        shift : int array
        
        Returns
        -------
        distance : float64
        """
        distance = quippy._quippy.f90wrap_atoms_types_module__distance(this=self._handle, i=i, j=j, shift=shift)
        return distance
    
    def copy_entry(self, src, dst, swap=None, error=None, interface_call=False):
        """
        Copy an atom to a different index
        Move a single atom from one location to another one.
        The destination will be overriden.
        
        copy_entry(self, src, dst[, swap, error])
        Defined at Atoms_types.fpp lines 1175-1257
        
        Parameters
        ----------
        this : Atoms
        src : int32
        dst : int32
        swap : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_copy_entry(this=self._handle, src=src, dst=dst, swap=swap, error=error)
    
    def __init__(self, n, lattice, properties=None, params=None, fixed_size=None, nbuffer=None, error=None, handle=None):
        """
        Initialise an Atoms object to store 'N' atoms and specify the initial lattice.
        
        self = Atoms(n, lattice[, properties, params, fixed_size, nbuffer, error])
        Defined at Atoms.fpp lines 404-478
        
        Parameters
        ----------
        n : int32
        lattice : float array
        properties : Dictionary
        params : Dictionary
        fixed_size : bool
        nbuffer : int32
        error : int32
        
        Returns
        -------
        this : Atoms
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_atoms_module__atoms_initialise(n=n, lattice=lattice, properties=(None if properties is \
                None else properties._handle), params=(None if params is None else params._handle), fixed_size=fixed_size, \
                nbuffer=nbuffer, error=error)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            destructor = getattr(quippy._quippy, "f90wrap_atoms_module__atoms_finalise")
            self._finalizer = weakref.finalize(self, destructor, self._handle)
    
    def is_initialised(self, interface_call=False):
        """
        Is this atoms object initialised?
        
        atoms_is_initialised = is_initialised(self)
        Defined at Atoms.fpp lines 501-503
        
        Parameters
        ----------
        this : Atoms
        
        Returns
        -------
        atoms_is_initialised : bool
        """
        atoms_is_initialised = quippy._quippy.f90wrap_atoms_module__atoms_is_initialised(this=self._handle)
        return atoms_is_initialised
    
    def is_domain_decomposed(self, interface_call=False):
        """
        Is this atoms object domain decomposed?
        
        atoms_is_domain_decomposed = is_domain_decomposed(self)
        Defined at Atoms.fpp lines 506-508
        
        Parameters
        ----------
        this : Atoms
        
        Returns
        -------
        atoms_is_domain_decomposed : bool
        """
        atoms_is_domain_decomposed = quippy._quippy.f90wrap_atoms_module__atoms_is_domain_decomposed(this=self._handle)
        return atoms_is_domain_decomposed
    
    def set_cutoff(self, cutoff, cutoff_skin=None, interface_call=False):
        """
        set a uniform cutoff
        Specify a uniform neighbour cutoff throughout the system.
        Optionally set 'cutoff_skin' at the same time.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        
        set_cutoff(self, cutoff[, cutoff_skin])
        Defined at Atoms.fpp lines 884-891
        
        Parameters
        ----------
        this : Atoms
        cutoff : float64
        cutoff_skin : float64
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_cutoff(this=self._handle, cutoff=cutoff, cutoff_skin=cutoff_skin)
    
    def has_property(self, name, interface_call=False):
        """
        Convenience function to test if a property is present. No checking
        of property type is done. Property names are case-insensitive.
        
        atoms_has_property = has_property(self, name)
        Defined at Atoms.fpp lines 735-739
        
        Parameters
        ----------
        this : Atoms
        name : str
        
        Returns
        -------
        atoms_has_property : bool
        """
        atoms_has_property = quippy._quippy.f90wrap_atoms_module__atoms_has_property(this=self._handle, name=name)
        return atoms_has_property
    
    def remove_property(self, name, error=None, interface_call=False):
        """
        Remove a property from this atoms object
        
        remove_property(self, name[, error])
        Defined at Atoms.fpp lines 725-733
        
        Parameters
        ----------
        this : Atoms
        name : str
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_remove_property(this=self._handle, name=name, error=error)
    
    def print(self, file=None, error=None, interface_call=False):
        """
        Print a verbose textual description of an Atoms object to the default logger or to
        a specificied Inoutput object.
        
        print(self[, file, error])
        Defined at Atoms.fpp lines 1955-1986
        
        Parameters
        ----------
        this : Atoms
        file : Inoutput
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_print(this=self._handle, file=None if file is None else file._handle, \
            error=error)
    
    def set_lattice(self, new_lattice, scale_positions, remap=None, reconnect=None, interface_call=False):
        """
        set the lattice of an atoms object - please use this, rather than setting atoms%lattice
        directly, because it also set up reciprocal lattice and orthorhombic/periodic logical flags
        Change the lattice vectors, keeping the inverse lattice vectors
        up to date. Optionally map the existing atoms into the new cell
        and recalculate connectivity.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        
        set_lattice(self, new_lattice, scale_positions[, remap, reconnect])
        Defined at Atoms.fpp lines 920-962
        
        Parameters
        ----------
        this : Atoms
        new_lattice : float array
        scale_positions : bool
        remap : bool
        reconnect : bool
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_lattice(this=self._handle, new_lattice=new_lattice, \
            scale_positions=scale_positions, remap=remap, reconnect=reconnect)
    
    def select(self, from_, mask=None, list=None, orig_index=None, error=None, interface_call=False):
        """
        Select a subset of the atoms in an atoms object, either using a logical
        mask array or a Table, in which case the first 'int' column is taken to
        be a list of the atoms that should be retained.
        
        select(self, from_[, mask, list, orig_index, error])
        Defined at Atoms.fpp lines 654-723
        
        Parameters
        ----------
        to : Atoms
        from_ : Atoms
        mask : int32 array
        list : int array
        orig_index : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_select(to=self._handle, from_=from_._handle, mask=mask, list=list, \
            orig_index=orig_index, error=error)
    
    def cell_volume(self, interface_call=False):
        """
        calculate volume of unit cell
        Returns the(unsigned) volume of the simulation cell of this Atoms
        
        atoms_cell_volume = cell_volume(self)
        Defined at Atoms.fpp lines 1649-1652
        
        Parameters
        ----------
        this : Atoms
        
        Returns
        -------
        atoms_cell_volume : float64
        """
        atoms_cell_volume = quippy._quippy.f90wrap_atoms_module__atoms_cell_volume(this=self._handle)
        return atoms_cell_volume
    
    def map_into_cell(self, interface_call=False):
        """
        Map atomic positions into the unit cell so that lattice
        coordinates satisfy $-0.5 \\le t_x,t_y,t_z < 0.5$
        Map atomic fractional positions back into the unit cell
        $-0.5 \\le t_x,t_y,t_z < 0.5$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        
        map_into_cell(self)
        Defined at Atoms.fpp lines 1476-1512
        
        Parameters
        ----------
        this : Atoms
        """
        quippy._quippy.f90wrap_atoms_module__atoms_map_into_cell(this=self._handle)
    
    def unskew_cell(self, error=None, interface_call=False):
        """
        Unskew lattice so the cosines of the lattice angles fall between
        $-0.5$ and $0.5$
        Unskew lattice so the cosines of the lattice angles fall between
        $-0.5$ and $0.5$XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        
        unskew_cell(self[, error])
        Defined at Atoms.fpp lines 1520-1561
        
        Parameters
        ----------
        this : Atoms
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_unskew_cell(this=self._handle, error=error)
    
    def copy_properties(self, from_, property_list, case_sensitive=None, error=None, interface_call=False):
        """
        Copy some properties from one atoms struct to another
        The destination will be overriden.
        
        copy_properties(self, from_, property_list[, case_sensitive, error])
        Defined at Atoms.fpp lines 2515-2527
        
        Parameters
        ----------
        this : Atoms
        from_ : Atoms
        property_list : str
        case_sensitive : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_copy_properties(this=self._handle, from_=from_._handle, \
            property_list=property_list, case_sensitive=case_sensitive, error=error)
    
    def transform_basis(self, l, rank1=None, rank2=None, error=None, interface_call=False):
        """
        Basis transformation of rank 0, 1 and 2 tensors real values in Atoms object.
        This routine transforms rank 1 and rank 2 tensors in this%params and
        this%properties. Tensors are identified by having the correct type
        (real arrays) and shape(i.e. 3, (3, 3), (3, this%N) (9, this%N) for
        vector paramters, tensor parameters, vector properties and tensor
        properties respectively), and by having a name which is included in
        the relevant list. Extra names can be added to the lists with the
        rank1 and rank2 arguments.
        
        transform_basis(self, l[, rank1, rank2, error])
        Defined at Atoms.fpp lines 2558-2633
        
        Parameters
        ----------
        this : Atoms
        l : float array
        rank1 : str
        rank2 : str
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_transform_basis(this=self._handle, l=l, rank1=rank1, rank2=rank2, \
            error=error)
    
    def rotate(self, axis, angle, rank1=None, rank2=None, interface_call=False):
        """
        Rotate this Atoms object, transforming all rank 1 and rank 2 tensors parameters and properties
        
        rotate(self, axis, angle[, rank1, rank2])
        Defined at Atoms.fpp lines 2636-2644
        
        Parameters
        ----------
        this : Atoms
        axis : float array
        angle : float64
        rank1 : str
        rank2 : str
        """
        quippy._quippy.f90wrap_atoms_module__atoms_rotate(this=self._handle, axis=axis, angle=angle, rank1=rank1, rank2=rank2)
    
    def index_to_z_index(self, index_bn, interface_call=False):
        """
        Convert from a single index in range 1..this%N to a CASTEP-style(element, index) pair
        
        z_index = index_to_z_index(self, index_bn)
        Defined at Atoms.fpp lines 2647-2655
        
        Parameters
        ----------
        this : Atoms
        index_bn : int32
        
        Returns
        -------
        z_index : int32
        """
        z_index = quippy._quippy.f90wrap_atoms_module__atoms_index_to_z_index(this=self._handle, index_bn=index_bn)
        return z_index
    
    def z_index_to_index(self, z, z_index, error=None, interface_call=False):
        """
        Inverse of atoms_index_to_z_index
        
        index_bn = z_index_to_index(self, z, z_index[, error])
        Defined at Atoms.fpp lines 2658-2670
        
        Parameters
        ----------
        this : Atoms
        z : int32
        z_index : int32
        error : int32
        
        Returns
        -------
        index_bn : int32
        """
        index_bn = quippy._quippy.f90wrap_atoms_module__atoms_z_index_to_index(this=self._handle, z=z, z_index=z_index, \
            error=error)
        return index_bn
    
    def calc_connect(self, alt_connect=None, own_neighbour=None, store_is_min_image=None, skip_zero_zero_bonds=None, \
        store_n_neighb=None, max_pos_change=None, did_rebuild=None, error=None, interface_call=False):
        """
        Fast $O(N)$ connectivity calculation routine. It divides the unit
        cell into similarly shaped subcells, of sufficient size that
        sphere of radius 'cutoff' is contained in a subcell, at least in
        the directions in which the unit cell is big enough. For very
        small unit cells, there is only one subcell, so the routine is
        equivalent to the standard $O(N^2)$ method.>
        If 'own_neighbour' is true, atoms can be neighbours with their
        own periodic images.
        If 'cutoff_skin' is present, effective cutoff is increased by this
        amount, and full recalculation of connectivity is only done when
        any atom has moved more than 0.5*cutoff_skin - otherwise
        calc_dists() is called to update the stored distance tables.
        
        calc_connect(self[, alt_connect, own_neighbour, store_is_min_image, skip_zero_zero_bonds, store_n_neighb, \
            max_pos_change, did_rebuild, error])
        Defined at Atoms.fpp lines 2747-2766
        
        Parameters
        ----------
        this : Atoms
        alt_connect : Connection
        own_neighbour : bool
        store_is_min_image : bool
        skip_zero_zero_bonds : bool
        store_n_neighb : bool
        max_pos_change : float64
        did_rebuild : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_calc_connect(this=self._handle, alt_connect=None if alt_connect is None else \
            alt_connect._handle, own_neighbour=own_neighbour, store_is_min_image=store_is_min_image, \
            skip_zero_zero_bonds=skip_zero_zero_bonds, store_n_neighb=store_n_neighb, max_pos_change=max_pos_change, \
            did_rebuild=did_rebuild, error=error)
    
    def calc_dists(self, alt_connect=None, parallel=None, error=None, interface_call=False):
        """
        Update stored distance tables. To be called after moving atoms, in between calls to calc_connect().
        
        calc_dists(self[, alt_connect, parallel, error])
        Defined at Atoms.fpp lines 2769-2782
        
        Parameters
        ----------
        this : Atoms
        alt_connect : Connection
        parallel : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_calc_dists(this=self._handle, alt_connect=None if alt_connect is None else \
            alt_connect._handle, parallel=parallel, error=error)
    
    def calc_connect_hysteretic(self, cutoff_factor, cutoff_break_factor, alt_connect=None, origin=None, extent=None, \
        own_neighbour=None, store_is_min_image=None, store_n_neighb=None, error=None, interface_call=False):
        """
        As for 'calc_connect', but perform the connectivity update
        hystertically: atoms must come within a relative distance of
        'cutoff_factor' to be considered neighbours, and then will remain
        connected until them move apart further than a relative distance
        of 'cutoff_break_factor' (all cutoff factors are relative
        to covalent radii).
        
        Typically 'alt_connect' should be set to the
        'hysteretic_connect' attribute. 'origin' and 'extent'
        vectors can be used to restrict the hysteretic region to only
        part of the entire system -- the 'estimate_origin_extent()'
        routine in clusters.f95 can be used to guess suitable values.
        
        calc_connect_hysteretic(self, cutoff_factor, cutoff_break_factor[, alt_connect, origin, extent, own_neighbour, \
            store_is_min_image, store_n_neighb, error])
        Defined at Atoms.fpp lines 2716-2733
        
        Parameters
        ----------
        this : Atoms
        cutoff_factor : float64
        cutoff_break_factor : float64
        alt_connect : Connection
        origin : float array
        extent : float array
        own_neighbour : bool
        store_is_min_image : bool
        store_n_neighb : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_calc_connect_hysteretic(this=self._handle, cutoff_factor=cutoff_factor, \
            cutoff_break_factor=cutoff_break_factor, alt_connect=None if alt_connect is None else alt_connect._handle, \
            origin=origin, extent=extent, own_neighbour=own_neighbour, store_is_min_image=store_is_min_image, \
            store_n_neighb=store_n_neighb, error=error)
    
    def is_min_image(self, i, alt_connect=None, error=None, interface_call=False):
        """
        is_min_image = is_min_image(self, i[, alt_connect, error])
        Defined at Atoms.fpp lines 2380-2428
        
        Parameters
        ----------
        this : Atoms
        i : int32
        alt_connect : Connection
        error : int32
        
        Returns
        -------
        is_min_image : bool
        """
        is_min_image = quippy._quippy.f90wrap_atoms_module__atoms_is_min_image(this=self._handle, i=i, alt_connect=None if \
            alt_connect is None else alt_connect._handle, error=error)
        return is_min_image
    
    def set_comm_property(self, propname, comm_atoms=None, comm_ghosts=None, comm_reverse=None, interface_call=False):
        """
        Set which properties to communicate when
        comm_atoms:   Communicate when atom is moved to different domain.
        Forces, for example, may be excluded since they are updated
        on every time step.
        comm_ghosts:  Communicate when atom is dublicated as a ghost on a domain.
        Masses, for example, might be excluded since atoms are
        propagated on the domain they reside in only.
        comm_reverse: Communicate back from ghost atoms to the original domain atom
        and accumulate
        By default, properties are not communicated.
        
        set_comm_property(self, propname[, comm_atoms, comm_ghosts, comm_reverse])
        Defined at Atoms.fpp lines 2795-2804
        
        Parameters
        ----------
        this : Atoms
        propname : str
        comm_atoms : bool
        comm_ghosts : bool
        comm_reverse : bool
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_comm_property(this=self._handle, propname=propname, \
            comm_atoms=comm_atoms, comm_ghosts=comm_ghosts, comm_reverse=comm_reverse)
    
    def set_zs(self, error=None, interface_call=False):
        """
        set Zs from species
        
        set_zs(self[, error])
        Defined at Atoms.fpp lines 2807-2818
        
        Parameters
        ----------
        this : Atoms
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_zs(this=self._handle, error=error)
    
    def sort_by_rindex(self, sort_index, error=None, interface_call=False):
        """
        sort atoms according to an externally provided field
        
        sort_by_rindex(self, sort_index[, error])
        Defined at Atoms.fpp lines 2530-2548
        
        Parameters
        ----------
        this : Atoms
        sort_index : float array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_sort_by_rindex(this=self._handle, sort_index=sort_index, error=error)
    
    def shuffle(self, new_indices, error=None, interface_call=False):
        """
        Reshuffle the order of the atomic indices to new_indices.
        
        shuffle(self, new_indices[, error])
        Defined at Atoms.fpp lines 1334-1389
        
        Parameters
        ----------
        this : Atoms
        new_indices : int array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_shuffle(this=self._handle, new_indices=new_indices, error=error)
    
    def n_neighbours(self, i, max_dist=None, max_factor=None, alt_connect=None, error=None, interface_call=False):
        """
        Neighbour list stuff
        Return the number of neighbour that atom 'i' has.  If the
        optional arguments max_dist or max_factor are present then only
        neighbours closer than this cutoff are included.  Do not use
        'max_dist' when iterating only over neighbours within a certain
        distance; instead, iterate over the full list and discard
        unnecessary neighbours in 'atoms_neighbour'.
        
        'alt_connect'
        can be set to another Connection object to use alternative
        connectivity information, for example 'hysteretic_connect'.
        
        n = n_neighbours(self, i[, max_dist, max_factor, alt_connect, error])
        Defined at Atoms.fpp lines 1008-1022
        
        Parameters
        ----------
        this : Atoms
        i : int32
        max_dist : float64
        max_factor : float64
        alt_connect : Connection
        error : int32
        
        Returns
        -------
        n : int32
        """
        n = quippy._quippy.f90wrap_atoms_module__atoms_n_neighbours(this=self._handle, i=i, max_dist=max_dist, \
            max_factor=max_factor, alt_connect=None if alt_connect is None else alt_connect._handle, error=error)
        return n
    
    def neighbour(self, i, n, distance=None, diff=None, cosines=None, shift=None, index_bn=None, max_dist=None, jn=None, \
        alt_connect=None, error=None, interface_call=False):
        """
        Return the index of the $n^\\mathrm{th}$ neighbour of atom $i$. Together with the
        previous function, this facilites a loop over the neighbours of atom $i$. Optionally, we
        return other geometric information, such as distance, direction cosines and difference vector,
        and also a direct index into the neighbour tables. If $i <= j$, this is an index into 'neighbour1(i)';
        if $i > j$, it is an index into 'neighbour1(j)'.
        
        >   do n = 1,atoms_n_neighbours(at, i)
        >      j = atoms_neighbour(at, i, n, distance, diff, cosines, shift, index)
        >
        >      ...
        >   end do
        
        If distance $>$ 'max_dist', return 0, and do not waste time calculating other quantities.
        This enables efficient iteration over the subset of neighbours located within the radius
        'max_dist'.  However, as the neighbour list is not sorted,
        you must first iterate over the whole list(i.e. do *not* use the
        'max_dist' parameter in 'atoms_n_neighbours'), then skip those
        neighbours where this function returns 0.
        
        'alt_connect' has the same meaning as in 'n_neighbours'.
        
        Here's a typical loop construct in Python. Note how `r` and `u`
        are created before the loop: arguments which are both optional
        and ``intent(out)`` in Fortran are converted to ``intent(in,out)`` for quippy. ::
        >
        >    r = farray(0.0)
        >    u = fzeros(3)
        >    for i in frange(at.n):
        >        for n in frange(at.n_neighbours(i)):
        >            j = at.neighbour(i, n, distance=r, diff=u)
        
        j = neighbour(self, i, n[, distance, diff, cosines, shift, index_bn, max_dist, jn, alt_connect, error])
        Defined at Atoms.fpp lines 1086-1107
        
        Parameters
        ----------
        this : Atoms
        i : int32
        n : int32
        distance : float64
        diff : float array
        cosines : float array
        shift : int array
        index_bn : int32
        max_dist : float64
        jn : int32
        alt_connect : Connection
        error : int32
        
        Returns
        -------
        j : int32
        """
        j = quippy._quippy.f90wrap_atoms_module__atoms_neighbour(this=self._handle, i=i, n=n, distance=distance, diff=diff, \
            cosines=cosines, shift=shift, index_bn=index_bn, max_dist=max_dist, jn=jn, alt_connect=None if alt_connect is None \
            else alt_connect._handle, error=error)
        return j
    
    def kinetic_energy(self, local_ke=None, error=None, interface_call=False):
        """
        Return the total kinetic energy $E_k = \\sum_{i} \\frac{1}{2} m v^2$
        
        ke = kinetic_energy(self[, local_ke, error])
        Defined at DynamicalSystem.fpp lines 1146-1174
        
        Parameters
        ----------
        this : Atoms
        local_ke : bool
        error : int32
        
        Returns
        -------
        ke : float64
        """
        ke = quippy._quippy.f90wrap_dynamicalsystem_module__atoms_kinetic_energy(this=self._handle, local_ke=local_ke, \
            error=error)
        return ke
    
    def kinetic_virial(self, error=None, interface_call=False):
        """
        Return the total kinetic virial $w_ij = \\sum_{k} \\frac{1}{2} m v_i v_j$
        
        kv = kinetic_virial(self[, error])
        Defined at DynamicalSystem.fpp lines 1204-1216
        
        Parameters
        ----------
        this : Atoms
        error : int32
        
        Returns
        -------
        kv : float array
        """
        kv = quippy._quippy.f90wrap_dynamicalsystem_module__atoms_kinetic_virial(this=self._handle, error=error)
        return kv
    
    def angular_momentum(self, origin=None, indices=None, interface_call=False):
        """
        Return the angular momentum of all the atoms in this DynamicalSystem, defined by
        $\\mathbf{L} = \\sum_{i} \\mathbf{r_i} \\times \\mathbf{v_i}$.
        
        l = angular_momentum(self[, origin, indices])
        Defined at DynamicalSystem.fpp lines 1050-1055
        
        Parameters
        ----------
        this : Atoms
        origin : float array
        indices : int array
        
        Returns
        -------
        l : float array
        """
        l = quippy._quippy.f90wrap_dynamicalsystem_module__atoms_angular_momentum(this=self._handle, origin=origin, \
            indices=indices)
        return l
    
    def momentum(self, indices=None, interface_call=False):
        """
        Return the total momentum $\\mathbf{p} = \\sum_i \\mathbf{m_i} \\mathbf{v_i}$.
        Optionally only include the contribution of a subset of atoms.
        
        p = momentum(self[, indices])
        Defined at DynamicalSystem.fpp lines 1013-1017
        
        Parameters
        ----------
        this : Atoms
        indices : int array
        
        Returns
        -------
        p : float array
        """
        p = quippy._quippy.f90wrap_dynamicalsystem_module__atoms_momentum(this=self._handle, indices=indices)
        return p
    
    def add_property_int(self, name, value, n_cols=None, overwrite=None, error=None, interface_call=False):
        """
        add_property_int(self, name, value[, n_cols, overwrite, error])
        Defined at Atoms_types.fpp lines 729-756
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : int32
        n_cols : int32
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_int(this=self._handle, name=name, value=value, \
            n_cols=n_cols, overwrite=overwrite, error=error)
    
    def add_property_int_a(self, name, value, n_cols=None, overwrite=None, error=None, interface_call=False):
        """
        add_property_int_a(self, name, value[, n_cols, overwrite, error])
        Defined at Atoms_types.fpp lines 758-794
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : int array
        n_cols : int32
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_int_a(this=self._handle, name=name, value=value, \
            n_cols=n_cols, overwrite=overwrite, error=error)
    
    def add_property_real(self, name, value, n_cols=None, overwrite=None, error=None, interface_call=False):
        """
        add_property_real(self, name, value[, n_cols, overwrite, error])
        Defined at Atoms_types.fpp lines 796-826
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : float64
        n_cols : int32
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_real(this=self._handle, name=name, value=value, \
            n_cols=n_cols, overwrite=overwrite, error=error)
    
    def add_property_real_a(self, name, value, n_cols=None, overwrite=None, error=None, interface_call=False):
        """
        add_property_real_a(self, name, value[, n_cols, overwrite, error])
        Defined at Atoms_types.fpp lines 828-867
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : float array
        n_cols : int32
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_real_a(this=self._handle, name=name, value=value, \
            n_cols=n_cols, overwrite=overwrite, error=error)
    
    def add_property_str(self, name, value, overwrite=None, error=None, interface_call=False):
        """
        add_property_str(self, name, value[, overwrite, error])
        Defined at Atoms_types.fpp lines 925-946
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : str
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_str(this=self._handle, name=name, value=value, \
            overwrite=overwrite, error=error)
    
    def add_property_str_2da(self, name, value, overwrite=None, error=None, interface_call=False):
        """
        add_property_str_2da(self, name, value[, overwrite, error])
        Defined at Atoms_types.fpp lines 948-972
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : str array
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_str_2da(this=self._handle, name=name, value=value, \
            overwrite=overwrite, error=error)
    
    def add_property_str_a(self, name, value, overwrite=None, error=None, interface_call=False):
        """
        add_property_str_a(self, name, value[, overwrite, error])
        Defined at Atoms_types.fpp lines 974-1006
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : str array
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_str_a(this=self._handle, name=name, value=value, \
            overwrite=overwrite, error=error)
    
    def add_property_logical(self, name, value, overwrite=None, error=None, interface_call=False):
        """
        add_property_logical(self, name, value[, overwrite, error])
        Defined at Atoms_types.fpp lines 1008-1025
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : bool
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_logical(this=self._handle, name=name, value=value, \
            overwrite=overwrite, error=error)
    
    def add_property_logical_a(self, name, value, overwrite=None, error=None, interface_call=False):
        """
        add_property_logical_a(self, name, value[, overwrite, error])
        Defined at Atoms_types.fpp lines 1027-1047
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : int32 array
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_logical_a(this=self._handle, name=name, value=value, \
            overwrite=overwrite, error=error)
    
    def add_property_int_2da(self, name, value, overwrite=None, error=None, interface_call=False):
        """
        add_property_int_2da(self, name, value[, overwrite, error])
        Defined at Atoms_types.fpp lines 869-895
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : int array
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_int_2da(this=self._handle, name=name, value=value, \
            overwrite=overwrite, error=error)
    
    def add_property_real_2da(self, name, value, overwrite=None, error=None, interface_call=False):
        """
        add_property_real_2da(self, name, value[, overwrite, error])
        Defined at Atoms_types.fpp lines 897-923
        
        Parameters
        ----------
        this : Atoms
        name : str
        value : float array
        overwrite : bool
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_real_2da(this=self._handle, name=name, value=value, \
            overwrite=overwrite, error=error)
    
    def add_property(*args, **kwargs):
        """
        Add a per-atom property to this atoms object, as extra entry with columns of
        integers, reals, logical, or strings in the 'properties' dictionary. For example,
        this interface is used by the DynamicalSystems module to create the 'velo', 'acc',
        etc. properties.
        Optionally, a pointer to the new property is returned.
        
        add_property(*args, **kwargs)
        Defined at Atoms_types.fpp lines 391-398
        
        Overloaded interface containing the following procedures:
          add_property_int
          add_property_int_a
          add_property_real
          add_property_real_a
          add_property_str
          add_property_str_2da
          add_property_str_a
          add_property_logical
          add_property_logical_a
          add_property_int_2da
          add_property_real_2da
        """
        for proc in [Atoms.add_property_int_a, Atoms.add_property_real_a, Atoms.add_property_str_2da, Atoms.add_property_str_a, \
            Atoms.add_property_logical_a, Atoms.add_property_int_2da, Atoms.add_property_real_2da, Atoms.add_property_int, \
            Atoms.add_property_real, Atoms.add_property_str, Atoms.add_property_logical]:
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
            "add_property compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def add_property_p_int(self, name, ptr, error=None, interface_call=False):
        """
        add_property_p_int(self, name, ptr[, error])
        Defined at Atoms_types.fpp lines 603-621
        
        Parameters
        ----------
        this : Atoms
        name : str
        ptr : int array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_p_int(this=self._handle, name=name, ptr=ptr, error=error)
    
    def add_property_p_int_a(self, name, ptr, error=None, interface_call=False):
        """
        add_property_p_int_a(self, name, ptr[, error])
        Defined at Atoms_types.fpp lines 623-644
        
        Parameters
        ----------
        this : Atoms
        name : str
        ptr : int array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_p_int_a(this=self._handle, name=name, ptr=ptr, \
            error=error)
    
    def add_property_p_real(self, name, ptr, error=None, interface_call=False):
        """
        add_property_p_real(self, name, ptr[, error])
        Defined at Atoms_types.fpp lines 646-664
        
        Parameters
        ----------
        this : Atoms
        name : str
        ptr : float array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_p_real(this=self._handle, name=name, ptr=ptr, error=error)
    
    def add_property_p_real_a(self, name, ptr, error=None, interface_call=False):
        """
        add_property_p_real_a(self, name, ptr[, error])
        Defined at Atoms_types.fpp lines 666-687
        
        Parameters
        ----------
        this : Atoms
        name : str
        ptr : float array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_p_real_a(this=self._handle, name=name, ptr=ptr, \
            error=error)
    
    def add_property_p_str(self, name, ptr, error=None, interface_call=False):
        """
        add_property_p_str(self, name, ptr[, error])
        Defined at Atoms_types.fpp lines 709-727
        
        Parameters
        ----------
        this : Atoms
        name : str
        ptr : str array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_p_str(this=self._handle, name=name, ptr=ptr, error=error)
    
    def add_property_p_logical(self, name, ptr, error=None, interface_call=False):
        """
        add_property_p_logical(self, name, ptr[, error])
        Defined at Atoms_types.fpp lines 689-707
        
        Parameters
        ----------
        this : Atoms
        name : str
        ptr : int32 array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_types_module__atoms_add_property_p_logical(this=self._handle, name=name, ptr=ptr, \
            error=error)
    
    def add_property_from_pointer(*args, **kwargs):
        """
        Add a per-atom property to this atoms object, but point to existing space
        rather than allocating new space for it(as add_property does).
        
        add_property_from_pointer(*args, **kwargs)
        Defined at Atoms_types.fpp lines 403-407
        
        Overloaded interface containing the following procedures:
          add_property_p_int
          add_property_p_int_a
          add_property_p_real
          add_property_p_real_a
          add_property_p_str
          add_property_p_logical
        """
        for proc in [Atoms.add_property_p_int, Atoms.add_property_p_int_a, Atoms.add_property_p_real, \
            Atoms.add_property_p_real_a, Atoms.add_property_p_str, Atoms.add_property_p_logical]:
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
            "add_property_from_pointer compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def distance8_atom_atom(self, i, j, shift=None, interface_call=False):
        """
        distance8_atom_atom = distance8_atom_atom(self, i, j[, shift])
        Defined at Atoms_types.fpp lines 1463-1468
        
        Parameters
        ----------
        this : Atoms
        i : int32
        j : int32
        shift : int array
        
        Returns
        -------
        distance8_atom_atom : float64
        """
        distance8_atom_atom = quippy._quippy.f90wrap_atoms_types_module__distance8_atom_atom(this=self._handle, i=i, j=j, \
            shift=shift)
        return distance8_atom_atom
    
    def distance8_atom_vec(self, i, v, shift=None, interface_call=False):
        """
        distance8_atom_vec = distance8_atom_vec(self, i, v[, shift])
        Defined at Atoms_types.fpp lines 1470-1476
        
        Parameters
        ----------
        this : Atoms
        i : int32
        v : float array
        shift : int array
        
        Returns
        -------
        distance8_atom_vec : float64
        """
        distance8_atom_vec = quippy._quippy.f90wrap_atoms_types_module__distance8_atom_vec(this=self._handle, i=i, v=v, \
            shift=shift)
        return distance8_atom_vec
    
    def distance8_vec_atom(self, v, j, shift=None, interface_call=False):
        """
        distance8_vec_atom = distance8_vec_atom(self, v, j[, shift])
        Defined at Atoms_types.fpp lines 1478-1484
        
        Parameters
        ----------
        this : Atoms
        v : float array
        j : int32
        shift : int array
        
        Returns
        -------
        distance8_vec_atom : float64
        """
        distance8_vec_atom = quippy._quippy.f90wrap_atoms_types_module__distance8_vec_atom(this=self._handle, v=v, j=j, \
            shift=shift)
        return distance8_vec_atom
    
    def distance8_vec_vec(self, v, w, shift=None, interface_call=False):
        """
        distance8_vec_vec = distance8_vec_vec(self, v, w[, shift])
        Defined at Atoms_types.fpp lines 1487-1518
        
        Parameters
        ----------
        this : Atoms
        v : float array
        w : float array
        shift : int array
        
        Returns
        -------
        distance8_vec_vec : float64
        """
        distance8_vec_vec = quippy._quippy.f90wrap_atoms_types_module__distance8_vec_vec(this=self._handle, v=v, w=w, \
            shift=shift)
        return distance8_vec_vec
    
    def distance_min_image(*args, **kwargs):
        """
        This interface calculates the distance between the nearest periodic images of two points(or atoms).
        Return minimum image distance between two atoms or positions.
        End points can be specified by any combination of atoms indices
        'i' and 'j' and absolute coordinates 'u' and 'w'. If 'shift' is
        present the periodic shift between the two atoms or points will
        be returned in it.
        
        distance_min_image(*args, **kwargs)
        Defined at Atoms_types.fpp lines 454-455
        
        Overloaded interface containing the following procedures:
          distance8_atom_atom
          distance8_atom_vec
          distance8_vec_atom
          distance8_vec_vec
        """
        for proc in [Atoms.distance8_vec_vec, Atoms.distance8_atom_vec, Atoms.distance8_vec_atom, Atoms.distance8_atom_atom]:
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
            "distance_min_image compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def diff_atom_atom(self, i, j, shift=None, interface_call=False):
        """
        diff_atom_atom = diff_atom_atom(self, i, j[, shift])
        Defined at Atoms_types.fpp lines 1383-1392
        
        Parameters
        ----------
        this : Atoms
        i : int32
        j : int32
        shift : int array
        
        Returns
        -------
        diff_atom_atom : float array
        """
        diff_atom_atom = quippy._quippy.f90wrap_atoms_types_module__diff_atom_atom(this=self._handle, i=i, j=j, shift=shift)
        return diff_atom_atom
    
    def diff_atom_vec(self, i, w, interface_call=False):
        """
        diff_atom_vec = diff_atom_vec(self, i, w)
        Defined at Atoms_types.fpp lines 1404-1412
        
        Parameters
        ----------
        this : Atoms
        i : int32
        w : float array
        
        Returns
        -------
        diff_atom_vec : float array
        """
        diff_atom_vec = quippy._quippy.f90wrap_atoms_types_module__diff_atom_vec(this=self._handle, i=i, w=w)
        return diff_atom_vec
    
    def diff_vec_atom(self, v, j, interface_call=False):
        """
        diff_vec_atom = diff_vec_atom(self, v, j)
        Defined at Atoms_types.fpp lines 1394-1402
        
        Parameters
        ----------
        this : Atoms
        v : float array
        j : int32
        
        Returns
        -------
        diff_vec_atom : float array
        """
        diff_vec_atom = quippy._quippy.f90wrap_atoms_types_module__diff_vec_atom(this=self._handle, v=v, j=j)
        return diff_vec_atom
    
    def diff_vec_vec(self, v, w, interface_call=False):
        """
        diff_vec_vec = diff_vec_vec(self, v, w)
        Defined at Atoms_types.fpp lines 1414-1421
        
        Parameters
        ----------
        this : Atoms
        v : float array
        w : float array
        
        Returns
        -------
        diff_vec_vec : float array
        """
        diff_vec_vec = quippy._quippy.f90wrap_atoms_types_module__diff_vec_vec(this=self._handle, v=v, w=w)
        return diff_vec_vec
    
    def diff_min_image(*args, **kwargs):
        """
        Return the minimum image difference vector between two atoms or
        positions. End points can be specified by any combination of
        atoms indices 'i' and 'j' and absolute coordinates 'u' and
        'w'.
        
        diff_min_image(*args, **kwargs)
        Defined at Atoms_types.fpp lines 461-462
        
        Overloaded interface containing the following procedures:
          diff_atom_atom
          diff_atom_vec
          diff_vec_atom
          diff_vec_vec
        """
        for proc in [Atoms.diff_vec_vec, Atoms.diff_atom_atom, Atoms.diff_atom_vec, Atoms.diff_vec_atom]:
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
            "diff_min_image compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def set_atoms(self, z, mass=None, interface_call=False):
        """
        Set atomic numbers and optionally masses(if mass property is present)
        If 'mass' is not specified then 'ElementMass(Z)' is used.
        
        set_atoms(self, z[, mass])
        Defined at Atoms.fpp lines 975-991
        
        Parameters
        ----------
        this : Atoms
        z : int array
        mass : float array
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_atoms(this=self._handle, z=z, mass=mass)
    
    def set_atoms_singlez(self, z, interface_call=False):
        """
        set_atoms_singlez(self, z)
        Defined at Atoms.fpp lines 964-971
        
        Parameters
        ----------
        this : Atoms
        z : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_atoms_singlez(this=self._handle, z=z)
    
    
    # Save references to the original methods before overloading
    _set_atoms_0 = set_atoms
    
    def set_atoms(*args, **kwargs):
        """
        Set atomic numbers(in the 'z' integer property), species names
        (in 'species' string property) and optionally masses(if 'mass'
        property exists in the Atoms object).
        
        set_atoms(*args, **kwargs)
        Defined at Atoms.fpp lines 228-229
        
        Overloaded interface containing the following procedures:
          set_atoms
          set_atoms_singlez
        """
        for proc in [Atoms._set_atoms_0, Atoms.set_atoms_singlez]:
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
            "set_atoms compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def add_atom_single(self, pos, z, mass=None, travel=None, error=None, interface_call=False):
        """
        add_atom_single(self, pos, z[, mass, travel, error])
        Defined at Atoms.fpp lines 1116-1137
        
        Parameters
        ----------
        this : Atoms
        pos : float array
        z : int32
        mass : float64
        travel : int array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__add_atom_single(this=self._handle, pos=pos, z=z, mass=mass, travel=travel, \
            error=error)
    
    def add_atom_multiple(self, pos, z, mass=None, velo=None, acc=None, travel=None, error=None, interface_call=False):
        """
        add_atom_multiple(self, pos, z[, mass, velo, acc, travel, error])
        Defined at Atoms.fpp lines 1140-1309
        
        Parameters
        ----------
        this : Atoms
        pos : float array
        z : int array
        mass : float array
        velo : float array
        acc : float array
        travel : int array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__add_atom_multiple(this=self._handle, pos=pos, z=z, mass=mass, velo=velo, acc=acc, \
            travel=travel, error=error)
    
    def join(self, from_, error=None, interface_call=False):
        """
        join(self, from_[, error])
        Defined at Atoms.fpp lines 1312-1321
        
        Parameters
        ----------
        this : Atoms
        from_ : Atoms
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_join(this=self._handle, from_=from_._handle, error=error)
    
    def add_atoms(*args, **kwargs):
        """
        Add one or more atoms to an Atoms object.
        To add a single atom, 'pos' should be an array of size 3 and 'z a
        single integer. To add multiple atoms either arrays of length
        'n_new' should be passed, or another Atoms from which to copy data
        should be given as the 'from' argument.
        
        add_atoms(*args, **kwargs)
        Defined at Atoms.fpp lines 247-248
        
        Overloaded interface containing the following procedures:
          add_atom_single
          add_atom_multiple
          join
        """
        for proc in [Atoms.add_atom_multiple, Atoms.add_atom_single, Atoms.join]:
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
            "add_atoms compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def remove_atom_single(self, i, error=None, interface_call=False):
        """
        remove_atom_single(self, i[, error])
        Defined at Atoms.fpp lines 1324-1330
        
        Parameters
        ----------
        this : Atoms
        i : int32
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__remove_atom_single(this=self._handle, i=i, error=error)
    
    def remove_atom_multiple(self, atom_indices, error=None, interface_call=False):
        """
        remove_atom_multiple(self, atom_indices[, error])
        Defined at Atoms.fpp lines 1391-1436
        
        Parameters
        ----------
        this : Atoms
        atom_indices : int array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__remove_atom_multiple(this=self._handle, atom_indices=atom_indices, error=error)
    
    def remove_atom_multiple_mask(self, mask, error=None, interface_call=False):
        """
        remove_atom_multiple_mask(self, mask[, error])
        Defined at Atoms.fpp lines 1438-1468
        
        Parameters
        ----------
        this : Atoms
        mask : int32 array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__remove_atom_multiple_mask(this=self._handle, mask=mask, error=error)
    
    def remove_atoms(*args, **kwargs):
        """
        Remove one or more atoms from an Atoms object.
        
        remove_atoms(*args, **kwargs)
        Defined at Atoms.fpp lines 252-254
        
        Overloaded interface containing the following procedures:
          remove_atom_single
          remove_atom_multiple
          remove_atom_multiple_mask
        """
        for proc in [Atoms.remove_atom_multiple, Atoms.remove_atom_multiple_mask, Atoms.remove_atom_single]:
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
            "remove_atoms compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def get_param_value_int(self, key, error=None, interface_call=False):
        """
        value = get_param_value_int(self, key[, error])
        Defined at Atoms.fpp lines 783-791
        
        Parameters
        ----------
        this : Atoms
        key : str
        error : int32
        
        Returns
        -------
        value : int32
        """
        value = quippy._quippy.f90wrap_atoms_module__atoms_get_param_value_int(this=self._handle, key=key, error=error)
        return value
    
    def get_param_value_int_a(self, key, value, error=None, interface_call=False):
        """
        get_param_value_int_a(self, key, value[, error])
        Defined at Atoms.fpp lines 793-801
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : int array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_get_param_value_int_a(this=self._handle, key=key, value=value, error=error)
    
    def get_param_value_real(self, key, error=None, interface_call=False):
        """
        value = get_param_value_real(self, key[, error])
        Defined at Atoms.fpp lines 803-813
        
        Parameters
        ----------
        this : Atoms
        key : str
        error : int32
        
        Returns
        -------
        value : float64
        """
        value = quippy._quippy.f90wrap_atoms_module__atoms_get_param_value_real(this=self._handle, key=key, error=error)
        return value
    
    def get_param_value_real_a(self, key, value, error=None, interface_call=False):
        """
        get_param_value_real_a(self, key, value[, error])
        Defined at Atoms.fpp lines 815-823
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : float array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_get_param_value_real_a(this=self._handle, key=key, value=value, error=error)
    
    def get_param_value_real_a2(self, key, value, error=None, interface_call=False):
        """
        get_param_value_real_a2(self, key, value[, error])
        Defined at Atoms.fpp lines 825-833
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : float array
        error : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_get_param_value_real_a2(this=self._handle, key=key, value=value, error=error)
    
    def get_param_value_str(self, key, error=None, interface_call=False):
        """
        value = get_param_value_str(self, key[, error])
        Defined at Atoms.fpp lines 835-843
        
        Parameters
        ----------
        this : Atoms
        key : str
        error : int32
        
        Returns
        -------
        value : str
        """
        value = quippy._quippy.f90wrap_atoms_module__atoms_get_param_value_str(this=self._handle, key=key, error=error)
        return value
    
    def get_param_value_logical(self, key, error=None, interface_call=False):
        """
        value = get_param_value_logical(self, key[, error])
        Defined at Atoms.fpp lines 855-863
        
        Parameters
        ----------
        this : Atoms
        key : str
        error : int32
        
        Returns
        -------
        value : bool
        """
        value = quippy._quippy.f90wrap_atoms_module__atoms_get_param_value_logical(this=self._handle, key=key, error=error)
        return value
    
    def get_param_value(*args, **kwargs):
        """
        get a(per-configuration) value from the atoms%params dictionary
        
        get_param_value(*args, **kwargs)
        Defined at Atoms.fpp lines 261-265
        
        Overloaded interface containing the following procedures:
          get_param_value_int
          get_param_value_int_a
          get_param_value_real
          get_param_value_real_a
          get_param_value_real_a2
          get_param_value_str
          get_param_value_logical
        """
        for proc in [Atoms.get_param_value_int_a, Atoms.get_param_value_real_a, Atoms.get_param_value_real_a2, \
            Atoms.get_param_value_int, Atoms.get_param_value_real, Atoms.get_param_value_str, Atoms.get_param_value_logical]:
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
            "get_param_value compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    def set_param_value_int(self, key, value, interface_call=False):
        """
        set_param_value_int(self, key, value)
        Defined at Atoms.fpp lines 741-745
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : int32
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_param_value_int(this=self._handle, key=key, value=value)
    
    def set_param_value_int_a(self, key, value, interface_call=False):
        """
        set_param_value_int_a(self, key, value)
        Defined at Atoms.fpp lines 747-751
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : int array
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_param_value_int_a(this=self._handle, key=key, value=value)
    
    def set_param_value_real(self, key, value, interface_call=False):
        """
        set_param_value_real(self, key, value)
        Defined at Atoms.fpp lines 753-757
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : float64
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_param_value_real(this=self._handle, key=key, value=value)
    
    def set_param_value_real_a(self, key, value, interface_call=False):
        """
        set_param_value_real_a(self, key, value)
        Defined at Atoms.fpp lines 759-763
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : float array
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_param_value_real_a(this=self._handle, key=key, value=value)
    
    def set_param_value_real_a2(self, key, value, interface_call=False):
        """
        set_param_value_real_a2(self, key, value)
        Defined at Atoms.fpp lines 765-769
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : float array
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_param_value_real_a2(this=self._handle, key=key, value=value)
    
    def set_param_value_str(self, key, value, interface_call=False):
        """
        set_param_value_str(self, key, value)
        Defined at Atoms.fpp lines 777-781
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : str
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_param_value_str(this=self._handle, key=key, value=value)
    
    def set_param_value_logical(self, key, value, interface_call=False):
        """
        set_param_value_logical(self, key, value)
        Defined at Atoms.fpp lines 771-775
        
        Parameters
        ----------
        this : Atoms
        key : str
        value : bool
        """
        quippy._quippy.f90wrap_atoms_module__atoms_set_param_value_logical(this=self._handle, key=key, value=value)
    
    def set_param_value(*args, **kwargs):
        """
        set a(per-configuration) value from the atoms%params dictionary
        
        set_param_value(*args, **kwargs)
        Defined at Atoms.fpp lines 272-276
        
        Overloaded interface containing the following procedures:
          set_param_value_int
          set_param_value_int_a
          set_param_value_real
          set_param_value_real_a
          set_param_value_real_a2
          set_param_value_str
          set_param_value_logical
        """
        for proc in [Atoms.set_param_value_int_a, Atoms.set_param_value_real_a, Atoms.set_param_value_real_a2, \
            Atoms.set_param_value_int, Atoms.set_param_value_real, Atoms.set_param_value_str, Atoms.set_param_value_logical]:
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
            "set_param_value compatible with the provided args:"
            "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))
    
    @property
    def own_this(self):
        """
        Do I own myself?
        
        Element own_this ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 292
        """
        return quippy._quippy.f90wrap_atoms__get__own_this(self._handle)
    
    @own_this.setter
    def own_this(self, own_this):
        quippy._quippy.f90wrap_atoms__set__own_this(self._handle, own_this)
    
    @property
    def ref_count(self):
        """
        Reference counter
        
        Element ref_count ftype=integer                                pytype=int32
        Defined at Atoms_types.fpp line 293
        """
        return quippy._quippy.f90wrap_atoms__get__ref_count(self._handle)
    
    @ref_count.setter
    def ref_count(self, ref_count):
        quippy._quippy.f90wrap_atoms__set__ref_count(self._handle, ref_count)
    
    @property
    def fixed_size(self):
        """
        Can the number of atoms be changed after initialisation?
        
        Element fixed_size ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 294
        """
        return quippy._quippy.f90wrap_atoms__get__fixed_size(self._handle)
    
    @fixed_size.setter
    def fixed_size(self, fixed_size):
        quippy._quippy.f90wrap_atoms__set__fixed_size(self._handle, fixed_size)
    
    @property
    def n(self):
        """
        The number of atoms held(including ghost particles)
        
        Element n ftype=integer                                pytype=int32
        Defined at Atoms_types.fpp line 295
        """
        return quippy._quippy.f90wrap_atoms__get__n(self._handle)
    
    @n.setter
    def n(self, n):
        quippy._quippy.f90wrap_atoms__set__n(self._handle, n)
    
    @property
    def ndomain(self):
        """
        The number of atoms held by the local process(excluding ghost particles)
        
        Element ndomain ftype=integer                                pytype=int32
        Defined at Atoms_types.fpp line 296
        """
        return quippy._quippy.f90wrap_atoms__get__ndomain(self._handle)
    
    @ndomain.setter
    def ndomain(self, ndomain):
        quippy._quippy.f90wrap_atoms__set__ndomain(self._handle, ndomain)
    
    @property
    def nbuffer(self):
        """
        The number of atoms that can be stored in the buffers of this Atoms object
        
        Element nbuffer ftype=integer                                pytype=int32
        Defined at Atoms_types.fpp line 297
        """
        return quippy._quippy.f90wrap_atoms__get__nbuffer(self._handle)
    
    @nbuffer.setter
    def nbuffer(self, nbuffer):
        quippy._quippy.f90wrap_atoms__set__nbuffer(self._handle, nbuffer)
    
    @property
    def cutoff(self):
        """
        Cutoff distance for neighbour calculations. Default -1.0(unset).
        
        Element cutoff ftype=real(dp) pytype=float64
        Defined at Atoms_types.fpp line 298
        """
        return quippy._quippy.f90wrap_atoms__get__cutoff(self._handle)
    
    @cutoff.setter
    def cutoff(self, cutoff):
        quippy._quippy.f90wrap_atoms__set__cutoff(self._handle, cutoff)
    
    @property
    def cutoff_skin(self):
        """
        If set, increase cutoff by this amount to reduce calc_connect() frequency
        
        Element cutoff_skin ftype=real(dp) pytype=float64
        Defined at Atoms_types.fpp line 299
        """
        return quippy._quippy.f90wrap_atoms__get__cutoff_skin(self._handle)
    
    @cutoff_skin.setter
    def cutoff_skin(self, cutoff_skin):
        quippy._quippy.f90wrap_atoms__set__cutoff_skin(self._handle, cutoff_skin)
    
    @property
    def pot_should_do_nn(self):
        """
        Element pot_should_do_nn ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 300
        """
        return quippy._quippy.f90wrap_atoms__get__pot_should_do_nn(self._handle)
    
    @pot_should_do_nn.setter
    def pot_should_do_nn(self, pot_should_do_nn):
        quippy._quippy.f90wrap_atoms__set__pot_should_do_nn(self._handle, pot_should_do_nn)
    
    @property
    def pot_needs_new_connect(self):
        """
        Element pot_needs_new_connect ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 300
        """
        return quippy._quippy.f90wrap_atoms__get__pot_needs_new_connect(self._handle)
    
    @pot_needs_new_connect.setter
    def pot_needs_new_connect(self, pot_needs_new_connect):
        quippy._quippy.f90wrap_atoms__set__pot_needs_new_connect(self._handle, pot_needs_new_connect)
    
    @property
    def pot_needs_new_dists(self):
        """
        Element pot_needs_new_dists ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 300
        """
        return quippy._quippy.f90wrap_atoms__get__pot_needs_new_dists(self._handle)
    
    @pot_needs_new_dists.setter
    def pot_needs_new_dists(self, pot_needs_new_dists):
        quippy._quippy.f90wrap_atoms__set__pot_needs_new_dists(self._handle, pot_needs_new_dists)
    
    @property
    def nneightol(self):
        """
        Count as nearest neighbour if sum of covalent radii
        times 'this%nneightol' greater than distance between atoms.
        Used in cluster carving.
        
        Element nneightol ftype=real(dp) pytype=float64
        Defined at Atoms_types.fpp line 301
        """
        return quippy._quippy.f90wrap_atoms__get__nneightol(self._handle)
    
    @nneightol.setter
    def nneightol(self, nneightol):
        quippy._quippy.f90wrap_atoms__set__nneightol(self._handle, nneightol)
    
    @property
    def lattice(self):
        """
        Lattice vectors, as columns:
        \\begin{displaymath}
        \\left(
        \\begin{array}{ccc}
        | & | & | \\\\ \\mathbf{a} & \\mathbf{b} & \\mathbf{c} \\\\ | & | & | \\\\ \\end{array}
        \\right)
        = \\left(
        \\begin{array}{ccc}
        R_{11} & R_{12} & R_{13} \\\\ R_{21} & R_{22} & R_{23} \\\\  R_{31} & R_{32} & R_{33} \\\\ \\end{array}
        \\right)
        \\end{displaymath}
        i.e. $\\mathbf{a}$ = 'lattice(:,1)', $\\mathbf{b}$ = 'lattice(:,2)' and
        $\\mathbf{c}$ 'lattice(:,3)'.( | | | | | | ) ( (1,1) (1,2) (1,3) )( | | | | | | ) ( )( |a| |b| |c| ) = ( (2,1) (2,2) \
            (2,3) )( | | | | | | ) ( )( | | | | | | ) ( (3,1) (3,2) (3,3) )
        
        Element lattice ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 305
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__lattice(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        lattice = self._arrays.get(array_hash)
        if lattice is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if lattice.ctypes.data != array_handle:
                lattice = None
        if lattice is None:
            try:
                lattice = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__lattice)
            except TypeError:
                lattice = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = lattice
        return lattice
    
    @lattice.setter
    def lattice(self, lattice):
        self.lattice[...] = lattice
    
    @property
    def is_orthorhombic(self):
        """
        Element is_orthorhombic ftype=logical pytype=bool
        Defined at Atoms_types.fpp line 323
        """
        return quippy._quippy.f90wrap_atoms__get__is_orthorhombic(self._handle)
    
    @is_orthorhombic.setter
    def is_orthorhombic(self, is_orthorhombic):
        quippy._quippy.f90wrap_atoms__set__is_orthorhombic(self._handle, is_orthorhombic)
    
    @property
    def is_periodic(self):
        """
        Element is_periodic ftype=logical pytype=int32 array
        Defined at Atoms_types.fpp line 323
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__is_periodic(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        is_periodic = self._arrays.get(array_hash)
        if is_periodic is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if is_periodic.ctypes.data != array_handle:
                is_periodic = None
        if is_periodic is None:
            try:
                is_periodic = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__is_periodic)
            except TypeError:
                is_periodic = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = is_periodic
        return is_periodic
    
    @is_periodic.setter
    def is_periodic(self, is_periodic):
        self.is_periodic[...] = is_periodic
    
    @property
    def g(self):
        """
        Inverse lattice(stored for speed)
        
        Element g ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 324
        """
        array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_atoms__array__g(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        g = self._arrays.get(array_hash)
        if g is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if g.ctypes.data != array_handle:
                g = None
        if g is None:
            try:
                g = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__g)
            except TypeError:
                g = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = g
        return g
    
    @g.setter
    def g(self, g):
        self.g[...] = g
    
    @property
    def properties(self):
        """
        :class:`~.Dictionary` of atomic properties. A property is an array
        of shape(`m`,`n`) where `n` is the number of atoms and `m` is
        either one(for scalar properties) or three(vector
        properties). Properties can be integer, real, string or logical.
        String properties have a fixed length of ``TABLE_STRING_LENGTH=10``
        characters.
        
        From Fortran, the following default properties are aliased with
        arrays within the Atoms type:
        
        * ``Z`` - Atomic numbers, dimension is actually $(N)$
        * ``species`` Names of elements
        * ``move_mask`` Atoms with 'move_mask' set to zero are fixed
        * ``damp_mask`` Damping is only applied to those atoms with 'damp_mask' set to 1. By default this is set to 1 for all \
            atoms.
        * ``thermostat_region`` Which thermostat is applied to each atoms. By default this is set to 1 for all atoms.
        * ``travel`` Travel across periodic conditions. $(3,N)$ integer array. See meth:`map_into_cell` below.
        * ``pos`` $(3,N)$ array of atomic positions, in $\\mathrm{\\AA}$. Position of atom $i$ is 'pos(:,i)'
        * ``mass`` Atomic masses, dimension is $(N)$
        * ``velo`` $(3,N)$ array  of atomic velocities, in $\\mathrm{AA}$/fs.
        * ``acc`` $(3,N)$ array  of accelerations in $\\mathrm{AA}$/fs$^2$
        * ``avgpos`` $(3,N)$ array  of time-averaged atomic positions.
        * ``oldpos`` $(3,N)$ array  of positions of atoms at previous time step.
        * ``avg_ke`` Time-averaged atomic kinetic energy
        
        Custom properties are most conveniently accessed by assign a pointer to
        them with the :meth:`assign_pointer` routines.
        
        From Python, each property is automatically visible as a
        array attribute of the :class:`Atoms` object,
        for example the atomic positions are stored in a real vector
        property called `pos`, and can be accessed as ``at.pos``.
        
        Properties can be added with the :meth:`add_property` method and
        removed with :meth:`remove_property`.
        
        Element properties ftype=type(dictionary) pytype=Dictionary
        Defined at Atoms_types.fpp line 325
        """
        properties_handle = quippy._quippy.f90wrap_atoms__get__properties(self._handle)
        if tuple(properties_handle) in self._objs:
            properties = self._objs[tuple(properties_handle)]
        else:
            properties = Dictionary.from_handle(properties_handle)
            self._objs[tuple(properties_handle)] = properties
        return properties
    
    @properties.setter
    def properties(self, properties):
        properties = properties._handle
        quippy._quippy.f90wrap_atoms__set__properties(self._handle, properties)
    
    @property
    def params(self):
        """
        :class:`~.Dictionary` of parameters. Useful for storing data about this
        Atoms object, for example the temperature, total energy or
        applied strain. The data stored here is automatically saved to
        and loaded from XYZ and NetCDF files.
        
        Element params ftype=type(dictionary) pytype=Dictionary
        Defined at Atoms_types.fpp line 359
        """
        params_handle = quippy._quippy.f90wrap_atoms__get__params(self._handle)
        if tuple(params_handle) in self._objs:
            params = self._objs[tuple(params_handle)]
        else:
            params = Dictionary.from_handle(params_handle)
            self._objs[tuple(params_handle)] = params
        return params
    
    @params.setter
    def params(self, params):
        params = params._handle
        quippy._quippy.f90wrap_atoms__set__params(self._handle, params)
    
    @property
    def z(self):
        """
        Atomic numbers, dimension is actually $(N)$
        
        Element z ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 363
        """
        array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_atoms__array__z(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        z = self._arrays.get(array_hash)
        if z is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if z.ctypes.data != array_handle:
                z = None
        if z is None:
            try:
                z = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__z)
            except TypeError:
                z = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = z
        return z
    
    @z.setter
    def z(self, z):
        self.z[...] = z
    
    @property
    def species(self):
        """
        Names of elements
        
        Element species ftype=character(1) pytype=str array
        Defined at Atoms_types.fpp line 364
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__species(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        species = self._arrays.get(array_hash)
        if species is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if species.ctypes.data != array_handle:
                species = None
        if species is None:
            try:
                species = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__species)
            except TypeError:
                species = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = species
        return species
    
    @species.setter
    def species(self, species):
        self.species[...] = species
    
    @property
    def move_mask(self):
        """
        Atoms with 'move_mask' set to false are fixed
        
        Element move_mask ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 365
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__move_mask(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        move_mask = self._arrays.get(array_hash)
        if move_mask is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if move_mask.ctypes.data != array_handle:
                move_mask = None
        if move_mask is None:
            try:
                move_mask = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__move_mask)
            except TypeError:
                move_mask = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = move_mask
        return move_mask
    
    @move_mask.setter
    def move_mask(self, move_mask):
        self.move_mask[...] = move_mask
    
    @property
    def damp_mask(self):
        """
        Damping is only applied to those atoms with
        'damp_mask' set to 1.
        By default this is set to 1 for all atoms.
        
        Element damp_mask ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 366
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__damp_mask(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        damp_mask = self._arrays.get(array_hash)
        if damp_mask is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if damp_mask.ctypes.data != array_handle:
                damp_mask = None
        if damp_mask is None:
            try:
                damp_mask = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__damp_mask)
            except TypeError:
                damp_mask = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = damp_mask
        return damp_mask
    
    @damp_mask.setter
    def damp_mask(self, damp_mask):
        self.damp_mask[...] = damp_mask
    
    @property
    def thermostat_region(self):
        """
        Which thermostat is applied to each atoms.
        By default this is set to 1 for all atoms.
        
        Element thermostat_region ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 369
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__thermostat_region(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        thermostat_region = self._arrays.get(array_hash)
        if thermostat_region is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if thermostat_region.ctypes.data != array_handle:
                thermostat_region = None
        if thermostat_region is None:
            try:
                thermostat_region = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__thermostat_region)
            except TypeError:
                thermostat_region = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = thermostat_region
        return thermostat_region
    
    @thermostat_region.setter
    def thermostat_region(self, thermostat_region):
        self.thermostat_region[...] = thermostat_region
    
    @property
    def travel(self):
        """
        Travel across periodic conditions. Actually $(3,N)$ array.
        See 'map_into_cell' below.
        
        Element travel ftype=integer pytype=int array
        Defined at Atoms_types.fpp line 371
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__travel(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        travel = self._arrays.get(array_hash)
        if travel is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if travel.ctypes.data != array_handle:
                travel = None
        if travel is None:
            try:
                travel = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__travel)
            except TypeError:
                travel = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = travel
        return travel
    
    @travel.setter
    def travel(self, travel):
        self.travel[...] = travel
    
    @property
    def pos(self):
        """
        $(3,N)$ array of atomic positions, in $\\mathrm{AA}$.
        Position of atom $i$ is 'pos(:,i)'
        
        Element pos ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 373
        """
        array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_atoms__array__pos(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        pos = self._arrays.get(array_hash)
        if pos is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if pos.ctypes.data != array_handle:
                pos = None
        if pos is None:
            try:
                pos = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__pos)
            except TypeError:
                pos = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = pos
        return pos
    
    @pos.setter
    def pos(self, pos):
        self.pos[...] = pos
    
    @property
    def mass(self):
        """
        Atomic masses, dimension is actually $(N)$
        
        Element mass ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 375
        """
        array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_atoms__array__mass(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        mass = self._arrays.get(array_hash)
        if mass is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if mass.ctypes.data != array_handle:
                mass = None
        if mass is None:
            try:
                mass = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__mass)
            except TypeError:
                mass = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = mass
        return mass
    
    @mass.setter
    def mass(self, mass):
        self.mass[...] = mass
    
    @property
    def velo(self):
        """
        $(3,N)$ array  of atomic velocities, in $\\mathrm{AA}$/fs.
        
        Element velo ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 376
        """
        array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_atoms__array__velo(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        velo = self._arrays.get(array_hash)
        if velo is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if velo.ctypes.data != array_handle:
                velo = None
        if velo is None:
            try:
                velo = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__velo)
            except TypeError:
                velo = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = velo
        return velo
    
    @velo.setter
    def velo(self, velo):
        self.velo[...] = velo
    
    @property
    def acc(self):
        """
        $(3,N)$ array  of accelerations in $\\mathrm{AA}$/fs$^2$
        
        Element acc ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 377
        """
        array_ndim, array_type, array_shape, array_handle =     quippy._quippy.f90wrap_atoms__array__acc(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        acc = self._arrays.get(array_hash)
        if acc is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if acc.ctypes.data != array_handle:
                acc = None
        if acc is None:
            try:
                acc = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__acc)
            except TypeError:
                acc = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = acc
        return acc
    
    @acc.setter
    def acc(self, acc):
        self.acc[...] = acc
    
    @property
    def avgpos(self):
        """
        $(3,N)$ array  of time-averaged atomic positions.
        
        Element avgpos ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 378
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__avgpos(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        avgpos = self._arrays.get(array_hash)
        if avgpos is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if avgpos.ctypes.data != array_handle:
                avgpos = None
        if avgpos is None:
            try:
                avgpos = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__avgpos)
            except TypeError:
                avgpos = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = avgpos
        return avgpos
    
    @avgpos.setter
    def avgpos(self, avgpos):
        self.avgpos[...] = avgpos
    
    @property
    def oldpos(self):
        """
        $(3,N)$ array  of positions of atoms at previous time step.
        
        Element oldpos ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 379
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__oldpos(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        oldpos = self._arrays.get(array_hash)
        if oldpos is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if oldpos.ctypes.data != array_handle:
                oldpos = None
        if oldpos is None:
            try:
                oldpos = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__oldpos)
            except TypeError:
                oldpos = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = oldpos
        return oldpos
    
    @oldpos.setter
    def oldpos(self, oldpos):
        self.oldpos[...] = oldpos
    
    @property
    def avg_ke(self):
        """
        Time-averaged atomic kinetic energy
        
        Element avg_ke ftype=real(dp) pytype=float array
        Defined at Atoms_types.fpp line 380
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_atoms__array__avg_ke(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        avg_ke = self._arrays.get(array_hash)
        if avg_ke is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if avg_ke.ctypes.data != array_handle:
                avg_ke = None
        if avg_ke is None:
            try:
                avg_ke = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_atoms__array__avg_ke)
            except TypeError:
                avg_ke = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = avg_ke
        return avg_ke
    
    @avg_ke.setter
    def avg_ke(self, avg_ke):
        self.avg_ke[...] = avg_ke
    
    @property
    def connect(self):
        """
        :class:`~.Connection` object
        
        Element connect ftype=type(connection) pytype=Connection
        Defined at Atoms_types.fpp line 381
        """
        connect_handle = quippy._quippy.f90wrap_atoms__get__connect(self._handle)
        if tuple(connect_handle) in self._objs:
            connect = self._objs[tuple(connect_handle)]
        else:
            connect = Connection.from_handle(connect_handle)
            self._objs[tuple(connect_handle)] = connect
        return connect
    
    @connect.setter
    def connect(self, connect):
        connect = connect._handle
        quippy._quippy.f90wrap_atoms__set__connect(self._handle, connect)
    
    @property
    def hysteretic_connect(self):
        """
        Hysteretic :class:`~.Connection` object
        
        Element hysteretic_connect ftype=type(connection) pytype=Connection
        Defined at Atoms_types.fpp line 382
        """
        hysteretic_connect_handle = quippy._quippy.f90wrap_atoms__get__hysteretic_connect(self._handle)
        if tuple(hysteretic_connect_handle) in self._objs:
            hysteretic_connect = self._objs[tuple(hysteretic_connect_handle)]
        else:
            hysteretic_connect = Connection.from_handle(hysteretic_connect_handle)
            self._objs[tuple(hysteretic_connect_handle)] = hysteretic_connect
        return hysteretic_connect
    
    @hysteretic_connect.setter
    def hysteretic_connect(self, hysteretic_connect):
        hysteretic_connect = hysteretic_connect._handle
        quippy._quippy.f90wrap_atoms__set__hysteretic_connect(self._handle, hysteretic_connect)
    
    @property
    def domain(self):
        """
        Domain decomposition object
        
        Element domain ftype=type(domaindecomposition) pytype=Domaindecomposition
        Defined at Atoms_types.fpp line 383
        """
        domain_handle = quippy._quippy.f90wrap_atoms__get__domain(self._handle)
        if tuple(domain_handle) in self._objs:
            domain = self._objs[tuple(domain_handle)]
        else:
            domain = DomainDecomposition.from_handle(domain_handle)
            self._objs[tuple(domain_handle)] = domain
        return domain
    
    @domain.setter
    def domain(self, domain):
        domain = domain._handle
        quippy._quippy.f90wrap_atoms__set__domain(self._handle, domain)
    
    def __str__(self):
        ret = ['<atoms>{\n']
        ret.append('    own_this : ')
        ret.append(repr(self.own_this))
        ret.append(',\n    ref_count : ')
        ret.append(repr(self.ref_count))
        ret.append(',\n    fixed_size : ')
        ret.append(repr(self.fixed_size))
        ret.append(',\n    n : ')
        ret.append(repr(self.n))
        ret.append(',\n    ndomain : ')
        ret.append(repr(self.ndomain))
        ret.append(',\n    nbuffer : ')
        ret.append(repr(self.nbuffer))
        ret.append(',\n    cutoff : ')
        ret.append(repr(self.cutoff))
        ret.append(',\n    cutoff_skin : ')
        ret.append(repr(self.cutoff_skin))
        ret.append(',\n    pot_should_do_nn : ')
        ret.append(repr(self.pot_should_do_nn))
        ret.append(',\n    pot_needs_new_connect : ')
        ret.append(repr(self.pot_needs_new_connect))
        ret.append(',\n    pot_needs_new_dists : ')
        ret.append(repr(self.pot_needs_new_dists))
        ret.append(',\n    nneightol : ')
        ret.append(repr(self.nneightol))
        ret.append(',\n    lattice : ')
        ret.append(repr(self.lattice))
        ret.append(',\n    is_orthorhombic : ')
        ret.append(repr(self.is_orthorhombic))
        ret.append(',\n    is_periodic : ')
        ret.append(repr(self.is_periodic))
        ret.append(',\n    g : ')
        ret.append(repr(self.g))
        ret.append(',\n    properties : ')
        ret.append(repr(self.properties))
        ret.append(',\n    params : ')
        ret.append(repr(self.params))
        ret.append(',\n    z : ')
        ret.append(repr(self.z))
        ret.append(',\n    species : ')
        ret.append(repr(self.species))
        ret.append(',\n    move_mask : ')
        ret.append(repr(self.move_mask))
        ret.append(',\n    damp_mask : ')
        ret.append(repr(self.damp_mask))
        ret.append(',\n    thermostat_region : ')
        ret.append(repr(self.thermostat_region))
        ret.append(',\n    travel : ')
        ret.append(repr(self.travel))
        ret.append(',\n    pos : ')
        ret.append(repr(self.pos))
        ret.append(',\n    mass : ')
        ret.append(repr(self.mass))
        ret.append(',\n    velo : ')
        ret.append(repr(self.velo))
        ret.append(',\n    acc : ')
        ret.append(repr(self.acc))
        ret.append(',\n    avgpos : ')
        ret.append(repr(self.avgpos))
        ret.append(',\n    oldpos : ')
        ret.append(repr(self.oldpos))
        ret.append(',\n    avg_ke : ')
        ret.append(repr(self.avg_ke))
        ret.append(',\n    connect : ')
        ret.append(repr(self.connect))
        ret.append(',\n    hysteretic_connect : ')
        ret.append(repr(self.hysteretic_connect))
        ret.append(',\n    domain : ')
        ret.append(repr(self.domain))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

def bond_length(z1, z2, interface_call=False):
    """
    Returns the sum of the covalent radii of two atoms
    
    bond_length = bond_length(z1, z2)
    Defined at Atoms_types.fpp lines 1311-1314
    
    Parameters
    ----------
    z1 : int32
    z2 : int32
    
    Returns
    -------
    bond_length : float64
    """
    bond_length = quippy._quippy.f90wrap_atoms_types_module__bond_length(z1=z1, z2=z2)
    return bond_length

def lattice_cell_volume(lattice, interface_call=False):
    """
    Returns the(unsigned) volume of the simulation cell of lattice
    
    lattice_cell_volume = lattice_cell_volume(lattice)
    Defined at Atoms_types.fpp lines 1350-1357
    
    Parameters
    ----------
    lattice : float array
    
    Returns
    -------
    lattice_cell_volume : float64
    """
    lattice_cell_volume = quippy._quippy.f90wrap_atoms_types_module__lattice_cell_volume(lattice=lattice)
    return lattice_cell_volume

def vec_map_into_cell(pos, lattice, g, shift=None, mapped=None, interface_call=False):
    """
    vec_map_into_cell(pos, lattice, g[, shift, mapped])
    Defined at Atoms_types.fpp lines 1324-1347
    
    Parameters
    ----------
    pos : float array
    lattice : float array
    g : float array
    shift : int array
    mapped : bool
    """
    quippy._quippy.f90wrap_atoms_types_module__vec_map_into_cell(pos=pos, lattice=lattice, g=g, shift=shift, mapped=mapped)

def array_map_into_cell(pos, lattice, g, interface_call=False):
    """
    array_map_into_cell(pos, lattice, g)
    Defined at Atoms_types.fpp lines 1316-1322
    
    Parameters
    ----------
    pos : float array
    lattice : float array
    g : float array
    """
    quippy._quippy.f90wrap_atoms_types_module__array_map_into_cell(pos=pos, lattice=lattice, g=g)

def map_into_cell(*args, **kwargs):
    """
    map_into_cell(*args, **kwargs)
    Defined at Atoms_types.fpp lines 441-442
    
    Overloaded interface containing the following procedures:
      vec_map_into_cell
      array_map_into_cell
    """
    for proc in [vec_map_into_cell, array_map_into_cell]:
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
        "map_into_cell compatible with the provided args:"
        "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))

def get_default_nneightol():
    """
    Default value for 'atoms%nneightol'
    
    Element default_nneightol ftype=real(dp) pytype=float64
    Defined at Atoms_types.fpp line 146
    """
    return quippy._quippy.f90wrap_atoms_types_module__get__default_nneightol()

DEFAULT_NNEIGHTOL = get_default_nneightol()

def get_dd_wrap_to_cell():
    """
    All particles, including ghosts, are wrapped into the cell
    
    Element dd_wrap_to_cell ftype=integer pytype=int32
    Defined at Atoms_types.fpp line 148
    """
    return quippy._quippy.f90wrap_atoms_types_module__get__dd_wrap_to_cell()

DD_WRAP_TO_CELL = get_dd_wrap_to_cell()

def get_dd_wrap_to_domain():
    """
    Particles are wrapped into the domain, ghost particles are
    located next to the domain.
    
    Element dd_wrap_to_domain ftype=integer pytype=int32
    Defined at Atoms_types.fpp line 149
    """
    return quippy._quippy.f90wrap_atoms_types_module__get__dd_wrap_to_domain()

DD_WRAP_TO_DOMAIN = get_dd_wrap_to_domain()


_array_initialisers = []
_dt_array_initialisers = []


try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module "atoms_types_module".')

for func in _dt_array_initialisers:
    func()
