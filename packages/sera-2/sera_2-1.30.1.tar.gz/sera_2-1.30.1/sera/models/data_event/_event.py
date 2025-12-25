from __future__ import annotations

from dataclasses import dataclass, field

from sera.models.data_event._action import EventAction
from sera.models.data_event._condition import EventCondition


@dataclass
class DataEvent:
    """Represents a reactive data event with conditions and actions.

    When the condition is met, all actions are executed.
    This enables conditional validation, normalization, and data dependencies.

    Example YAML:
    ```yaml
    events:
      - when:
          - field: type
            operator: eq
            value: 'NoVAT'
        then:
          - action_type: clear_value
            target_field: value
          - action_type: set_optional
            target_field: value
    ```
    """

    # Condition that triggers this event (CNF expression)
    when: EventCondition
    # List of actions to execute when condition is met
    then: list[EventAction] = field(default_factory=list)
