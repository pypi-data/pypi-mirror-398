# SPDX-License-Identifier: MIT-HUMAINS-Attribution
#
# Copyright (c) 2024 HUMAINS Research Group (University of Córdoba, Spain).
# Copyright (c) 2024 The authors.
# All rights reserved.
#
# MIT License – HUMAINS Research Group Attribution Variant
# For full license text, see the LICENSE file in the repository root.

"""
Model selection module for the Genetic Programming algorithm.
"""

from ._split import BaseCrossValidator, KFold, StratifiedKFold, train_test_split

__all__ = [
    'BaseCrossValidator',
    'KFold',
    'StratifiedKFold',
    'train_test_split',
]
