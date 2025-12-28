# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.core.validation as MUT

    expected_module_name = 'easydiffraction.core.validation'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_type_validator_accepts_and_rejects(monkeypatch):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.utils.logging import log

    # So that errors do not raise in test process
    log.configure(reaction=log.Reaction.WARN)

    spec = AttributeSpec(type_=DataTypes.STRING, default='abc')
    # valid
    expected = 'xyz'
    actual = spec.validated('xyz', name='p')
    assert expected == actual
    # invalid -> fallback to default
    expected_fallback = 'abc'
    actual_fallback = spec.validated(10, name='p')
    assert expected_fallback == actual_fallback


def test_range_validator_bounds(monkeypatch):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.core.validation import RangeValidator
    from easydiffraction.utils.logging import log

    log.configure(reaction=log.Reaction.WARN)
    spec = AttributeSpec(
        type_=DataTypes.NUMERIC, default=1.0, content_validator=RangeValidator(ge=0, le=2)
    )
    # inside range
    expected = 1.5
    actual = spec.validated(1.5, name='p')
    assert expected == actual
    # outside -> fallback default
    expected_fallback = 1.0
    actual_fallback = spec.validated(5.0, name='p')
    assert expected_fallback == actual_fallback


def test_membership_and_regex_validators(monkeypatch):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import MembershipValidator
    from easydiffraction.core.validation import RegexValidator
    from easydiffraction.utils.logging import log

    log.configure(reaction=log.Reaction.WARN)
    mspec = AttributeSpec(default='b', content_validator=MembershipValidator(['a', 'b']))
    assert mspec.validated('a', name='m') == 'a'
    # reject -> fallback default
    assert mspec.validated('c', name='m') == 'b'

    rspec = AttributeSpec(default='a1', content_validator=RegexValidator(r'^[a-z]\d$'))
    assert rspec.validated('b2', name='r') == 'b2'
    assert rspec.validated('BAD', name='r') == 'a1'
