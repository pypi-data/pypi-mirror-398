"""zernikepolpy main class to handle everything"""
import math
from enum import Enum
from gmpy2 import mpz, mpfr # pylint: disable=no-name-in-module  # this warning is wrong
#no need for numpy at the moment: import numpy as np
from zernikepolpy.__init__ import __version__

def dummy_fast():
    '''just a dummy function to check switching of functions: fast version'''

def dummy_normal():
    '''just a dummy function to check switching of functions: normal version'''

def dummy_normal_big():
    '''just a dummy function to check switching of functions: normal version with big numbers'''

def dummy_fast_big():
    '''just a dummy function to check switching of functions: fast version with big numbers'''

class ZernikeType(Enum):
    '''enum for each possible version of Zernike calculation
       NONE       should not happen, something is not initialized
       NORMAL     normal functions are used as described in the math books
       FAST       a faster algorithm is used for calculation (XXX not yet defined which one)
       NORMALBIG  normal functions are used as described in the math books, but with big numbers
       FASTBIG    the faster algorithm with big number is used
    '''
    NONE = 0
    NORMAL = 1
    FAST = 2
    NORMALBIG = 3
    FASTBIG = 4

class Zernike:
    r"""Class to represent Zernike polynoms.

    """

    def __init__(self):
        r"""Constructor.

        Parameters
        ----------
        """
        self.feature = ZernikeType.NORMAL
        self.switch (self.feature)

    def switch(self,feature):
        '''switch between the different algorithms for calculation, see Enmum above'''
        self.feature = feature
        if feature == ZernikeType.NORMAL:
            self.dummy = dummy_normal
            self._m_n_rho=self._m_n_rho_radial_normal
            self._m_n_rho_phi=self._m_n_rho_phi_radial_normal

        if feature == ZernikeType.FAST:
            self.dummy = dummy_fast
            self._m_n_rho=self._notimplemented
            self._m_n_rho_phi=self._notimplemented

        if feature == ZernikeType.NORMALBIG:
            self.dummy = dummy_normal_big
            self._m_n_rho=self._m_n_rho_radial_normal_big
            self._m_n_rho_phi=self._m_n_rho_phi_radial_normal_big

        if feature == ZernikeType.FASTBIG:
            self.dummy = dummy_fast_big
            self._m_n_rho=self._notimplemented
            self._m_n_rho_phi=self._notimplemented

    def _notimplemented(self):
        '''there is no implementation for the underlying function yet'''
        raise ValueError("not implemented")

    def version(self):
        '''return the current version of this library'''
        return __version__

    def _m_n_rho_radial_normal(self, m, n, rho):
        result = 0.0
        if n <= 20:
            if (n-m) % 2 == 0: # is n-m even?
                loopend=int((n-m)/2)
                intnmdiff=int((n-m)/2)
                intnmsum=int((n+m)/2)
                # range uses an half open interval [start, end), so we need to loop until end+1
                for k in range(loopend+1):
                    numerator = math.pow(-1,k) * math.factorial(n-k)
                    # sign=-1
                    # if k % 2 == 0:
                    #    sign=1
                    # numerator = sign * math.factorial(n-k)
                    # n-m is even, so this is an integer
                    denominator = math.factorial(k) * \
                                  math.factorial(intnmsum-k) * \
                                  math.factorial(intnmdiff-k)
                    value = numerator / denominator * math.pow(rho, n-2*k)
                    result = result + value
# result = 0 was already set before if, so nothing to do here
#            else:
#                result = 0
        else:
            raise RuntimeError("value of N is too big, should be below 20")

        return result

    def _m_n_rho_radial_normal_big(self, m, n, rho):
        result = mpfr(0.0,100)
        if (n-m) % 2 == 0: # is n-m even?
            loopend=mpz((n-m)/2)
            intnmdiff=mpz((n-m)/2)
            intnmsum=mpz((n+m)/2)
            # range uses an half open interval [start, end), so we need to loop until end+1
            for k in range(loopend+1):
                numerator = mpz(math.pow(-1,k)) * math.factorial(mpz(n-k))
                # n-m is even, so this is an integer
                denominator = math.factorial(k) * \
                              math.factorial(intnmsum-k) * \
                              math.factorial(intnmdiff-k)
                value = mpfr(numerator / denominator * math.pow(rho, n-2*k),100)
                result = mpfr(value + result,100)
# result = 0 was already set before if, so nothing to do here
#        else:
#           result = 0

        return result

    def _m_n_rho_phi_radial_normal(self, m, n, rho, phi):
        result = 0.
        result_z = self._m_n_rho(m, n, rho)
        if m%2 == 0:
            result = result_z * math.cos(m*phi)
        else:
            result = result_z * math.sin(m*phi)

        return result

    def _m_n_rho_phi_radial_normal_big(self, m, n, rho, phi):
        result = 0.
        result_z = self._m_n_rho(m, n, rho)
        if m%2 == 0:
            result = mpfr(result_z * math.cos(m*phi),100)
        else:
            result = mpfr(result_z * math.sin(m*phi),100)

        return result


    def m_n_rho(self, m, n, rho):
        '''radial Zernike polynom with parameter m, n and rho'''
        result = 0.0
        if m < 0:
            raise ValueError("M must not be negative")
        if n < 0:
            raise ValueError("N must not be negative")
        if n < m:
            raise ValueError("N must not be smaller than M")

        result = self._m_n_rho(m, n, rho)
        return result


    def m_n_rho_phi(self, m, n, rho, phi):
        '''radial Zernike polynom with parameter m, n, rho and phi'''
        result = 0.0
        if m < 0:
            raise ValueError("M must not be negative")
        if n < 0:
            raise ValueError("N must not be negative")
        if n < m:
            raise ValueError("N must not be smaller than M")

        result = self._m_n_rho_phi(m, n, rho, phi)
        return result
