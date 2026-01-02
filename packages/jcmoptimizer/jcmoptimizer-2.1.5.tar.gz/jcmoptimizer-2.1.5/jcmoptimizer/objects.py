from typing import Any, Optional, Union
import time

class Observation:
    """
    This class provides a container to collect data to be sent to the
    optimizer. This includes scalar or vectorial inputs for
    the objective or surrogate models of an active learning-based
    driver.
    """

    def __init__(self) -> None:
        self._data: dict[Union[str, None], list] = {}
        self._finished = time.time()
    
    def add(
            self,
            value: Union[float, list[float]],
            derivative: Optional[str]=None,
            uncertainty: Optional[Union[float, list[float]]]=None,
            model_name: Optional[str]=None,
            environment_value: Optional[list[float]]=None
    ) -> None:
        """
        Add data to observation. Example::

             obs.add(val)
             obs.add(dval_dx1, derivative='x1')
             obs.add(dval_dx2, derivative='x2')

        Args:
          value: Numerical value or list of values.
          derivative: If the values are derivatives w.r.t. a
              design or environment parameter, this should be the 
              name of the parameter.
          uncertainty: The uncertainty of the provided values,
              i.e. the estimated standard deviation of multiple
              observations for same parameter.
          model_name: Name of the surrogate model that
              is trained on the data. Can be also ``None``
              for drivers that do not support multiple models.
          environment_value: List of environment value for all
              entries of the environment of the study. Optionally,
              entries for different environment values can be added
              consecutively, such that also scans of environment values
              can be collected into one observation.

        """
        try:
            self._data[model_name]
        except KeyError:
            self._data[model_name] = []

        entry: dict[str, Any] = dict(env = environment_value, val=None, der={})
        if derivative is None:        
            entry["val"] = dict(o=value, u=uncertainty)
        else:
            entry["der"][derivative] = dict(o=value, u=uncertainty)
            
        self._data[model_name].append(entry)
            
        self._finished = time.time()

    @property
    def data(self) -> dict[Optional[str], list]:
        return self._data
    
    @property
    def finished(self) -> float:
        return self._finished
    
        
class Suggestion:

    """This class provides the sample to be evaluated and the id
    which is required to identify results for this suggestion.
    Example::
    
      def evaluate(study: Study, x1: float, x2: float) -> Observation:
         obs = study.new_observation()
         obs.add(x1**2 + x2**2)
         return obs
    
      suggestion = study.get_suggestion()
      obs = evaluate(study, **suggestion.kwargs)
      study.add_observation(observation=obs, suggestion_id=suggestion.id)
    
    The constructor should not be used directly.
    Instead, one creates suggestions using :func:`Study.get_suggestion`.
    """
    def __init__(self,
                 sample: dict[str, Union[str, float]],
                 id: int) -> None:
        self._created = time.time()
        self._id = id
        self._sample = sample

    @property
    def id(self) -> int:
        """The id of the suggestion."""
        return self._id

    @property
    def created(self) -> float:
        return self._created
    
    @property
    def kwargs(self) -> dict[str, Union[str, float]]:
        """Dictionary which maps names of design parameters to their values
        for which an observation is suggested.
        """
        return self._sample
    

