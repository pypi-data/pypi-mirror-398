# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.analysis.categories.joint_fit_experiments import JointFitExperiment
from easydiffraction.analysis.categories.joint_fit_experiments import JointFitExperiments


def test_joint_fit_experiment_and_collection():
    j = JointFitExperiment(id='ex1', weight=0.5)
    assert j.id.value == 'ex1'
    assert j.weight.value == 0.5
    coll = JointFitExperiments()
    coll.add(id='ex1', weight=0.5)
    assert 'ex1' in coll.names
    assert coll['ex1'].weight.value == 0.5
