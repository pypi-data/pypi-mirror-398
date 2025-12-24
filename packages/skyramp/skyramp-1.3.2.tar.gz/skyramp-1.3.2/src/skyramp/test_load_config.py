"""
Contains helpers for configuring load test parameters
"""
from typing import Optional

class _LoadTestConfig:
    def __init__(self,
                 load_target_rps: Optional[int] = None,
                 at_once: Optional[int] = None,
                 load_count: Optional[int] = None,
                 load_num_threads: Optional[int] = None,
                 load_duration: Optional[str] = None,
                 load_rampup_interval: Optional[str] = None,
                 load_rampup_duration: Optional[str] = None,
                 stop_on_failure: Optional[bool] = False,
                 ) -> None:

        # load_config = skyramp.load_config(
        #   load_num_threads=1,
        # )
        self.load_target_rps = load_target_rps
        self.load_num_threads = load_num_threads
        self.at_once = at_once
        self.load_count = load_count
        self.load_duration = load_duration
        self.load_rampup_interval = load_rampup_interval
        self.load_rampup_duration = load_rampup_duration
        self.stop_on_failure = stop_on_failure

    @staticmethod
    def from_kwargs(**kwargs):
        """
        convert kwargs into loadTestConfig object
        """
        load_target_rps = kwargs.get('load_target_rps', None)
        load_num_threads = kwargs.get('load_num_threads', None)
        at_once = kwargs.get('at_once', None)
        load_count = kwargs.get('load_count', None)
        load_duration = kwargs.get('load_duration', None)
        load_rampup_interval = kwargs.get('load_rampup_interval', None)
        load_rampup_duration = kwargs.get('load_rampup_duration', None)
        stop_on_failure = kwargs.get('stop_on_failure', False)
        return _LoadTestConfig(load_target_rps,
                               at_once,
                               load_count,
                               load_num_threads,
                               load_duration,
                               load_rampup_interval,
                               load_rampup_duration,
                               stop_on_failure)

    def apply_to_dict(self, pattern: dict):
        """
        apply load test values to dictionary
        """
        if self.load_target_rps is not None:
            pattern["targetRPS"] = self.load_target_rps
        if self.load_num_threads is not None:
            pattern["numThreads"] = self.load_num_threads
        if self.at_once is not None:
            pattern["atOnce"] = self.at_once
        if self.load_duration is not None:
            pattern["duration"] = self.load_duration
        if self.load_count is not None:
            pattern["count"] = self.load_count
        if (
            self.load_rampup_interval is not None
            or self.load_rampup_duration is not None
        ):
            pattern["rampUp"] = {}
            if self.load_rampup_interval is not None:
                pattern["rampUp"]["interval"] = self.load_rampup_interval
            if self.load_rampup_duration is not None:
                pattern["rampUp"]["duration"] = self.load_rampup_duration
        if self.stop_on_failure is True:
            pattern["stopOnFailure"] = True
