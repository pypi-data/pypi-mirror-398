# BSD 3-Clause License; see https://github.com/aaronm6/varray/blob/main/LICENSE
"""
varray (variable array): 

A light-weight array type that supports numpy-like arrays in which the last dimension has
variable length.

Why reinvent the wheel, when awkward (awk) arrays exist?  awk arrays are efficient and versatile
and are an excellent tool when one's needs align with the features they provide.  However, I 
found myself avoiding them in my own work for two reasons:

    1: awk arrays are IMMUTABLE, and hence read-only.  This means they're great to read from,
       but tricky to use if you actually want to use them in a script or notebook.  For
       example, a common usage of numpy arrays is to initialize an empty 2d array with 
       np.empty(...) and then fill in the rows in a loop.  This is possible with numpy
       arrays because they are mutable.  But one cannot do this with awk arrays.  This used 
       to be possible in earlier versions of awk, but this important functionality has since 
       been removed.  This is my main motivation for creating varray: awk arrays' 
       immutability makes them unusable for the vast majority of my own use cases.
    2: awk is a large package that involves c++ code and all of its plethora of functionality
       might not always be needed.  Hence the desire for a light-weight alternative that
       involves python code only.

The focus here is on a simple and light-weight implementation of limited capabilities, 
rather than a breadth of many capabilities.  For example, numpy arrays and ak arrays support 
efficient slicing, where a slice of an array produces a new "view" to the underlying data, 
but does not copy the data.  So too does varray work with array "views".  Data are only 
copied when required.

In addition to creating a varray with the class constructor, one can create a varray with 
one of the numpy-inspired creation functions: empty, ones, and zeros (and 'empty_like', 
etc.), which allocated the space, and then fill in the values later.

Contents:

Class:
    varray : variable-array class. See its docstring for instantiation syntax

Functions:
    empty           varray creation routine
    empty_like      varray creation routine
    ones            varray creation routine
    ones_like       varray creation routine
    zeros           varray creation routine
    zeros_like      varray creation routine
    save            save varrays, numpy arrays, numpy masked arrays to *.vrz file
    load            load items from file that was created by varray.save
    row_concat      concatenate multiple varrays along the 0th axis
    inner_concat    concatenate multiple varrays along an inner axis (not 0th, not last)
    inner_stack     stack multiple arrays along an inner axis (not 0th, not last)

Misc:
    version
    version_tuple
"""
import numpy as np
import operator
import re
from numbers import Number

__all__ = ['varray','empty','empty_like','ones','ones_like','zeros','zeros_like',
    'save','load','row_concat','inner_concat','inner_stack']


version = __version__ = '1.0.3'
version_tuple = __version_tuple__ = tuple([int(item) for item in __version__.split('.')])

_linewidth = np.get_printoptions()['linewidth']
_udecline = np.frompyfunc(lambda x, y: x-1 if x>0 else 0, 2, 1)
_ufindrows = np.frompyfunc(lambda x, y: x-1 if y==0 else y, 2, 1)
_urowindex = np.frompyfunc(lambda x, y: x if y==-1 else y, 2, 1)
_ucolindex = np.frompyfunc(lambda x, y: x+1 if y<0 else 0, 2, 1)

_binops = ('add','and','mul','pow','sub','truediv','floordiv','eq','lt','gt','le','ge','mod','or','xor')
_unops = ('abs','neg','pos','conjugate','conj')
_rowops_reduce = ('all','any','argmax','argmin','max','mean','min','prod','std','sum','var')
_rowops_accumulate = ('cumprod','cumsum')

def r_explore_nesting(nested_list, depth=0):
    """
    Check that the nesting of an iterable is good, i.e. the depth is the same for all elements
    
    If nesting is good: returns depth.  
    If nesting is bad: raises ValueError
    
        A non-nested list (i.e. [1,2,3]) has depth of 1.
        A singly-nested list (i.e. [[1,2],[3],[4,5,6]]) has depth of 2
        etc.
    If nesting is bad: raises ValueError
        Bad nesting means that all elements are not the same depth. For example,
        [ [1,2], [[3,4],[5,6]] ] is bad because the first element is a non-nested list,
        but the second element is a singly-nested list.
        [[1,2],3,[4,5,6]] is bad nesting
    This function uses recursion; in order to prevent runaway recursion, the function
    raises a RecursionError if the depth of recursion is more than 10.
    """
    if depth > 10:
        raise RecursionError("Depth is too big; recursion is going nuts")
    if hasattr(nested_list, '__len__'):
        if len(nested_list) == 0:
            return None
        depths = [r_explore_nesting(item, depth=depth+1) for item in nested_list]
        if len(set((item for item in depths if item))) > 1:
            raise ValueError("Nesting is bad")
        else:
            return depths[0]
    else:
        return depth

def unpack_nested_list(nested_list):
    """
    Take a nested list and return a [possibly multidimensional] darray and sarray
    """
    darray = np.array([item for sublist in nested_list for item in sublist])
    darray_ndim = darray.ndim
    re_pose = [(item+1)%darray_ndim for item in range(darray_ndim)]
    darray = darray.transpose(*re_pose)
    sarray = np.array([len(item) for item in nested_list], dtype=np.int16)
    return darray, sarray

def unpack_masked_array(ma_obj):
    """
    Take a masked array and turn it into a darray and sarray
    """
    ndim = ma_obj.ndim
    ma_shape = ma_obj.shape
    final_init_dims = ma_shape[1:-1]
    transpose_list = [(item+1)%(ndim-1) for item in range(ndim-1)] + [ndim-1]
    transpose_tuple = tuple(transpose_list)
    ma_manipulated = ma_obj.transpose(transpose_tuple).reshape(*final_init_dims,-1)
    ma_notmask = ~ma_manipulated.mask
    final_slice = (0,)*(ma_manipulated.ndim-1) + (slice(None,None,None),)
    d_array = ma_manipulated.data[...,ma_notmask[final_slice]]
    s_array_item = (slice(None,None,None),)+(0,)*(ndim-2)+(slice(None,None,None),)
    s_array = (~ma_obj.mask[(slice(None,None,None),)+(0,)*(ndim-2)+(slice(None,None,None),)]).sum(axis=-1)
    if not np.issubdtype(s_array.dtype, np.dtype('int16')):
        s_array = s_array.astype(np.int16)
    return d_array, s_array

