from typing import Any, Optional, Literal
import requests

from .driver import Driver, Minimizer, LeastSquaresDriver
from ..requestor import OptimizerRequestor

class ActiveLearningDriver(Driver):
    def describe(self) -> dict[str, Any]:
        """Get description of all modules and their parameters that are used
        by the driver. Example::

            description = driver.describe()
            print(description["members"]["surrogates"]["0"])

        Returns: A nested dictionary with description of submodules consisting
               of a name and a descriptive text. If the entry describes a module,
               it has an additional ``"members"`` entry with dictionaries describing
               submodules and parameters. If the entry describes a parameter,
               it has an additional entry ``"settable"``, which is true if the parameter
               can be overridden by the client (see :func:`override_parameter`).
        """
        return super().describe()

    def override_parameter(self, path: str, value: Any) -> None:
        """Override an internal parameter of the driver that is otherwise
        selected automatically. Example::

            driver.override_parameter(
                "surrogates.0.matrix.kernel.design_length_scales",
                [1.0, 2.0]
            )

        Args:
          path: A dot-separated path to the parameter to be overridden.
          value: The new value of the parameter.

        .. note:: A description of the meaning of each parameter can be retrieved
            by :func:`describe`.
        """
        self._post(
            "override parameter of the driver",
            "driver",
            "override_parameter",
            data={"path": path, "value": value},
        )

    def get_observed_values(
        self,
        object_type: Literal["variable", "objective"] = "objective",
        name: str = "objective",
        num_samples: Optional[int] = None,
    ) -> dict[str, Any]:
        """Get observed values and variances of variables or objectives. For noisy
        input data, the values are obtained on the basis of predictions of the
        surrogate models. Therefore, they can slightly differ from the input data.
        Example::

            data = driver.get_observed_values("variable", "loss")

        Args:
          object_type: The type of object for which a prediction
              is required.
          name: The name of the object for which predictions are required.
          num_samples: Number of samples used for posteriors that have
              a sampling-based distribution.
              If not specified, the same number as in the acquisition is used.
              If the posterior is described by a fixed number of ensemble points,
              the minimum of num_samples and the ensemble size is used.


        Returns: Dictionary, with the following keys:

            :samples: The observed samples (design and possibly environment values).
            :means: Mean values of observations. For noiseless observations, this
                is the observed value itself.
            :variance: Variance of observed values. For noiseless observations, this is
                typically a negligibly small number.

        """
        answer = self._post(
            "get observed values",
            "driver",
            "get_observed_values",
            data={
                "object_type": object_type,
                "name": name,
                "num_samples": num_samples,
            },
        )
        return answer["observed_values"]

    def predict(
        self,
        points: list[list[float]],
        object_type: Literal["surrogate", "variable", "objective"] = "objective",
        name: str = "objective",
        output_type: Literal["mean_var", "quantiles", "samples"] = "mean_var",
        min_dist: float = 0.0,
        quantiles: Optional[list[float]] = None,
        num_samples: Optional[int] = None,
    ) -> dict[str, list]:
        """Make predictions on various objects.
        Example::

            prediction = driver.predict(points=[[1,0,0],[2,0,1]])
        
        Args:
          points: Vectors of the space (design space + environment)
              of shape ``(num_points, num_dim)``
          object_type: The type of object for which a prediction
              is required.
          name: The name of the object for which predictions are required.
          output_type: The type of output.
            Options are:

              :mean_var: Mean and variance of the posterior distribution.
                   This describes the posterior distribution only for
                   normally distributed posteriors. The function returns a
                   dictionary with keywords ``"mean"`` and ``"variance"``
                   mapping to array of length num_points. If the posterior
                   distribution is multivariate normal, for each point
                   a covariance matrix of shape ``(output_dim, output_dim)``
                   is returned, otherwise a list of variances of shape
                   ``(output_dim,)`` is returned.
              :quantiles: A list of quantiles of the distribution is
                   estimated based on samples drawn from the distribution.
                   The function returns a dict with entry ``"quantiles"``
                   and a tensor of shape ``(num_quantiles, num_points, output_dim)``
              :samples: Random samples drawn from the posterior distribution.
                   The function returns a dict with the entry ``"samples"``
                   and a tensor of shape ``(num_samples, num_points, output_dim)``

          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.
          quantiles: A list with quantiles. If not specified, the quantiles
              [0.16,0.5,0.84] are used.
          num_samples: Number of samples used for posteriors that have
              a sampling-based distribution or if output_type is "samples".
              If not specified, the same number as in the acquisition is used.
              If the posterior is described by a fixed number of ensemble points,
              the minimum of num_samples and the ensemble size is used.

        Returns: A dictionary with the entries "mean" and "variance" if
            ``output_type = "mean_var"`` and "samples" if ``output_type = "samples"``
        """

        answer = self._post(
            "get prediction",
            "driver",
            "predict",
            data={
                "points": points,
                "object_type": object_type,
                "name": name,
                "output_type": output_type,
                "min_dist": min_dist,
                "quantiles": quantiles,
                "num_samples": num_samples,
            },
        )
        return answer["prediction"]

    def optimize_hyperparameters(
        self, path: Optional[str] = None, num_samples: int = 1, min_dist: float = 0.0
    ) -> None:
        """Optimize the hyperparameters of submodules of the driver.
        This is usually done automatically.
        Example::

            driver.optimize_hyperparameters("driver.surrogates.0")

        Args:
          path: A dot-separated path to a submodule. If no path is specified,
              all submodules are optimized.
          num_samples: Number of initial start samples for optimization
             (default: automatic determination)
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.
        """
        self._run_task(
            "optimize hyperparameters",
            "optimize_hyperparameters",
            data={"path": path, "num_samples": num_samples, "min_dist": min_dist},
        )

    def get_minima(
        self,
        object_type: Literal["surrogate", "variable", "objective"] = "objective",
        name: str = "objective",
        environment_value: Optional[list[float]] = None,
        num_initial_samples: Optional[int] = None,
        num_output: int = 10,
        epsilon: float = 0.1,
        delta: float = 0.1,
        ftol: float = 1e-9,
        min_dist: float = 0.0,
    ) -> dict[str, list[float]]:
        r"""Get a list of information about local minima of a
        single-output surrogate, variable or objective. The width
        :math:`\sigma` in each parameter direction is determined by a
        fit of the minimum to a Gaussian function that goes
        asymptotically to the mean value of the object. The minima are
        found using predictions of the surrogate models.  The validity
        of constraints is completely ignored.  Example::

            import pandas as pd
            minima = driver.get_minima(num_output=10)
            print(pd.DataFrame(minima))

        Args:
          object_type: The type of object for which a prediction
              is required.
          name: The name of the object for which predictions are required.
          environment_value: Optional environment value for which local minima of
              design values are determined. If None, the local minima are also determined
              with respect to environemtn parameters.
          num_initial_samples: Number of initial samples for searching
              (default: automatic determination).
          num_output: Maximum number of minima that are returned.
          epsilon: Parameter used for identifying identical minima (i.e.
              minima with distance < length scale * epsilon)
              and minima with non-vanishing gradient (e.g. minima at the
              boundary of the search space)
          ftol: Precision goal for the minimum function value.
          delta: step size parameter used for approximating second
              derivatives.
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with information about local minima
            with lists of object values, uncertainties of the objective values,
            the parameter values and the width :math:`\sigma` in each parameter direction
            (i.e. standard deviation after a fit to a Gaussian function)

        """

        return self._run_task(
            "get minima",
            "get_minima",
            data={
                "object_type": object_type,
                "name": name,
                "environment_value": environment_value,
                "num_initial_samples": num_initial_samples,
                "num_output": num_output,
                "epsilon": epsilon,
                "delta": delta,
                "ftol": ftol,
                "min_dist": min_dist,
            },
        )

    def get_statistics(
        self,
        object_type: Literal["surrogate", "variable", "objective"] = "objective",
        name: str = "objective",
        quantiles: Optional[list[float]] = None,
        rel_precision: float = 1e-3,
        abs_precision: float = 1e-9,
        max_time: float = float("inf"),
        max_samples: float = 1e6,
        min_dist: float = 0.0,
    ) -> dict[str, Any]:
        r"""
        Determines statistics like the mean and variance of a
        surrogate, variable or objective under a parameter
        distribution. By default the probability density of the
        parameters is a uniform distribution in the whole parameter
        domain. Other parameter distributions can be defined via
        ``study.configure(parameter_distribution = dict(...))``.

        Example::

            study.configure(parameter_distribution = dict(
                distributions=[
                    {type="normal", parameter="param1", mean=1.0, stddev=2.0},
                    {type="uniform", parameter="param2", domain=[-1.0,1.0]}
                ]
            ))
            stats = study.driver.get_statistics(abs_precision=0.001)

        Args:
          object_type: The type of object for which a prediction
              is required.
          name: The name of the object for which predictions are required.
          quantiles: A list with quantiles. If not specified, the quantiles
              [0.16,0.5,0.84] are used.
          rel_precision: The Monte Carlo integration is stopped when
              the empiric relative uncertainty of the mean value of all outputs
              is smaller than rel_precision.
          abs_precision: The Monte Carlo integration is stopped when
              the empiric absolute uncertainty of the mean value of all outputs
              is smaller than abs_precision.
          max_time: The Monte Carlo integration is stopped when the
              time max_time has passed.
          max_samples: The Monte Carlo integration is stopped when the
              number of evaluated samples equals or exceeds the given value.
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with the entries

            :mean: Expectation values :math:`\mathbf{m}=\mathbb{E}[\mathbf{g}(\mathbf{x})]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the
                parameter distribution
            :variance: Variance
                :math:`\mathbf{v}=\mathbb{E}[(\mathbf{g}(\mathbf{x})-\mathbf{m})^2]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the parameter
                distribution
            :quantiles: A list of quantiles of shape `(num_quantiles, num_outputs)`.
            :num_samples: Number of sampling points :math:`N` that were used in the
                Monte Carlo integration. The numerical uncertainty of the computed
                mean value is :math:`\sqrt{v/N}`.

        """
        return self._run_task(
            "get statistics",
            "get_statistics",
            data=dict(
                object_type=object_type,
                name=name,
                quantiles=quantiles,
                rel_precision=rel_precision,
                abs_precision=abs_precision,
                max_time=max_time,
                max_samples=max_samples,
                min_dist=min_dist,
            ),
        )

    def get_sobol_indices(
        self,
        object_type: Literal["surrogate", "variable", "objective"] = "objective",
        name: str = "objective",
        max_uncertainty: float = 0.001,
        max_time: float = float("inf"),
        max_samples: float = 1e6,
        min_dist: float = 0.0,
    ) -> dict[str, Any]:
        r"""Determines Sobol' indices of a surrogate, variable or objective under a
        parameter distribution. By default the probability density of the parameters
        is a uniform distribution in the whole parameter domain. Other parameter
        distributions can be defined via ``study.configure(parameter_distribution =
        dict(...))``.

        Example::

            study.configure(parameter_distribution = dict(
                distributions=[
                    {type="normal", parameter="param1", mean=1.0, stddev=2.0},
                    {type="uniform", parameter="param2", domain=[-1.0,1.0]}
                ]
            ))
            sobol_indices = study.driver.get_sobol_indices(max_uncertainty=0.001)        

        Args:
          object_type: The type of object for which a prediction
              is required.
          name: The name of the object for which predictions are required.
          max_uncertainty: The uncertainty of the first-order Sobol' indices
          max_time: The Monte Carlo integration is stopped when the
              time max_time has passed.
          max_samples: The Monte Carlo integration is stopped when the
              number of evaluated samples equals or exceeds the given value.
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with the entries

            :first_oder: First-order (or main-effect) Sobol' indices of shape
                (n, d), where n is the number of parameters and d is the number of
                outputs of the object.
                The :math:`i`-th first-order Sobol' index of a parameter :math:`x_i`
                is the contribution to the output variance
                stemming from the effect of varying :math:`x_i` alone,
                but averaged over variations in other input parameters.
            :total_oder: Total-order (or total effect) Sobol' indices of shape
                (n, d), where n is the number of parameters and d is the number of
                outputs of the object.
                The :math:`i`-th total-order Sobol' index of a parameter :math:`x_i`
                measures the contribution to the output variance of :math:`x_i`,
                including all variance caused by its interactions with any other parameter.
            :mean: Expectation values :math:`\mathbf{m}=\mathbb{E}[\mathbf{g}(\mathbf{x})]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the
                parameter distribution
            :variance: Variance
                :math:`\mathbf{v}=\mathbb{E}[(\mathbf{g}(\mathbf{x})-\mathbf{m})^2]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the parameter
                distribution
            :num_samples: Number of sampling points :math:`N` that were used in the
                Monte Carlo integration. The numerical uncertainty of the computed
                mean value is :math:`\sqrt{v/N}`.

        .. note::

          For information on Sobol' indices and variance-based sensitivity analysis
          see https://en.wikipedia.org/wiki/Variance-based_sensitivity_analysis
        
        """
        return self._run_task(
            "get Sobol' indices",
            "get_sobol_indices",
            data=dict(
                object_type=object_type,
                name=name,
                max_uncertainty=max_uncertainty,
                max_time=max_time,
                max_samples=max_samples,
                min_dist=min_dist,
            ),
        )
    
    def run_mcmc(            
            self,
            name: str = "chisq",
            num_walkers: Optional[int] = None,
            max_iter: int = 50000,
            max_time: float = float("inf"),
            rel_error: float = 0.05,
            thin_chains: bool=False,
            multi_modal: bool = False,
            append: bool = False,
            max_sigma_dist: float = float("inf"),
            min_dist: float = 0.0,
    ) -> dict[str, Any]:
        r"""Runs a Markov Chain Monte Carlo (MCMC) sampling of a chi-squared
        or negative log-probability variable.
        The output value is interpreted as a likelihood function. By default the
        prior probability density of the parameters is a uniform distribution in the
        whole parameter domain. Other parameter distributions can be defined via
        ``study.configure(parameter_distribution = dict(...))``.  Example::

            study.run()
            study.configure(parameter_distribution = dict(
                distributions=[
                    {type="normal", parameter="param1", mean=1.0, stddev=2.0},
                    {type="uniform", parameter="param2", domain=[-1.0,1.0]}
                ]
            ))
            samples = study.driver.run_mcmc()

        The estimated error of a Monte-Carlo integration of some function :math:`f` is
        :math:`\delta = \sigma / \sqrt{N_{\rm ind}}` where :math:`\sigma^2` is the
        variance of :math:`f` and :math:`N_{\rm ind}` is the number of *independent*
        samples from the probability distribution.  The error relative to the
        variance :math:`\sigma^2` is therefore :math:`\delta_{\rm rel}=1/\sqrt{N_{\rm
        ind}}`. Assuming, that subsequent samples of a chain are correlated and this
        correlation vanishes at a correlation time :math:`\tau`, :math:`N_{\rm ind} =
        N/\tau` of all :math:`N` MCMC samples are independent.  Note, that
        :math:`\tau` can only be estimated and thus the relative Monte-Carlo
        integration error :math:`\delta_{\rm rel}=\tau/\sqrt{N}` can be under or
        overestimated.
        
        Args:
          name: The name of the chi-squared or negative log-probability variable
              that defines the probability density.
          num_walkers: Number of walkers. If not specified, the value is
              automatically chosen.
          max_iter: Maximum absolute chain length. 
          max_time: Maximum run time in seconds. If not specified, the runtime
              is not limited.
          rel_error: Targeted relative Monte-Carlo integration error
              :math:`\delta_{\rm rel}` of the samples.
          thin_chains: If true, only every :math:`\tau`-th sample of all
              MCMC samples is returned. This is helpful if the full number of samples
              gets too large and a representative uncorrelated subset is required.
          multi_modal: If true, a more explorative sampling strategy
              is used.
          append: If true, the samples are appended to the samples of
              the previous MCMC run.
          max_sigma_dist: If set, the sampling is restricted to a
              a distance max_sigma_dist * sigma to the maximum likelihood
              estimate. E.g. ``max_sigma_dist=3.0`` means that only the 99.7% 
              probability region of each parameter is sampled. 
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with the following entries:

            :samples: The drawn samples without "burn-in" samples thinned by
                     half of the correlation time.
            :medians: The medians of all random parameters
            :lower_uncertainties: The distances between the medians and the
                     16% quantile of all random parameters
            :upper_uncertainties: The distance between the medians and the
                     84% quantile of all random parameters
            :tau: Estimated correlation time of each parameter.

        """

        return self._run_task(
            "run MCMC sampling",
            "run_mcmc",
            data=dict(
                name=name,
                num_walkers=num_walkers,
                max_iter=max_iter,
                max_time=max_time,
                rel_error=rel_error,
                thin_chains=thin_chains,
                multi_modal=multi_modal,
                append=append,
                max_sigma_dist=max_sigma_dist,
                min_dist=min_dist                            
            )
        )


