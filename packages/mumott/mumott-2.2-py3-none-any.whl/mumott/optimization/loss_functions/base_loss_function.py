from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from mumott.core.hashing import list_to_hash
from mumott.methods.residual_calculators.base_residual_calculator import ResidualCalculator
from mumott.optimization.regularizers.base_regularizer import Regularizer


class LossFunction(ABC):

    """This is the base class from which specific loss functions are derived.

    Parameters
    ----------
    residual_calculator
        A class derived from
        :class:`ResidualCalculator
        <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator>`
    use_weights
        Whether to multiply residuals with weights before calculating the residual norm. The calculation
        is also applied to the gradient.
    preconditioner
        A preconditioner to be applied to the residual norm gradient. Must have the same shape as
        :attr:`residual_calculator.coefficients
        <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator.coefficients>`
        or it must be possible to broadcast by multiplication.
        Entries that are set to ``0`` in the preconditioner will be masked out in the application of
        the regularization gradient if ``use_preconditioner_mask`` is set to ``True``.
    residual_norm_multiplier
        A multiplier that is applied to the residual norm and gradient. Useful in cases where
        a very small or large loss function value changes the optimizer behaviour.
    use_preconditioner_mask
        If set to ``True`` (default), a mask will be derived from the ``preconditioner`` which
        masks out the entire gradient in areas where the ``preconditioner`` is not greater than 0.
    """

    def __init__(self,
                 residual_calculator: ResidualCalculator,
                 use_weights: bool = False,
                 preconditioner: np.ndarray[float] = None,
                 residual_norm_multiplier: float = 1,
                 use_preconditioner_mask: bool = True):
        self._residual_calculator = residual_calculator
        self.use_weights = use_weights
        self._preconditioner = preconditioner
        self.use_preconditioner_mask = use_preconditioner_mask
        self.residual_norm_multiplier = residual_norm_multiplier
        self._regularizers = {}
        self._regularization_weights = {}

    def get_loss(self,
                 coefficients: np.ndarray[float] = None,
                 get_gradient: bool = False,
                 gradient_part: str = None):
        """Returns loss function value and possibly gradient based on the given :attr:`coefficients`.

        Notes
        -----
        This method simply calls the methods :meth:`get_residual_norm` and :meth:`get_regularization_norm`
        and sums up their respective contributions.

        Parameters
        ----------
        coefficients
            An ``np.ndarray`` of values of the same shape as :attr:`residual_calculator.coefficients
            <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator.coefficients>`.
            Default value is ``None``, which leaves it up to :meth:`get_residual_norm`
            to handle the choice of coefficients, which in general defaults to using the coefficients
            of the attached :attr:`residual_calculator`.
        get_gradient
            If ``True``, returns a ``'gradient'`` of the same shape as :attr:`residual_calculator.coefficients
            <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator.coefficients>`.
            Otherwise, the entry ``'gradient'`` will be ``None``.

        Returns
        -------
            A dictionary with at least two entries, ``loss`` and ``gradient``.
        """
        residual_norm = self.get_residual_norm(coefficients, get_gradient, gradient_part)
        regularization = self.get_regularization_norm(self._residual_calculator.coefficients,
                                                      get_gradient, gradient_part)

        result = dict(loss=0., gradient=None)
        result['loss'] += residual_norm['residual_norm'] * self.residual_norm_multiplier
        for name in regularization:
            result['loss'] += regularization[name]['regularization_norm'] * self.regularization_weights[name]

        if get_gradient:
            result['gradient'] = residual_norm['gradient'] * self.residual_norm_multiplier
            if self.preconditioner is not None:
                if self._residual_calculator.coefficients.shape[:-1] != self.preconditioner.shape[:-1]:
                    raise ValueError('The first three dimensions of the preconditioner must'
                                     ' have the same size as the coefficients of the residual calculator,'
                                     ' and the last index must be the same or 1, but the'
                                     ' residual calculator coefficients have shape'
                                     f' {self._residual_calculator.coefficients.shape},'
                                     ' while the preconditioner has shape'
                                     f' {self.preconditioner.shape}!')
                result['gradient'] *= self.preconditioner
            for name in regularization:
                result['gradient'] += regularization[name]['gradient'] * self.regularization_weights[name]
            result['gradient'] *= self._gradient_mask
        return result

    def get_residual_norm(self,
                          coefficients: np.ndarray[float] = None,
                          get_gradient: bool = False,
                          gradient_part: str = None,) -> dict:
        """Returns residual norm and possibly gradient based on the attached
        :attr:`residual_calculator
        <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator>`.
        If :attr:`coefficients` is given, :attr:`residual_calculator.coefficients
        <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator.coefficients>`
        will be updated with these new values, otherwise, the residual norm and possibly the gradient
        will just be calculated using the current coefficients.

        Parameters
        ----------
        coefficients
            An ``np.ndarray`` of values of the same shape as :attr:`residual_calculator.coefficients
            <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator.coefficients>`.
        get_gradient
            If ``True``, returns a ``'gradient'`` of the same shape as :attr:`residual_calculator.coefficients
            <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator.coefficients>`.
            Otherwise, the entry ``'gradient'`` will be ``None``.

        Returns
        -------
            A dictionary with at least two entries, ``residual_norm`` and ``gradient``.
        """
        if coefficients is not None:
            self._residual_calculator.coefficients = coefficients
        result = self._get_residual_norm_internal(get_gradient, gradient_part)
        return result

    @abstractmethod
    def _get_residual_norm_internal(self, get_gradient: bool, gradient_part: str) -> dict:
        """ Method that implements the actual calculation of the residual norm. """
        pass

    @property
    def use_weights(self) -> bool:
        """ Whether to use weights or not in calculating the residual
        and gradient. """
        return self._use_weights

    @use_weights.setter
    def use_weights(self, val: bool) -> None:
        self._use_weights = val

    @property
    def residual_norm_multiplier(self) -> float:
        """ Multiplicative factor by which the residual norm will be scaled. Can be used,
        together with any :attr:`regularization_weights`, to scale the loss function,
        in order to address unexpected behaviour that arises when some optimizers are given
        very small or very large loss functions. """
        return self._residual_norm_multiplier

    @residual_norm_multiplier.setter
    def residual_norm_multiplier(self, val: float) -> None:
        self._residual_norm_multiplier = val

    @property
    def initial_values(self) -> np.ndarray[float]:
        """ Initial coefficient values for optimizer; defaults to zeros. """
        return np.zeros_like(self._residual_calculator.coefficients)

    @property
    def use_preconditioner_mask(self) -> bool:
        """ Determines whether a mask is calculated from the preconditioner."""
        return self._use_preconditioner_mask

    @use_preconditioner_mask.setter
    def use_preconditioner_mask(self, value: bool) -> None:
        self._use_preconditioner_mask = value
        self._update_mask()

    @property
    def preconditioner(self) -> np.ndarray[float]:
        """ Preconditioner that is applied to the gradient by multiplication. """
        return self._preconditioner

    @property
    def preconditioner_hash(self) -> str:
        """ Hash of the preconditioner. """
        if self._preconditioner is None:
            return None
        return list_to_hash([self._preconditioner])[:6]

    @preconditioner.setter
    def preconditioner(self, value: np.ndarray[float]) -> None:
        self._preconditioner = value
        self._update_mask()

    def _update_mask(self):
        """Updates the gradient mask."""
        if self.preconditioner is not None and self.use_preconditioner_mask is True:
            self._gradient_mask = np.round(self.preconditioner > 0).astype(self._residual_calculator.dtype)
        else:
            self._gradient_mask = np.ones_like(self._residual_calculator.coefficients)

    @property
    @abstractmethod
    def _function_as_str(self) -> str:
        """ Should return a string representation of the associated loss function
        of the residual in Python idiom, e.g. 'L(r) = 0.5 * r ** 2' for squared loss. """
        pass

    @property
    @abstractmethod
    def _function_as_tex(self) -> str:
        """ Should return a string representation of the associated loss function
        of the residual in MathJax-renderable TeX, e.g. $L(r) = \frac{r^2}{2}$ for squared loss"""
        pass

    def get_regularization_norm(self,
                                coefficients: np.ndarray[float] = None,
                                get_gradient: bool = False,
                                gradient_part: str = None) -> dict[str, dict[str, Any]]:
        """ Returns the regularization norm, and if requested, the gradient, from all
        regularizers attached to this instance, based on the provided :attr`coefficients`.
        If no coefficients are provided, the ones from the attached :attr:`residual_calculator` are used.

        Parameters
        ----------
        coefficients
            An ``np.ndarray`` of values of the same shape as :attr:`residual_calculator.coefficients
            <mumott.methods.residual_calculators.base_residual_calculator.ResidualCalculator.coefficients>`.
        get_gradient
            Whether to compute and return the gradient. Default is ``False``
        gradient_part
            Used for the zonal harmonics resonstructions to determine what part of the gradient is
            being calculated. Default is None.

        Returns
        -------
            A dictionary with one entry for each regularizer in :attr:`regularizers`, containing
            ``'regularization_norm'`` and ``'gradient'`` as entries.
        """
        regularization = dict()

        if coefficients is None:
            coefficients = self._residual_calculator.coefficients

        for name in self._regularizers:
            reg = self._regularizers[name].get_regularization_norm(coefficients=coefficients,
                                                                   get_gradient=get_gradient)
            sub_dict = dict(gradient=None)
            sub_dict['regularization_norm'] = reg['regularization_norm']

            if get_gradient:
                sub_dict['gradient'] = reg['gradient']
            regularization[name] = sub_dict
        return regularization

    def add_regularizer(self,
                        name: str,
                        regularizer: Regularizer,
                        regularization_weight: float) -> None:
        r""" Add a :ref:`regularizer <regularizers>` to the loss function.

        Parameters
        ----------
        name
            Name of the regularizer, to be used as its key.
        regularizer
            The :class:`Regularizer` instance to be attached.
        regularization_weight
            The regularization weight (often denoted :math:`\lambda`),
            by which the residual norm and gradient will be scaled.
        """
        self._regularizers[name] = regularizer
        self._regularization_weights[name] = regularization_weight

    @property
    def regularizers(self) -> dict[str, Regularizer]:
        """ The dictionary of regularizers appended to this loss function."""
        return self._regularizers

    @property
    def regularization_weights(self) -> dict[str, float]:
        """ The dictionary of regularization weights appended to this
        loss function. """
        return self._regularization_weights

    def __str__(self) -> str:
        s = []
        wdt = 74
        s += ['=' * wdt]
        s += [self.__class__.__name__.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, precision=5, linewidth=60, edgeitems=1):
            s += ['{:18} : {}'.format('ResidualCalculator', self._residual_calculator.__class__.__name__)]
            s += ['{:18} : {}'.format('Uses weights', self.use_weights)]
            s += ['{:18} : {}'.format('preconditioner_hash', self.preconditioner_hash)]
            s += ['{:18} : {}'.format('residual_norm_multiplier',
                                      self._residual_norm_multiplier)]
            s += ['{:18} : {}'.format('Function of residual', self._function_as_str)]
            s += ['{:18} : {}'.format('Use preconditioner mask', self.use_preconditioner_mask)]
            s += ['{:18} : {}'.format('hash', hex(hash(self))[2:8])]
        s += ['-' * wdt]
        return '\n'.join(s)

    def _repr_html_(self) -> str:
        s = []
        s += [f'<h3>{__class__.__name__}</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th><th>Data</th></tr></thead>']
        s += ['<tbody>']
        with np.printoptions(threshold=4, edgeitems=2, precision=2, linewidth=40):
            s += ['<tr><td style="text-align: left;">ResidualCalculator</td>']
            s += [f'<td>{1}</td><td>{self._residual_calculator.__class__.__name__}</td></tr>']
            s += ['<tr><td style="text-align: left;">use_weights</td>']
            s += [f'<td>{1}</td><td>{self.use_weights}</td></tr>']
            s += ['<tr><td style="text-align: left;">preconditioner_hash</td>']
            s += [f'<td>{1}</td><td>{self.preconditioner_hash}</td></tr>']
            s += ['<tr><td style="text-align: left;">residual_norm_multiplier</td>']
            s += [f'<td>{1}</td><td>{self._residual_norm_multiplier}</td></tr>']
            s += ['<tr><td style="text-align: left;">Function of residual r</td>']
            s += [f'<td>1</td><td>{self._function_as_tex}</td></tr>']
            s += ['<tr><td style="text-align: left;">Use preconditioner mask</td>']
            s += [f'<td>1</td><td>{self._use_preconditioner_mask}</td></tr>']
            s += ['<tr><td style="text-align: left;">Hash</td>']
            h = hex(hash(self))
            s += [f'<td>{len(h)}</td><td>{h[2:8]}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)

    def __hash__(self) -> int:
        to_hash = [hash(self._residual_calculator),
                   self.use_weights,
                   self._residual_norm_multiplier,
                   self._preconditioner,
                   self._use_preconditioner_mask]
        for r in self.regularizers:
            to_hash.append(hash(self.regularizers[r]))
            to_hash.append(hash(self.regularization_weights[r]))
        return int(list_to_hash(to_hash), 16)