def expand_slices(item, varray_dims):
    """
    Takes an item passed to __getitem__ and expands it to be a full tuple of indices.
    
    For example, if the varray has 4 dimensions and [...,1,:] is given,
    this needs to be expanded to [:,:,1,:]
    or if [0] is given, this needs to be expanded to [0,:,:,:]
    This function does that.
    
    Inputs:
               item: raw item received in __getitem__
        varray_dims: the number of dimensions of the varray, which will be one more than
                     the number of dimensions of its darray.
    Output:
           new_item: A drop-in replacement that has expanded the raw item.
    """
    s_full = slice(None, None, None) # full slice
    if not isinstance(item, tuple):
        item = (item,)
    if len(item) > varray_dims:
        raise IndexError("Too many indices given")
    #if item.count(Ellipsis) > 1: # <-- doesn't work if numpy array in item
    Ellipsis_count = [1 for el in item if el is Ellipsis]
    if len(Ellipsis_count) > 1:
        raise IndexError("An index can only have a single ellipsis ('...')")
    if Ellipsis_count:
        #idx = item.index(Ellipsis) # <-- doesn't work if numpy array in item
        idx, = [yy for xx,yy in zip(item,range(len(item))) if xx is Ellipsis]
        return item[:idx] + (s_full,)*(varray_dims-len(item)+1) + item[(idx+1):]
    if len(item) == varray_dims:
        return item
    return item + (s_full,)*(varray_dims-len(item))

def check_shape_consistency(va1, va2):
    """
    Given two varray objects (va1 and va2) check that their shapes are the same.
    
    Returns True if they have the same shape, or False if not
    
    getting the shape of either array can throw an exception if their darray or sarray have
    not been set, so that exception will propagate here.
    """
    if not isinstance(va1, varray):
        raise TypeError("input va1 must be a varray object")
    if not isinstance(va2, varray):
        raise TypeError("input va2 must be a varray object")
    va1_shape = va1.shape
    va2_shape = va2.shape
    if len(va1_shape) != len(va2_shape):
        return False
    reg_dims_same = all([x==y for x, y in zip(va1_shape, va2_shape)])
    if len(va1.sarray) != len(va2.sarray):
        return False
    var_dims_same = np.all(va1.sarray == va2.sarray)
    return reg_dims_same and var_dims_same

def check_bool_shape_validity(va_data, va_bool):
    """
    If a boolean varray is given as an index via square brackets, its shape must be appropriate
    for the varray object to be sliced.  The boolean varray can only be 2d (with the second
    dimension of variable size).  If this boolean varray is being applied to a varray of >2d,
    it is essentially broadcast to the full varray size.
    
    if the shapes are valid for such boolean slicing, return True
    otherwise, return False (will not raise an exception).
    
    For example, if va_data is 3d with shape
    >>> va_data.shape
    (34, 2, 3, None)
    and sarray
    >>> va_data.sarray
    array([2,6,5,8,11,1,3])
    Then the boolean varray, "va_bool" applied via:
    >>> va_data[va_bool]
    must have shape:
    >>> va_bool.shape
    (34, None)
    and sarray the same as va_data's:
    >>> np.all(va_data.sarray == va_bool.sarray)
    True
    """
    sarray_data = va_data.sarray
    sarray_bool = va_bool.sarray
    if len(sarray_data) != len(sarray_bool):
        return False
    if np.all(sarray_data == sarray_bool):
        return True
    return False

class repr_precision_context:
    def __init__(self, **kwargs):
        self.current_settings = np.get_printoptions()
        self.new_settings = kwargs
        for item in kwargs:
            if item not in self.current_settings:
                raise KeyError(f"Setting '{item}' not listed in np.get_printoptions")
    def __enter__(self):
        np.set_printoptions(**self.new_settings)
    def __exit__(self, thetype, thevalue, thetraceback):
        modified_originals = {key:self.current_settings[key] for key in self.new_settings}
        np.set_printoptions(**modified_originals)

