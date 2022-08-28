"""
Experiment constants.
"""


IDENTITY_MAPPER = "identity-mapper"
SINGLE_STEP_MAPPER = "single-step-mapper"
AVERAGE_REWARD_MAPPER = "average-reward-mapper"
REWARD_ESTIMATION_LS_MAPPER = "reward-estimation-ls-mapper"
REWARD_IMPUTATION_MAPPER = "reward-imputation-mapper"
CUMULATIVE_REWARD_MAPPER = "cumulative-reward-mapper"
CU_MAPPER_METHODS = (
    IDENTITY_MAPPER,
    SINGLE_STEP_MAPPER,
    AVERAGE_REWARD_MAPPER,
    REWARD_IMPUTATION_MAPPER,
    REWARD_ESTIMATION_LS_MAPPER,
    CUMULATIVE_REWARD_MAPPER,
)

DEFAULT_BUFFER_SIZE_MULTIPLIER = 2**8
