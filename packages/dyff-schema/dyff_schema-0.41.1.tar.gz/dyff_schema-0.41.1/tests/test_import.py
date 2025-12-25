# SPDX-FileCopyrightText: 2024 UL Research Institutes
# SPDX-License-Identifier: Apache-2.0

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "dyff.schema",
        "dyff.schema.io",
        "dyff.schema.io.vllm",
        "dyff.schema.adapters",
        "dyff.schema.base",
        "dyff.schema.requests",
        "dyff.schema.ids",
        "dyff.schema.quantity",
        "dyff.schema.platform",
        "dyff.schema.copydoc",
        "dyff.schema.dataset",
        "dyff.schema.dataset.binary",
        "dyff.schema.dataset.text",
        "dyff.schema.dataset.arrow",
        "dyff.schema.dataset.vision",
        "dyff.schema.dataset.classification",
        "dyff.schema.v0",
        "dyff.schema.v0.r1",
        "dyff.schema.v0.r1.io",
        "dyff.schema.v0.r1.io.vllm",
        "dyff.schema.v0.r1.adapters",
        "dyff.schema.v0.r1.base",
        "dyff.schema.v0.r1.dataset",
        "dyff.schema.v0.r1.dataset.binary",
        "dyff.schema.v0.r1.dataset.text",
        "dyff.schema.v0.r1.dataset.arrow",
        "dyff.schema.v0.r1.dataset.vision",
        "dyff.schema.v0.r1.dataset.classification",
        "dyff.schema.v0.r1.platform",
        "dyff.schema.v0.r1.requests",
        "dyff.schema.v0.r1.version",
        "dyff.schema.v0.r1.test",
        "dyff.schema.version",
        "dyff.schema.test",
    ],
)
def test_import_module(module_name):
    importlib.import_module(module_name)