class _varray_base:
    def __init__(self, /, nested_list=None, *, darray=None, sarray=None, dtype=None, csarray=None):
        self.cls_name = self.__class__.__name__ #dynamically set because another class inherits from this one
        if not [item for item in (nested_list, darray, sarray) if item is not None]:
            raise ValueError(f"Some kind of data must be given to instantiate the {self.cls_name}")
        if (darray is None or sarray is None) and (csarray is not None):
            raise TypeError("keyword 'csarray' can be given only if darray and sarray are given")
        if isinstance(nested_list, (list, tuple)):
            r_explore_nesting(nested_list) # not doing anything with this fn's output, just checking nesting
            self._darray, self._sarray = unpack_nested_list(nested_list)
        elif isinstance(nested_list, np.ma.core.MaskedArray):
            self._darray, self._sarray = unpack_masked_array(nested_list)
        elif isinstance(nested_list, np.ndarray):
            self._darray, self._sarray = unpack_masked_array(np.ma.masked_array(nested_list))
        else:
            self._darray = darray
            self._sarray = sarray
        if dtype is not None:
            self._darray = self._darray.astype(dtype)
        if self._sarray.dtype != np.uint16:
            self._sarray = self._sarray.astype(np.uint16)
        if csarray is None:
            self._csarray = np.r_[0,self._sarray[:-1]].cumsum()
        else:
            self._csarray = csarray
        if self._csarray.dtype != np.uint32:
            self._csarray = self._csarray.astype(np.uint32)
        self.max_lines = 20
        self.base = None
        self._repr_flag = False
        fill_value = None
        if np.issubdtype(self.dtype, np.floating):
            fill_value = np.nan
        elif np.issubdtype(self.dtype, np.integer):
            fill_value = np.iinfo(self.dtype).min
        elif np.issubdtype(self.dtype, np.bool_):
            fill_value = False
        self._fill_value = fill_value
        self.float_precision = 3
    @property
    def dtype(self):
        return self._darray.dtype
    @property
    def sarray(self):
        return self._sarray
    @property
    def ndim(self):
        if hasattr(self._darray, 'ndim'):
            return self._darray.ndim + 1
        return None
    @property
    def size(self):
        if not hasattr(self._darray, 'shape'):
            raise TypeError(f"Cannot determine {self.cls_name} size until darray is set")
        if len(self._sarray) == 0:
            raise TypeError(f"Cannot determine {self.cls_name} size if sarray is not set")
        if not hasattr(self._sarray, 'sum'):
            raise TypeError(f"Cannot determine {self.cls_name} size if sarray is not a numpy array")
        darray_shape = self._darray.shape
        return np.prod(darray_shape[:-1]) * self._sarray.sum()
    @property
    def shape(self):
        if self._sarray is None:
            raise TypeError(f"Cannot determine {self.cls_name} shape if it has no sarray")
        if self._darray is None:
            raise TypeError(f"Cannot determine {self.cls_name} shape if it has no darray")
        if not hasattr(self._darray,'shape'):
            raise TypeError(f"Cannot determine {self.cls_name} shape if its darray has no shape")
        darray_shape = self._darray.shape
        last_dim = None
        if len(set(self._sarray)) == 1:
            last_dim = self._sarray[0]
        #return (len(self),) + darray_shape[:-1] + (tuple(self._sarray),)
        return (len(self),) + darray_shape[:-1] + (last_dim,)
    def astype(self, new_type):
        return self.__class__(darray=self.flatten(), sarray=self.sarray, dtype=new_type)
    def _get_col_slice(self, row_idx, last_idx):
        """
        When a single row is indexed, i.e. the first index is an integer, then the output
        of __getitem__ should be a numpy array (not a varray).  Likewise, when given as
        indices in __setitem__ then the desired row should be settable with a numpy array.
        
        We therefore need to determine what slice to apply to the darray.  This function
        determines this (since it's the same operation required for both __getitem__ and
        __setitem__).
        """
        if not np.issubdtype(type(row_idx), np.integer):
            raise ValueError("_get_col_slice can only accept an integer for input 'row_idx'")
        if np.issubdtype(type(last_idx), np.integer):
            i_start, i_stop, i_step = last_idx, last_idx+1, 1
        elif isinstance(last_idx, slice):
            i_start, i_stop, i_step = (getattr(last_idx,item) for item in ('start','stop','step'))
        if i_start is None:
            i_start = 0
        if i_start > self._sarray[row_idx]:
            raise IndexError(f"Col index {i_start} requested but row {row_idx} only has {self._sarray[row_idx]}")
        if i_stop is None:
            i_stop = self._sarray[row_idx]
        i_stop = min(i_stop, self._sarray[row_idx])
        if i_step is None:
            i_step = 1
        col_slice = slice(i_start+self._csarray[row_idx], i_stop+self._csarray[row_idx], i_step)
        return col_slice
    def __getitem__(self, item):
        varray_dims = self.ndim
        if self._darray is None:
            raise IndexError("Cannot access array until it has data")
        if isinstance(item, self.__class__) and np.issubdtype(item.dtype, np.bool_):
            if not check_bool_shape_validity(self, item):
                raise IndexError("A boolean varray in __getitem__ must have a valid shape")
            new_sarray = item.to_ma().sum(axis=-1)
            new_darray = self.flatten()[...,item.flatten()]
            return self.__class__(darray=new_darray, sarray=new_sarray)
        item = expand_slices(item, varray_dims)
        first_idx, middle_idx, last_idx = item[0], item[1:-1], item[-1]
        if np.issubdtype(type(first_idx), np.integer):
            column_slice = self._get_col_slice(first_idx, last_idx)
            full_item = self._darray[middle_idx + (column_slice,)]
            if (full_item.size == 1) and (not self._repr_flag):
                full_item, = full_item
            if self._repr_flag:
                self._repr_flag = False
            return full_item
        i_start, i_stop, i_step = None, None, None
        if np.issubdtype(type(last_idx), np.integer):
            i_start, i_stop = last_idx, last_idx+1
        elif isinstance(last_idx, slice):
            i_start, i_stop, i_step = (getattr(last_idx, item) for item in ('start','stop','step'))
        else:
            raise IndexError("Last index must be an integer or a slice object")
        if i_start is None:
            i_start = 0
        if i_stop is None:
            # set i_stop to the max possible integer of sarray's type
            i_stop = np.iinfo(self._sarray.dtype).max
        if i_step is None:
            i_step = 1
        if i_step != 1:
            raise IndexError("Using any step size in the last dimension other than None or 1 is not allowed")
        use_sarray = np.where(self._sarray<i_start, i_start, self._sarray)
        use_sarray = np.where(use_sarray>i_stop, i_stop, use_sarray) - i_start
        use_sarray = use_sarray[first_idx]
        use_csarray = self._csarray + i_start
        use_csarray = use_csarray[first_idx]
        outvar = self.__class__(darray=self._darray[middle_idx], sarray=use_sarray, csarray=use_csarray)
        if self.base is None:
            outvar.base = self
        else:
            outvar.base = self.base
        return outvar        
    def __setitem__(self, item, val):
        varray_dims = self._darray.ndim + 1
        item = expand_slices(item, varray_dims)
        if np.issubdtype(type(item[0]), np.integer):
            first_idx, middle_idx, last_idx = item[0], item[1:-1], item[-1]
            column_slice = self._get_col_slice(first_idx, last_idx)
            self._darray[middle_idx + (column_slice,)] = val
        else:
            if not (isinstance(val, self.__class__) or isinstance(val, Number)):
                raise TypeError(f"Setting data in this way must be done with another {self.cls_name} or a number")
            if isinstance(val, self.__class__) and not check_shape_consistency(self[item], val):
                raise ValueError(f"Setting data can only be done with a {self.cls_name} of the same shape")
            if item[-1] != slice(None, None, None):
                raise IndexError("Setting data in this way can only be done on the full row")
            tag_array = np.zeros(self._darray.shape[-1], dtype=int)
            tag_array[self._csarray[item[0]]] = self._sarray[item[0]]
            tag_array = _ufindrows.accumulate(tag_array)
            cut_used_rows = tag_array>0
            if isinstance(val, self.__class__):
                self._darray[item[1:-1]+(cut_used_rows,)] = val.flatten()
            else:
                self._darray[item[1:-1]+(cut_used_rows,)] = val
    def __repr__(self):
        numlines = min(len(self), self.max_lines)
        outstr = f'{self.cls_name}(['
        pad_space = len(outstr)
        with repr_precision_context(precision=self.float_precision):
            for k in range(numlines):
                self._repr_flag = True
                entry_str = '\n'.join([' '*pad_space + item for item in str(self[k]).split('\n')])
                if k==0:
                    entry_str = entry_str[pad_space:]
                entry_str += '\n' * (self._darray.ndim)
                outstr += entry_str
            if len(self) > self.max_lines:
                outstr = outstr.rstrip(' \n')
                outstr += f'\n... ({len(self) - self.max_lines} more rows)\n'
            else:
                outstr = outstr.rstrip(' \n') + f'], dtype={str(self.dtype)})'
        return outstr
    def __str__(self):
        row_dim = self.shape[1:-1]
        if not row_dim:
            row_dim = (1,)
        return f"{self.cls_name} with {len(self)} rows of " + str(row_dim).strip('(),') + ' x N'
    def __len__(self):
        return len(self._sarray)
    def _reduce_darray(self):
        tag_array = np.zeros(self._darray.shape[-1], dtype=np.uint32)
        cut_nonempty_rows = self._sarray > 0
        tag_array[self._csarray[cut_nonempty_rows]] = self._sarray[cut_nonempty_rows]
        tag_array = _ufindrows.accumulate(tag_array)
        cut_used_rows = tag_array>0
        return self._darray[...,cut_used_rows]
    def __copy__(self):
        return self.__class__(darray=self.flatten(), sarray=self.sarray.copy())
    def copy(self):
        return self.__copy__()
    def __bool__(self):
        return self is not None
    def flatten(self):
        """
        Not completely flatten, in the numpy sense.  This essentially produces a copy of the
        part of the darray that is in use.
        """
        return self._reduce_darray()
    def to_masked_array(self):
        return self.to_ma()
    def to_ma(self):
        """
        Take the variable dimension (the last one), expand it for all
        rows to be the length of the last one.  It is now a regular array
        and can be represented as a numpy array object.  The expanded
        elements are filled in with a value that is appropriate for the
        dtype.  The result is a numpy masked array, with only valid entries
        showing.
        """
        rdarray = self._reduce_darray()
        tag_array = np.zeros((*rdarray.shape[:-1], len(self._sarray), self._sarray.max()), dtype=self._sarray.dtype)
        sarray_item = (np.newaxis,)*(rdarray.ndim-1) + (slice(None, None, None),)
        tag_array[..., 0] = self._sarray[sarray_item]
        tag_cut = _udecline.accumulate(tag_array, axis=-1).astype(self._sarray.dtype) > 0
        new_array = np.full_like(tag_array, self._fill_value, dtype=self.dtype)
        new_array[tag_cut] = rdarray.flatten()
        dims = new_array.ndim
        transpose_dims = (dims-2, *range(dims-2), dims-1)
        new_array = new_array.transpose(transpose_dims).squeeze()
        new_mask = ~tag_cut.transpose(transpose_dims).squeeze()
        return np.ma.masked_array(data=new_array, mask=new_mask)
    def get_row_index(self):
        """
        Returns an array of the same shape that indicates the column of each entry
        """
        tag_array = -np.ones_like(self.flatten(), dtype=np.int32)
        cs_index = np.r_[:len(self._csarray)]
        tag_array[...,cs_index] = cs_index
        return _urowindex.accumulate(tag_array, axis=-1).astype(np.int32)
    def get_col_index(self):
        """
        Returns an array of the same shape that indicates the column of each entry
        """
        tag_array = -np.ones_like(self.flatten(), dtype=np.int32)
        tag_array[..., self._csarray] = 0
        return _ucolindex.accumulate(tag_array, axis=-1).astype(np.int32)

