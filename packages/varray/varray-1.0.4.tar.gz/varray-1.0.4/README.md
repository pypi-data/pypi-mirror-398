# varray

[![PyPI](https://img.shields.io/pypi/v/varray.svg?style=flat)](https://pypi.org/project/varray/)

A numpy-like array that supports variable-length rows

## Installation
```
pip install varray
```
or try
```
pip install git+https://github.com/aaronm6/varray.git
```

## Description
Sometimes one needs to store data in a list of sublists.  If all the sublists are the same size and their contents the same data type, then a numpy array is a very useful and efficient way to store the data; data operations are vectorized and optimized with compiled machine code.  However, if the condition that each sublist contains the same number of elements is not met, numpy is not much help.  

Put another way, numpy allows
```python
array([[1, 2, 3],
       [4, 5, 6]])
```
but **not**
```python
array([[1, 2],
       [4, 5, 6]])
```

Here, **varray** (for "variable array") provides a numpy-like array type that supports multi-dimensional arrays with variable-length rows.  It is "numpy-like" in that it behaves in much the same way that numpy arrays do, operations are vectorized, slicing produces "views" instead of duplicating data, etc.  Most vectorized operations that work on numpy arrays also seamlessly work on varrays (e.g. `np.exp`, `np.sin`, etc., also binary operations).  To be clear, only one dimension of a varray may be variable: the last dimension.

**Why reinvent the wheel, when [awkward](https://awkward-array.org/doc/main/) (awk) arrays exist?**  Awk arrays do all this, are efficient and versatile and are an excellent tool when one's needs align with the features they provide.  However, I found myself avoiding awk arrays in my own work for two reasons:

1. awk arrays are IMMUTABLE, and hence read-only.  This means they're great to read from, but tricky to use if you actually want to use them in a script or notebook.  For example, a common usage of numpy arrays is to initialize an empty 2d array with np.empty(...) and then fill in the rows in a loop.  This is possible with numpy arrays because they are mutable.  But one cannot do this with awk arrays.  This used to be possible in earlier versions of awk, but this important functionality has since been removed.  This is my main motivation for creating varray: awk arrays' immutability makes them unusable for the vast majority of my own use cases.
2. awk is a large package that involves compiled c++ code and its plethora of functionalities might not always be needed.  Hence the desire for a light-weight alternative that is written in pure python.

A varray object essentially wraps two numpy arrays: a `darray` ("data array") and an `sarray` ("shape array").  The `darray` stores all the data values in a contiguous array.  The `sarray` is an array of ints which describe the length of each row of the array.  If the data could be described by the nested list,
```
[ [0., 1.], [2., 3., 4.], [5.], [6., 7., 8., 9.] ]
```
then `darray` would be 
```
[0., 1., 2., 3., 4., 5., 6., 7., 8., 9.]
```
and the `sarray` would be
```
[2, 3, 1, 4]
```
which are the lengths of each of the sublists above.  When the varray is created, an array of indices is calculated for the start of each sublist; this is stored internally as the `csarray`, which in this case is
```python
[0, 2, 5, 6]
```
It is named `csarray` because it is calculated from the cumulative sum over the `sarray`.  In this way, `csarray` acts as a kind of array of addresses to the `darray`.  When a varray is sliced, the new varray can point to the orginal `darray`, but with modified `sarray` and `csarray`, thereby avoiding the need to replicate the data: in this way, varray slicing produces a "view" in much the same way that numpy arrays work.

## Usage
We can create a varray in many ways; here we will use the original nested list above:
```python
>>> import varray as va
>>> nested_data = [ [0., 1.], [2., 3., 4.], [5.], [6., 7., 8., 9.]]
>>> va1 = va.varray(nested_data, dtype=float)
>>> va1
varray([[0. 1.]
        [2. 3. 4.]
        [5.]
        [6. 7. 8. 9.]], dtype=float64)
```
We can perform some basic slicing.  For example, picking off the first column (i.e. first element of each row) is the same slicing as in a 2d numpy array:
```python
>>> va1[:,0]
varray([[0.]
        [2.]
        [5.]
        [6.]], dtype=float64)
```
This object can be passed to `matplotlib.pyplot.plot`, for example.  We can also slice a column that not all rows have:
```python
>>> va1[:,2]
varray([[]
        [4.]
        []
        [8.]], dtype=float64)
```
We can sum over rows:
```python
>>> va1.sum(axis=1)
array([ 1., 9., 5., 30.])
```
or sum over columns:
```python
>>> va1.sum(axis=0)
array([13., 11., 12., 9.])
```
where rows that don't have the specified column don't contribute.
We can also do a cumulative sum:
```python
>>> va1.cumsum(axis=1)
varray([[0. 1.]
        [2. 5. 9.]
        [5.]
        [ 6. 13. 21. 30.]], dtype=float64)
```
Slices of varrays are "views" to the original data, so that data is not reproduced.  This behavior is similar to how numpy array "views" work.  For example, we could slice just the even rows:
```python
>>> va1_even = va1[::2,...]
>>> va1_even
varray([[0. 1.]
        [5.]], dtype=float)
>>> va1._darray
array([0., 1., 2., 3., 4., 5., 6., 7., 8., 9.])
>>> hex(va1._darray.ctypes.data)  # gives the memory address of the first element in the array
'0x600000eaeda0'
>>> va1_even._darray
array([0., 1., 2., 3., 4., 5., 6., 7., 8., 9.])
>>> hex(va1_even._darray.ctypes.data)  # gives the memory address of the first element in the array
'0x600000eaeda0'
```
Notice that the internal data of `va1` and `va1_even` is the same array, with data pointing to the same point in memory.

We can make multidimensional arrays
```python
>>> darray2 = np.vstack([np.r_[:10.], np.r_[100.:110.]])
>>> darray2
array([[  0.,   1.,   2.,   3.,   4.,   5.,   6.,   7.,   8.,   9.],
       [100., 101., 102., 103., 104., 105., 106., 107., 108., 109.]])
>>> sarray = np.r_[2,3,1,4]
>>> va2 = va.varray(darray=darray2, sarray=sarray)
>>> va2
varray([[[  0.   1.]
         [100. 101.]]

        [[  2.   3.   4.]
         [102. 103. 104.]]

        [[  5.]
         [105.]]

        [[  6.   7.   8.   9.]
         [106. 107. 108. 109.]]], dtype=float64)
```
This behaves like a numpy (4,2,N) array, where N is variable here.  We can slice this up too:
```python
>>> va2[:,1,:]
varray([[100. 101.]
        [102. 103. 104.]
        [105.]
        [106. 107. 108. 109.]], dtype=float64)
```
Math operations on and between varrays, and between varrays and numbers, works just like numpy arrays.

Varrays can be cast as numpy masked arrays:
```python
>>> va1
varray([[0. 1.]
        [2. 3. 4.]
        [5.]
        [6. 7. 8. 9.]], dtype=float64)
>>> va1.to_ma()
masked_array(
  data=[[0.0, 1.0, --, --],
        [2.0, 3.0, 4.0, --],
        [5.0, --, --, --],
        [6.0, 7.0, 8.0, 9.0]],
  mask=[[False, False,  True,  True],
        [False, False, False,  True],
        [False,  True,  True,  True],
        [False, False, False, False]],
  fill_value=1e+20)
```

**A note about broadcasting**

We are limited in how we can broadcast shapes like in numpy.  Only scalars can be broadcast to varrays.

We can use `va.empty`, `va.zeros`, etc., just like their numpy equivalents.

## Saving to file
The provided method `va.save` is simply a wrapper for `numpy.savez_compressed`, but it accepts varrays (and numpy arrays and masked arrays) and applies a suffix of `.vrz`; it handles the saving of a varray's `darray` and `sarray`.  The paired `va.load` is also just a wrapper for `numpy.load`, but it detects which arrays should go into varrays and creates those, and the same for numpy masked arrays.
