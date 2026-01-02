from typing import Any, Callable, Optional, Union
import time
import threading
import warnings
import traceback
import atexit
import requests

from .requestor import OptimizerRequestor, NumParallelError, warn
from .objects import Observation, Suggestion
from .drivers import Driver


class Study:

    """
    This class provides methods for controlling a numerical optimization study.
    Example::

         def evaluate(study: Study, x1: float, x2: float) -> Observation:
             observation = study.new_observation()
             observation.add(x1**2+x2**2)
             return observation
         study.configure(max_iter=30, num_parallel=3)

         #Start optimization loop
         study.set_evaluator(evaluate)
         study.run()

         #Alternatively, one can explicitly define an optimization loop
         def acquire(suggestion: Suggestion) -> None:
            try: observation = evaluator(study, **suggestion.kwargs)
            except: study.clear_suggestion(suggestion.id, 'Evaluator failed')
            else: study.add_observation(observation, suggestion.id)

         while (not study.is_done()):
             suggestion = study.get_suggestion()
             t = Threading.thread(target=acquire, args=(suggestion,))
             t.start()

    The constructor should not be used directly since it does not create a
    study on the server side. Instead, one should use :func:`Client.create_study`.
    """

    def __init__(
        self,
        study_id: str,
        project_id: str,
        driver: Driver,
        requestor: OptimizerRequestor,
    ) -> None:
        self.study_id = study_id
        self.project_id = project_id
        self._driver = driver
        self._requestor = requestor
        self.evaluator: Optional[Callable[..., Observation]] = None
        self.num_failed = 0
        self.max_num_failed = 3
        self.deleted = False
        self.suggestions: dict[int, Suggestion] = {}
        self.threads: list[threading.Thread] = []
        atexit.register(self._delete_on_server)

    @property
    def driver(self) -> Driver:
        """
        The driver of the study. For a documentation see the :ref:`DriverReference`
        of the corresponding driver.
        """
        return self._driver

    @property
    def qualifier(self) -> str:
        return self.project_id + "." + self.study_id

    def _post(
        self,
        purpose: str,
        object: str,
        operation: str,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return self._requestor.post(
            purpose, object, operation, self.qualifier, data
        )

    def _get(self, purpose: str, object: str, type: str) -> dict[str, Any]:
        return self._requestor.get(purpose, object, type, self.qualifier)

    def _delete_on_server(self) -> None:
        if self.deleted:
            return
        try:
            self._post("delete study", "study", "delete")
        except ConnectionError:
            pass
        self.deleted = True

    def __del__(self) -> None:
        self._delete_on_server()

    def set_parameters(self, **kwargs: Any) -> None:
        raise AttributeError(
            "The method 'set_parameters()' is deprecated. "
            "Please, use the method 'configure()' instead."
        )

    def configure(
        self,
        num_parallel: int = 1,
        max_iter: Optional[int] = None,
        max_time: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Configures the study for its run. Example::

            study.configure(max_iter=100, num_parallel=5)

        Args:
          num_parallel: Number of parallel observations of the evaluator function
            (default: ``1``).

          max_iter: Maximum number of evaluations of the evaluator 2
            function (default: ``inf``).

          max_time: Maximum optimization time in seconds (default: ``inf``).

        .. note:: The full list of parameters depends on the chosen driver.
           For a parameter description, see the the corresponding driver in the
           :ref:`driver reference <DriverReference>`.
        """
        data = kwargs
        data["num_parallel"] = num_parallel
        if max_iter is not None:
            data["max_iter"] = max_iter
        if max_time is not None:
            data["max_time"] = max_time

        self._post("configure study", "study", "configure", data=data)

    @property
    def configuration(self) -> dict[str, Any]:
        """Return the current configuration for the driver. Example::

        config = study.configuration
        study2.configure(**config)

        """
        answer = self._post(
            "get configuration",
            "driver",
            "configuration",
            data={},
        )
        return answer["configuration"]

    def start_clock(self) -> None:
        """The optimization stops after the time ``max_time``
        (see :func:`configure`). This function resets the
        clock to zero. Example::

            study.start_clock()


        .. note:: The clock is also set to zero by calling :func:`configure`.
        """
        self._post("start clock", "study", "start_clock")

    def get_state(self, path: Optional[str] = None) -> dict[str, Any]:
        """Get state of the study. Example::

            acquisition_time = study.get_state(
                path="observation.acquisition_time"
            )

        Args:
          path: A dot-separated path to a submodule or parameter.
            If none, the full state is returned.

        Returns: If path is None, a dictionary with the following entries
            is returned:

            :driver: Dictionary with information of driver state.
            :observation: Dictionary with information of the latest observation.
            :suggestion: Dictionary with information about the suggestion that
                corresponds to the last observation

        .. note:: A description of the meaning of each entry in the state
            can be retrieved by :func:`describe`.
        """
        answer = self._post(
            "get study state", "study", "get_state", data={"path": path}
        )
        return answer["state"]

    def describe(self) -> dict[str, Any]:
        """Get description of all modules and their parameters that are used
        by the study. Example::

            description = study.describe()
            print(description["observation"]["acquisition_time"])
            print(description["driver"]["members"]["surrogates"]["0"])

        Returns: A dictionary with the root entries:

            :driver: Nested dictionary with description of submodules consisting
               of a name and a descriptive text. If the entry describes a module,
               it has an additional ``"members"`` entry with dictionaries describing
               submodules and parameters.
            :observation: Dictionary with a description of the parameters of
               an observation.
            :suggestion: Dictionary with a description of the parameters of
               a suggestion of the driver.
        """
        answer = self._get("get description of the study", "study", "describe")
        return answer["description"]

    def historic_parameter_values(self, path: str) -> list[Any]:
        """Get the values of an internal parameter for each iteration of the study. Example::

            acquisition_times = study.historic_parameter_values(
                path="observation.acquisition_time")

        Args:
          path: A dot-separated path to the parameter.

        .. note:: A description of the meaning of each parameter can be retrieved
            by :func:`describe`.
        """
        answer = self._post(
            "get historic parameter values",
            "study",
            "historic_parameter_values",
            data={"path": path},
        )
        return answer["values"]

    def get_observation_data(self) -> dict[str, Any]:
        """Get table with data of the observations. This can be used to copy
        the data manually to another study. Example::

            obs_data = study.get_observation_data()
            other_study.add_observation_data(obs_data)

        Returns: Dictionary, where each entry holds an equally long list of observation
            data. The keys of the dictionary are:

            :value: Observed value of black-box function
            :derivative: Name of derivative parameter or None for non-derivative observation
            :uncertainty: Uncertainty of observed value or None if no uncertainty
            :model_name: Name of the surrogate model that is trained on the data or None
            :design_value: Value of design parameters
            :environment_value: Value of environment parameters or None if no environment
                is specified
        """
        answer = self._get("get observation data", "study", "get_observation_data")
        return answer["observation_data"]

    def add_observation_data(self, data: dict[str, Any]) -> None:
        """Add data from another study to the study. Example::

           obs_data = study.get_observation_data()
           other_study.add_observation_data(obs_data)

        Args:
            data: Dict with observation data. See :func:`get_observation_data` for the details.
        """
        observations: list[Observation] = []
        design_values: list[list[Union[float, str]]] = []
        last_design_value = None
        for idx in range(len(data["value"])):
            design_value = data["design_value"][idx]
            if last_design_value != design_value:
                if last_design_value is not None:
                    observations.append(obs)
                    design_values.append(last_design_value)
                obs = self.new_observation()
                last_design_value = design_value
            obs.add(
                value=data["value"][idx],
                derivative=data["derivative"][idx],
                uncertainty=data["uncertainty"][idx],
                model_name=data["model_name"][idx],
                environment_value=data["environment_value"][idx],
            )
        if last_design_value is not None:
            observations.append(obs)
            design_values.append(last_design_value)
            self.add_many(observations, design_values)

    def is_done(self) -> bool:
        """Checks if the study has finished. Example::

               if study.is_done(): break

        Returns: True if some stopping criterion set by
            :func:`configure` was met.

        .. note:: Before returning true, the function call waits until all open
            suggestions have been added to the study.
        """
        answer = self._get("get running status of study", "study", "is_done")
        is_done: bool = answer["is_done"]
        if is_done:
            self._wait_for_open_suggestions()
        return is_done

    def _wait_for_open_suggestions(self) -> None:
        while True:
            state = self.get_state()
            num_open_suggestions = state["driver"]["num_open_suggestions"]
            if num_open_suggestions > 0:
                time.sleep(0.5)
            else:
                break

    def get_suggestion(
        self, environment_value: Optional[list[float]] = None
    ) -> Suggestion:
        """Get a new suggestion to be evaluated by the user.
        Example::

          def evaluate(study: Study, x1: float, x2: float) -> Observation:
             obs = study.new_observation()
             obs.add(x1**2 + x2**2)
             return obs

          suggestion = study.get_suggestion()
          obs = evaluate(study, **suggestion.kwargs)
          study.add_observation(observation=obs, suggestion_id=suggestion.id)

        Args:
          environment_value: If an environment is specified, this optional
            argument specifies the list of variable environment parameter values,
            for which a suggestion should be computed. E.g. ``[0.1, 1.2]``.
            If an environment exists and no values are specified, the last known
            environment values are used.

        .. warning:: The function has to wait until the number of open suggestions is smaller
            than ``num_parallel`` before receiving a new suggestion. This can cause a deadlock
            if no observation is added by an independent thread.
        """
        while True:
            try:
                answer = self._post(
                    "get suggestion",
                    "suggestion",
                    "create",
                    data={"environment_value": environment_value},
                )
            except NumParallelError:
                time.sleep(0.2)
            else:
                break

        s = Suggestion(sample=answer["sample"], id=answer["suggestion_id"])
        self.suggestions[s.id] = s
        return s

    def clear_suggestion(self, suggestion_id: int, message: str = "") -> None:
        """If the evaluation for a certain suggestion fails, the suggestion
        can be cleared from the study. Example::

            study.clear_suggestion(suggestion.id, 'Computation failed')

        .. note:: The study only creates ``num_parallel`` suggestions (see
            :func:`configure`) until it waits for an
            observation to be added (see :func:`add_observation`)
            or a suggestion to be cleared.

        Args:
          suggestion_id: Id of the suggestion to be cleared.
          message: An optional message that is printed out.
        """
        del self.suggestions[suggestion_id]
        self._post(
            "clear suggestion",
            "suggestion",
            "remove",
            data={"suggestion_id": suggestion_id, "message": message},
        )

    def clear_all_suggestions(self) -> None:
        """Clear all open suggestions. Example::

            study.clear_all_suggestions()


        .. note:: The study only creates ``num_parallel`` suggestions (see
            :func:`configure`) until it waits for an
            observation to be added (see :func:`add_observation`)
            or a suggestion to be cleared.

        """
        sids = list(self.suggestions.keys())
        for sid in sids:
            self.clear_suggestion(sid)

    def new_observation(self) -> Observation:
        """Create a new :class:`Observation` object that allows
        to add data via :func:`~Observation.add`. Example::

            observation = study.new_observation()
            observation.add(1.2)
            observation.add(0.1, derivative='x1')

        """
        return Observation()

    def add_observation(
        self,
        observation: Observation,
        suggestion_id: Optional[int] = None,
        design_value: Optional[list[Union[float, str]]] = None,
        environment_value: Optional[list[float]] = None,
        acquisition_time: Optional[float] = None,
        check: bool = True,
    ) -> None:
        """Adds an observation to the study. Example::

            study.add_observation(observation, suggestion.id)

        Args:
          observation: :class:`Observation` object with added values
             (see :func:`new_observation`)
          suggestion_id: Id of the corresponding suggestion if it exists.
          design_value: If the observation does not belong to an open suggestion,
             the corresponding design value must be provided as a list of floats for
             continuous and discrete parameters or string for categorial parameters.
             E.g. ``[0.1, 2.0, 'cat1']``.
          environment_value: If an environment parameters are specified, this
             specifies the value of variable environment parameters as a list of
             floats that is valid for all values added to the observation.
             E.g. ``[1.0, 2.0]``.
             Alternatively, one can also set different environment values for
             each entry of the observation (see :func:`~Observation.add`).
          acquisition_time: If the observation does not belong to an open
             suggestion, it is possible to specify the time it took to retrieve
             the observation (e.g. the computation time). This information can be
             used to adapt the effort of computing the next suggestions.
          check: If true, the validity of the observation is checked
        """
        if not isinstance(observation, Observation):
            raise TypeError(
                "observation -> expected Observation object. "
                + "Check return value of evaluator function"
            )

        if suggestion_id is not None:
            acquisition_time = (
                observation.finished - self.suggestions[suggestion_id].created
            )

        self._post(
            "add observation",
            "observation",
            "create",
            data={
                "observation_data": observation.data,
                "acquisition_time": acquisition_time,
                "suggestion_id": suggestion_id,
                "design_value": design_value,
                "environment_value": environment_value,
                "check": check,
            },
        )

        if suggestion_id:
            del self.suggestions[suggestion_id]

    def add_many(
        self,
        observations: list[Observation],
        design_values: list[list[Union[float, str]]],
        environment_values: Optional[list[list[float]]] = None,
        acquisition_times: Optional[list[float]] = None,
        check: bool = True,
    ) -> None:
        """Adds many observations to the study. Example::

            study.add_many(observations, design_values)

        Args:
          observations: List of :class:`Observation`
            objects for each sample
            (see :func:`new_observation`)
          design_values: List of design values.
             E.g. ``[[0.1, 1.0, 'cat1'], [0.2, 2.0, 'cat2']]``
          environment_values: Optional list of environment values.
             If not specified, the last known environment values are taken.
             E.g. ``[[1.0, 2.0], [1.1, 2.3]]``
          acquisition_times: Optional list of times required to acquire
             each observation.
          check: If true, the validity of the observation is checked

        .. warning:: The purpose of this function is to speed up the process
           of adding many observations to the study. To this end, the intermediate
           driver states are not computed. This means that all driver-specific
           historic data (any path of :func:`historic_parameter_values` starting
           with `driver...`) is incorrect. The same holds for most of the data
           shown on the dashboard. To avoid this, one has to add the observations
           one by one using :func:`add_observation`.

        """
        obs_data = []
        for o in observations:
            if not isinstance(o, Observation):
                raise TypeError("observations -> expected Observation objects.")
            obs_data.append(o.data)

        # todo: check
        self._post(
            "add observations",
            "observation",
            "create_many",
            data={
                "observations": obs_data,
                "design_values": design_values,
                "environment_values": environment_values,
                "acquisition_times": acquisition_times,
                "check": check,
            },
        )

    def set_objective(self, objective: Callable) -> None:
        raise AttributeError(
            "The method 'set_objective()' is deprecated. "
            "Please, use the method 'set_evaluator()' instead."
        )

    def set_evaluator(self, evaluator: Callable[..., Observation]) -> None:
        """Set the function that maps design parameters to an :class:`Observation`.
        Example::

            def evaluate(study: Study, x1: float, x2: float) -> Observation:
                observation = study.new_observation()
                observation.add(x1**2 + x2**2)
                return observation
            study.set_evaluator(evaluate)

        Args:
          evaluator: Function handle for a function of the
            variable parameters that returns a corresponding :class:`Observation` object.
            The function must accept a ``"study"`` argument as well as
            an argument with the name of each design parameter and fixed environment
            parameter.
        """
        if self.evaluator is not None and evaluator != self.evaluator:
            warn(
                "The evaluator was already set before. "
                "Changing the evaluator function (that is the mapping "
                "between parameters and observations) can lead to undefined "
                "behaviour."
            )

        self.evaluator = evaluator

    def run(self) -> None:
        """Run the acquisition loop after the evaluator has been set
        (see :func:`set_evaluator`).
        The acquisition loop stops after a stopping
        criterion has been met (see :func:`configure`).
        Example::

            study.run()

        """
        if self.evaluator is None:
            raise EnvironmentError("The evaluator was not set")

        self.start_clock()
        try:
            while not self.is_done():
                if self.num_failed >= self.max_num_failed:
                    warn(f"The previous {self.num_failed} computations failed.")
                    self._stop_study()
                    return
                suggestion = self.get_suggestion()
                t = threading.Thread(target=self._acquire, args=(suggestion,))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            self._stop_study()

        while self.threads:
            self.threads[0].join()

    def _stop_study(self) -> None:
        try:
            if num_open := len(self.threads):
                warn(
                    f"Study stopped. Waiting for {num_open} open "
                    f"evaluation{'s'[:num_open^1]}."
                )
                while self.threads:
                    self.threads[0].join()
            else:
                warn("Study stopped.")
        finally:
            self._post("stop study", "study", "stop", data={})

    def _acquire(self, suggestion: Suggestion) -> None:
        assert self.evaluator is not None
        self.threads.append(threading.current_thread())
        try:
            observation = self.evaluator(study=self, **suggestion.kwargs)
            self.add_observation(observation, suggestion.id)
        except Exception as err:
            self.clear_suggestion(
                suggestion.id, f"Evaluator function failed with error: {err}"
            )
            warn(
                f"For the arguments {suggestion.kwargs}, "
                f"the evaluator function raised the error: {err}\n"
                + traceback.format_exc()
            )
            self.num_failed += 1
        else:
            self.num_failed = 0
        self.threads.remove(threading.current_thread())