class varray(_varray_base, np.lib.mixins.NDArrayOperatorsMixin):
    """
    Create a varray.
    
    Constructor Parameters
    ----------------------
    nested_array : (optional) list of arrays or numpy masked array
        If a list is given, it should be a nested list that represents the varray.
        If a masked array is given, the resulting varray will essentially be the same
        size but with the masked elements removed.
    darray : None or 1d array or list or tuple (optional, keyword argument)
        The array that holds all the data values of the varray.
    sarray : None or 1d array of ints (or list or tuple) (optional, keyword argument)
        The array of row lengths; this would be the second dimension in a regular 2d array
    dtype : data-type (optional, keyword argument)
        The data type of the elements of darray.  Default is np.float64
    csarray : ndarray (optional, keyword argument)
        Should not be provided by the user

    Class methods and attributes
    ----------------------------
    shape : property (tuple)
        A tuple containing the length of each row
    dtype : property (type)
        The dtype of the data contained in the varray
    size  : property (int)
        Number of elements
    flatten() : numpy.ndarray
        Returns the data numpy array with the 0th dimension removed.  This works lightly different
        than the numpy version of this function.
    astype(type) : varray
        Works just like the numpy.ndarray version of this.  Returns a version of the varray
        with the dtype as specified.
    get_flat_row_index(): numpy.ndarray
        Returns an numpy array (dtype=np.uint32) the same size as the flattened array, whose elements
        indicate which row each element of the flattened array came from.
    get_flat_col_index(): numpy.ndarray
        Returns an numpy array (dtype=np.uint32) the same size as the flattened array, whose elements
        indicate which column each element of the flattened array came from.
    copy() : method
        Returns a copy of the current varray (using `ndarray.copy` under the hood).
    serialize_as_numpy_arrays(array_name='va') : method
        Serializes the data and shape arrays into a dict object containing two numpy arrays, so
        that they can be saved to disk.
    to_masked_array() : np.masked_array
        Returns a version of the varray in the form of a masked array.  The returned varray's last
        dimension (the variable one) is expanded to its largest element and the added elements are
        masked.
    to_ma() : np.masked_array
        Alias for to_masked_array
    get_row_index(): me
    
    Examples
    --------
    Example 1:
    >>> import varray as va
    >>> nested_list = [[1,2,3],[4,5],[6,7,8,9],[10,11,12]]
    >>> my_varray = va.varray(nested_list)
    >>> my_varray
    varray([[1. 2. 3.]
            [4. 5.]
            [6. 7. 8. 9.]
            [10. 11. 12.]], dtype=float64)
    >>> my_varray.shape
    (4, None)
    
    Example 2:
    >>> my_varray = np.empty((3,2,4,3))
    >>> my_varray[0,:] = np.r_[1,2,3]
    >>> my_varray[1,:] = np.r_[4,5]
    >>> my_varray[2,:] = np.r_[6,7,8,9]
    >>> my_varray[3,:] = np.r_[10,11,12]
    >>> my_varray
    varray([[1. 2. 3.]
            [4. 5.]
            [6. 7. 8. 9.]
            [10. 11. 12.]], dtype=float64)
    <slicing, access>
    >>> my_varray[2] #grab the third row
    array([6., 7., 8., 9.])
    >>> my_varray[:,0] # grab the first element from each row
    varray([[1.]
            [4.]
            [6.]
            [10.]], dtype=float64)
    >>> my_varray[:,2] # grab the third element from each row 
    varray([[3.]
            []
            [8.]
            [12.]], dtype=float64)
    <note that rows with less than 2 elements are empty>
    
    Example 3:
    >>> darray1 = np.arange(10.)
    >>> sarray1 = np.array([2, 3, 1, 4])
    >>> my_varray = va.varray(darray=darray1, sarray=sarray1)
    >>> my_varray
    varray([[0. 1.]
            [2. 3. 4.]
            [5.]
            [6. 7. 8. 9.]], dtype=float64)
    
    Example 4:
    >>> darray2 = np.vstack([arange(10.), arange(100.,110.)])
    >>> sarray1 = np.array([2, 3, 1, 4])
    >>> my_varray = va.varray(darray=darray2, sarray=sarray1)
    >>> my_varray  # each "row" is a 2xN numpy array
    varray([[[  0.   1.]
             [100. 101.]]
    
            [[  2.   3.   4.]
             [102. 103. 104.]]
    
            [[  5.]
             [105.]]
    
            [[  6.   7.   8.   9.]
             [106. 107. 108. 109.]]], dtype=float64)
    >>> my_varray[:,:,:2] # same as my_varray[...,:2]
    varray([[[  0.   1.]
             [100. 101.]]
    
            [[  2.   3.]
             [102. 103.]]
    
            [[  5.]
             [105.]]
    
            [[  6.   7.]
             [106. 107.]]], dtype=float64)
    >>> my_varray[:,0,:]
    varray([[100. 101.]
            [102. 103. 104.]
            [105.]
            [106. 107. 108. 109.]], dtype=float64)    
    """
    def _binary_op(self, other, op_name):
        if isinstance(other, self.__class__) and (not check_shape_consistency(self, other)):
            raise ValueError("Cannot do arithmetic on {self.cls_name}s of different shapes")
        other_use = other.flatten() if isinstance(other, self.__class__) else other
        new_darray = getattr(operator,op_name)(self.flatten(), other_use)
        return self.__class__(darray=new_darray, sarray=self._sarray)
    def _rbinary_op(self, other, op_name):
        if isinstance(other, self.__class__) and (not check_shape_consistency(self, other)):
            raise ValueError("Cannot do arithmetic on {self.cls_name} of different shapes")
        other_use = other.flatten() if isinstance(other, self.__class__) else other
        new_darray = getattr(operator,op_name)(other_use, self.flatten())
        return self.__class__(darray=new_darray, sarray=self._sarray)
    def _unary_op(self, op_name):
        new_darray = self._reduce_darray()
        if hasattr(np, op_name):
            return self.__class__(darray=getattr(np,op_name)(new_darray), sarray=self._sarray)
        elif hasattr(operator, op_name):
            return self.__class__(darray=getattr(operator,op_name)(self._darray), sarray=self._sarray)
        else:
            raise TypeError(f"Function {op_name} not recognized")
    def _row_op_reduce(self, op_name, **kwargs):
        self_ma = self.to_ma()
        return np.asarray(getattr(self_ma, op_name)(**kwargs).data)
    def _row_op_accumulate(self, op_name, **kwargs):
        self_ma = self.to_ma()
        return self.__class__(getattr(self_ma,op_name)(**kwargs))
    def __array__(self, dtype=None, copy=None):
        if copy is False:
            raise ValueError("copy=False is not allowed")
        new_npy_array = self.to_ma().data
        if dtype is not None:
            new_npy_array = new_npy_array.astype(dtype)
        return new_npy_array
    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        scalars = []
        for item in inputs:
            if isinstance(item, Number):
                scalars.append(item)
            elif isinstance(item, self.__class__):
                scalars.append(item.flatten())
            else:
                return NotImplemented
        return self.__class__(darray=ufunc(*scalars, **kwargs), sarray=self.sarray)
    def __array_function__(self, func, types, args, kwargs):
        return self.__class__(func(args[0].to_ma(), *args[1:], **kwargs))
    def serialize_as_numpy_arrays(self, array_name='va'):
        """
        Since varrays are simply wrappers of a pair of numpy arrays, we can just use numpy's savez
        and savez_compressed if we want to save them.  But, like numpy arrays, the array itself
        is just a view to an underlying region of memory.  That view may or may not pull elements
        that are contiguous in memory, and the view may not take all elements of the memory region,
        if e.g. one array is produced by slicing another array.  One therefore needs to produce
        a copy of the array where the data *are* contiguous, so that one is only saving the data
        that one wants.  Here too, we must produce a varray whose underlying data and shape arrays
        are reduced.
        Input:
            array_name : the label that one wants the two arrays to be saved as.  
            
        Output:
            A dict object with two keys: 
                <array_name>_d (1d numpy array containing the varray data)
                <array_name>_s (1d numpy array containing the varray row lengths)
        The dict object can then be given to e.g. np.savez_compressed:
        >>> myvarray = varray(...)
        >>> va_serialized = myvarray.serialize_as_numpy_arrays(array_name='myvarray')
        >>> np.savez_compressed('filename.npz', **va_serialized)
        
        One can save more than one array and more than one varray:
        >>> np.savez_compressed('filename.npz', ndarray_1=ndarray_1, **va1_serialized, **va2_serialized)
        
        To then load these:
        >>> d = np.load('filename.npz')
        >>> myvarray = varray(darray=d['myarray_d'], sarray=d['myarray_s'])
        """
        darray_name = f'va__{array_name}_d'
        sarray_name = f'va__{array_name}_s'
        return {darray_name:self.flatten(), sarray_name:self.sarray.copy()}

