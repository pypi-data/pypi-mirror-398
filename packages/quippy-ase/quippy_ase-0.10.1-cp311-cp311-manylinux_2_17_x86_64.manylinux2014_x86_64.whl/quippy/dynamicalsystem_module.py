"""
A DynamicalSystem object contains an Atoms object, which holds infomation about
velocities and accelerations of each atom, scalar quantities such as
thermostat settings, and logical masks so that thermostatting can be applied
to selected atoms etc.

In Fortran code, initialise a DynamicalSystem object like this:
>         call initialise(MyDS, MyAtoms)
which(shallowly) copies MyAtoms into the internal atoms structure(and so
MyAtoms is not required by MyDS after this call and can be finalised). In Python,
a DynamicalSystem can be initialised from an Atoms instance:
>     MyDS = DynamicalSystem(MyAtoms)


A DynamicalSystem is constructed from an Atoms object
'atoms'. The initial velocities and accelerations can optionally be
specificed as '(3,atoms.n)' arrays. The 'constraints' and
'rigidbodies' arguments can be used to specify the number of
constraints and rigid bodies respectively(the default is zero in
both cases).

DynamicalSystem has an integrator,
>         call advance_verlet(MyDS,dt,forces)
which takes a set of forces and integrates the equations of motion forward
for a time 'dt'.

All dynamical variables are stored inside the Atoms' :attr:`~quippy.atoms.Atoms.properties` Dictionary.
XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

Module dynamicalsystem_module
Defined at DynamicalSystem.fpp lines 154-2580
"""
from __future__ import print_function, absolute_import, division
import quippy._quippy
import f90wrap.runtime
import logging
import numpy
import warnings
import weakref
from quippy.atoms_types_module import Atoms

logger = logging.getLogger(__name__)
warnings.filterwarnings("error", category=numpy.exceptions.ComplexWarning)
_arrays = {}
_objs = {}

