from __future__ import annotations

from dataclasses import dataclass

from sera.misc._utils import filter_duplication
from sera.models._class import Class
from sera.models._property import DataProperty, ObjectProperty


@dataclass
class DataCollection:
    """Represent a data collection, which can be a class or a data product created via some transformation."""

    cls: Class

    @property
    def name(self) -> str:
        """Get the name of the collection."""
        return self.cls.name

    def get_pymodule_name(self) -> str:
        """Get the python module name of this collection as if there is a python module created to store this collection only."""
        return self.cls.get_pymodule_name()

    def get_queryable_fields(
        self,
    ) -> list[
        DataProperty | ObjectProperty | tuple[DataProperty | ObjectProperty, ...]
    ]:
        """Get the fields of this collection that can be used in a queries."""
        output: list[
            DataProperty | ObjectProperty | tuple[DataProperty | ObjectProperty, ...]
        ] = []
        for prop in self.cls.properties.values():
            if prop.db is None or prop.data.is_private:
                # This property is not stored in the database or it's private, so we skip it
                continue
            if (
                isinstance(prop, DataProperty)
                and prop.db is not None
                and not prop.db.is_indexed
            ):
                # This property is not indexed, so we skip it
                continue
            if isinstance(prop, ObjectProperty) and prop.target.db is None:
                # TODO: Implement this! This property is an embedded object property, we need to figure out
                # which necessary properties are queryable and add them to the field names
                continue

            output.append(prop)

        # composite indexes are also queryable
        # e.g. (tenant_id & email)
        if self.cls.db is not None:
            for index in self.cls.db.indices:
                composite_cols = []
                for col in index.columns:
                    composite_cols.append(self.cls.properties[col])

                if len(composite_cols) == 1:
                    output.append(composite_cols[0])
                else:
                    output.append(tuple(composite_cols))

        return filter_duplication(
            output,
            lambda x: (
                x.name
                if isinstance(x, (DataProperty, ObjectProperty))
                else tuple(p.name for p in x)
            ),
        )

    def get_join_queryable_fields(
        self,
    ) -> dict[str, list[DataProperty | ObjectProperty]]:
        """Get the fields of this collection that can be used in join queries."""
        output = {}
        for prop in self.cls.properties.values():
            if (
                isinstance(prop, DataProperty)
                and prop.db is not None
                and prop.db.foreign_key is not None
            ):
                # This property is a foreign key, so we add it to the output
                output[prop.name] = DataCollection(
                    prop.db.foreign_key
                ).get_queryable_fields()
            elif isinstance(prop, ObjectProperty) and prop.target.db is not None:
                output[prop.name] = DataCollection(prop.target).get_queryable_fields()

            assert all(
                all(isinstance(f, (DataProperty, ObjectProperty)) for f in fields)
                for fields in output.values()
            ), "All join queryable fields must be DataProperty or ObjectProperty"
        return output

    def get_service_name(self):
        return f"{self.name}Service"
