from typing import Any, Optional, Union
import requests
import time

from ..requestor import OptimizerRequestor

class Driver:
    """This class provides methods for retrieving and setting driver-specific
    information of the study. Depending on the chosen driver of
    :func:`Client.create_study` the driver provides specific methods. More details
    for each driver are available in the :ref:`driver reference <DriverReference>`.
    Example::

       study.run()
       driver = study.driver
       min_objective_values = driver.historic_parameter_values(
           path="acquisition_function.min_objective")

    The constructor should not be used directly since it does not create a
    driver on the server side. Instead, one should use :attr:`Study.driver`.
    """
    
    def __init__(self, study_id: str, project_id: str, requestor: OptimizerRequestor) -> None:
        self._requestor = requestor
        self.study_id = study_id
        self.project_id = project_id

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
        return self._requestor.post(purpose, object, operation, self.qualifier, data)

    def _get(self, purpose:str, object: str, type: str) -> dict[str, Any]:
        return self._requestor.get(purpose, object, type, self.qualifier)

    def _run_task(self, purpose: str, task: str, data: dict[str, Any]) -> Any:
        data["task"] = task
        answer = self._post(purpose, "driver", "start_task", data=data)

        print("\r" + purpose[0].capitalize() + purpose[1:] + ":      ", end="")
        task_id = answer["task_id"]
        try:
            while True:
                answer = self._post(
                    purpose, "driver", "get_task_status", data={"task_id": task_id}
                )

                progress_msg = answer["progress_msg"]
                status = answer["status"]
                print("\r" + progress_msg + "      ", end="")

                if status in ["stopped", "finished"]:
                    print("")
                    break
                time.sleep(1)

        except KeyboardInterrupt:
            answer = self._post(
                purpose, "driver", "stop_task", data={"task_id": task_id}
            )

        answer = self._post(
            purpose, "driver", "fetch_task_result", data={"task_id": task_id}
        )
        return answer["result"]

    def describe(self) -> dict[str, Any]:
        """Get description of all modules and their parameters that are used
        by the driver. Example::

            description = driver.describe()
            print(description["members"]["surrogates"]["0"])

        Returns: A nested dictionary with description of submodules consisting
               of a name and a descriptive text. If the entry describes a module,
               it has an additional ``"members"`` entry with dictionaries describing
               submodules and parameters. 
        """
        answer = self._get("get description of the driver", "driver", "describe")
        return answer["description"]
    
    def get_state(self, path: Optional[str] = None) -> dict[str, Any]:
        """Get state of the driver. Example::

            best_sample = driver.get_state(path="best_sample")

        Args:
          path: A dot-separated path to a submodule or parameter.
            If none, the full state is returned.

        Returns: If path is None, a dictionary with information of driver state.

        .. note:: A description of the meaning of each entry in the state
            can be retrieved by :func:`describe`.
        """
        answer = self._post(
            "get driver state", "driver", "get_state", data={"path": path}
        )
        return answer["state"]
    
    def historic_parameter_values(self, path: str) -> list[Any]:
        """Get the values of an internal parameter for each iteration of the study. Example::

            min_objective_values = driver.historic_parameter_values(
                path="acquisition_function.min_objective")

        Args:
          path: A dot-separated path to the parameter.

        .. note:: A description of the meaning of each parameter can be retrieved
            by :func:`describe`.
        """
        answer = self._post(
            "get historic parameter values",
            "driver",
            "historic_parameter_values",
            data={"path": path},
        )
        return answer["values"]
    
class Minimizer(Driver):
    """
    This class provides methods for retieving and setting information of the
    minimization driver of the study.
    """

    @property
    def best_sample(self) -> dict[str, Union[float, int, str]]:
        """
        Best sample with minimal objective value found during the minimization. Example::

          for key, value in driver.best_sample.items():
             print(f"{key} = {value}")
        
        """
        answer = self._post(
            "get best sample", "driver", "get_state", data={"path": "best_sample"}
        )
        return answer["state"]

    @property
    def min_objective(self) -> float:
        """
        Minimal objective value found during the minimization. Example::

          min_objective = driver.min_objective

        """
        answer = self._post(
            "get minimal objective value", "driver", "get_state", data={"path": "min_objective"}
        )
        return answer["state"]

class LeastSquaresDriver(Minimizer):
    """
    This class provides methods for retieving information of the
    result of the least squares minimization using ``scipy.optimize.least_squares``.
    """

    @property
    def best_sample(self) -> dict[str, Union[float, int, str]]:
        """
        Best sample with minimal chi-squared value found during the minimization. Example::

          for key, value in best_sample.items():
             print(f"{key} = {value}")

        """
        return super().best_sample

    @property
    def min_objective(self) -> float:
        """
        Minimal chi-squared value found during the minimization. Example::

          min_chi_sq = study.driver.min_objective

        """
        return super().min_objective

    @property
    def uncertainties(self) -> dict[str, float]:
        """
        Uncertainties of the continuous parameters of the :py:attr:`best_sample`. Example::

          for key, value in uncertainties.items():
              print(f"uncertainty of {key}: {value}")

        """
        answer = self._post(
            "get uncertainties",
            "driver",
            "get_state",
            data={"path": "parameter_uncertainties"},
        )
        return answer["state"]