@f90wrap.runtime.register_class("quippy.DynamicalSystem")
class DynamicalSystem(f90wrap.runtime.FortranDerivedType):
    """
    Type(name=dynamicalsystem)
    Defined at DynamicalSystem.fpp lines 195-228
    """
    def ds_save_state(self, from_, error=None, interface_call=False):
        """
        Save the state of a DynamicalSystem. The output object
        cannot be used as an initialised DynamicalSystem since
        connectivity and group information is not copied to save
        memory. Only scalar members and the 'ds%atoms' object
        (minus 'ds%atoms%connect') are copied. The current
        state of the random number generator is also saved.
        
        ds_save_state(self, from_[, error])
        Defined at DynamicalSystem.fpp lines 564-596
        
        Parameters
        ----------
        to : Dynamicalsystem
        from_ : Dynamicalsystem
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_save_state(to=self._handle, from_=from_._handle, error=error)
    
    def ds_restore_state(self, from_, interface_call=False):
        """
        Restore a DynamicalSystem to a previously saved state.
        Only scalar members and 'ds%atoms' (minus 'ds%atoms%connect')
        are copied back; 'to' should be a properly initialised
        DynamicalSystem object. The saved state of the random
        number generator is also restored. 'calc_dists()' is
        called on the restored atoms object.
        
        ds_restore_state(self, from_)
        Defined at DynamicalSystem.fpp lines 604-625
        
        Parameters
        ----------
        to : Dynamicalsystem
        from_ : Dynamicalsystem
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_restore_state(to=self._handle, from_=from_._handle)
    
    def n_thermostat(self, interface_call=False):
        """
        n_thermostat = n_thermostat(self)
        Defined at DynamicalSystem.fpp lines 832-835
        
        Parameters
        ----------
        this : Dynamicalsystem
        
        Returns
        -------
        n_thermostat : int32
        """
        n_thermostat = quippy._quippy.f90wrap_dynamicalsystem_module__n_thermostat(this=self._handle)
        return n_thermostat
    
    def is_damping_enabled(self, interface_call=False):
        """
        is_damping_enabled = is_damping_enabled(self)
        Defined at DynamicalSystem.fpp lines 970-977
        
        Parameters
        ----------
        this : Dynamicalsystem
        
        Returns
        -------
        is_damping_enabled : bool
        """
        is_damping_enabled = quippy._quippy.f90wrap_dynamicalsystem_module__is_damping_enabled(this=self._handle)
        return is_damping_enabled
    
    def get_damping_time(self, interface_call=False):
        """
        get_damping_time = get_damping_time(self)
        Defined at DynamicalSystem.fpp lines 979-984
        
        Parameters
        ----------
        this : Dynamicalsystem
        
        Returns
        -------
        get_damping_time : float64
        """
        get_damping_time = quippy._quippy.f90wrap_dynamicalsystem_module__get_damping_time(this=self._handle)
        return get_damping_time
    
    def enable_damping(self, damp_time, interface_call=False):
        """
        Enable damping, with damping time set to `damp_time`. Only atoms
        flagged in the `damp_mask` property will be affected.
        
        enable_damping(self, damp_time)
        Defined at DynamicalSystem.fpp lines 988-992
        
        Parameters
        ----------
        this : Dynamicalsystem
        damp_time : float64
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__enable_damping(this=self._handle, damp_time=damp_time)
    
    def disable_damping(self, interface_call=False):
        """
        disable_damping(self)
        Defined at DynamicalSystem.fpp lines 994-996
        
        Parameters
        ----------
        this : Dynamicalsystem
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__disable_damping(this=self._handle)
    
    def thermostat_temperatures(self, temps, interface_call=False):
        """
        thermostat_temperatures(self, temps)
        Defined at DynamicalSystem.fpp lines 1246-1258
        
        Parameters
        ----------
        this : Dynamicalsystem
        temps : float array
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__thermostat_temperatures(this=self._handle, temps=temps)
    
    def temperature(self, property=None, value=None, include_all=None, instantaneous=None, error=None, \
        interface_call=False):
        """
        Return the temperature, assuming each degree of freedom contributes
        $\\frac{1}{2}kT$. By default only moving and thermostatted atoms are
        included --- this can be overriden by setting 'include_all' to true.
        'region' can be used to restrict
        the calculation to a particular thermostat
        region. 'instantaneous' controls whether the calculation should
        be carried out using the current values of the velocities and
        masses, or whether to return the value at the last Verlet step
        (the latter is the default).
        
        temperature = temperature(self[, property, value, include_all, instantaneous, error])
        Defined at DynamicalSystem.fpp lines 1270-1324
        
        Parameters
        ----------
        this : Dynamicalsystem
        property : str
        value : int32
        include_all : bool
        instantaneous : bool
        error : int32
        
        Returns
        -------
        temperature : float64
        """
        temperature = quippy._quippy.f90wrap_dynamicalsystem_module__temperature(this=self._handle, property=property, \
            value=value, include_all=include_all, instantaneous=instantaneous, error=error)
        return temperature
    
    def rescale_velo(self, temp, mass_weighted=None, zero_l=None, interface_call=False):
        """
        Rescale the atomic velocities to temperature 'temp'. If the
        current temperature is zero, we first randomise the velocites.
        If 'mass_weighted' is true, then the velocites are weighted by
        $1/sqrt{m}$. Linear momentum is zeroed automatically.  If
        'zero_l' is true then the angular momentum is also zeroed.
        
        rescale_velo(self, temp[, mass_weighted, zero_l])
        Defined at DynamicalSystem.fpp lines 1342-1370
        
        Parameters
        ----------
        this : Dynamicalsystem
        temp : float64
        mass_weighted : bool
        zero_l : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__rescale_velo(this=self._handle, temp=temp, mass_weighted=mass_weighted, \
            zero_l=zero_l)
    
    def zero_momentum(self, indices=None, interface_call=False):
        """
        Change velocities to those that the system would have in the zero momentum frame.
        Optionalally zero the total momentum of a subset of atoms, specified by 'indices'.
        
        zero_momentum(self[, indices])
        Defined at DynamicalSystem.fpp lines 1422-1434
        
        Parameters
        ----------
        this : Dynamicalsystem
        indices : int array
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__zero_momentum(this=self._handle, indices=indices)
    
    def advance_verlet1(self, dt, virial=None, parallel=None, store_constraint_force=None, do_calc_dists=None, error=None, \
        interface_call=False):
        """
        Advance the velocities by half the time-step 'dt' and the
        positions by a full time-step. A typical MD loop should
        resemble the following code(Python example, Fortran is similar):
        
        > ds.atoms.calc_connect()
        > for n in range(n_steps):
        >    ds.advance_verlet1(dt)
        >    pot.calc(ds.atoms, force=True, energy=True)
        >    ds.advance_verlet2(dt, ds.atoms.force)
        >    ds.print_status(epot=ds.atoms.energy)
        >    if n % connect_interval == 0:
        >       ds.atoms.calc_connect()
        
        advance_verlet1(self, dt[, virial, parallel, store_constraint_force, do_calc_dists, error])
        Defined at DynamicalSystem.fpp lines 1547-1714
        
        Parameters
        ----------
        this : Dynamicalsystem
        dt : float64
        virial : float array
        parallel : bool
        store_constraint_force : bool
        do_calc_dists : bool
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__advance_verlet1(this=self._handle, dt=dt, virial=virial, \
            parallel=parallel, store_constraint_force=store_constraint_force, do_calc_dists=do_calc_dists, error=error)
    
    def advance_verlet2(self, dt, f, virial=None, e=None, parallel=None, store_constraint_force=None, error=None, \
        interface_call=False):
        """
        Advances the velocities by the second half time-step
        
        advance_verlet2(self, dt, f[, virial, e, parallel, store_constraint_force, error])
        Defined at DynamicalSystem.fpp lines 1740-1857
        
        Parameters
        ----------
        this : Dynamicalsystem
        dt : float64
        f : float array
        virial : float array
        e : float64
        parallel : bool
        store_constraint_force : bool
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__advance_verlet2(this=self._handle, dt=dt, f=f, virial=virial, e=e, \
            parallel=parallel, store_constraint_force=store_constraint_force, error=error)
    
    def advance_verlet(self, dt, f, virial=None, e=None, parallel=None, store_constraint_force=None, do_calc_dists=None, \
        error=None, interface_call=False):
        """
        Calls' advance_verlet2' followed by 'advance_verlet1'. Outside this routine the
        velocities will be half-stepped. This allows a simpler MD loop:
        >  for n in range(n_steps):
        >      pot.calc(ds.atoms, force=True, energy=True)
        >      ds.advance_verlet(dt, ds.atoms.force)
        >      ds.print_status(epot=ds.atoms.energy)
        >      if n % connect_interval == 0:
        >         ds.atoms.calc_connect()
        
        advance_verlet(self, dt, f[, virial, e, parallel, store_constraint_force, do_calc_dists, error])
        Defined at DynamicalSystem.fpp lines 1867-1887
        
        Parameters
        ----------
        ds : Dynamicalsystem
        dt : float64
        f : float array
        virial : float array
        e : float64
        parallel : bool
        store_constraint_force : bool
        do_calc_dists : bool
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__advance_verlet(ds=self._handle, dt=dt, f=f, virial=virial, e=e, \
            parallel=parallel, store_constraint_force=store_constraint_force, do_calc_dists=do_calc_dists, error=error)
    
    def ds_print_status(self, label=None, epot=None, instantaneous=None, file=None, error=None, interface_call=False):
        """
        Print a status line showing the current time, temperature, the mean temperature
        the total energy and the total momentum for this DynamicalSystem. If present, the optional
        'label' parameter should be a one character label for the log lines and is printed
        in the first column of the output. 'epot' should be the potential energy
        if this is available. 'instantaneous' has the same meaning as in 'temperature' routine.
        
        ds_print_status(self[, label, epot, instantaneous, file, error])
        Defined at DynamicalSystem.fpp lines 1899-1963
        
        Parameters
        ----------
        this : Dynamicalsystem
        label : str
        epot : float64
        instantaneous : bool
        file : Inoutput
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_print_status(this=self._handle, label=label, epot=epot, \
            instantaneous=instantaneous, file=None if file is None else file._handle, error=error)
    
    def constrain_bondanglecos(self, i, j, k, c=None, restraint_k=None, bound=None, tol=None, print_summary=None, \
        interface_call=False):
        """
        Constrain the bond angle cosine between atoms i, j, and k
        
        constrain_bondanglecos(self, i, j, k[, c, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2005-2038
        
        Parameters
        ----------
        this : Dynamicalsystem
        i : int32
        j : int32
        k : int32
        c : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_bondanglecos(this=self._handle, i=i, j=j, k=k, c=c, \
            restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_bondlength(self, i, j, d, di=None, t0=None, tau=None, restraint_k=None, bound=None, tol=None, \
        print_summary=None, interface_call=False):
        """
        Constrain the bond between atoms i and j
        
        constrain_bondlength(self, i, j, d[, di, t0, tau, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2041-2082
        
        Parameters
        ----------
        this : Dynamicalsystem
        i : int32
        j : int32
        d : float64
        di : float64
        t0 : float64
        tau : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_bondlength(this=self._handle, i=i, j=j, d=d, di=di, t0=t0, \
            tau=tau, restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_bondlength_sq(self, i, j, d=None, restraint_k=None, bound=None, tol=None, print_summary=None, \
        interface_call=False):
        """
        Constrain the bond between atoms i and j
        
        constrain_bondlength_sq(self, i, j[, d, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2085-2111
        
        Parameters
        ----------
        this : Dynamicalsystem
        i : int32
        j : int32
        d : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_bondlength_sq(this=self._handle, i=i, j=j, d=d, \
            restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_bondlength_dev_pow(self, i, j, p, d, di=None, t0=None, tau=None, restraint_k=None, bound=None, tol=None, \
        print_summary=None, interface_call=False):
        """
        Constrain the bond between atoms i and j
        
        constrain_bondlength_dev_pow(self, i, j, p, d[, di, t0, tau, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2114-2155
        
        Parameters
        ----------
        this : Dynamicalsystem
        i : int32
        j : int32
        p : float64
        d : float64
        di : float64
        t0 : float64
        tau : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_bondlength_dev_pow(this=self._handle, i=i, j=j, p=p, d=d, \
            di=di, t0=t0, tau=tau, restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_bondlength_diff(self, i, j, k, d, di=None, t0=None, tau=None, restraint_k=None, bound=None, tol=None, \
        print_summary=None, interface_call=False):
        """
        Constrain the difference of bond length between atoms i--j and j--k
        
        constrain_bondlength_diff(self, i, j, k, d[, di, t0, tau, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2161-2195
        
        Parameters
        ----------
        this : Dynamicalsystem
        i : int32
        j : int32
        k : int32
        d : float64
        di : float64
        t0 : float64
        tau : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_bondlength_diff(this=self._handle, i=i, j=j, k=k, d=d, di=di, \
            t0=t0, tau=tau, restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_gap_energy(self, d, restraint_k=None, bound=None, tol=None, print_summary=None, interface_call=False):
        """
        Constrain the energy gap of two resonance structures
        
        constrain_gap_energy(self, d[, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2201-2222
        
        Parameters
        ----------
        this : Dynamicalsystem
        d : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_gap_energy(this=self._handle, d=d, restraint_k=restraint_k, \
            bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_atom_plane(self, i, plane_n, d=None, restraint_k=None, bound=None, tol=None, print_summary=None, \
        interface_call=False):
        """
        Constrain an atom to lie in a particluar plane
        
        constrain_atom_plane(self, i, plane_n[, d, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2225-2248
        
        Parameters
        ----------
        this : Dynamicalsystem
        i : int32
        plane_n : float array
        d : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_atom_plane(this=self._handle, i=i, plane_n=plane_n, d=d, \
            restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_struct_factor_like_mag(self, z, q, sf, restraint_k=None, bound=None, tol=None, print_summary=None, \
        interface_call=False):
        """
        Constrain an atom to lie in a particluar plane
        
        constrain_struct_factor_like_mag(self, z, q, sf[, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2251-2296
        
        Parameters
        ----------
        this : Dynamicalsystem
        z : int32
        q : float array
        sf : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_struct_factor_lik127f(this=self._handle, z=z, q=q, sf=sf, \
            restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_struct_factor_like_r(self, z, q, sf, restraint_k=None, bound=None, tol=None, print_summary=None, \
        interface_call=False):
        """
        Constrain an atom to lie in a particluar plane
        
        constrain_struct_factor_like_r(self, z, q, sf[, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2299-2344
        
        Parameters
        ----------
        this : Dynamicalsystem
        z : int32
        q : float array
        sf : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_struct_factor_like_r(this=self._handle, z=z, q=q, sf=sf, \
            restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def constrain_struct_factor_like_i(self, z, q, sf, restraint_k=None, bound=None, tol=None, print_summary=None, \
        interface_call=False):
        """
        Constrain an atom to lie in a particluar plane
        
        constrain_struct_factor_like_i(self, z, q, sf[, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2347-2392
        
        Parameters
        ----------
        this : Dynamicalsystem
        z : int32
        q : float array
        sf : float64
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__constrain_struct_factor_like_i(this=self._handle, z=z, q=q, sf=sf, \
            restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def ds_add_constraint(self, atoms, func, data, update_ndof=None, restraint_k=None, bound=None, tol=None, \
        print_summary=None, interface_call=False):
        """
        Add a constraint to the DynamicalSystem and reduce the number of degrees of freedom,
        unless 'update_Ndof' is present and false.
        
        ds_add_constraint(self, atoms, func, data[, update_ndof, restraint_k, bound, tol, print_summary])
        Defined at DynamicalSystem.fpp lines 2396-2468
        
        Parameters
        ----------
        this : Dynamicalsystem
        atoms : int array
        func : int32
        data : float array
        update_ndof : bool
        restraint_k : float64
        bound : int32
        tol : float64
        print_summary : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_add_constraint(this=self._handle, atoms=atoms, func=func, data=data, \
            update_ndof=update_ndof, restraint_k=restraint_k, bound=bound, tol=tol, print_summary=print_summary)
    
    def ds_amend_constraint(self, constraint, func, data, k=None, interface_call=False):
        """
        Replace a constraint involving some atoms with a different constraint involving
        the same atoms
        
        ds_amend_constraint(self, constraint, func, data[, k])
        Defined at DynamicalSystem.fpp lines 2474-2479
        
        Parameters
        ----------
        this : Dynamicalsystem
        constraint : int32
        func : int32
        data : float array
        k : float64
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_amend_constraint(this=self._handle, constraint=constraint, func=func, \
            data=data, k=k)
    
    def ds_print(self, file=None, interface_call=False):
        """
        Print lots of information about this DynamicalSystem in text format.
        
        ds_print(self[, file])
        Defined at DynamicalSystem.fpp lines 1970-1994
        
        Parameters
        ----------
        this : Dynamicalsystem
        file : Inoutput
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_print(this=self._handle, file=None if file is None else file._handle)
    
    def __init__(self, atoms_in, velocity=None, acceleration=None, constraints=None, restraints=None, rigidbodies=None, \
        error=None, handle=None):
        """
        Initialise this DynamicalSystem from an Atoms object
        
        self = Dynamicalsystem(atoms_in[, velocity, acceleration, constraints, restraints, rigidbodies, error])
        Defined at DynamicalSystem.fpp lines 308-454
        
        Parameters
        ----------
        atoms_in : Atoms
        velocity : float array
        acceleration : float array
        constraints : int32
        restraints : int32
        rigidbodies : int32
        error : int32
        
        Returns
        -------
        this : Dynamicalsystem
        """
        f90wrap.runtime.FortranDerivedType.__init__(self)
        if isinstance(handle, numpy.ndarray) and handle.ndim == 1 and handle.dtype.num == 5:
            self._handle = handle
            self._alloc = True
        else:
            result = quippy._quippy.f90wrap_dynamicalsystem_module__ds_initialise(atoms_in=atoms_in._handle, velocity=velocity, \
                acceleration=acceleration, constraints=constraints, restraints=restraints, rigidbodies=rigidbodies, error=error)
            self._handle = result[0] if isinstance(result, tuple) else result
            self._alloc = True
        self._setup_finalizer()
    
    def _setup_finalizer(self):
        """Set up weak reference destructor to prevent Fortran memory leaks."""
        if self._alloc:
            self._finalizer = weakref.finalize(self, quippy._quippy.f90wrap_dynamicalsystem_module__ds_finalise, self._handle)
    
    def ds_kinetic_energy(self, local_ke=None, error=None, interface_call=False):
        """
        Return the total kinetic energy $E_k = \\sum_{i} \\frac{1}{2} m v^2$
        
        ke = ds_kinetic_energy(self[, local_ke, error])
        Defined at DynamicalSystem.fpp lines 1135-1143
        
        Parameters
        ----------
        this : Dynamicalsystem
        local_ke : bool
        error : int32
        
        Returns
        -------
        ke : float64
        """
        ke = quippy._quippy.f90wrap_dynamicalsystem_module__ds_kinetic_energy(this=self._handle, local_ke=local_ke, error=error)
        return ke
    
    def ds_kinetic_virial(self, error=None, interface_call=False):
        """
        Return the total kinetic virial $w_ij = \\sum_{k} \\frac{1}{2} m v_i v_j$
        
        kv = ds_kinetic_virial(self[, error])
        Defined at DynamicalSystem.fpp lines 1194-1201
        
        Parameters
        ----------
        this : Dynamicalsystem
        error : int32
        
        Returns
        -------
        kv : float array
        """
        kv = quippy._quippy.f90wrap_dynamicalsystem_module__ds_kinetic_virial(this=self._handle, error=error)
        return kv
    
    def ds_angular_momentum(self, origin=None, indices=None, interface_call=False):
        """
        Return the angular momentum of all the atoms in this DynamicalSystem, defined by
        $\\mathbf{L} = \\sum_{i} \\mathbf{r_i} \\times \\mathbf{v_i}$.
        
        l = ds_angular_momentum(self[, origin, indices])
        Defined at DynamicalSystem.fpp lines 1041-1046
        
        Parameters
        ----------
        this : Dynamicalsystem
        origin : float array
        indices : int array
        
        Returns
        -------
        l : float array
        """
        l = quippy._quippy.f90wrap_dynamicalsystem_module__ds_angular_momentum(this=self._handle, origin=origin, \
            indices=indices)
        return l
    
    def ds_momentum(self, indices=None, interface_call=False):
        """
        Return the total momentum $\\mathbf{p} = \\sum_i \\mathbf{m_i} \\mathbf{v_i}$.
        Optionally only include the contribution of a subset of atoms.
        
        p = ds_momentum(self[, indices])
        Defined at DynamicalSystem.fpp lines 1005-1009
        
        Parameters
        ----------
        this : Dynamicalsystem
        indices : int array
        
        Returns
        -------
        p : float array
        """
        p = quippy._quippy.f90wrap_dynamicalsystem_module__ds_momentum(this=self._handle, indices=indices)
        return p
    
    def ds_add_thermostat(self, type_bn, t, gamma=None, q=None, tau=None, tau_cell=None, p=None, bulk_modulus_estimate=None, \
        cell_oscillation_time=None, nhl_tau=None, nhl_mu=None, massive=None, region_i=None, interface_call=False):
        """
        Add a new thermostat to this DynamicalSystem. 'type' should
        be one of the following thermostat types:
        
        * 'THERMOSTAT_NONE'
        * 'THERMOSTAT_LANGEVIN'
        * 'THERMOSTAT_NOSE_HOOVER'
        * 'THERMOSTAT_NOSE_HOOVER_LANGEVIN'
        * 'THERMOSTAT_LANGEVIN_NPT'
        * 'THERMOSTAT_LANGEVIN_PR'
        * 'THERMOSTAT_NPH_ANDERSEN'
        * 'THERMOSTAT_NPH_PR'
        * 'THERMOSTAT_LANGEVIN_OU'
        * 'THERMOSTAT_LANGEVIN_NPT_NB'
        
        'T' is the target temperature. 'Q' is the Nose-Hoover coupling constant. Only one
        of 'tau' or 'gamma' should be given. 'p' is the external
        pressure for the case of Langevin NPT.
        
        ds_add_thermostat(self, type_bn, t[, gamma, q, tau, tau_cell, p, bulk_modulus_estimate, cell_oscillation_time, nhl_tau, \
            nhl_mu, massive, region_i])
        Defined at DynamicalSystem.fpp lines 842-889
        
        Parameters
        ----------
        this : Dynamicalsystem
        type_bn : int32
        t : float64
        gamma : float64
        q : float64
        tau : float64
        tau_cell : float64
        p : float64
        bulk_modulus_estimate : float64
        cell_oscillation_time : float64
        nhl_tau : float64
        nhl_mu : float64
        massive : bool
        region_i : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_add_thermostat(this=self._handle, type_bn=type_bn, t=t, gamma=gamma, \
            q=q, tau=tau, tau_cell=tau_cell, p=p, bulk_modulus_estimate=bulk_modulus_estimate, \
            cell_oscillation_time=cell_oscillation_time, nhl_tau=nhl_tau, nhl_mu=nhl_mu, massive=massive, region_i=region_i)
    
    def ds_remove_thermostat(self, index_bn, interface_call=False):
        """
        ds_remove_thermostat(self, index_bn)
        Defined at DynamicalSystem.fpp lines 837-840
        
        Parameters
        ----------
        this : Dynamicalsystem
        index_bn : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_remove_thermostat(this=self._handle, index_bn=index_bn)
    
    def ds_print_thermostats(self, interface_call=False):
        """
        ds_print_thermostats(self)
        Defined at DynamicalSystem.fpp lines 1965-1967
        
        Parameters
        ----------
        this : Dynamicalsystem
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_print_thermostats(this=self._handle)
    
    def ds_set_barostat(self, type_bn, p_ext, hydrostatic_strain, diagonal_strain, finite_strain_formulation, tau_epsilon, \
        w_epsilon=None, t=None, w_epsilon_factor=None, thermalise=None, interface_call=False):
        """
        ds_set_barostat(self, type_bn, p_ext, hydrostatic_strain, diagonal_strain, finite_strain_formulation, tau_epsilon[, \
            w_epsilon, t, w_epsilon_factor, thermalise])
        Defined at DynamicalSystem.fpp lines 814-830
        
        Parameters
        ----------
        this : Dynamicalsystem
        type_bn : int32
        p_ext : float64
        hydrostatic_strain : bool
        diagonal_strain : bool
        finite_strain_formulation : bool
        tau_epsilon : float64
        w_epsilon : float64
        t : float64
        w_epsilon_factor : float64
        thermalise : bool
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_set_barostat(this=self._handle, type_bn=type_bn, p_ext=p_ext, \
            hydrostatic_strain=hydrostatic_strain, diagonal_strain=diagonal_strain, \
            finite_strain_formulation=finite_strain_formulation, tau_epsilon=tau_epsilon, w_epsilon=w_epsilon, t=t, \
            w_epsilon_factor=w_epsilon_factor, thermalise=thermalise)
    
    def ds_add_thermostats(self, type_bn, n, t=None, t_a=None, gamma=None, gamma_a=None, q=None, q_a=None, tau=None, \
        tau_a=None, region_i=None, interface_call=False):
        """
        ds_add_thermostats(self, type_bn, n[, t, t_a, gamma, gamma_a, q, q_a, tau, tau_a, region_i])
        Defined at DynamicalSystem.fpp lines 896-942
        
        Parameters
        ----------
        this : Dynamicalsystem
        type_bn : int32
        n : int32
        t : float64
        t_a : float array
        gamma : float64
        gamma_a : float array
        q : float64
        q_a : float array
        tau : float64
        tau_a : float array
        region_i : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_add_thermostats(this=self._handle, type_bn=type_bn, n=n, t=t, t_a=t_a, \
            gamma=gamma, gamma_a=gamma_a, q=q, q_a=q_a, tau=tau, tau_a=tau_a, region_i=region_i)
    
    def ds_update_thermostat(self, t=None, p=None, i=None, interface_call=False):
        """
        ds_update_thermostat(self[, t, p, i])
        Defined at DynamicalSystem.fpp lines 949-957
        
        Parameters
        ----------
        this : Dynamicalsystem
        t : float64
        p : float64
        i : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_update_thermostat(this=self._handle, t=t, p=p, i=i)
    
    def ds_add_atom_single(self, z, mass=None, p=None, v=None, a=None, t=None, error=None, interface_call=False):
        """
        ds_add_atom_single(self, z[, mass, p, v, a, t, error])
        Defined at DynamicalSystem.fpp lines 632-652
        
        Parameters
        ----------
        this : Dynamicalsystem
        z : int32
        mass : float64
        p : float array
        v : float array
        a : float array
        t : int array
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_add_atom_single(this=self._handle, z=z, mass=mass, p=p, v=v, a=a, t=t, \
            error=error)
    
    def ds_add_atom_multiple(self, z, mass=None, p=None, v=None, a=None, t=None, error=None, interface_call=False):
        """
        ds_add_atom_multiple(self, z[, mass, p, v, a, t, error])
        Defined at DynamicalSystem.fpp lines 657-709
        
        Parameters
        ----------
        this : Dynamicalsystem
        z : int array
        mass : float array
        p : float array
        v : float array
        a : float array
        t : int array
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_add_atom_multiple(this=self._handle, z=z, mass=mass, p=p, v=v, a=a, \
            t=t, error=error)
    
    def add_atoms(*args, **kwargs):
        """
        Add one or more atoms to this DynamicalSystem. Equivalent to 'Atoms%add_atoms',
        but also appends the number of degrees of freedom correctly.
        
        add_atoms(*args, **kwargs)
        Defined at DynamicalSystem.fpp lines 235-236
        
        Overloaded interface containing the following procedures:
          ds_add_atom_single
          ds_add_atom_multiple
        """
        for proc in [DynamicalSystem.ds_add_atom_multiple, DynamicalSystem.ds_add_atom_single]:
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
    
    def ds_remove_atom_single(self, i, error=None, interface_call=False):
        """
        ds_remove_atom_single(self, i[, error])
        Defined at DynamicalSystem.fpp lines 711-717
        
        Parameters
        ----------
        this : Dynamicalsystem
        i : int32
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_remove_atom_single(this=self._handle, i=i, error=error)
    
    def ds_remove_atom_multiple(self, atomlist_in, error=None, interface_call=False):
        """
        ds_remove_atom_multiple(self, atomlist_in[, error])
        Defined at DynamicalSystem.fpp lines 719-776
        
        Parameters
        ----------
        this : Dynamicalsystem
        atomlist_in : int array
        error : int32
        """
        quippy._quippy.f90wrap_dynamicalsystem_module__ds_remove_atom_multiple(this=self._handle, atomlist_in=atomlist_in, \
            error=error)
    
    def remove_atoms(*args, **kwargs):
        """
        Remove one or more atoms from this DynamicalSystem. Equivalent of 'Atoms%remove_atoms',
        but also amends the number of degrees of freedom correctly.
        
        remove_atoms(*args, **kwargs)
        Defined at DynamicalSystem.fpp lines 240-241
        
        Overloaded interface containing the following procedures:
          ds_remove_atom_single
          ds_remove_atom_multiple
        """
        for proc in [DynamicalSystem.ds_remove_atom_multiple, DynamicalSystem.ds_remove_atom_single]:
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
    
    @property
    def n(self):
        """
        Number of atoms
        
        Element n ftype=integer                                pytype=int32
        Defined at DynamicalSystem.fpp line 197
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__n(self._handle)
    
    @n.setter
    def n(self, n):
        quippy._quippy.f90wrap_dynamicalsystem__set__n(self._handle, n)
    
    @property
    def nsteps(self):
        """
        Number of integration steps
        
        Element nsteps ftype=integer                                pytype=int32
        Defined at DynamicalSystem.fpp line 198
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__nsteps(self._handle)
    
    @nsteps.setter
    def nsteps(self, nsteps):
        quippy._quippy.f90wrap_dynamicalsystem__set__nsteps(self._handle, nsteps)
    
    @property
    def nrigid(self):
        """
        Number of rigid bodies
        
        Element nrigid ftype=integer                                pytype=int32
        Defined at DynamicalSystem.fpp line 199
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__nrigid(self._handle)
    
    @nrigid.setter
    def nrigid(self, nrigid):
        quippy._quippy.f90wrap_dynamicalsystem__set__nrigid(self._handle, nrigid)
    
    @property
    def nconstraints(self):
        """
        Number of constraints
        
        Element nconstraints ftype=integer                                pytype=int32
        Defined at DynamicalSystem.fpp line 200
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__nconstraints(self._handle)
    
    @nconstraints.setter
    def nconstraints(self, nconstraints):
        quippy._quippy.f90wrap_dynamicalsystem__set__nconstraints(self._handle, nconstraints)
    
    @property
    def nrestraints(self):
        """
        Number of restraints
        
        Element nrestraints ftype=integer                                pytype=int32
        Defined at DynamicalSystem.fpp line 201
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__nrestraints(self._handle)
    
    @nrestraints.setter
    def nrestraints(self, nrestraints):
        quippy._quippy.f90wrap_dynamicalsystem__set__nrestraints(self._handle, nrestraints)
    
    @property
    def ndof(self):
        """
        Number of degrees of freedom
        
        Element ndof ftype=integer                                pytype=int32
        Defined at DynamicalSystem.fpp line 202
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__ndof(self._handle)
    
    @ndof.setter
    def ndof(self, ndof):
        quippy._quippy.f90wrap_dynamicalsystem__set__ndof(self._handle, ndof)
    
    @property
    def t(self):
        """
        Time
        
        Element t ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 203
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__t(self._handle)
    
    @t.setter
    def t(self, t):
        quippy._quippy.f90wrap_dynamicalsystem__set__t(self._handle, t)
    
    @property
    def dt(self):
        """
        Last time step
        
        Element dt ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 204
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__dt(self._handle)
    
    @dt.setter
    def dt(self, dt):
        quippy._quippy.f90wrap_dynamicalsystem__set__dt(self._handle, dt)
    
    @property
    def avg_temp(self):
        """
        Time-averaged temperature
        
        Element avg_temp ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 205
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__avg_temp(self._handle)
    
    @avg_temp.setter
    def avg_temp(self, avg_temp):
        quippy._quippy.f90wrap_dynamicalsystem__set__avg_temp(self._handle, avg_temp)
    
    @property
    def cur_temp(self):
        """
        Current temperature
        
        Element cur_temp ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 206
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__cur_temp(self._handle)
    
    @cur_temp.setter
    def cur_temp(self, cur_temp):
        quippy._quippy.f90wrap_dynamicalsystem__set__cur_temp(self._handle, cur_temp)
    
    @property
    def avg_time(self):
        """
        Averaging time, in fs
        
        Element avg_time ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 207
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__avg_time(self._handle)
    
    @avg_time.setter
    def avg_time(self, avg_time):
        quippy._quippy.f90wrap_dynamicalsystem__set__avg_time(self._handle, avg_time)
    
    @property
    def dw(self):
        """
        Increment of work done this time step
        
        Element dw ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 208
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__dw(self._handle)
    
    @dw.setter
    def dw(self, dw):
        quippy._quippy.f90wrap_dynamicalsystem__set__dw(self._handle, dw)
    
    @property
    def work(self):
        """
        Total work done
        
        Element work ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 209
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__work(self._handle)
    
    @work.setter
    def work(self, work):
        quippy._quippy.f90wrap_dynamicalsystem__set__work(self._handle, work)
    
    @property
    def epot(self):
        """
        Total potential energy
        
        Element epot ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 210
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__epot(self._handle)
    
    @epot.setter
    def epot(self, epot):
        quippy._quippy.f90wrap_dynamicalsystem__set__epot(self._handle, epot)
    
    @property
    def ekin(self):
        """
        Current kinetic energy
        
        Element ekin ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 211
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__ekin(self._handle)
    
    @ekin.setter
    def ekin(self, ekin):
        quippy._quippy.f90wrap_dynamicalsystem__set__ekin(self._handle, ekin)
    
    @property
    def wkin(self):
        """
        Current kinetic contribution to the virial
        
        Element wkin ftype=real(dp) pytype=float array
        Defined at DynamicalSystem.fpp line 212
        """
        array_ndim, array_type, array_shape, array_handle = quippy._quippy.f90wrap_dynamicalsystem__array__wkin(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        wkin = self._arrays.get(array_hash)
        if wkin is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if wkin.ctypes.data != array_handle:
                wkin = None
        if wkin is None:
            try:
                wkin = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_dynamicalsystem__array__wkin)
            except TypeError:
                wkin = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = wkin
        return wkin
    
    @wkin.setter
    def wkin(self, wkin):
        self.wkin[...] = wkin
    
    @property
    def ext_energy(self):
        """
        Extended energy
        
        Element ext_energy ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 213
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__ext_energy(self._handle)
    
    @ext_energy.setter
    def ext_energy(self, ext_energy):
        quippy._quippy.f90wrap_dynamicalsystem__set__ext_energy(self._handle, ext_energy)
    
    @property
    def thermostat_dw(self):
        """
        Increment of work done by thermostat
        
        Element thermostat_dw ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 214
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__thermostat_dw(self._handle)
    
    @thermostat_dw.setter
    def thermostat_dw(self, thermostat_dw):
        quippy._quippy.f90wrap_dynamicalsystem__set__thermostat_dw(self._handle, thermostat_dw)
    
    @property
    def thermostat_work(self):
        """
        Total work done by thermostat
        
        Element thermostat_work ftype=real(dp) pytype=float64
        Defined at DynamicalSystem.fpp line 215
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__thermostat_work(self._handle)
    
    @thermostat_work.setter
    def thermostat_work(self, thermostat_work):
        quippy._quippy.f90wrap_dynamicalsystem__set__thermostat_work(self._handle, thermostat_work)
    
    @property
    def initialised(self):
        """
        Element initialised ftype=logical pytype=bool
        Defined at DynamicalSystem.fpp line 216
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__initialised(self._handle)
    
    @initialised.setter
    def initialised(self, initialised):
        quippy._quippy.f90wrap_dynamicalsystem__set__initialised(self._handle, initialised)
    
    @property
    def random_seed(self):
        """
        RNG seed, used by 'ds_save_state' and 'ds_restore_state' only.Array members
        
        Element random_seed ftype=integer                                pytype=int32
        Defined at DynamicalSystem.fpp line 217
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__random_seed(self._handle)
    
    @random_seed.setter
    def random_seed(self, random_seed):
        quippy._quippy.f90wrap_dynamicalsystem__set__random_seed(self._handle, random_seed)
    
    @property
    def group_lookup(self):
        """
        Stores which group atom $i$ is inDerived type members
        
        Element group_lookup ftype=integer pytype=int array
        Defined at DynamicalSystem.fpp line 219
        """
        array_ndim, array_type, array_shape, array_handle = \
            quippy._quippy.f90wrap_dynamicalsystem__array__group_lookup(self._handle)
        array_hash = hash((array_ndim, array_type, tuple(array_shape), array_handle))
        group_lookup = self._arrays.get(array_hash)
        if group_lookup is not None:
            # Validate cached array: check data pointer matches current handle (issue #222)
            # Arrays can be deallocated and reallocated at same address, invalidating cache
            if group_lookup.ctypes.data != array_handle:
                group_lookup = None
        if group_lookup is None:
            try:
                group_lookup = f90wrap.runtime.get_array(f90wrap.runtime.sizeof_fortran_t,
                                        self._handle,
                                        quippy._quippy.f90wrap_dynamicalsystem__array__group_lookup)
            except TypeError:
                group_lookup = f90wrap.runtime.direct_c_array(array_type, array_shape, array_handle)
            self._arrays[array_hash] = group_lookup
        return group_lookup
    
    @group_lookup.setter
    def group_lookup(self, group_lookup):
        self.group_lookup[...] = group_lookup
    
    @property
    def atoms(self):
        """
        Element atoms ftype=type(atoms) pytype=Atoms
        Defined at DynamicalSystem.fpp line 221
        """
        atoms_handle = quippy._quippy.f90wrap_dynamicalsystem__get__atoms(self._handle)
        if tuple(atoms_handle) in self._objs:
            atoms = self._objs[tuple(atoms_handle)]
        else:
            atoms = Atoms.from_handle(atoms_handle)
            self._objs[tuple(atoms_handle)] = atoms
        return atoms
    
    @atoms.setter
    def atoms(self, atoms):
        atoms = atoms._handle
        quippy._quippy.f90wrap_dynamicalsystem__set__atoms(self._handle, atoms)
    
    @property
    def print_thermostat_temps(self):
        """
        Element print_thermostat_temps ftype=logical pytype=bool
        Defined at DynamicalSystem.fpp line 228
        """
        return quippy._quippy.f90wrap_dynamicalsystem__get__print_thermostat_temps(self._handle)
    
    @print_thermostat_temps.setter
    def print_thermostat_temps(self, print_thermostat_temps):
        quippy._quippy.f90wrap_dynamicalsystem__set__print_thermostat_temps(self._handle, print_thermostat_temps)
    
    def __str__(self):
        ret = ['<dynamicalsystem>{\n']
        ret.append('    n : ')
        ret.append(repr(self.n))
        ret.append(',\n    nsteps : ')
        ret.append(repr(self.nsteps))
        ret.append(',\n    nrigid : ')
        ret.append(repr(self.nrigid))
        ret.append(',\n    nconstraints : ')
        ret.append(repr(self.nconstraints))
        ret.append(',\n    nrestraints : ')
        ret.append(repr(self.nrestraints))
        ret.append(',\n    ndof : ')
        ret.append(repr(self.ndof))
        ret.append(',\n    t : ')
        ret.append(repr(self.t))
        ret.append(',\n    dt : ')
        ret.append(repr(self.dt))
        ret.append(',\n    avg_temp : ')
        ret.append(repr(self.avg_temp))
        ret.append(',\n    cur_temp : ')
        ret.append(repr(self.cur_temp))
        ret.append(',\n    avg_time : ')
        ret.append(repr(self.avg_time))
        ret.append(',\n    dw : ')
        ret.append(repr(self.dw))
        ret.append(',\n    work : ')
        ret.append(repr(self.work))
        ret.append(',\n    epot : ')
        ret.append(repr(self.epot))
        ret.append(',\n    ekin : ')
        ret.append(repr(self.ekin))
        ret.append(',\n    wkin : ')
        ret.append(repr(self.wkin))
        ret.append(',\n    ext_energy : ')
        ret.append(repr(self.ext_energy))
        ret.append(',\n    thermostat_dw : ')
        ret.append(repr(self.thermostat_dw))
        ret.append(',\n    thermostat_work : ')
        ret.append(repr(self.thermostat_work))
        ret.append(',\n    initialised : ')
        ret.append(repr(self.initialised))
        ret.append(',\n    random_seed : ')
        ret.append(repr(self.random_seed))
        ret.append(',\n    group_lookup : ')
        ret.append(repr(self.group_lookup))
        ret.append(',\n    atoms : ')
        ret.append(repr(self.atoms))
        ret.append(',\n    print_thermostat_temps : ')
        ret.append(repr(self.print_thermostat_temps))
        ret.append('}')
        return ''.join(ret)
    
    _dt_array_initialisers = []
    

def moment_of_inertia_tensor(self, origin=None, interface_call=False):
    """
    moi = moment_of_inertia_tensor(self[, origin])
    Defined at DynamicalSystem.fpp lines 1111-1132
    
    Parameters
    ----------
    this : Atoms
    origin : float array
    
    Returns
    -------
    moi : float array
    """
    moi = quippy._quippy.f90wrap_dynamicalsystem_module__moment_of_inertia_tensor(this=self._handle, origin=origin)
    return moi

def torque(pos, force, origin=None, interface_call=False):
    """
    tau = torque(pos, force[, origin])
    Defined at DynamicalSystem.fpp lines 1231-1244
    
    Parameters
    ----------
    pos : float array
    force : float array
    origin : float array
    
    Returns
    -------
    tau : float array
    """
    tau = quippy._quippy.f90wrap_dynamicalsystem_module__torque(pos=pos, force=force, origin=origin)
    return tau

def gaussian_velocity_component(m, t, interface_call=False):
    """
    Draw a velocity component from the correct Gaussian distribution for
    a degree of freedom with(effective) mass 'm' at temperature 'T'
    
    v = gaussian_velocity_component(m, t)
    Defined at DynamicalSystem.fpp lines 1406-1409
    
    Parameters
    ----------
    m : float64
    t : float64
    
    Returns
    -------
    v : float64
    """
    v = quippy._quippy.f90wrap_dynamicalsystem_module__gaussian_velocity_component(m=m, t=t)
    return v

def zero_angular_momentum(self, interface_call=False):
    """
    give the system a rigid body rotation so as to zero the angular momentum about the centre of mass
    
    zero_angular_momentum(self)
    Defined at DynamicalSystem.fpp lines 1437-1458
    
    Parameters
    ----------
    this : Atoms
    """
    quippy._quippy.f90wrap_dynamicalsystem_module__zero_angular_momentum(this=self._handle)

def distance_relative_velocity(self, i, j, interface_call=False):
    """
    Return the distance between two atoms and the relative velocity
    between them projected along the bond direction.
    This is useful for time dependent constraints.
    
    dist, rel_velo = distance_relative_velocity(self, i, j)
    Defined at DynamicalSystem.fpp lines 2486-2494
    
    Parameters
    ----------
    at : Atoms
    i : int32
    j : int32
    
    Returns
    -------
    dist : float64
    rel_velo : float64
    """
    dist, rel_velo = quippy._quippy.f90wrap_dynamicalsystem_module__distance_relative_velocity(at=self._handle, i=i, j=j)
    return dist, rel_velo

def arrays_angular_momentum(mass, pos, velo, origin=None, indices=None, interface_call=False):
    """
    Return the angular momentum of all the atoms in this DynamicalSystem, defined by
    $\\mathbf{L} = \\sum_{i} \\mathbf{r_i} \\times \\mathbf{v_i}$.
    
    l = arrays_angular_momentum(mass, pos, velo[, origin, indices])
    Defined at DynamicalSystem.fpp lines 1059-1083
    
    Parameters
    ----------
    mass : float array
    pos : float array
    velo : float array
    origin : float array
    indices : int array
    
    Returns
    -------
    l : float array
    """
    l = quippy._quippy.f90wrap_dynamicalsystem_module__arrays_angular_momentum(mass=mass, pos=pos, velo=velo, origin=origin, \
        indices=indices)
    return l

def arrays_momentum(mass, velo, indices=None, interface_call=False):
    """
    Return the total momentum $\\mathbf{p} = \\sum_i \\mathbf{m_i} \\mathbf{v_i}$.
    Optionally only include the contribution of a subset of atoms.
    
    p = arrays_momentum(mass, velo[, indices])
    Defined at DynamicalSystem.fpp lines 1021-1037
    
    Parameters
    ----------
    mass : float array
    velo : float array
    indices : int array
    
    Returns
    -------
    p : float array
    """
    p = quippy._quippy.f90wrap_dynamicalsystem_module__arrays_momentum(mass=mass, velo=velo, indices=indices)
    return p

def single_kinetic_energy(mass, velo, interface_call=False):
    """
    Return the kinetic energy given a mass and a velocity
    
    ke = single_kinetic_energy(mass, velo)
    Defined at DynamicalSystem.fpp lines 1177-1180
    
    Parameters
    ----------
    mass : float64
    velo : float array
    
    Returns
    -------
    ke : float64
    """
    ke = quippy._quippy.f90wrap_dynamicalsystem_module__single_kinetic_energy(mass=mass, velo=velo)
    return ke

def arrays_kinetic_energy(mass, velo, local_ke=None, interface_call=False):
    """
    Return the total kinetic energy given atomic masses and velocities
    
    ke = arrays_kinetic_energy(mass, velo[, local_ke])
    Defined at DynamicalSystem.fpp lines 1183-1191
    
    Parameters
    ----------
    mass : float array
    velo : float array
    local_ke : float array
    
    Returns
    -------
    ke : float64
    """
    ke = quippy._quippy.f90wrap_dynamicalsystem_module__arrays_kinetic_energy(mass=mass, velo=velo, local_ke=local_ke)
    return ke

def kinetic_energy(*args, **kwargs):
    """
    kinetic_energy(*args, **kwargs)
    Defined at DynamicalSystem.fpp lines 254-255
    
    Overloaded interface containing the following procedures:
      single_kinetic_energy
      arrays_kinetic_energy
    """
    for proc in [arrays_kinetic_energy, single_kinetic_energy]:
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
        "kinetic_energy compatible with the provided args:"
        "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))

def single_kinetic_virial(mass, velo, interface_call=False):
    """
    Return the kinetic virial given a mass and a velocity
    
    kv = single_kinetic_virial(mass, velo)
    Defined at DynamicalSystem.fpp lines 1219-1222
    
    Parameters
    ----------
    mass : float64
    velo : float array
    
    Returns
    -------
    kv : float array
    """
    kv = quippy._quippy.f90wrap_dynamicalsystem_module__single_kinetic_virial(mass=mass, velo=velo)
    return kv

def arrays_kinetic_virial(mass, velo, interface_call=False):
    """
    Return the total kinetic virial given atomic masses and velocities
    
    kv = arrays_kinetic_virial(mass, velo)
    Defined at DynamicalSystem.fpp lines 1225-1229
    
    Parameters
    ----------
    mass : float array
    velo : float array
    
    Returns
    -------
    kv : float array
    """
    kv = quippy._quippy.f90wrap_dynamicalsystem_module__arrays_kinetic_virial(mass=mass, velo=velo)
    return kv

def kinetic_virial(*args, **kwargs):
    """
    kinetic_virial(*args, **kwargs)
    Defined at DynamicalSystem.fpp lines 257-259
    
    Overloaded interface containing the following procedures:
      single_kinetic_virial
      arrays_kinetic_virial
    """
    for proc in [arrays_kinetic_virial, single_kinetic_virial]:
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
        "kinetic_virial compatible with the provided args:"
        "\n%s\nLast exception was: %s"%("\n".join(argTypes), exception))

def get_type_atom():
    """
    Element type_atom ftype=integer pytype=int32
    Defined at DynamicalSystem.fpp line 192
    """
    return quippy._quippy.f90wrap_dynamicalsystem_module__get__type_atom()

TYPE_ATOM = get_type_atom()

def get_type_constrained():
    """
    Element type_constrained ftype=integer pytype=int32
    Defined at DynamicalSystem.fpp line 193
    """
    return quippy._quippy.f90wrap_dynamicalsystem_module__get__type_constrained()

TYPE_CONSTRAINED = get_type_constrained()


_array_initialisers = []
_dt_array_initialisers = []


try:
    for func in _array_initialisers:
        func()
except ValueError:
    logger.debug('unallocated array(s) detected on import of module "dynamicalsystem_module".')

for func in _dt_array_initialisers:
    func()
