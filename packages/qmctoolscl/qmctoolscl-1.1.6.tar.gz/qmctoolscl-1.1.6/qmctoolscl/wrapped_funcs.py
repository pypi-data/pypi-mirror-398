from .util import _opencl_c_func
from .c_funcs import *

@_opencl_c_func
def gdn_digital_permutation():
    """Permutation of digits for a generalized digital net

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    r_x (np.uint64): replications of xdig
    r_b (np.uint64): replications of bases
    tmax (np.uint64): rows of each generating matrix
    tmax_new (np.uint64): rows of each new generating matrix
    bmax (np.uint64): common permutation size, typically the maximum basis
    perms (np.ndarray of np.uint64): permutations of size r*d*tmax_new*bmax
    xdig (np.ndarray of np.uint64): binary digital net points of size r_x*n*d*tmax
    xdig_new (np.ndarray of np.uint64): float digital net points of size r*n*d*tmax_new"""
    pass

@_opencl_c_func
def dnb2_integer_to_float():
    """Convert base 2 binary digital net points to floats

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    tmaxes (np.ndarray of np.uint64): bits in integers of each generating matrix of size r
    xb (np.ndarray of np.uint64): binary digital net points of size r*n*d
    x (np.ndarray of np.double): float digital net points of size r*n*d"""
    pass

@_opencl_c_func
def lat_gen_linear():
    """Lattice points in linear order

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    g (np.ndarray of np.uint64): pointer to generating vector of size r*d
    x (np.ndarray of np.double): pointer to point storage of size r*n*d"""
    pass

@_opencl_c_func
def gdn_gen_natural():
    """Generalized digital net where the base can be different for each dimension e.g. for the Halton sequence

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    r_b (np.uint64): number of replications of bases
    mmax (np.uint64): columns in each generating matrix
    tmax (np.uint64): rows of each generating matrix
    n_start (np.uint64): starting index in sequence
    bases (np.ndarray of np.uint64): bases for each dimension of size r_b*d
    C (np.ndarray of np.uint64): generating matrices of size r*d*mmax*tmax
    xdig (np.ndarray of np.uint64): generalized digital net sequence of digits of size r*n*d*tmax"""
    pass

@_opencl_c_func
def dnb2_undo_interlace():
    """Undo interlacing of generating matrices in base 2

Args:
    r (np.uint64): replications
    d (np.uint64): dimension of resulting generating matrices 
    mmax (np.uint64): columns in generating matrices
    d_alpha (np.uint64): dimension of interlaced generating matrices
    tmax (np.uint64): bits in integers of original generating matrices 
    tmax_alpha (np.uint64): bits in integers of interlaced generating matrices
    alpha (np.uint64): interlacing factor
    C_alpha (np.ndarray of np.uint64): interlaced generating matrices of size r*d_alpha*mmax
    C (np.ndarray of np.uint64): original generating matrices of size r*d*mmax"""
    pass

@_opencl_c_func
def dnb2_linear_matrix_scramble():
    """Linear matrix scrambling for base 2 generating matrices

Args:
    r (np.uint64): replications
    d (np.uint64): dimension
    mmax (np.uint64): columns in each generating matrix 
    r_C (np.uint64): original generating matrices
    tmax_new (np.uint64): bits in the integers of the resulting generating matrices
    S (np.ndarray of np.uint64): scrambling matrices of size r*d*tmax_new
    C (np.ndarray of np.uint64): original generating matrices of size r_C*d*mmax
    C_lms (np.ndarray of np.uint64): resulting generating matrices of size r*d*mmax"""
    pass

@_opencl_c_func
def fft_bro_1d_radix2():
    """Fast Fourier Transform for inputs in bit reversed order.
FFT is done in place along the last dimension where the size is required to be a power of 2.
Follows a decimation-in-time procedure described in https://www.cmlab.csie.ntu.edu.tw/cml/dsp/training/coding/transform/fft.html.

Args:
    d1 (np.uint64): first dimension
    d2 (np.uint64): second dimension
    n_half (np.uint64): half of the last dimension of size n = 2n_half along which FFT is performed
    twiddler (np.ndarray of np.double): size n vector used to store real twiddle factors
    twiddlei (np.ndarray of np.double): size n vector used to store imaginary twiddle factors 
    xr (np.ndarray of np.double): real array of size d1*d2*n on which to perform FFT in place
    xi (np.ndarray of np.double): imaginary array of size d1*d2*n on which to perform FFT in place"""
    pass

