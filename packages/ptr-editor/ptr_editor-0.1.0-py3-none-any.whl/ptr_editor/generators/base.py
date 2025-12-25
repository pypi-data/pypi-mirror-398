from attrs_xml import element_define
from ptr_editor import PtrElement
from ptr_solver.solvable_mixin import PtrSolvableMixin


from attrs import define


@element_define
class PtrElementGenerator(PtrElement, PtrSolvableMixin):
    """Base class for PTR element generators at any level."""

    def _element_generate_(self) -> PtrElement: ...


    def generate_ptr_element(self) -> PtrElement:
        """
        Generate the PTR element using the generator.

        Returns:
            Generated PTR element
        """
        return self._element_generate_()

    