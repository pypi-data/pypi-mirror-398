# distutils: language = c++
# cython: language_level=3

from libcpp cimport bool
from libcpp.optional cimport optional
from libc.stdint cimport uint32_t
from libcpp.string cimport string

cimport candy_bar.defs as cpp

# Declare the python wrapper
cdef class CandyBar:
    cdef uint32_t total
    cdef uint32_t current
    cdef object iterable
    cdef cpp.CandyBar *thisptr

    def __cinit__(self, iterable=None, total=None, message="", messageWidth=None, width=None,
                  linePos=0, leftJustified=True, bool disable=False):
        self.iterable = iterable
        self.current = 0
        if self.iterable is not None:
            try:
                self.total = len(self.iterable)
            except TypeError:
                # If iterable doesn't have len(), convert to list
                self.iterable = list(self.iterable)
                self.total = len(self.iterable)
        elif total is not None:
            self.total = total
        else:
            raise ValueError("Either an iterable or the total number must be provided")

        cdef string msg = message.encode('UTF-8')
        cdef optional[uint32_t] msgWidth = optional[uint32_t]()
        cdef optional[uint32_t] barWidth = optional[uint32_t]()

        if messageWidth is not None:
            msgWidth = optional[uint32_t](<uint32_t>messageWidth)

        if width is not None:
            barWidth = optional[uint32_t](<uint32_t>width)

        self.thisptr = new cpp.CandyBar(self.total, msg, msgWidth, barWidth,
                                        linePos, leftJustified, disable)

    def __dealloc__(self):
        if self.thisptr != NULL:
            del self.thisptr

    def disable(self, bool disable=False):
        """ Disable the progress bar """
        self.thisptr.disable(disable)

    def update(self, uint32_t current):
        """ Update the progress bar """
        self.thisptr.update(current)

    @property
    def total(self):
        """ Getter for the total value """
        return self.thisptr.getTotal()

    @total.setter
    def total(self, total):
        """ Set the total value of the progress bar (i.e. 100%) """
        self.thisptr.setTotal(total)

    @property
    def linePos(self):
        """ Getter for the line position value """
        return self.thisptr.getLinePos()

    @linePos.setter
    def linePos(self, value):
        """ Set the line position value """
        self.thisptr.setLinePos(value)

    def setMessage(self, message, messageWidth=None):
        """ Set the message printed before the progress bar """
        cdef string msg = message.encode('UTF-8')
        cdef optional[uint32_t] msgWidth = optional[uint32_t]()

        if messageWidth is not None:
            msgWidth = optional[uint32_t](<uint32_t>messageWidth)
        self.thisptr.setMessage(msg, msgWidth)

    def setLeftJustified(self, bool lft):
        """ Change the justification of the progress bar """
        self.thisptr.setLeftJustified(lft)

    def __iter__(self):
        """Make the progress bar iterable"""
        self.current = 0
        if self.iterable is not None:
            return self
        raise ValueError("ProgressBar must be initialized with an iterable")

    def __next__(self):
        """Get next item and update progress"""
        if self.current >= self.total:
            #self.thisptr.update(self.total)
            raise StopIteration

        item = self.iterable[self.current]
        self.current += 1
        self.thisptr.update(self.current)
        return item