@_opencl_c_func
def gdn_integer_to_float():
    """Convert digits of generalized digital net to floats

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    r_b (np.uint64): replications of bases 
    tmax (np.uint64): rows of each generating matrix
    bases (np.ndarray of np.uint64): bases for each dimension of size r_b*d
    xdig (np.ndarray of np.uint64): binary digital net points of size r*n*d*tmax
    x (np.ndarray of np.double): float digital net points of size r*n*d"""
    pass

@_opencl_c_func
def dnb2_gen_gray():
    """Binary representation of digital net in base 2 in Gray code order

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    n_start (np.uint64): starting index in sequence
    mmax (np.uint64): columns in each generating matrix
    C (np.ndarray of np.uint64): generating matrices of size r*d*mmax
    xb (np.ndarray of np.uint64): binary digital net points of size r*n*d"""
    pass

@_opencl_c_func
def lat_gen_natural():
    """Lattice points in natural order

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    n_start (np.uint64): starting index in sequence
    g (np.ndarray of np.uint64): pointer to generating vector of size r*d 
    x (np.ndarray of np.double): pointer to point storage of size r*n*d"""
    pass

@_opencl_c_func
def gdn_undo_interlace():
    """Undo interlacing of generating matrices

Args:
    r (np.uint64): replications
    d (np.uint64): dimension of resulting generating matrices 
    mmax (np.uint64): columns in generating matrices
    d_alpha (np.uint64): dimension of interlaced generating matrices
    tmax (np.uint64): rows of original generating matrices
    tmax_alpha (np.uint64): rows of interlaced generating matrices
    alpha (np.uint64): interlacing factor
    C_alpha (np.ndarray of np.uint64): interlaced generating matrices of size r*d_alpha*mmax*tmax_alpha
    C (np.ndarray of np.uint64): original generating matrices of size r*d*mmax*tmax"""
    pass

@_opencl_c_func
def dnb2_interlace():
    """Interlace generating matrices or transpose of point sets to attain higher order digital nets in base 2

Args:
    r (np.uint64): replications
    d_alpha (np.uint64): dimension of resulting generating matrices 
    mmax (np.uint64): columns of generating matrices
    d (np.uint64): dimension of original generating matrices
    tmax (np.uint64): bits in integers of original generating matrices
    tmax_alpha (np.uint64): bits in integers of resulting generating matrices
    alpha (np.uint64): interlacing factor
    C (np.ndarray of np.uint64): original generating matrices of size r*d*mmax
    C_alpha (np.ndarray of np.uint64): resulting interlaced generating matrices of size r*d_alpha*mmax"""
    pass

@_opencl_c_func
def dnb2_gen_natural():
    """Binary representation of digital net in base 2 in natural order

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    n_start (np.uint64): starting index in sequence
    mmax (np.uint64): columns in each generating matrix
    C (np.ndarray of np.uint64): generating matrices of size r*d*mmax
    xb (np.ndarray of np.uint64): binary digital net points of size r*n*d"""
    pass

@_opencl_c_func
def fwht_1d_radix2():
    """Fast Walsh-Hadamard Transform for real valued inputs.
FWHT is done in place along the last dimension where the size is required to be a power of 2.
Follows the divide-and-conquer algorithm described in https://en.wikipedia.org/wiki/Fast_Walsh%E2%80%93Hadamard_transform

Args:
    d1 (np.uint64): first dimension
    d2 (np.uint64): second dimension
    n_half (np.uint64): half of the last dimension along which FWHT is performed
    x (np.ndarray of np.double): array of size d1*d2*2n_half on which to perform FWHT in place"""
    pass

@_opencl_c_func
def dnb2_digital_shift():
    """Digital shift base 2 digital net

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    r_x (np.uint64): replications of xb
    lshifts (np.ndarray of np.uint64): left shift applied to each element of xb
    xb (np.ndarray of np.uint64): binary base 2 digital net points of size r_x*n*d
    shiftsb (np.ndarray of np.uint64): digital shifts of size r*d
    xrb (np.ndarray of np.uint64): digital shifted digital net points of size r*n*d"""
    pass

@_opencl_c_func
def gdn_linear_matrix_scramble():
    """Linear matrix scramble for generalized digital net

Args:
    r (np.uint64): replications 
    d (np.uint64): dimension 
    mmax (np.uint64): columns in each generating matrix
    r_C (np.uint64): number of replications of C 
    r_b (np.uint64): number of replications of bases
    tmax (np.uint64): number of rows in each generating matrix 
    tmax_new (np.uint64): new number of rows in each generating matrix 
    bases (np.ndarray of np.uint64): bases for each dimension of size r*d 
    S (np.ndarray of np.uint64): scramble matrices of size r*d*tmax_new*tmax
    C (np.ndarray of np.uint64): generating matrices of size r_C*d*mmax*tmax 
    C_lms (np.ndarray of np.uint64): new generating matrices of size r*d*mmax*tmax_new"""
    pass

