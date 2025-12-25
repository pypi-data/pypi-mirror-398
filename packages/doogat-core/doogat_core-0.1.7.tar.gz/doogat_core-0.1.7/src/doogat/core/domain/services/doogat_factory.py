"""
This module defines the DoogatFactory class which is responsible for creating instances of :class:`doogat_entities.Zettel`.

Imports:
    - :class:`doogat.core.domain.entities` for accessing Doogat entities.
    - :class:`buvis.pybase.formatting.StringOperator` for string operations.
"""

import doogat.core.domain.entities as doogat_entities
from buvis.pybase.formatting import StringOperator


class DoogatFactory:
    """
    A factory class for creating Doogats.

    Doogat is downcasted Zettel entity based on the zettel type.
    """

    @staticmethod
    def create(zettel: doogat_entities.Zettel) -> doogat_entities.Zettel:
        """
        Create a Zettel instance, potentially downcasting it to a more specific type based on its 'type' attribute.

        :param zettel: The original Zettel instance.
        :type zettel: :class:`doogat.core.domain.entities.zettel.zettel.Zettel`
        :return: A Zettel instance, either the original or a downcasted version (aka Doogat).
        :rtype: :class:`doogat.core.domain.entities.zettel.zettel.Zettel`
        """
        zettel_type = getattr(zettel, "type", "")

        if zettel_type in ("note", ""):  # generic Zettel
            return zettel

        # Try downcasting to more specific Zettel type
        class_name = StringOperator.camelize(zettel_type) + "Zettel"

        try:
            entity_class = getattr(doogat_entities, class_name)
        except AttributeError:
            return zettel
        else:
            downcasted_zettel = entity_class()
            downcasted_zettel.replace_data(zettel.get_data())
            return downcasted_zettel
