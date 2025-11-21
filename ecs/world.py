from typing import TypeVar, cast

from ecs.components import Component
from ecs.resources import Resource

T = TypeVar("T", bound=Component)
R = TypeVar("R", bound=Resource)


class World:
    def __init__(self):
        self._next_entity_id: int = 0
        self._entities: set[int] = {}
        self._components: dict[type[Component], dict[int, Component]]
        self._resources: dict[type[Resource], Resource]

    def create_entity(self) -> int:
        entity_id: int = self._next_entity_id
        self._next_entity_id += 1
        self._entities.add(entity_id)
        return entity_id

    def add_component(self, entity: int, component: Component) -> None:
        component_type: type[Component] = type(component)
        if component_type not in self._components:
            self._components[component_type] = {}

        self._components[component_type][entity] = component

    def get_component(self, entity: int, component_type: type[T]) -> T | None:
        component = self._components.get(component_type, {}).get(entity)
        return cast(T | None, component)

    def component_for(self, entity: int, component_type: type[T]) -> T:
        """Get component that must exist (use after querying)"""
        component = self.get_component(entity, component_type)
        assert component is not None, (
            f"Entity {entity} missing {component_type.__name__}"
        )
        return component

    def get_entities_with(self, *component_types: type[Component]) -> set[int]:
        if not component_types:
            return iter(self._entities)

        entity_sets = [
            set(self._components.get(ct, {}).keys()) for ct in component_types
        ]

        return set.intersection(*entity_sets) if entity_sets else set()

    def add_resource(self, resource: Resource) -> None:
        self._resources[type(resource)] = resource

    def get_resource(self, resource_type: type[Resource]) -> Resource | None:
        return self._resources.get(resource_type).instance

    def resource_for(self, resource_type: type[R]) -> R:
        """Get resource that must exist"""
        resource = self.get_resource(resource_type)
        assert resource is not None, f"Missing {resource_type.__name__}"
        return resource

    def has_resource(self, resource_type: type[Resource]) -> bool:
        return resource_type in self._resources