@_opencl_c_func
def gdn_interlace():
    """Interlace generating matrices or transpose of point sets to attain higher order digital nets

Args:
    r (np.uint64): replications
    d_alpha (np.uint64): dimension of resulting generating matrices 
    mmax (np.uint64): columns of generating matrices
    d (np.uint64): dimension of original generating matrices
    tmax (np.uint64): rows of original generating matrices
    tmax_alpha (np.uint64): rows of interlaced generating matrices
    alpha (np.uint64): interlacing factor
    C (np.ndarray of np.uint64): original generating matrices of size r*d*mmax*tmax
    C_alpha (np.ndarray of np.uint64): resulting interlaced generating matrices of size r*d_alpha*mmax*tmax_alpha"""
    pass

@_opencl_c_func
def lat_gen_gray():
    """Lattice points in Gray code order

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    n_start (np.uint64): starting index in sequence
    g (np.ndarray of np.uint64): pointer to generating vector of size r*d 
    x (np.ndarray of np.double): pointer to point storage of size r*n*d"""
    pass

@_opencl_c_func
def gdn_digital_shift():
    """Digital shift a generalized digital net

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    r_x (np.uint64): replications of xdig
    r_b (np.uint64): replications of bases
    tmax (np.uint64): rows of each generating matrix
    tmax_new (np.uint64): rows of each new generating matrix
    bases (np.ndarray of np.uint64): bases for each dimension of size r_b*d
    shifts (np.ndarray of np.uint64): digital shifts of size r*d*tmax_new
    xdig (np.ndarray of np.uint64): binary digital net points of size r_x*n*d*tmax
    xdig_new (np.ndarray of np.uint64): float digital net points of size r*n*d*tmax_new"""
    pass

@_opencl_c_func
def lat_shift_mod_1():
    """Shift mod 1 for lattice points

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    r_x (np.uint64): replications in x
    x (np.ndarray of np.double): lattice points of size r_x*n*d
    shifts (np.ndarray of np.double): shifts of size r*d
    xr (np.ndarray of np.double): pointer to point storage of size r*n*d"""
    pass

@_opencl_c_func
def gdn_gen_natural_same_base():
    """Generalized digital net with the same base for each dimension e.g. a digital net in base greater than 2

Args:
    r (np.uint64): replications
    n (np.uint64): points
    d (np.uint64): dimension
    mmax (np.uint64): columns in each generating matrix
    tmax (np.uint64): rows of each generating matrix
    n_start (np.uint64): starting index in sequence
    b (np.uint64): common base
    C (np.ndarray of np.uint64): generating matrices of size r*d*mmax*tmax
    xdig (np.ndarray of np.uint64): generalized digital net sequence of digits of size r*n*d*tmax"""
    pass

@_opencl_c_func
def dnb2_gmat_lsb_to_msb():
    """Convert base 2 generating matrices with integers stored in Least Significant Bit order to Most Significant Bit order

Args:
    r (np.uint64): replications
    d (np.uint64): dimension
    mmax (np.uint64): columns in each generating matrix 
    tmaxes (np.ndarray of np.uint64): length r vector of bits in each integer of the resulting MSB generating matrices
    C_lsb (np.ndarray of np.uint64): original generating matrices of size r*d*mmax
    C_msb (np.ndarray of np.uint64): new generating matrices of size r*d*mmax"""
    pass

@_opencl_c_func
def ifft_bro_1d_radix2():
    """Inverse Fast Fourier Transform with outputs in bit reversed order.
FFT is done in place along the last dimension where the size is required to be a power of 2.
Follows a procedure described in https://www.expertsmind.com/learning/inverse-dft-using-the-fft-algorithm-assignment-help-7342873886.aspx.

Args:
    d1 (np.uint64): first dimension
    d2 (np.uint64): second dimension
    n_half (np.uint64): half of the last dimension of size n = 2n_half along which FFT is performed
    twiddler (np.ndarray of np.double): size n vector used to store real twiddle factors
    twiddlei (np.ndarray of np.double): size n vector used to store imaginary twiddle factors 
    xr (np.ndarray of np.double): real array of size d1*d2*n on which to perform FFT in place
    xi (np.ndarray of np.double): imaginary array of size d1*d2*n on which to perform FFT in place"""
    pass