'''
# Binary-operation definitions all follow the same framework, so we define these in a loop
for op_name in _binops:
    def method(self, other, op=op_name):
        return self._binary_op(other, op)
    setattr(varray, f'__{op_name}__', method)
    def rmethod(self, other, op=op_name):
        return self._rbinary_op(other, op)
    setattr(varray, f'__r{op_name}__', rmethod)

# Similar for unitary operations
for op_name in _unops:
    def method(self, op=op_name):
        return self._unary_op(op)
    #setattr(varray, f'__{op_name}__', method)
    setattr(varray, f'__{op_name}__', method)
'''
# Similar for row-wise operations that reduce
for op_name in _rowops_reduce:
    def method(self, op=op_name, **kwargs):
        return self._row_op_reduce(op, **kwargs)
    setattr(varray, op_name, method)

for op_name in _rowops_accumulate:
    def method(self, op=op_name, **kwargs):
        return self._row_op_accumulate(op, **kwargs)
    setattr(varray, op_name, method)

def save(file_name, **kwargs):
    """
    Save a dict of varrays and/or numpy arrays into a file.  varrays and arrays are given
    as keyword arguments.  So if we had e.g. varrays called 'va1' and 'va2', and we wanted
    to save them named as such, we would do:
    >>> va.save('thefile.vrz', va1=va1, va2=va2)
    """
    save_dict = {}
    for key in kwargs:
        if isinstance(kwargs[key], varray):
            save_dict.update(kwargs[key].serialize_as_numpy_arrays(array_name=key))
        elif isinstance(kwargs[key], np.ma.core.MaskedArray):
            dname = f'ma__{key}_d'
            mname = f'ma__{key}_m'
            save_dict.update({dname:kwargs[key].data, mname:kwargs[key].mask})
        elif isinstance(kwargs[key], np.ndarray):
            save_dict.update({key: kwargs[key]})
        else:
            raise TypeError("Only varrays and numpy arrays (masked and normal) can be saved")
    if not file_name.endswith('.vrz'):
        file_name += '.vrz'
    with open(file_name, 'wb') as ff:
        np.savez_compressed(ff, **save_dict)

