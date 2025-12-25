import numpy as np
from ipamd.public.utils.output import *

class _Sequence:
    unit = ''
    allowed_types = ''
    def __init__(self, name, sequence):
        sequence = self.__check(sequence)
        self.__seq_name__ = name
        self.__sequence__ = np.array(list(sequence), dtype='U1')

    def __str__(self):
        return f"{''.join(self.__sequence__)}"

    def __len__(self):
        return len(self.__sequence__)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.__sequence__[key]
        if isinstance(key, slice):
            sliced_arr = self.__sequence__[key]
            new_inst = self.__class__(self.__seq_name__, ''.join(sliced_arr))
            return new_inst
        raise TypeError(f"Unsupported index type: {type(key)}")

    def __check(self, sequence):
        if not isinstance(sequence, (str, list, np.ndarray)):
            error("Sequence must be a string, list, or numpy array.")
            raise TypeError()
        for res in sequence:
            if res not in self.__class__.allowed_types:
                error(f"Invalid {self.__class__.unit} '{res}' in sequence.")
                raise ValueError()
        return str(sequence)

    @property
    def name(self):
        return self.__seq_name__

    @property
    def sequence(self):
        return str(self)

    def __setitem__(self, key, value):
        value = self.__check(value)
        match key:
            case slice():
                seq_list = list(self.__sequence__)
                seq_list[key] = list(value)
                self.__sequence__ = np.array(seq_list, dtype='U1')
            case int():
                if key < 0 or key >= len(self.__sequence__):
                    error(f"Index {key} is out of bounds for sequence of length {len(self.__sequence__)}.")
                    raise IndexError()
                self.__sequence__ = np.delete(self.__sequence__, key)
                if value:
                    self.__sequence__ = np.insert(self.__sequence__, key, list(value))
            case str():
                seq_string = ''.join(self.__sequence__).replace(key, value)
                self.__sequence__ = np.array(list(seq_string), dtype='U1')
            case _:
                raise TypeError(f"Unsupported index type: {type(key)}")

    def __add__(self, other):
        match other:
            case _Sequence():
                if self.__class__ != other.__class__:
                    error(f"Cannot add {self.__class__.__name__} and {other.__class__.__name__}.")
                    raise TypeError()
                new_sequence = ''.join(self.sequence) + ''.join(other.sequence)
                return self.__class__(self.__seq_name__, new_sequence)
            case str():
                other = self.__check(other)
                return self.__class__(self.name, ''.join(self.sequence) + other)
            case _:
                error(f"Unsupported type for addition: {type(other)}")
                raise TypeError()

class ProteinSequence(_Sequence):
    allowed_types = 'ACDEFGHIKLMNPQRSTVWYX'
    unit = 'amino acid'
    def __init__(self, name, sequence):
        super().__init__(name, sequence)

class DNASequence(_Sequence):
    allowed_types = 'ACGTX'
    unit = 'nucleotide'
    def __init__(self, name, sequence):
        super().__init__(name, sequence)

class RNASequence(_Sequence):
    allowed_types = 'ACGUX'
    unit = 'nucleotide'
    def __init__(self, name, sequence):
        super().__init__(name, sequence)