class ActiveLearning(ActiveLearningDriver):
    pass


class SpecializedActiveLearning(Driver):
    def __init__(self, study_id: str, project_id: str, requestor: OptimizerRequestor) -> None:
        super(SpecializedActiveLearning, self).__init__(study_id, project_id, requestor)
        self._ald = ActiveLearningDriver(study_id, project_id, requestor)


    @property
    def active_learning_configuration(self) -> dict[str, Any]:
        """Return a configuration for the :ref:`ActiveLearning` driver that can
        be used to reproduce the behavior of the current driver. Example::

          config = driver.active_learning_configuration
          study_active_learning = client.create_study(
              driver="ActiveLearning",
              ...              
          )
          study_active_learning.configure(**config)
        
        """
        answer = self._post(
            "get active learning configuration",
            "driver",
            "active_learning_configuration", 
            data={},
        )
        return answer["configuration"]
        
    def override_parameter(self, path: str, value: Any) -> None:
        """Override an internal parameter of the driver that is otherwise
        selected automatically. Example::

            driver.override_parameter(
                "surrogates.0.matrix.kernel.design_length_scales",
                [1.0, 2.0]
            )

        Args:
          path: A dot-separated path to the parameter to be overridden.
          value: The new value of the parameter.
        
        .. note:: A description of the meaning of each parameter can be retrieved
            by :func:`describe`.
        """
        self._ald.override_parameter(path, value)