def _unpack_vrz_file(d_file):
    d = dict(d_file)
    va_names = [re.findall(r'va__(.*)_d',item)[0] for item in d if re.match(r'va__.*_d',item)]
    ma_names = [re.findall(r'ma__(.*)_d',item)[0] for item in d if re.match(r'ma__.*_d',item)]
    array_dict = {}
    for va_name in va_names:
        temp_va = varray(darray=d.pop(f'va__{va_name}_d'), sarray=d.pop(f'va__{va_name}_s'))
        array_dict[va_name] = temp_va
    for ma_name in ma_names:
        temp_ma = np.ma.masked_array(d.pop(f'ma__{ma_name}_d'), mask=d.pop(f'ma__{ma_name}_s'))
        array_dict[ma_name] = temp_ma
    array_dict.update(d)
    return array_dict

def load(file_name):
    """
    Load a vrz file (which is just a numpy npz file with formatting keys for saving/loading
    varrays and numpy masked arrays).
    """
    with np.load(file_name) as ff:
        d = _unpack_vrz_file(ff)
    return d


def empty(sarray, /, inner_shape=(), *, dtype=np.float64):
    """
    Create a new varray with the specified shape and dtype.  The data array is
    initialized via numpy.empty
    
    Parameters
    ----------
    sarray : 1d numpy array of dtype int
        The array of row lengths
    inner_shape : a tuple containing the inner dimensions.  For example, if each "row" of the
        varray (i.e. accessed by va_1[0,...]) is a 2d numpy array with 4 rows and N columns
        (where N is the 0th element of sarray), then inner_shape=(4,).  Put another way, it 
        is the shape of a row of the varray, but with the last element of the shape removed.
    dtype : data type, optional
        The data type of the data values contained in the varray.
    
    Returns
    -------
    new_varray : varray
        A new empty array of the specified shape and dtype.
    """
    if not isinstance(sarray, np.ndarray):
        sarray = np.array(sarray)
    if not all([np.issubdtype(type(item), np.integer) for item in inner_shape]):
        raise TypeError("All elements of inner_shape must be ints")
    if not isinstance(dtype, type):
        raise TypeError("Specified dtype must be a type instance")
    shape_tuple = inner_shape + (sarray.sum(),)
    darray = np.empty(shape_tuple, dtype=dtype)
    return varray(darray=darray, sarray=sarray, dtype=dtype)

