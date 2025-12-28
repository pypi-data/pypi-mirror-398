# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi


def document_from_path(path: str) -> gemmi.cif.Document:
    """Read a CIF document from a file path."""
    return gemmi.cif.read_file(path)


def document_from_string(text: str) -> gemmi.cif.Document:
    """Read a CIF document from a raw text string."""
    return gemmi.cif.read_string(text)


def pick_sole_block(doc: gemmi.cif.Document) -> gemmi.cif.Block:
    """Pick the sole data block from a CIF document."""
    return doc.sole_block()


def name_from_block(block: gemmi.cif.Block) -> str:
    """Extract a model name from the CIF block name."""
    # TODO: Need validator or normalization?
    return block.name


# def experiment_type_from_block(
#        exp_type: ExperimentType,
#        block: gemmi.cif.Block,
# ) -> dict:
#    """Extract experiment type information from a CIF block."""
#    for param in exp_type.parameters:
#        param.from_cif(block)
