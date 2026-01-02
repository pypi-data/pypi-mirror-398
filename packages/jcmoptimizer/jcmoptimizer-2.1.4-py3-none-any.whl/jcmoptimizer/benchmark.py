from typing import Any, Callable, Literal, Optional, Union
import time
import datetime as dt
import requests
import atexit

from .requestor import OptimizerRequestor, warn, inform
from .study import Study
from .objects import Observation


class Benchmark:

    """
    This class provides methods for benchmarking different studies against each other
    that try to minimize the same objective. Example::

       benchmark = client.create_benchmark(num_average=6)
       benchmark.add_study(study1)
       benchmark.add_study(study2)
       benchmark.set_evaluator(evaluate)
       benchmark.run()
       data = benchmark.get_data(x_type='num_evaluations',y_type='objective',
                  average_type='mean')
       fig = plt.figure(figsize=(8,4))
       for idx,name in enumerate(data['names']):
           X = data['X'][idx]
           Y = np.array(data['Y'][idx])
           std_error = np.array(data['sdev'][idx])/np.sqrt(6)
           p = plt.plot(X,Y,linewidth=2.0, label=name)
           plt.fill_between(X, Y-std_error, Y+std_error, alpha=0.2, color = p[0].get_color())
       plt.legend(loc='upper right',ncol=1)
       plt.grid()
       plt.ylim([0.1,10])
       plt.rc('font',family='serif')
       plt.xlabel('number of iterations',fontsize=12)
       plt.ylabel('average objective',fontsize=12)
       plt.show()

    The constructor should not be used directly since it does not create a
    benchmark on the server side. Instead, one should use :func:`Client.create_benchmark`.
    """

    def __init__(
            self, benchmark_id: str, num_average: int, requestor: OptimizerRequestor
    ):
        self.id = benchmark_id
        self.num_average = num_average
        self._studies: list[Study] = []
        self._requestor = requestor
        self.deleted = False
        atexit.register(self._delete_on_server)

    def _post(
        self,
        purpose: str,
        operation: str,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return self._requestor.post(
            purpose, "benchmark", operation, self.id, data
        )

    def _get(self, purpose: str, type: str) -> dict[str, Any]:
        return self._requestor.get(purpose, "benchmark", type, self.id)

    def _delete_on_server(self) -> None:
        self._post("delete benchmark", "delete")
        self.deleted = True

    def __del__(self) -> None:
        if not self.deleted:
            self._delete_on_server()

    def add_study(self, study: Study) -> None:
        """Adds a study to the benchmark. Example::

                benchmark.add_study(study1)

        Args:
          study: A :class:`~jcmoptimizer.Study` object for which a benchmark
           should be run.
        """
        self._post("add study", "add_study", data={"study_qualifier": study.qualifier})
        self._studies.append(study)

    @property
    def studies(self) -> list[Study]:
        """A list of studies to be run for the benchmark."""
        studies: list[Study] = []
        for s in self._studies:
            for num_run in range(self.num_average):
                studies.append(s)
        return studies

    def add_study_results(self, study: Study) -> None:
        """Adds the results of a benchmark study at the end of an optimization run.
        Example::

            benchmark.add_study_results(study1)

        Args:
          study: A :class:`~jcmoptimizer.Study` object after the study was run.
        """
        answer = self._post(
            "add study results", "add_study_results", data={"study_qualifier": study.qualifier}
        )
        if answer["new_study_id"] != "":
            study.study_id = answer["new_study_id"]

    def get_data(
        self,
        x_type: Literal["num_evaluations", "time"] = "num_evaluations",
        y_type: Literal["objective", "distance"] = "objective",
        average_type: Literal["mean", "median"] = "mean",
        invert: bool = False,
        log_scale: bool = False,
        minimum: Optional[list[float]] = None,
        scales: Optional[list[float]] = None,
        norm: Union[str, int, None] = None,
        num_samples: int = 100,
    ) -> dict[str, list[Union[str, float]]]:
        """Get benchmark data. Example::

            data = benchmark.get_data( x_type='num_evaluations', y_type='objective',
                 average_type='mean')
            plt.plot(data['X'][0],data['Y'][0])

        Args:
          x_type: Data on x-axis. Can be either 'num_evaluations' or 'time'.
            The time data is given in units of seconds.
          y_type: Data type on y-axis. Can be either 'objective', 'distance',
            (i.e. accumulated minimum distance off all samples to overall minimum),
            or 'min_distance' (i.e. distance of current minimum to overall
            minimum).
          average_type: Type of averaging over study runs. Can be either
            'mean' w.r.t. x-axis data or 'median' w.r.t. y-axis data
          invert: If True, the objective is multiplied by -1.
            (Parameter not available for distance average types)
          log_scale: If True, the output of Y and sdev are determined as
            mean and standard deviations of the natural logarithm of the
            considered y_type.
          minimum: Vector with minimum position. (Only available for
             distance average types)
          scales: Vector with positive weights for scaling distance in
             different directions. (Only available for distance average types)
          norm: Order of distance norm as defined in
             numpy.linalg.norm. (Only available for distance average types)
          num_samples: Number of samples on y-axis. (Only available for
             median average type or time on x-axis)
        """

        answer = self._post(
            "get data",
            "get_data",
            data={
                "x_type": x_type,
                "y_type": y_type,
                "average_type": average_type,
                "invert": invert,
                "log_scale": log_scale,
                "minimum": minimum,
                "scales": scales,
                "norm": norm,
                "num_samples": num_samples,
            },
        )
        return answer["data"]

    def set_objective(self, objective: Callable) -> None:
        raise AttributeError(
            "The method 'set_objective()' is deprecated. "
            "Please, use the method 'set_evaluator()' instead"
        )

    def set_evaluator(self, evaluator: Callable[..., Observation]) -> None:
        """Set the function that maps design parameters to an :class:`Observation`.
        Example::

            def evaluate(study: Study, x1: float, x2: float) -> Observation:
                observation = study.new_observation()
                observation.add(x1**2 + x2**2)
                return observation
            benchmark.set_evaluator(evaluate)

        .. note::  Call this function only after all studies have been added
            to the benchmark.

        Args:
          evaluator: Function handle for a function of the
            variable parameters that returns a corresponding :class:`Observation` object.
            The function must accept a ``"study"`` argument as well as
            an argument with the name of each design parameter and fixed environment
            parameter.
        """

        for study in self._studies:
            study.set_evaluator(evaluator)

    def run(self) -> None:
        """Run the benchmark after the evaluator has been set
        (see :func:`~Benchmark.set_evaluator`).
        Example::

            benchmark.run()

        """
        time_zero_benchmark = time.time()
        for study in self._studies:
            inform(f"Running study '{study.study_id}'")
            for i in range(self.num_average):
                time_zero = time.time()
                inform(f"Run {i+1}/{self.num_average} of study '{study.study_id}'")
                try:
                    study.run()
                except EnvironmentError as err:
                    warn(f"Study '{study.study_id}' stopped due to error: {err}")
                self.add_study_results(study)
                timedelta = dt.timedelta(seconds=int(time.time() - time_zero))
                inform(f"Run of study '{study.study_id}' finished after {timedelta}.")
        timedelta = dt.timedelta(seconds=int(time.time() - time_zero_benchmark))
        inform(f"Benchmark finished after {timedelta}")
