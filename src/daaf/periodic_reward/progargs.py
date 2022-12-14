import dataclasses
from typing import Optional

from daaf.periodic_reward import constants


@dataclasses.dataclass(frozen=True)
class ControlArgs:
    """
    Class holds experiment arguments.
    """

    epsilon: float
    alpha: float
    gamma: float


@dataclasses.dataclass(frozen=True)
class CPRArgs:
    """
    Class holds arguments for cumulative periodic rewards (CPR) experiments.

    Args:
        reward_period: the period for generating cumulative rewards.
        cu_step_mapper: the method to handle cumulative rewards - generally estimating rewards.
        buffer_size: how many steps to keep in memory for reward estimation, if applicable.
        buffer_size_multiplier: if provided, gets multiplied by (num_states x num_actions) to
            determine the `buffer_size` for the reward estimation, if applicable.

    Raises:

    """

    reward_period: int
    cu_step_mapper: str
    buffer_size: Optional[int]
    buffer_size_multiplier: Optional[int]

    def __post_init__(self):
        if (
            self.cu_step_mapper
            and self.cu_step_mapper not in constants.CU_MAPPER_METHODS
        ):
            raise ValueError(
                f"cu_step_mapper value `{self.cu_step_mapper}` is unknown. Should one of: {constants.CU_MAPPER_METHODS}"
            )

        if self.buffer_size is not None and self.buffer_size_multiplier is not None:
            raise ValueError(
                "Either buffer_size or buffer_size_multiplier can be defined, never both:\n"
                + f"\tbuffer_size={self.buffer_size}, buffer_size_multiplier={self.buffer_size_multiplier}"
            )
