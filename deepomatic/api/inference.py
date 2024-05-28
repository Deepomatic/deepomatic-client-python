from deepomatic.api.exceptions import DeepomaticException
from deepomatic.api.resources.task import Task
from deepomatic.api.inputs import format_inputs


class InferenceResource(object):
    def inference(self, return_task=False, wait_task=True, **kwargs):
        assert(self._pk is not None)

        inputs = kwargs.pop('inputs', None)
        if inputs is None:
            raise DeepomaticException("Missing keyword argument: inputs")
        content_type, data, files = format_inputs(inputs, kwargs)
        result = self._helper.post(self._uri(pk=self._pk, suffix='/inference'), content_type=content_type, data=data, files=files)
        task_id = result['task_id']
        task = Task(self._helper, pk=task_id)
        if wait_task:
            task.wait()

        if return_task:
            return task
        else:
            return task['data']
