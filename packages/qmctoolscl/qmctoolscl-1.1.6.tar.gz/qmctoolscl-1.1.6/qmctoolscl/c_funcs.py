import ctypes
import numpy as np
from .util import c_lib

gdn_digital_permutation_c = c_lib.gdn_digital_permutation
gdn_digital_permutation_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

dnb2_integer_to_float_c = c_lib.dnb2_integer_to_float
dnb2_integer_to_float_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

lat_gen_linear_c = c_lib.lat_gen_linear
lat_gen_linear_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

gdn_gen_natural_c = c_lib.gdn_gen_natural
gdn_gen_natural_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

dnb2_undo_interlace_c = c_lib.dnb2_undo_interlace
dnb2_undo_interlace_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

dnb2_linear_matrix_scramble_c = c_lib.dnb2_linear_matrix_scramble
dnb2_linear_matrix_scramble_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

fft_bro_1d_radix2_c = c_lib.fft_bro_1d_radix2
fft_bro_1d_radix2_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

gdn_integer_to_float_c = c_lib.gdn_integer_to_float
gdn_integer_to_float_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

dnb2_gen_gray_c = c_lib.dnb2_gen_gray
dnb2_gen_gray_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

lat_gen_natural_c = c_lib.lat_gen_natural
lat_gen_natural_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

gdn_undo_interlace_c = c_lib.gdn_undo_interlace
gdn_undo_interlace_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

dnb2_interlace_c = c_lib.dnb2_interlace
dnb2_interlace_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

dnb2_gen_natural_c = c_lib.dnb2_gen_natural
dnb2_gen_natural_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

fwht_1d_radix2_c = c_lib.fwht_1d_radix2
fwht_1d_radix2_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

dnb2_digital_shift_c = c_lib.dnb2_digital_shift
dnb2_digital_shift_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

gdn_linear_matrix_scramble_c = c_lib.gdn_linear_matrix_scramble
gdn_linear_matrix_scramble_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

gdn_interlace_c = c_lib.gdn_interlace
gdn_interlace_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

lat_gen_gray_c = c_lib.lat_gen_gray
lat_gen_gray_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

gdn_digital_shift_c = c_lib.gdn_digital_shift
gdn_digital_shift_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

lat_shift_mod_1_c = c_lib.lat_shift_mod_1
lat_shift_mod_1_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

gdn_gen_natural_same_base_c = c_lib.gdn_gen_natural_same_base
gdn_gen_natural_same_base_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

dnb2_gmat_lsb_to_msb_c = c_lib.dnb2_gmat_lsb_to_msb
dnb2_gmat_lsb_to_msb_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_uint64,flags='C_CONTIGUOUS')
]

ifft_bro_1d_radix2_c = c_lib.ifft_bro_1d_radix2
ifft_bro_1d_radix2_c.argtypes = [
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	ctypes.c_uint64,
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS'),
	np.ctypeslib.ndpointer(ctypes.c_double,flags='C_CONTIGUOUS')
]

