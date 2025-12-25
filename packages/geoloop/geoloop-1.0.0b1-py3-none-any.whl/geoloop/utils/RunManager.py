import time

import numpy as np
from scipy.stats import lognorm, norm, triang, uniform
from tqdm import tqdm

from geoloop.bin.SingleRunSim import SingleRun, optimize_forkeys
from geoloop.configuration import SingleRunConfig
from geoloop.geoloopcore.simulationparameters import SimulationParameters
from geoloop.utils.helpers import get_param_names


def sample_parameter_space(config: SingleRunConfig) -> tuple[dict, list[str]]:
    """
    Sample the model parameter space based on definitions provided in `config`.

    Parameters
    ----------
    config : SingleRunConfig
        Object containing parameter definitions. Must include:
        ``n_samples`` : int
            Number of Monte Carlo samples to generate.
        Remaining keys should define either:
            * A fixed numerical value, or
            * A distribution definition list: [dist_type, p1, p2, (optional p3)]
              where dist_type ∈ {"normal", "uniform", "lognormal", "triangular"}.

    Returns
    -------
    sample_space : dict of array-like
        Dictionary mapping parameter names → sampled values with shape ``(n_samples,)``.
    varying_parameters : list of str
        List of parameter names that were sampled from statistical distributions.

    Notes
    -----
    Locked parameters (non-varying) are broadcast to all samples.
    """
    variables_config = config.variables_config
    n_samples = variables_config.n_samples

    sample_space = dict()

    variable_param_names, locked_param_names = get_param_names(config)

    np.random.seed(1)
    varying_parameters = []

    for param_name in variable_param_names:
        dist = getattr(variables_config, param_name)

        if isinstance(dist, tuple):
            dist_name = dist[0].lower()
            varying_parameters.append(param_name)

            if dist_name == "normal":
                mean, std_dev = dist[1], dist[2]
                samples = norm(loc=mean, scale=std_dev).rvs(size=n_samples)
            elif dist_name == "uniform":
                min, max = dist[1], dist[2]
                samples = uniform(loc=min, scale=max - min).rvs(size=n_samples)

            elif dist_name == "lognormal":
                mu, sigma = dist[1], dist[2]
                samples = lognorm(s=sigma, scale=np.exp(mu)).rvs(n_samples)

            elif dist_name == "triangular":
                min, peak, max = dist[1], dist[2], dist[3]
                samples = triang(
                    loc=min, scale=max - min, c=(peak - min) / (max - min)
                ).rvs(size=n_samples)

            else:
                raise ValueError(f"Unknown distribution '{dist_name}' in {param_name}")

            sample_space[param_name] = samples
            continue

        # Case 2: No distribution → lock to fixed value in main config
        fixed_value = getattr(config, param_name)
        sample_space[param_name] = np.full(n_samples, float(fixed_value))

    # broadcast locked (non-varying) parameters
    for param_name in locked_param_names:
        sample_space[param_name] = [
            getattr(config, param_name) for _ in range(n_samples)
        ]

    return sample_space, varying_parameters


def run_models(config: SingleRunConfig) -> tuple[dict, list]:
    """
    Execute Monte Carlo model runs based on sampled parameters.

    Parameters
    ----------
    config : SingleRunConfig

        Model configuration. Must include:
        ``n_samples`` : int
            Number of stochastic simulations.
        Must also be compatible with ``sample_parameter_space`` and
        ``SingleRun.from_config``.

    Returns
    -------
    parameters : dict
        Sampled input parameter space with arrays sized ``(n_samples,)``.
    results : list
        List of SingleRunResult model result objects, one per sample.
    """
    parameters, varying_param = sample_parameter_space(
        config
    )  # parameters = sample space

    n_samples = config.variables_config.n_samples
    print(f"Running {n_samples} models")
    print("Varying: {}".format(", ".join(varying_param)))
    time.sleep(0.1)  # For pretty printing

    base_dict = config.model_dump(serialize_as_any=True)

    results = []
    for a in tqdm(range(n_samples)):
        # Inject sampled parameters
        for key in parameters:
            try:
                base_dict[key] = parameters[key][a]
            except:
                print("Parameter assignment error for:", key)

        # Create SimulationParameters and update time in the base_dict
        sim_params = SimulationParameters.from_config(config)
        base_dict["time"] = sim_params.time

        # Optional optimization
        if config.dooptimize:
            cop_crit = config.copcrit
            optimize_keys = config.optimize_keys
            optimize_bounds = config.optimize_keys_bounds

            print(f"Optimizing flow rate for COP: {cop_crit}")
            if config.dploopcrit:
                print(f"Maximum pressure constraint: {config.dploopcrit}")
            print(f"Optimizing keys: {optimize_keys}")
            print(f"Bounds: {optimize_bounds}")

            # find optimized config parameters
            _, optimized_params = optimize_forkeys(
                base_dict, cop_crit, optimize_keys, optimize_bounds, a
            )
            # Update the parameters dict with the optimized values
            for key in optimize_keys:
                parameters[key][a] = optimized_params[key]

        sample_config = SingleRunConfig(**base_dict)

        # Run full model
        single_run = SingleRun.from_config(sample_config)
        run_result = single_run.run(a)
        results.append(run_result)

    return parameters, results
