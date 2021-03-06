"""Classes for describing work and results.
"""
import enum
import json
import pathlib


class StrEnum(str, enum.Enum):
    "An Enum subclass with str values."


class WorkerOutcome(StrEnum):
    """Possible outcomes for a worker.
    """
    NORMAL = 'normal'  # The worker exited normally, producing valid output
    EXCEPTION = 'exception'  # The worker exited with an exception
    ABNORMAL = 'abnormal'  # The worker did not exit normally or with an exception (e.g. a segfault)
    NO_TEST = 'no-test'  # The worker had no test to run
    SKIPPED = 'skipped'  # The job was skipped (worker was not executed)


class TestOutcome(StrEnum):
    """A enum of the possible outcomes for any mutant test run.
    """
    SURVIVED = 'survived'
    KILLED = 'killed'
    INCOMPETENT = 'incompetent'


class WorkResult:
    """The result of a single mutation and test run.
    """

    def __init__(self,
                 worker_outcome,
                 output=None,
                 test_outcome=None,
                 diff=None):
        if worker_outcome is None:
            raise ValueError('Worker outcome must always have a value.')

        self._output = output
        self._test_outcome = test_outcome
        self._worker_outcome = worker_outcome
        self._diff = diff

    @property
    def worker_outcome(self):
        "A `WorkerOutcome` indicating how the worker finished."
        return self._worker_outcome

    @property
    def test_outcome(self):
        "A `TestOutcome` indicating how the test runner finished. Possibly `None`."
        return self._test_outcome

    @property
    def output(self):
        "Any output returned by the test command. Possibly `None`."
        return self._output

    @property
    def diff(self):
        "A sequence of strings containing the diff generated by the mutation. Possibly `None`."
        return self._diff

    def as_dict(self):
        "Get the WorkResult as a dict."
        return {
            'output': self.output,
            'test_outcome': self.test_outcome,
            'worker_outcome': self.worker_outcome,
            'diff': self.diff,
        }

    @property
    def is_killed(self):
        "Whether the mutation should be considered 'killed'"
        return self.test_outcome != TestOutcome.SURVIVED

    def __eq__(self, rhs):
        return self.as_dict() == rhs.as_dict()

    def __neq__(self, rhs):
        return not self == rhs

    def __repr__(self):
        return "<WorkResult {test_outcome}/{worker_outcome}: '{output}'>".format(
            test_outcome=self._test_outcome,
            worker_outcome=self.worker_outcome,
            output=self.output)


class WorkItem:
    """Description of the work for a single mutation and test run.
    """

    # pylint: disable=R0913
    def __init__(self,
                 module_path=None,
                 operator_name=None,
                 occurrence=None,
                 start_pos=None,
                 end_pos=None,
                 job_id=None):
        if start_pos[0] > end_pos[0]:
            raise ValueError('Start line must not be after end line')

        if start_pos[0] == end_pos[0]:
            if start_pos[1] >= end_pos[1]:
                raise ValueError(
                    'End position must come after start position.')

        self._module_path = pathlib.Path(module_path)
        self._operator_name = operator_name
        self.occurrence = occurrence
        self._start_pos = start_pos
        self._end_pos = end_pos
        self._job_id = job_id

    @property
    def module_path(self):
        "pathlib.Path to module being mutated."
        return self._module_path

    @property
    def operator_name(self):
        "The name of the operator (i.e. as defined by the provider)"
        return self._operator_name

    @property
    def start_pos(self):
        "Start of the mutation location as a `(line, column)` tuple."
        return self._start_pos

    @property
    def end_pos(self):
        """End of the mutation location as a `(line, column)` tuple.

        Note that this represents the offset *one past* the end of the mutated
        segment. If the mutated segment is at the end of a file, this offset
        will be past the end of the file.
        """
        return self._end_pos

    @property
    def job_id(self):
        "The unique ID of the job"
        return self._job_id

    def as_dict(self):
        """Get fields as a dict.
        """
        return {
            'module_path': str(self.module_path),
            'operator_name': self.operator_name,
            'occurrence': self.occurrence,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'job_id': self.job_id,
        }

    def __eq__(self, rhs):
        return self.as_dict() == rhs.as_dict()

    def __neq__(self, rhs):
        return not self == rhs

    def __repr__(self):
        return "<WorkItem {job_id}: ({start_pos}/{end_pos}) {occurrence} - {operator} ({module})>".format(
            job_id=self.job_id,
            start_pos=self.start_pos,
            end_pos=self.end_pos,
            occurrence=self.occurrence,
            operator=self.operator_name,
            module=self.module_path)


class WorkItemJsonEncoder(json.JSONEncoder):
    "Custom JSON encoder for workitems and workresults."

    def default(self, o):  # pylint: disable=E0202
        if isinstance(o, WorkItem):
            return {"_type": "WorkItem", "values": o.as_dict()}

        if isinstance(o, WorkResult):
            return {"_type": "WorkResult", "values": o.as_dict()}

        return super().default(o)


class WorkItemJsonDecoder(json.JSONDecoder):
    "Custom JSON decoder for WorkItems and WorkResults."

    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self._decode_work_items)

    @staticmethod
    def _decode_work_items(obj):
        if (obj.get('_type') == 'WorkItem') and ('values' in obj):
            values = obj['values']
            return WorkItem(**values)

        if (obj.get('_type') == 'WorkResult') and ('values' in obj):
            values = obj['values']
            return WorkResult(**values)

        return obj