class SingleGPSingleVariable(SpecializedActiveLearning):
    
    def get_observed_values(self) -> dict[str, Any]:
        """Get observed values. For noisy input data, the values are obtained on the
        basis of predictions of the surrogate models. Therefore, they can slightly
        differ from the input data. Example::

            data = driver.get_observed_values()
        
        Returns: Dictionary, with the following keys:

            :samples: The observed samples (design and possibly environment values).
            :means: Mean values of observations. For noiseless observations, this
                is the observed value itself.
            :variance: Variance of observed values. For noiseless observations, this is
                typically a negligibly small number.

        """
        return self._ald.get_observed_values()

    def optimize_hyperparameters(
        self, num_samples: int = 1, min_dist: float = 0.0
    ) -> None:
        """Optimize the hyperparameters of the driver.
        This is usually done automatically.
        Example::

            driver.optimize_hyperparameters()

        Args:
          num_samples: Number of initial start samples for optimization
              (default: automatic determination)
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.
        """
        self._ald.optimize_hyperparameters("driver.surrogates.0", num_samples, min_dist)

    def get_minima(
        self,
        environment_value: Optional[list[float]] = None,
        num_initial_samples: Optional[int] = None,
        num_output: int = 10,
        epsilon: float = 0.1,
        delta: float = 0.1,
        ftol: float = 1e-9,
        min_dist: float = 0.0,
    ) -> dict[str, list[float]]:
        r"""Get a list of information about local minima of the objective. The width
        :math:`\sigma` in each parameter direction is determined by a fit of the
        minimum to a Gaussian function that goes asymptotically to the mean value of
        the object. The minima are found using predictions of the surrogate models.
        The validity of constraints is completely ignored. Example::

            import pandas as pd
            minima = driver.get_minima(num_output=10)
            print(pd.DataFrame(minima))

        Args:
          environment_value: Optional environment value for which local minima of
              design values are determined. If None, the local minima are also determined
              with respect to environment parameters.
          num_initial_samples: Number of initial samples for searching
              (default: automatic determination).
          num_output: Maximum number of minima that are returned (Default: 10)
          epsilon: Parameter used for identifying identical minima (i.e.
              minima with distance < length scale * epsilon)
              and minima with non-vanishing gradient (e.g. minima at the
              boundary of the search space) (default: 0.1)
          delta: step size parameter used for approximating second
              derivatives. (default: 0.1)
          ftol: Precision goal for the minimum function value.
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with information about local minima
            with lists of object values, uncertainties of the objective values,
            the parameter values and the width :math:`\sigma` in each parameter direction
            (i.e. standard deviation after a fit to a Gaussian function)

        """
        return self._ald.get_minima(
            object_type="objective",
            name="objective",
            environment_value=environment_value,
            num_initial_samples=num_initial_samples,
            num_output=num_output,
            epsilon=epsilon,
            delta=delta,
            ftol=ftol,
            min_dist=min_dist,
        )


