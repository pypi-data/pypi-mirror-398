# distutils: language = c++
# distutils: sources = src/candybar.cpp
# cython: c_string_type=unicode, c_string_encoding=utf8

# Declare the class with cdef
from libcpp cimport bool
from libcpp.string cimport string
from libc.stdint cimport uint32_t
from libcpp.optional cimport optional

cdef extern from "candybar.h":
    cdef cppclass CandyBar:
        CandyBar(uint32_t, string, optional[uint32_t], optional[uint32_t], uint32_t, bool, bool) except +
        void update(uint32_t)
        void disable(bool)
        void setTotal(uint32_t)
        uint32_t getTotal()
        void setMessage(string, optional[uint32_t])
        void setLeftJustified(bool)
        uint32_t getLinePos()
        void setLinePos(uint32_t)