def ones(sarray, /, inner_shape=(), *, dtype=np.float64):
    """
    Create a new varray with the specified shape and dtype.  The data array is
    initialized via numpy.ones
    
    Parameters
    ----------
    sarray : 1d numpy array of dtype int
        The array of row lengths
    inner_shape : a tuple containing the inner dimensions.  For example, if each "row" of the
        varray (i.e. accessed by va_1[0,...]) is a 2d numpy array with 4 rows and N columns
        (where N is the 0th element of sarray), then inner_shape=(4,).  Put another way, it 
        is the shape of a row of the varray, but with the last element of the shape removed.
    dtype : data type, optional
        The data type of the data values contained in the varray.
    
    Returns
    -------
    new_varray : varray
        A new ones array of the specified shape and dtype.
    """
    if not isinstance(sarray, np.ndarray):
        sarray = np.array(sarray)
    if not all([np.issubdtype(type(item), np.integer) for item in inner_shape]):
        raise TypeError("All elements of inner_shape must be ints")
    if not isinstance(dtype, type):
        raise TypeError("Specified dtype must be a type instance")
    shape_tuple = inner_shape + (sarray.sum(),)
    darray = np.ones(shape_tuple, dtype=dtype)
    return varray(darray=darray, sarray=sarray, dtype=dtype)

def zeros(sarray, /, inner_shape=(), *, dtype=np.float64):
    """
    Create a new varray with the specified shape and dtype.  The data array is
    initialized via numpy.zeros
    
    Parameters
    ----------
    sarray : 1d numpy array of dtype int
        The array of row lengths
    inner_shape : a tuple containing the inner dimensions.  For example, if each "row" of the
        varray (i.e. accessed by va_1[0,...]) is a 2d numpy array with 4 rows and N columns
        (where N is the 0th element of sarray), then inner_shape=(4,).  Put another way, it 
        is the shape of a row of the varray, but with the last element of the shape removed.
    dtype : data type, optional
        The data type of the data values contained in the varray.
    
    Returns
    -------
    new_varray : varray
        A new empty array of the specified shape and dtype.
    """
    if not isinstance(sarray, np.ndarray):
        sarray = np.array(sarray)
    if not all([np.issubdtype(type(item), np.integer) for item in inner_shape]):
        raise TypeError("All elements of inner_shape must be ints")
    if not isinstance(dtype, type):
        raise TypeError("Specified dtype must be a type instance")
    shape_tuple = inner_shape + (sarray.sum(),)
    darray = np.zeros(shape_tuple, dtype=dtype)
    return varray(darray=darray, sarray=sarray, dtype=dtype)

def full(sarray, fill_value, /, inner_shape=(), *, dtype=np.float64):
    """
    Create a new varray with the specified shape and dtype.  The data array is
    initialized via numpy.empty
    
    Parameters
    ----------
    sarray : 1d numpy array of dtype int
        The array of row lengths
    fill_value : The value that will be initialized in every element of the array
    inner_shape : a tuple containing the inner dimensions.  For example, if each "row" of the
        varray (i.e. accessed by va_1[0,...]) is a 2d numpy array with 4 rows and N columns
        (where N is the 0th element of sarray), then inner_shape=(4,).  Put another way, it 
        is the shape of a row of the varray, but with the last element of the shape removed.
    dtype : data type, optional
        The data type of the data values contained in the varray.
    
    Returns
    -------
    new_varray : varray
        A new empty array of the specified shape and dtype.
    """
    if not isinstance(sarray, np.ndarray):
        sarray = np.array(sarray)
    if not isinstance(fill_value, Number):
        raise TypeError("Input 'fill_value' must be a valid number")
    if not all([np.issubdtype(type(item), np.integer) for item in inner_shape]):
        raise TypeError("All elements of inner_shape must be ints")
    if not isinstance(dtype, type):
        raise TypeError("Specified dtype must be a type instance")
    shape_tuple = inner_shape + (sarray.sum(),)
    darray = np.empty(shape_tuple, dtype=dtype)
    return varray(darray=darray, sarray=sarray, dtype=dtype)

def empty_like(v_obj, dtype=None):
    """
    Create a new varray with the same shape as the prototype provided
    
    Parameters
    ----------
    v_obj : varray
        A prototype varray object.  The new object that is created will have the
        same size and dtype (unless otherwise specified) as v_obj.
    dtype : data type, optional
    
    Returns
    -------
    new_varray : varray
        A new empty array of the same shape as the provided v_obj
    """
    if not isinstance(v_obj, varray):
        raise TypeError("Provided object must be a varray")
    if not (isinstance(dt, type) or (dt is None)):
        raise TypeError("Specified dtype must be a type instance")
    darray = np.empty_like(v_obj.flatten(), dtype=dt)
    return varray(darray=darray, sarray=v_obj.sarray)

def ones_like(v_obj, dtype=None):
    """
    Create a new varray with the same shape as the prototype provided
    
    Parameters
    ----------
    v_obj : varray
        A prototype varray object.  The new object that is created will have the
        same size and dtype (unless otherwise specified) as v_obj.
    dtype : data type, optional
    
    Returns
    -------
    new_varray : varray
        A new empty array of the same shape as the provided v_obj
    """
    if not isinstance(v_obj, varray):
        raise TypeError("Provided object must be a varray")
    if not (isinstance(dt, type) or (dt is None)):
        raise TypeError("Specified dtype must be a type instance")
    darray = np.ones_like(v_obj.flatten(), dtype=dt)
    return varray(darray=darray, sarray=v_obj.sarray)

def zeros_like(v_obj, dtype=None):
    """
    Create a new varray with the same shape as the prototype provided
    
    Parameters
    ----------
    v_obj : varray
        A prototype varray object.  The new object that is created will have the
        same size and dtype (unless otherwise specified) as v_obj.
    dtype : data type, optional
    
    Returns
    -------
    new_varray : varray
        A new empty array of the same shape as the provided v_obj
    """
    if not isinstance(v_obj, varray):
        raise TypeError("Provided object must be a varray")
    if not (isinstance(dt, type) or (dt is None)):
        raise TypeError("Specified dtype must be a type instance")
    darray = np.zeros_like(v_obj.flatten(), dtype=dt)
    return varray(darray=darray, sarray=v_obj.sarray)