class BayesianOptimization(SingleGPSingleVariable, Minimizer):
    def predict(
        self,
        points: list[list[float]],
        output_type: Literal["mean_var", "quantiles", "samples"] = "mean_var",
        min_dist: float = 0.0,
        quantiles: Optional[list[float]] = None,
        num_samples: Optional[int] = None,
    ) -> dict[str, list]:
        """Make predictions on the objective value.
        Example::

            prediction = driver.predict(points=[[1,0,0],[2,0,1]])

        Args:
          points: Vectors of the space (design space + environment)
            of shape ``(num_points, num_dim)``
          output_type: The type of output.
            Options are:

              :mean_var: Mean and variance of the posterior distribution.
                 This describes the posterior distribution only for
                 normally distributed posteriors. The function returns a
                 dictionary with keywords ``"mean"`` and ``"variance"``
                 mapping to array of length num_points. If the posterior
                 distribution is multivariate normal, for each point
                 a covariance matrix of shape ``(output_dim, output_dim)``
                 is returned, otherwise a list of variances of shape
                 ``(output_dim,)`` is returned.
              :quantiles: A list of quantiles of the distribution is
                 estimated based on samples drawn from the distribution.
                 The function returns a dict with entry ``"quantiles"``
                 and a tensor of shape ``(num_quantiles, num_points, output_dim)``
              :samples: Random samples drawn from the posterior distribution.
                 The function returns a dict with the entry ``"samples"``
                 and a tensor of shape ``(num_samples, num_points, output_dim)``

          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.
          quantiles: A list with quantiles. If not specified, the quantiles
              [0.16,0.5,0.84] are used.
          num_samples: Number of samples used for posteriors that have
              a sampling-based distribution or if output_type is "samples".
              If not specified, the same number as in the acquisition is used.
              If the posterior is described by a fixed number of ensemble points,
              the minimum of num_samples and the ensemble size is used.

        Returns: A dictionary with the entries "mean" and "variance" if
            ``output_type = "mean_var`` and "samples" if ``output_type = "samples"``
        """
        return self._ald.predict(
            points=points,
            output_type=output_type,
            min_dist=min_dist,
            quantiles=quantiles,
            num_samples=num_samples,
        )

    def get_statistics(
        self,
        quantiles: Optional[list[float]] = None,
        rel_precision: float = 1e-3,
        abs_precision: float = 1e-9,
        max_time: float = float("inf"),
        max_samples: float = 1e6,
        min_dist: float = 0.0,
    ) -> dict[str, Any]:
        r"""Determines statistics like the mean and variance of the objective under a
        parameter distribution. By default the probability density of the parameters
        is a uniform distribution in the whole parameter domain. Other parameter
        distributions can be defined via study.configure(parameter_distribution =
        dict(...)).

        Example::

            study.configure(parameter_distribution = dict(
                distributions=[
                    {type="normal", parameter="param1", mean=1.0, stddev=2.0},
                    {type="uniform", parameter="param2", domain=[-1.0,1.0]}
                ]
            ))
            stats = study.driver.get_statistics(abs_precision=0.001)

        Args:
          quantiles: A list with quantiles. If not specified, the quantiles
              ``[0.16,0.5,0.84]`` are used.
          abs_precision: The Monte Carlo integration is stopped when
              the empiric absolute uncertainty of the mean value of all outputs
              is smaller than abs_precision.
          rel_precision: The Monte Carlo integration is stopped when
              the empiric relative uncertainty of the mean value of all outputs
              is smaller than rel_precision.
          max_time: The Monte Carlo integration is stopped when the
              time max_time has passed.
          max_samples: The Monte Carlo integration is stopped when the
              number of evaluated samples equals or exceeds the given value.
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with the entries

            :mean: Expectation values :math:`\mathbf{m}=\mathbb{E}[\mathbf{g}(\mathbf{x})]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the
                parameter distribution
            :variance: Variance
                :math:`\mathbf{v}=\mathbb{E}[(\mathbf{g}(\mathbf{x})-\mathbf{m})^2]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the parameter
                distribution
            :quantiles: A list of quantiles of shape `(num_quantiles, num_outputs)`.
            :num_samples: Number of sampling points :math:`N` that were used in the
                Monte Carlo integration. The numerical uncertainty of the computed
                mean value is :math:`\sqrt{v/N}`.

        """
        return self._ald.get_statistics(
            object_type="objective",
            name="objective",
            quantiles=quantiles,
            rel_precision=rel_precision,
            abs_precision=abs_precision,
            max_time=max_time,
            max_samples=max_samples,
            min_dist=min_dist,
        )


