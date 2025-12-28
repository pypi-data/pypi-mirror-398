from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import CifHandler
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.utils.logging import Logger
from easydiffraction.utils.logging import log

Logger.configure(
    level=Logger.Level.DEBUG,
    mode=Logger.Mode.COMPACT,
    reaction=Logger.Reaction.WARN,
)


class Cell(CategoryItem):
    def __init__(self, *, length_a=None):
        super().__init__()

        self._length_a = Parameter(
            value_spec=AttributeSpec(
                value=length_a,
                default=10.0,
                content_validator=RangeValidator(ge=0, le=1000),
            ),
            name='length_a',
            description='Length of the a-axis of the unit cell.',
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_a']),
        )

    @property
    def length_a(self) -> Parameter:
        """Parameter representing the a-axis length of the unit cell."""
        return self._length_a

    @length_a.setter
    def length_a(self, v):
        """Assign a raw value to length_a (validated internally)."""
        self._length_a.value = v


# ---------------------- Example usage ---------------------- #

if __name__ == '__main__':
    c = Cell()

    c.length_a.value = 1.234
    log.info(f'c.length_a.value: {c.length_a.value}')

    c.length_a.value = -5.5
    log.info(f'c.length_a.value: {c.length_a.value}')

    c.length_a.value = 'xyz'
    log.info(f'c.length_a.value: {c.length_a.value}')

    c.length_a.free = True
    log.info(f'c.length_a.free: {c.length_a.free}')

    c.length_a.free = 'oops'
    log.info(f'c.length_a.free: {c.length_a.free}')

    c.length_a = 'xyz'
    log.info(f'c.length_a.value (after direct assign attempt): {c.length_a.value}')

    c_bad = Cell(length_a='xyz')
    log.info(f'c_bad.length_a.value: {c_bad.length_a.value}')

    c_ok = Cell(length_a=2.5)
    log.info(f'c_ok.length_a.value: {c_ok.length_a.value}')

    c_ok.length_a.description = 'read-only'
    log.info(f'c_ok.length_a.description: {c_ok.length_a.description}')

    c_ok.length_a.aaa = 'aaa'
    log.info(f'c_ok.length_a.aaa: {c_ok.length_a.aaa}')

    log.info(f'c_ok.length_a.bbb: {c_ok.length_a.bbb}')

    log.info(f'c_ok.length_a.fre: {c_ok.length_a.fre}')

    log.info(c.as_cif)
    log.info(c.length_a.as_cif)

    log.info(c.length_a._cif_handler.uid)