def full_like(v_obj, fill_value, dtype=None):
    """
    Create a new varray with the same shape as the prototype provided
    
    Parameters
    ----------
    v_obj : varray
        A prototype varray object.  The new object that is created will have the
        same size and dtype (unless otherwise specified) as v_obj.
    fill_value : value to insert into each element of the new array
    dtype : data type, optional
    
    Returns
    -------
    new_varray : varray
        A new empty array of the same shape as the provided v_obj
    """
    if not isinstance(v_obj, varray):
        raise TypeError("Provided object must be a varray")
    if not isinstance(fill_value, Number):
        raise TypeError("fill_value must be a valid number")
    if not (isinstance(dt, type) or (dt is None)):
        raise TypeError("Specified dtype must be a type instance")
    darray = np.full_like(v_obj.flatten(), fill_value, dtype=dt)
    return varray(darray=darray, sarray=v_obj.sarray)

def row_concat(varray_list, *, dtype=None, casting='same_kind'):
    """
    row_concatenate((va1, va2, ...), dtype=None, casting='same_kind')
    Concatenate two or more varrays along their first axis.
    
    Returns varray.
    
    For example, if
        va1 = varray([[1 2]
                      [3 4 5]], dtype=int64)
    and
        va2 = varray([[6]
                      [7 8]], dtype=int64)
    then
        row_concatenate((va1, va2)) is
           varray([[1 2]
                   [3 4 5]
                   [6]
                   [7 8]], dtype=int64)
    """
    inner_dims = [item.shape[1:-1] for item in varray_list]
    if len(set(inner_dims)) > 1:
        raise ValueError("All varrays must have compatible shapes for the concatenation along given axis")
    new_darray = np.concatenate([item.flatten() for item in varray_list], axis=-1, casting=casting)
    new_sarray = np.concatenate([item.sarray for item in varray_list], dtype=np.uint16)
    return varray(darray=new_darray, sarray=new_sarray, dtype=dtype)

def inner_concat(varray_list, /, axis=0, *, dtype=None, casting='same_kind'):
    """
    inner_concat((va1, va2, ...), axis=0, dtype=None, casting='same_kind')
    
    Concatenate the inner arrays along an axis.  The inner arrays are defined as the dimensions
    between the first last elements of va1.shape.  For example, 
    >>> va.zeros([4,6], inner_shape=(2,3))
    varray([[[[0. 0. 0. 0.]
              [0. 0. 0. 0.]
              [0. 0. 0. 0.]]
            
             [[0. 0. 0. 0.]
              [0. 0. 0. 0.]
              [0. 0. 0. 0.]]]
    
    
            [[[0. 0. 0. 0. 0. 0.]
              [0. 0. 0. 0. 0. 0.]
              [0. 0. 0. 0. 0. 0.]]
            
             [[0. 0. 0. 0. 0. 0.]
              [0. 0. 0. 0. 0. 0.]
              [0. 0. 0. 0. 0. 0.]]]], dtype=float64)
    This has two 'rows', with shape (2,3,4) and (2,3,6).  So the inner arrays are these two 3d 
    arrays.  
    
    ** Cannot concatenate along the last dimension, as this is the variable-length one. **
    
    This is most useful for example
    >>> va1 = va.zeros([4,6])
    >>> va1
    varray([[0. 0. 0. 0.]
            [0. 0. 0. 0. 0. 0.]], dtype=float64)
    >>> va2 = va.ones([4,6])
    >>> va2
    varray([[1. 1. 1. 1.]
            [1. 1. 1. 1. 1. 1.]], dtype=float64)
    >>> va12 = va.inner_concat([va1, va2])
    >>> va12
    varray([[[0. 0. 0. 0.]
             [1. 1. 1. 1.]]
    
            [[0. 0. 0. 0. 0. 0.]
             [1. 1. 1. 1. 1. 1.]]], dtype=float64)
    va1 could be recovered, for example, by slicing:
    >>> va12[:,0,:]
    varray([[0. 0. 0. 0.]
            [0. 0. 0. 0. 0. 0.]], dtype=float64)
    """
    if axis==0:
        raise ValueError("Axis must be one of the inner dimensions, not zero.  To concatenate " + \
            "along the zero'th axis, use row_concat")
    if not all([isinstance(item, varray) for item in varray_list]):
        raise TypeError("Items in list must be varray objects")
    if len(set([len(item) for item in varray_list])) != 1:
        raise ValueError("inner_concat can only be performed on varrays of the same length")
    ndims = np.array([item.ndim for item in varray_list])
    if axis >= ndims.min():
        raise ValueError("Axis must be one of the inner dimensions.")
    darray_shapes_2d = [item._darray.shape for item in varray_list]
    darray_shapes_2d = [list((1,)+item) if len(item)==1 else list(item) for item in darray_shapes_2d]
    for item in darray_shapes_2d:
        item.pop(index=-1)
    if len(set(darray_shapes_2d))>1:
        raise ValueError("varray inner dimensions must be compatible with requested concat")
    if not all([np.all(item._sarray == varray_list[0]._sarray) for item in varray_list[1:]]):
        raise ValueError("Items in list of varrays must have the same sarray")
    new_darray = np.concatenate([np.atleast_2d(item.flatten()) for item in varray_list], 
        axis=(axis-1), dtype=dtype, casting=casting)
    new_sarray = varray_list[0].sarray
    return varray(darray=new_darray, sarray=new_sarray)

def inner_stack(varray_list, /, axis=0, *, dtype=None, casting='same_kind'):
    """
    inner_stack((va1, va2, ...), axis=0, dtype=None, casting='same_kind')
    
    inner stack: stack two or more varrays along a new inner dimension.  In order to do
    an inner stack, the shapes and sarrays of all listed varrays must be the same.
    """
    # need to do error checking, but here is the code assuming things are valid
    if axis==0:
        raise ValueError("Axis must be one of the inner dimensions, not zero.")
    if len(set([item.shape for item in varray_list])) > 1:
        raise ValueError("All listed varrays must have the same shape")
    if not all([np.all(item.sarray==varray_list[0].sarray) for item in varray_list[1:]]):
        raise ValueError("All sarrays must be the same")
    new_darray = np.stack([item.flatten() for item in varray_list],
        axis=(axis-1), dtype=dtype, casting=casting)
    new_sarray = varray_list[0].sarray
    return varray(darray=new_darray, sarray=new_sarray)