class BayesianLeastSquares(SingleGPSingleVariable, LeastSquaresDriver):
    @property
    def uncertainties(self) -> dict[str, float]:
        """
        Uncertainties of the continuous parameters of the best sample. Example::

          for key, value in uncertainties.items():
              print(f"uncertainty of {key}: {value}")

        """
        answer = self._post(
            "get uncertainties",
            "driver",
            "get_state",
            data={"path": "variables.0.parameter_uncertainties"},
        )
        return answer["state"]

    def predict(
        self,
        points: list[list[float]],
        object_type: Literal["surrogate", "objective"] = "objective",
        output_type: Literal["mean_var", "quantiles", "samples"] = "mean_var",
        min_dist: float = 0.0,
        quantiles: Optional[list[float]] = None,
        num_samples: Optional[int] = None,
    ) -> dict[str, list]:
        """Make predictions on the multi-output surrogate or the chi-squared objective.
        Example::

            prediction = driver.predict(points=[[1,0,0],[2,0,1]])

        Args:
          points: Vectors of the space (design space + environment)
              of shape ``(num_points, num_dim)``
          object_type: The type of object for which a prediction
              is required.
          output_type: The type of output.
              Options are:

              :mean_var: Mean and variance of the posterior distribution.
                 This describes the posterior distribution only for
                 normally distributed posteriors. The function returns a
                 dictionary with keywords ``"mean"`` and ``"variance"``
                 mapping to array of length ``num_points``. If the posterior
                 distribution is multivariate normal, for each point
                 a covariance matrix of shape ``(output_dim, output_dim)``
                 is returned, otherwise a list of variances of shape
                 ``(output_dim,)`` is returned.
              :quantiles: A list of quantiles of the distribution is
                 estimated based on samples drawn from the distribution.
                 The function returns a dict with entry ``"quantiles"``
                 and a tensor of shape ``(num_quantiles, num_points, output_dim)``
              :samples: Random samples drawn from the posterior distribution.
                 The function returns a dict with the entry ``"samples"``
                 and a tensor of shape ``(num_samples, num_points, output_dim)``

          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.
          quantiles: A list with quantiles. If not specified, the quantiles
              [0.16,0.5,0.84] are used.
          num_samples: Number of samples used for posteriors that have
              a sampling-based distribution or if output_type is "samples".
              If not specified, the same number as in the acquisition is used.
              If the posterior is described by a fixed number of ensemble points,
              the minimum of num_samples and the ensemble size is used.

        Returns: A dictionary with the entries "mean" and "variance" if
            ``output_type = "mean_var`` and "samples" if ``output_type = "samples"``
        """

        name = "model_vector" if object_type == "surrogate" else "objective"
        return self._ald.predict(
            points=points,
            object_type=object_type,
            name=name,
            output_type=output_type,
            min_dist=min_dist,
            quantiles=quantiles,
            num_samples=num_samples,
        )

    def get_statistics(
        self,
        object_type: Literal["surrogate", "objective"] = "objective",
        quantiles: Optional[list[float]] = None,
        rel_precision: float = 1e-3,
        abs_precision: float = 1e-9,
        max_time: float = float("inf"),
        max_samples: float = 1e6,
        min_dist: float = 0.0,
    ) -> dict[str, Any]:
        r"""
        Determines statistics like the mean and variance of a
        the surrogate or chi-squared objective under a parameter
        distribution. By default the probability density of the
        parameters is a uniform distribution in the whole parameter
        domain. Other parameter distributions can be defined via
        study.configure(parameter_distribution = dict(...)).

        Example::

            study.configure(parameter_distribution = dict(
                distributions=[
                    {type="normal", parameter="param1", mean=1.0, stddev=2.0},
                    {type="uniform", parameter="param2", domain=[-1.0,1.0]}
                ]
            ))
            stats = study.driver.get_statistics(abs_precision=0.001)

        Args:
          object_type: The type of object for which a prediction is required.
              name: The name of the object for which predictions are required.
          quantiles: A list with quantiles. If not specified, the quantiles
              ``[0.16,0.5,0.84]`` are used.
          abs_precision: The Monte Carlo integration is stopped when
              the empiric absolute uncertainty of the mean value of all outputs
              is smaller than abs_precision.
          rel_precision: The Monte Carlo integration is stopped when
              the empiric relative uncertainty of the mean value of all outputs
              is smaller than rel_precision.
          max_time: The Monte Carlo integration is stopped when the
              time max_time has passed.
          max_samples: The Monte Carlo integration is stopped when the
              number of evaluated samples equals or exceeds the given value.
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with the entries

            :mean: Expectation values :math:`\mathbf{m}=\mathbb{E}[\mathbf{g}(\mathbf{x})]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the
                parameter distribution
            :variance: Variance
                :math:`\mathbf{v}=\mathbb{E}[(\mathbf{g}(\mathbf{x})-\mathbf{m})^2]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the parameter
                distribution
            :quantiles: A list of quantiles of shape `(num_quantiles, num_outputs)`.
            :num_samples: Number of sampling points :math:`N` that were used in the
                Monte Carlo integration. The numerical uncertainty of the computed
                mean value is :math:`\sqrt{v/N}`.

        """
        name = "model_vector" if object_type == "surrogate" else "objective"
        return self._ald.get_statistics(
            object_type=object_type,
            name=name,
            quantiles=quantiles,
            rel_precision=rel_precision,
            abs_precision=abs_precision,
            max_time=max_time,
            max_samples=max_samples,
            min_dist=min_dist,
        )

    def run_mcmc(            
            self,
            num_walkers: Optional[int] = None,
            max_iter: int = 50000,
            max_time: float = float("inf"),
            rel_error: float = 0.05,
            thin_chains: bool=False,
            multi_modal: bool = False,
            append: bool = False,
            max_sigma_dist: float = float("inf"),
            min_dist: float = 0.0,

    ) -> dict[str, Any]:
        r"""Runs a Markov Chain Monte Carlo (MCMC) sampling of posterior probability
        of the parameters. By default the prior probability density of the parameters
        is a uniform distribution in the whole parameter domain. Other parameter
        distributions can be defined via ``study.configure(parameter_distribution =
        dict(...))``. Example::

            study.run()
            study.configure(parameter_distribution = dict(
                distributions=[
                    {type="normal", parameter="param1", mean=1.0, stddev=2.0},
                    {type="uniform", parameter="param2", domain=[-1.0,1.0]}
                ]
            ))
            samples = study.driver.run_mcmc()

        The estimated error of a Monte-Carlo integration of some function :math:`f` is
        :math:`\delta = \sigma / \sqrt{N_{\rm ind}}` where :math:`\sigma^2` is the
        variance of :math:`f` and :math:`N_{\rm ind}` is the number of *independent*
        samples from the probability distribution.  The error relative to the
        variance :math:`\sigma^2` is therefore :math:`\delta_{\rm rel}=1/\sqrt{N_{\rm
        ind}}`. Assuming, that subsequent samples of a chain are correlated and this
        correlation vanishes at a correlation time :math:`\tau`, :math:`N_{\rm ind} =
        N/\tau` of all :math:`N` MCMC samples are independent.  Note, that
        :math:`\tau` can only be estimated and thus the relative Monte-Carlo
        integration error :math:`\delta_{\rm rel}=\tau/\sqrt{N}` can be under or
        overestimated.
        
        Args:
          num_walkers: Number of walkers. If not specified, the value is
              automatically chosen.
          max_iter: Maximum absolute chain length. 
          max_time: Maximum run time in seconds. If not specified, the runtime
              is not limited.
          rel_error: Targeted relative Monte-Carlo integration error
              :math:`\delta_{\rm rel}` of the samples.
          thin_chains: If true, only every :math:`\tau`-th sample of all
              MCMC samples is returned. This is helpful if the full number of samples
              gets too large and a representative uncorrelated subset is required.
          multi_modal: If true, a more explorative sampling strategy
              is used.
          append: If true, the samples are appended to the samples of
              the previous MCMC run.
          float max_sigma_dist: If set, the sampling is restricted to a
               a distance max_sigma_dist * sigma to the maximum likelihood
               estimate. E.g. max_sigma_dist=3.0 means that only the 99.7% 
               probability region of each parameter is sampled. (default: inf)
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with the following entries:

            :samples: The drawn samples without "burn-in" samples thinned by
                     half of the correlation time.
            :medians: The medians of all random parameters
            :lower_uncertainties: The distances between the medians and the
                     16% quantile of all random parameters
            :upper_uncertainties: The distance between the medians and the
                     84% quantile of all random parameters
            :tau: Estimated correlation time of each parameter.

        """
        return self._ald.run_mcmc(
            name="chisq",
            num_walkers=num_walkers,
            max_iter=max_iter,
            max_time=max_time,
            rel_error=rel_error,
            thin_chains=thin_chains,
            multi_modal=multi_modal,
            append=append,
            max_sigma_dist=max_sigma_dist,
            min_dist=min_dist                            
        )        


