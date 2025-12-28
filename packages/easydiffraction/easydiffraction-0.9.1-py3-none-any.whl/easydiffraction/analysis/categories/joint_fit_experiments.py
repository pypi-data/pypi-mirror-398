# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Joint-fit experiment weighting configuration.

Stores per-experiment weights to be used when multiple experiments are
fitted simultaneously.
"""

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import NumericDescriptor
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class JointFitExperiment(CategoryItem):
    """A single joint-fit entry.

    Args:
        id: Experiment identifier used in the fit session.
        weight: Relative weight factor in the combined objective.
    """

    def __init__(
        self,
        *,
        id: str,
        weight: float,
    ) -> None:
        super().__init__()

        self._id: StringDescriptor = StringDescriptor(
            name='id',  # TODO: need new name instead of id
            description='...',
            value_spec=AttributeSpec(
                value=id,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_joint_fit_experiment.id',
                ]
            ),
        )
        self._weight: NumericDescriptor = NumericDescriptor(
            name='weight',
            description='...',
            value_spec=AttributeSpec(
                value=weight,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_joint_fit_experiment.weight',
                ]
            ),
        )

        self._identity.category_code = 'joint_fit_experiment'
        self._identity.category_entry_name = lambda: str(self.id.value)

    @property
    def id(self):
        """Experiment identifier descriptor."""
        return self._id

    @id.setter
    def id(self, value):
        """Set the experiment identifier.

        Args:
            value: New id string.
        """
        self._id.value = value

    @property
    def weight(self):
        """Weight factor descriptor."""
        return self._weight

    @weight.setter
    def weight(self, value):
        """Set the weight factor.

        Args:
            value: New weight value.
        """
        self._weight.value = value


class JointFitExperiments(CategoryCollection):
    """Collection of :class:`JointFitExperiment` items."""

    def __init__(self):
        """Create an empty joint-fit experiments collection."""
        super().__init__(item_type=JointFitExperiment)
