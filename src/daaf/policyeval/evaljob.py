"""
Module contains job to run policy evaluation with replay mappers.
"""

import argparse
import dataclasses
import logging
import random
from typing import Any, Mapping, Optional, Sequence, Tuple

import ray

from daaf import expconfig, task, utils
from daaf.policyeval import evaluation


@dataclasses.dataclass(frozen=True)
class EvalPipelineArgs:
    """
    Program arguments.
    """

    # problem args
    envs_path: str
    config_path: str
    num_runs: int
    num_episodes: int
    assets_dir: int
    output_dir: str
    log_episode_frequency: int
    task_prefix: str
    # ray args
    cluster_uri: Optional[str]


def main(args: EvalPipelineArgs):
    """
    Program entry point.
    """

    ray_env = {}
    logging.info("Ray environment: %s", ray_env)
    with ray.init(args.cluster_uri, runtime_env=ray_env) as context:
        logging.info("Ray Context: %s", context)
        logging.info("Ray Nodes: %s", ray.nodes())

        tasks_futures = create_tasks(
            envs_path=args.envs_path,
            config_path=args.config_path,
            num_runs=args.num_runs,
            num_episodes=args.num_episodes,
            assets_dir=args.assets_dir,
            output_dir=args.output_dir,
            task_prefix=args.task_prefix,
            log_episode_frequency=args.log_episode_frequency,
        )

        # since ray tracks objectref items
        # we swap the key:value
        futures = [future for _, future in tasks_futures]
        unfinished_tasks = futures
        while True:
            finished_tasks, unfinished_tasks = ray.wait(unfinished_tasks)
            for finished_task in finished_tasks:
                logging.info(
                    "Completed task %s, %d left out of %d.",
                    ray.get(finished_task),
                    len(unfinished_tasks),
                    len(futures),
                )

            if len(unfinished_tasks) == 0:
                break


def create_tasks(
    envs_path: str,
    config_path: str,
    num_runs: int,
    num_episodes: int,
    assets_dir: str,
    output_dir: str,
    task_prefix: str,
    log_episode_frequency: int,
) -> Sequence[Tuple[ray.ObjectRef, expconfig.ExperimentTask]]:
    """
    Runs numerical experiments on policy evaluation.
    """
    envs_configs = expconfig.parse_environments(envs_path=envs_path)
    experiment_configs = expconfig.parse_experiment_configs(
        config_path=config_path,
    )
    experiments = tuple(
        expconfig.create_experiments(
            envs_configs=envs_configs,
            experiment_configs=experiment_configs,
        )
    )
    experiments_and_context = add_experiment_context(experiments, assets_dir=assets_dir)
    experiment_tasks = tuple(
        expconfig.generate_tasks_from_experiments_context_and_run_config(
            run_config=expconfig.RunConfig(
                num_episodes=num_episodes,
                log_episode_frequency=log_episode_frequency,
                output_dir=output_dir,
            ),
            experiments_and_context=experiments_and_context,
            num_runs=num_runs,
            task_prefix=task_prefix,
        )
    )
    # shuffle tasks to balance workload
    experiment_tasks = random.sample(experiment_tasks, len(experiment_tasks))
    logging.info(
        "Parsed %d DAAF configs and %d environments into %d tasks",
        len(experiment_configs),
        len(envs_configs),
        len(experiment_tasks),
    )
    futures = []
    for exp_task in experiment_tasks:
        future = evaluate.remote(exp_task)
        futures.append((exp_task, future))
    return futures


def add_experiment_context(
    experiments: Sequence[expconfig.Experiment], assets_dir: str
) -> Sequence[Tuple[expconfig.Experiment, Mapping[str, Any]]]:
    """
    Enriches expeirment config with context.
    """
    dyna_prog_specs = []
    for experiment in experiments:
        env_spec = task.create_env_spec(
            problem=experiment.env_config.name, env_args=experiment.env_config.args
        )
        dyna_prog_specs.append(
            (
                env_spec.name,
                env_spec.level,
                experiment.learning_args.discount_factor,
                env_spec.mdp,
            )
        )

    dyna_prog_index = utils.DynaProgStateValueIndex.build_index(
        specs=dyna_prog_specs, path=assets_dir
    )

    experiments_and_context = []
    for experiment, (name, level, gamma, _) in zip(experiments, dyna_prog_specs):
        experiments_and_context.append(
            (
                experiment,
                {
                    "dyna_prog_state_values": dyna_prog_index.get(
                        name, level, gamma
                    ).tolist(),  # so it can be serialized
                },
            )
        )
    return experiments_and_context


@ray.remote
def evaluate(experiment_task: expconfig.ExperimentTask) -> str:
    """
    Runs evaluation.
    """
    task_id = f"{experiment_task.exp_id}/{experiment_task.run_id}"
    logging.info("Experiment %s starting", task_id)
    evaluation.run_fn(experiment_task)
    logging.info("Experiment %s finished", task_id)
    return task_id


def parse_args() -> EvalPipelineArgs:
    """
    Parses program arguments.
    """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--envs-path", type=str, required=True)
    arg_parser.add_argument("--config-path", type=str, required=True)
    arg_parser.add_argument("--num-runs", type=int, required=True)
    arg_parser.add_argument("--num-episodes", type=int, required=True)
    arg_parser.add_argument("--assets-dir", type=str, required=True)
    arg_parser.add_argument("--output-dir", type=str, required=True)
    arg_parser.add_argument("--log-episode-frequency", type=int, required=True)
    arg_parser.add_argument("--task-prefix", type=str, required=True)
    arg_parser.add_argument("--cluster-uri", type=str, default=None)
    known_args, unknown_args = arg_parser.parse_known_args()
    logging.info("Unknown args: %s", unknown_args)
    return EvalPipelineArgs(**vars(known_args))


if __name__ == "__main__":
    main(parse_args())