class BayesianReconstruction(SingleGPSingleVariable, Minimizer):

    def predict(
        self,
        points: list[list[float]],
        object_type: Literal["surrogate", "objective"] = "objective",
        output_type: Literal["mean_var", "quantiles", "samples"] = "mean_var",
        min_dist: float = 0.0,
        quantiles: Optional[list[float]] = None,
        num_samples: Optional[int] = None,
    ) -> dict[str, list]:
        """Make predictions on the multi-output surrogate or the negative
        log-probability objective.
        Example::

            prediction = driver.predict(points=[[1,0,0],[2,0,1]])

        Args:
          points: Vectors of the space (design space + environment)
              of shape ``(num_points, num_dim)``
          object_type: The type of object for which a prediction
              is required.
          output_type: The type of output.
              Options are:

              :mean_var: Mean and variance of the posterior distribution.
                 This describes the posterior distribution only for
                 normally distributed posteriors. The function returns a
                 dictionary with keywords ``"mean"`` and ``"variance"``
                 mapping to array of length ``num_points``. If the posterior
                 distribution is multivariate normal, for each point
                 a covariance matrix of shape ``(output_dim, output_dim)``
                 is returned, otherwise a list of variances of shape
                 ``(output_dim,)`` is returned.
              :quantiles: A list of quantiles of the distribution is
                 estimated based on samples drawn from the distribution.
                 The function returns a dict with entry ``"quantiles"``
                 and a tensor of shape ``(num_quantiles, num_points, output_dim)``
              :samples: Random samples drawn from the posterior distribution.
                 The function returns a dict with the entry ``"samples"``
                 and a tensor of shape ``(num_samples, num_points, output_dim)``

          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.
          quantiles: A list with quantiles. If not specified, the quantiles
              [0.16,0.5,0.84] are used.
          num_samples: Number of samples used for posteriors that have
              a sampling-based distribution or if output_type is "samples".
              If not specified, the same number as in the acquisition is used.
              If the posterior is described by a fixed number of ensemble points,
              the minimum of num_samples and the ensemble size is used.

        Returns: A dictionary with the entries "mean" and "variance" if
            ``output_type = "mean_var`` and "samples" if ``output_type = "samples"``
        """

        name = "model_vector" if object_type == "surrogate" else "objective"
        return self._ald.predict(
            points=points,
            object_type=object_type,
            name=name,
            output_type=output_type,
            min_dist=min_dist,
            quantiles=quantiles,
            num_samples=num_samples,
        )

    def get_statistics(
        self,
        object_type: Literal["surrogate", "objective"] = "objective",
        quantiles: Optional[list[float]] = None,
        rel_precision: float = 1e-3,
        abs_precision: float = 1e-9,
        max_time: float = float("inf"),
        max_samples: float = 1e6,
        min_dist: float = 0.0,
    ) -> dict[str, Any]:
        r"""Determines statistics like the mean and variance of a the
        surrogate or negative log-probability objective under a
        parameter distribution. By default the probability density of
        the parameters is a uniform distribution in the whole
        parameter domain. Other parameter distributions can be defined
        via study.configure(parameter_distribution = dict(...)).

        Example::

            study.configure(parameter_distribution = dict(
                distributions=[
                    {type="normal", parameter="param1", mean=1.0, stddev=2.0},
                    {type="uniform", parameter="param2", domain=[-1.0,1.0]}
                ]
            ))
            stats = study.driver.get_statistics(abs_precision=0.001)

        Args:
          object_type: The type of object for which a prediction is required.
              name: The name of the object for which predictions are required.
          quantiles: A list with quantiles. If not specified, the quantiles
              ``[0.16,0.5,0.84]`` are used.
          abs_precision: The Monte Carlo integration is stopped when
              the empiric absolute uncertainty of the mean value of all outputs
              is smaller than abs_precision.
          rel_precision: The Monte Carlo integration is stopped when
              the empiric relative uncertainty of the mean value of all outputs
              is smaller than rel_precision.
          max_time: The Monte Carlo integration is stopped when the
              time max_time has passed.
          max_samples: The Monte Carlo integration is stopped when the
              number of evaluated samples equals or exceeds the given value.
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with the entries

            :mean: Expectation values :math:`\mathbf{m}=\mathbb{E}[\mathbf{g}(\mathbf{x})]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the
                parameter distribution
            :variance: Variance
                :math:`\mathbf{v}=\mathbb{E}[(\mathbf{g}(\mathbf{x})-\mathbf{m})^2]`
                of the object function :math:`\mathbf{g}(\mathbf{x})` under the parameter
                distribution
            :quantiles: A list of quantiles of shape `(num_quantiles, num_outputs)`.
            :num_samples: Number of sampling points :math:`N` that were used in the
                Monte Carlo integration. The numerical uncertainty of the computed
                mean value is :math:`\sqrt{v/N}`.

        """
        name = "model_vector" if object_type == "surrogate" else "objective"
        return self._ald.get_statistics(
            object_type=object_type,
            name=name,
            quantiles=quantiles,
            rel_precision=rel_precision,
            abs_precision=abs_precision,
            max_time=max_time,
            max_samples=max_samples,
            min_dist=min_dist,
        )

    def run_mcmc(            
            self,
            num_walkers: Optional[int] = None,
            max_iter: int = 50000,
            max_time: float = float("inf"),
            rel_error: float = 0.05,
            thin_chains: bool=False,
            multi_modal: bool = False,
            append: bool = False,
            max_sigma_dist: float = float("inf"),
            min_dist: float = 0.0,

    ) -> dict[str, Any]:
        r"""Runs a Markov Chain Monte Carlo (MCMC) sampling of posterior probability
        of the parameters. By default the prior probability density of the parameters
        is a uniform distribution in the whole parameter domain. Other parameter
        distributions can be defined via ``study.configure(parameter_distribution =
        dict(...))``. Example::

            study.run()
            study.configure(parameter_distribution = dict(
                distributions=[
                    {type="normal", parameter="param1", mean=1.0, stddev=2.0},
                    {type="uniform", parameter="param2", domain=[-1.0,1.0]}
                ]
            ))
            samples = study.driver.run_mcmc()

        The estimated error of a Monte-Carlo integration of some function :math:`f` is
        :math:`\delta = \sigma / \sqrt{N_{\rm ind}}` where :math:`\sigma^2` is the
        variance of :math:`f` and :math:`N_{\rm ind}` is the number of *independent*
        samples from the probability distribution.  The error relative to the
        variance :math:`\sigma^2` is therefore :math:`\delta_{\rm rel}=1/\sqrt{N_{\rm
        ind}}`. Assuming, that subsequent samples of a chain are correlated and this
        correlation vanishes at a correlation time :math:`\tau`, :math:`N_{\rm ind} =
        N/\tau` of all :math:`N` MCMC samples are independent.  Note, that
        :math:`\tau` can only be estimated and thus the relative Monte-Carlo
        integration error :math:`\delta_{\rm rel}=\tau/\sqrt{N}` can be under or
        overestimated.
        
        Args:
          num_walkers: Number of walkers. If not specified, the value is
              automatically chosen.
          max_iter: Maximum absolute chain length. 
          max_time: Maximum run time in seconds. If not specified, the runtime
              is not limited.
          rel_error: Targeted relative Monte-Carlo integration error
              :math:`\delta_{\rm rel}` of the samples.
          thin_chains: If true, only every :math:`\tau`-th sample of all
              MCMC samples is returned. This is helpful if the full number of samples
              gets too large and a representative uncorrelated subset is required.
          multi_modal: If true, a more explorative sampling strategy
              is used.
          append: If true, the samples are appended to the samples of
              the previous MCMC run.
          float max_sigma_dist: If set, the sampling is restricted to a
               a distance max_sigma_dist * sigma to the maximum likelihood
               estimate. E.g. max_sigma_dist=3.0 means that only the 99.7% 
               probability region of each parameter is sampled. (default: inf)
          min_dist: In order to speed up the prediction, one can use a
              sparsified version of the base surrogates where sampling
              with a distance smaller than min_dist (in terms of the length
              scales of the surrogate) are neglected.

        Returns: A dictionary with the following entries:

            :samples: The drawn samples without "burn-in" samples thinned by
                     half of the correlation time.
            :medians: The medians of all random parameters
            :lower_uncertainties: The distances between the medians and the
                     16% quantile of all random parameters
            :upper_uncertainties: The distance between the medians and the
                     84% quantile of all random parameters
            :tau: Estimated correlation time of each parameter.

        """
        return self._ald.run_mcmc(
            name="neg_log_prob",
            num_walkers=num_walkers,
            max_iter=max_iter,
            max_time=max_time,
            rel_error=rel_error,
            thin_chains=thin_chains,
            multi_modal=multi_modal,
            append=append,
            max_sigma_dist=max_sigma_dist,
            min_dist=min_dist                            
        )        
