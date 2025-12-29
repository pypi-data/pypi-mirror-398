# -*- coding: utf-8 -*-
from .laplacian import Laplacian
from .l1_norm import L1Norm
from .l2_norm import L2Norm
from .huber_norm import HuberNorm
from .total_variation import TotalVariation
from .group_lasso import GroupLasso


__all__ = [
    'HuberNorm',
    'Laplacian',
    'L1Norm',
    'L2Norm',
    'TotalVariation',
    'GroupLasso',
]
