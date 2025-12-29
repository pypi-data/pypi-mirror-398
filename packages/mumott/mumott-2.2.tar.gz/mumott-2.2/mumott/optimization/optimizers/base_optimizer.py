import sys
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Tuple

import tqdm
import numpy as np

from mumott.optimization.loss_functions.base_loss_function import LossFunction

logger = logging.getLogger(__name__)


class Optimizer(ABC):

    """This is the base class from which specific optimizers are derived.
    """

    def __init__(self,
                 loss_function: LossFunction,
                 **kwargs: Dict[str, Any]):
        self._loss_function = loss_function

        if 'no_tqdm' in kwargs:
            self._no_tqdm = kwargs.pop('no_tqdm')
        else:
            self._no_tqdm = False
        # empty kwargs automatically yields empty dict
        self._options = kwargs

    # set, get and iter methods for kwargs interface
    def __setitem__(self, key: str, val: Any) -> None:
        """ Sets options akin to ``**kwargs`` during initialization. Allows
        access to instance as a dictionary.

        Parameters
        ----------
        key
            The key used in ``dict``-like interface to instance.
        val
            The value to store in association with ``key``.
        """
        if key not in self._options.keys():
            logger.info(f'Key {key} added to options with value {val}.')
        self._options[key] = val

    def __getitem__(self, key: str) -> Any:
        """ Sets options akin to ``**kwargs`` during initialization. Allows
        access to instance as a dictionary.

        Parameters
        ----------
        key
            The key used in ``dict``-like interface to instance.
        val
            The value to store in association with ``key``.
        Returns
            Value stored in association with ``key``
        """
        if key in self._options.keys():
            return self._options[key]
        else:
            raise KeyError(f'Unrecognized key: {key}')

    def __iter__(self) -> Iterator[Tuple[str, Any]]:
        """ Allows casting as dict and use as an iterator. """
        for t in self._options.items():
            yield t

    @property
    def no_tqdm(self):
        """Whether to avoid making a ``tqdm`` progress bar."""
        return self._no_tqdm

    def _tqdm(self, length: int):
        """
        Returns tqdm iterable, unless ``no_tqdm`` is set to true, in which case
        it returns a ``range``.
        """
        if self._no_tqdm:
            return range(length)
        else:
            return tqdm.tqdm(range(length), file=sys.stdout)

    @abstractmethod
    def optimize(self) -> Dict:
        """ Function for executing the optimization. Should return a ``dict`` of the
        optimization results. """
        pass

    def __str__(self) -> str:
        wdt = 74
        s = []
        s += ['=' * wdt]
        s += [__class__.__name__.center(wdt)]
        s += ['-' * wdt]
        with np.printoptions(threshold=4, precision=5, linewidth=60, edgeitems=1):
            s += ['{:18} : {}'.format('LossFunction', self._loss_function.__class__.__name__)]
            s += ['{:18} : {}'.format('hash', hex(hash(self))[2:8])]
            for key, value in self._options.items():
                s += ['{:18} : {}'.format(f'option[{key}]', value)]
        s += ['-' * wdt]
        return '\n'.join(s)

    def _repr_html_(self) -> str:
        s = []
        s += [f'<h3>{__class__.__name__}</h3>']
        s += ['<table border="1" class="dataframe">']
        s += ['<thead><tr><th style="text-align: left;">Field</th><th>Size</th><th>Data</th></tr></thead>']
        s += ['<tbody>']
        with np.printoptions(threshold=4, edgeitems=2, precision=2, linewidth=40):
            s += ['<tr><td style="text-align: left;">LossFunction</td>']
            s += [f'<td>{1}</td><td>{self._loss_function.__class__.__name__}</td></tr>']
            h = hex(hash(self))
            s += ['<tr><td style="text-align: left;">Hash</td>']
            s += [f'<td>{len(h)}</td><td>{h[2:8]}</td></tr>']
            for key, value in self._options.items():
                s += [f'<tr><td style="text-align: left;">options[{key}]</td>']
                s += [f'<td>{1}</td><td>{value}</td></tr>']
        s += ['</tbody>']
        s += ['</table>']
        return '\n'.join(s)
