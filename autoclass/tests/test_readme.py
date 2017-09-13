import pytest
from autoclass import autoargs, autoprops, setter_override, Boolean, minlens, validate, ValidationError, gt, autodict
from typing import List


def test_readme_old_way():
    """ Makes sure that the code in the documentation page is correct for the 'old way' of writing classes """

    from autoclass import check_var, Boolean
    from numbers import Real, Integral
    from typing import Optional, Union

    class HouseConfiguration(object):
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            self.name = name
            self.surface = surface
            self.nb_floors = nb_floors
            self.with_windows = with_windows

        # --name
        @property
        def name(self):
            return self._name

        @name.setter
        def name(self, name: str):
            check_var(name, var_name='name', var_types=str)
            self._name = name

        # --surface
        @property
        def surface(self) -> Real:
            return self._surface

        @surface.setter
        def surface(self, surface: Real):
            check_var(surface, var_name='surface', var_types=Real, min_value=0, min_strict=True)
            self._surface = surface

        # --nb_floors
        @property
        def nb_floors(self) -> Optional[Integral]:
            return self._nb_floors

        @nb_floors.setter
        def nb_floors(self, nb_floors: Optional[Integral]):
            check_var(nb_floors, var_name='nb_floors', var_types=Integral, enforce_not_none=False)
            self._surface = nb_floors  # !**

        # --with_windows
        @property
        def with_windows(self) -> Boolean:
            return self._with_windows

        @with_windows.setter
        def with_windows(self, with_windows: Boolean):
            check_var(with_windows, var_name='with_windows', var_types=Boolean)
            self._with_windows = with_windows

    HouseConfiguration('test', 0.1)


def test_readme_pycontracts():
    """ Makes sure that the code in the documentation page is correct for the PyContracts example """

    from contracts import contract, ContractNotRespected
    from numbers import Real, Integral
    from typing import Optional

    @autoprops
    class HouseConfiguration(object):
        @autoargs
        @contract(name='str[>0]',
                  surface='(int|float),>=0',
                  nb_floors='None|int',
                  with_windows='bool')
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            pass

        # -- overriden setter for surface - no need to repeat the @contract
        @setter_override
        def surface(self, surface: Real):
            assert surface > 0
            self._surface = surface

    t = HouseConfiguration('test', 0.1)
    t.nb_floors = None
    with pytest.raises(ContractNotRespected):
        t.nb_floors = 2.2
    with pytest.raises(ContractNotRespected):
        t.surface = -1


def test_readme_enforce():
    """ Makes sure that the code in the documentation page is correct for the enforce example """

    # from autoclass import autoargs, autoprops, Boolean
    import enforce as en
    from enforce import runtime_validation
    from numbers import Real, Integral
    from typing import Optional

    en.config(dict(mode='covariant'))  # allow subclasses when validating types

    @runtime_validation
    @autoprops
    class HouseConfiguration(object):
        @autoargs
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            pass

        # -- overriden setter for surface for custom validation
        @setter_override
        def surface(self, surface):
            assert surface > 0
            self._surface = surface

    t = HouseConfiguration('test', 12, 2)

    # 'Optional' works
    t.nb_floors = None

    # Type validation works
    from enforce.exceptions import RuntimeTypeError
    with pytest.raises(RuntimeTypeError):
        t.nb_floors = 2.2

    # Custom validation works
    with pytest.raises(AssertionError):
        t.surface = 0


def test_readme_enforce_validate():
    """ Makes sure that the code in the documentation page is correct for the enforce + validate example """

    # from autoclass import autoargs, autoprops, Boolean
    import enforce as en
    from enforce import runtime_validation
    from numbers import Real, Integral
    from typing import Optional

    en.config(dict(mode='covariant'))  # allow subclasses when validating types

    @runtime_validation
    @autoprops
    class HouseConfiguration(object):
        @autoargs
        @validate(name=minlens(0),
                  surface=gt(0))
        def __init__(self,
                     name: str,
                     surface: Real,
                     nb_floors: Optional[Integral] = 1,
                     with_windows: Boolean = False):
            pass

        # -- overriden setter for surface for custom validation or other things
        @setter_override
        def surface(self, surface):
            print('Set surface to {}'.format(surface))
            self._surface = surface

    t = HouseConfiguration('test', 12, 2)

    # 'Optional' works
    t.nb_floors = None

    # Type validation works
    from enforce.exceptions import RuntimeTypeError
    with pytest.raises(RuntimeTypeError):
        t.nb_floors = 2.2

    # Value validation works
    with pytest.raises(ValidationError):
        t.surface = -1

    # Value validation works in constructor
    with pytest.raises(ValidationError):
        HouseConfiguration('', 12, 2)


def test_readme_usage_autoprops_validate():
    @autoprops
    class FooConfigA(object):
        @autoargs
        @validate(a=minlens(0))
        def __init__(self, a: str):
            pass

    t = FooConfigA('rhubarb')

    # check that the generated getters work
    t.a = 'r'
    assert t.a == 'r'

    # check that there are validators on the generated setters
    with pytest.raises(ValidationError):
        t.a = ''  # raises ValidationError


def test_readme_usage_autodict_1():
    """ basic autodict without and with autoargs """

    # ** without autoargs
    @autodict
    class A(object):
        def __init__(self, a: int, b: str):
            self.a = a
            self.b = b

    o = A(1, 'r')
    # o behaves like a read-only dict
    assert o == dict(o)
    assert o == {'a': 1, 'b': 'r'}

    # you can create an object from a dict too thanks to the generated class function
    p = A.from_dict({'a': 2, 'b': 's'})
    assert vars(p) == {'a': 2, 'b': 's'}

    # ** with autoargs
    @autodict
    class B(object):
        @autoargs
        def __init__(self, a: int, b: str):
            pass

    o = B(1, 'r')
    # same results
    assert o == {'a': 1, 'b': 'r'}

    # you can create an object from a dict too thanks to the generated class function
    p = B.from_dict({'a': 2, 'b': 's'})
    assert vars(p) == {'a': 2, 'b': 's'}


def test_readme_usage_autodict_2():
    """ basic autodict with other and private fields """

    @autodict
    class C(object):
        @autoargs
        def __init__(self, a: str, b: List[str]):
            self.non_constructor_arg = 't'
            self._private = 1
            self.__class_private = 't'

    o = C(1, 'r')
    # only fields corresponding to constructor arguments are visible
    assert o == {'a': 1, 'b': 'r'}


def test_readme_usage_autodict_3():

    @autodict(only_constructor_args=False, only_public_fields=False)
    class D(object):
        @autoargs
        def __init__(self, a: str, b: List[str]):
            self.non_constructor_arg = 'b'
            self._private = 1
            self.__class_private = 't'

    o = D(1, 'r')
    # o behaves like a read-only dict, all fields are now visible
    assert o == dict(o)
    assert o == {'a': 1, 'b': 'r',
                 'non_constructor_arg': 'b',
                 '_private': 1,
                 '_D__class_private': 't'}  # notice the name
