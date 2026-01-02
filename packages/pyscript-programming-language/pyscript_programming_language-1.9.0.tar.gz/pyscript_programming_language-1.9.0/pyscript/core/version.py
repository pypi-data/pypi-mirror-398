from .bases import Pys
from .utils.decorators import immutable, inheritable, singleton
from .utils.generic import version_match

from types import MappingProxyType

__version__ = '1.9.0'
__date__ = '28 December 2025, 17:30 UTC+7'

version = f'{__version__} ({__date__})'

TAG_VERSION_MAP = MappingProxyType({
    'a': 'alpha',
    'b': 'beta',
    'rc': 'release candidate',
    'dev': 'development',
    'post': 'post'
})

@singleton
@immutable
@inheritable
class PysVersionInfo(Pys, tuple):

    __slots__ = ()

    def __new_singleton__(cls) -> 'PysVersionInfo':
        match = version_match(__version__)
        if not match:
            raise ValueError(f"invalid format version: {__version__!r}")

        major, minor, micro, pre_full, pre_num1, pre_tag2, pre_num2 = match.groups()

        if pre_full:

            if pre_tag2:
                pre_num = int(pre_num2)
                pre_tag_full = TAG_VERSION_MAP[pre_tag2]
            else:
                pre_num = int(pre_num1)
                pre_tag_full = (
                    TAG_VERSION_MAP[pre_full[0]]
                    if pre_full.startswith(('a', 'b')) else
                    TAG_VERSION_MAP['rc']
                )

        else:
            pre_tag_full = pre_num = None

        global version_info
        version_info = tuple.__new__(cls, (int(major), int(minor), int(micro), pre_tag_full, pre_num))
        return version_info

    @property
    def major(self) -> int:
        return self[0]

    @property
    def minor(self) -> int:
        return self[1]

    @property
    def micro(self) -> int:
        return self[2]

    @property
    def pre_tag(self) -> str | None:
        return self[3]

    @property
    def pre_num(self) -> int | None:
        return self[4]

    @property
    def release(self) -> tuple[int, int, int]:
        return self[0:3]

    def __lt__(self, other: tuple) -> bool:
        return self.release < other

    def __gt__(self, other: tuple) -> bool:
        return self.release > other

    def __le__(self, other: tuple) -> bool:
        return self.release <= other

    def __ge__(self, other: tuple) -> bool:
        return self.release >= other

    def __eq__(self, other: tuple) -> bool:
        return self.release == other

    def __ne__(self, other: tuple) -> bool:
        return self.release != other

    def __repr__(self) -> str:
        return (
            'VersionInfo('
                f'major={self.major!r}, '
                f'minor={self.minor!r}, '
                f'micro={self.micro!r}' +
                (
                    ''
                    if self.pre_tag is None else
                    ', '
                    f'pre_tag={self.pre_tag!r}, '
                    f'pre_num={self.pre_num!r}'
                ) +
            ')'
        )

PysVersionInfo()