# Copyright 2025 Global Computing Lab.
# See top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

from typing import Any, Mapping


class AnnotationType:
    def __init__(self):
        self.annotations_attr = {}

    @property
    def annotations(self):
        return self.annotations_attr

    @annotations.setter
    def annotations(self, val: Mapping[str, Any]):
        if not isinstance(val, Mapping):
            raise TypeError("Cannot store a non-Mapping object as annotations")
        self.annotations_attr = val
