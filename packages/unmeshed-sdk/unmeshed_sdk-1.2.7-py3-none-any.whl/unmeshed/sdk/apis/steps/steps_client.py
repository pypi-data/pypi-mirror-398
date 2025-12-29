from typing import Optional

from ...common.step_definition import StepDefinition
from ...common.unmeshed_constants import StepType


class StepClient:

    @staticmethod
    def get_default_step_definition_template(
            stepType: StepType,
            namespace: Optional[str] = "default",
    ) -> StepDefinition:
        if stepType == StepType.HTTP:
            return StepDefinition(
                ref=f"new_http_ref",
                name="new_http",
                namespace=namespace,
                type=stepType,
                input={
                    "method": "POST",
                    "url": "http://localhost:8080/api/test/post",
                    "headers": {
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Authorization": "Bearer test"
                    },
                    "params": {
                        "sampleKey": "sampleValue"
                    },
                    "body": {
                        "type": "json",
                        "content": {
                            "title": "foo",
                            "body": "bar",
                            "userId": 1
                        }
                    },
                    "repeatUntilEnabled": None,
                    "repeatUntilCondition": {
                        "script": (
                            "// (steps, context) will be provided as default inputs\n"
                            "(steps, context) => {\n"
                            "    return steps.__self.output.response.counter === 100;\n"
                            "}"
                        )
                    },
                    "repeatIntervalSeconds": None,
                    "maxRepeatCount": None,
                    "includeFullResponseString": False,
                    "noEncode": False,
                    "extraLongTimeouts": False
                }
            )

        if stepType == StepType.JAVASCRIPT:
            return StepDefinition(
                ref=f"new_javascript_ref",
                name="new_javascript",
                namespace=namespace,
                type=stepType,
                input={
                    "script": (
                        "// (steps, context) will be provided as default inputs\n"
                        "(steps, context) => {\n"
                        "    return {\n"
                        "        \"processId\": context.id,\n"
                        "        \"currentStepId\": steps.__self.id,\n"
                        "    }\n"
                        "}"
                    )
                }
            )

        if stepType == StepType.PYTHON:
            return StepDefinition(
                ref=f"new_python_ref",
                name="new_python",
                namespace=namespace,
                type=stepType,
                input={
                    "script": "# Do not change the parameters count, order, or types.\n# The parameter names must remain the same.\n# `steps` and `context` are Python dictionaries provided by default.\n# For simplicity, a dict is used as an example here.\ndef main(steps, context):\n    # Maintain the parameter count, order, and types as required.\n    # Write your custom logic below.\n    return {\n        \"processId\": context.get(\"id\"),\n        \"currentStepId\": steps[\"__self\"][\"id\"],\n        \"statusMessage\": \"Process completed\",  # Test string\n        \"isSuccessful\": True  # Test boolean\n    }\n"
                }
            )

        if stepType == StepType.JQ:
            return StepDefinition(
                ref=f"new_jq_ref",
                name="new_jq",
                namespace=namespace,
                type=stepType,
                input={
                    "script": ".color",
                    "input": {
                        "name": "apple",
                        "color": "red",
                        "price": 10
                    }
                }
            )

        if stepType == StepType.WAIT:
            return StepDefinition(
                ref=f"new_wait_ref",
                name="new_wait",
                namespace=namespace,
                type=stepType,
                input={
                    "script": "\n(steps, context) => {\n    // Use \"steps.__self.start\" or if inside loops - \"steps.__self.executionsList?.at(-1)?.scheduled\" as reference\n    return {\n        \"waitUntil\" : steps.__self.start + (3 * 1000) // 3 seconds\n    }\n}\n"
                }
            )

        if stepType == StepType.NOOP:
            return StepDefinition(
                ref=f"new_noop_ref",
                name="new_noop",
                namespace=namespace,
                type=stepType,
                input={
                    "key1": "val1",
                    "key2": "val2"
                }
            )

        if stepType == StepType.DEPENDSON:
            return StepDefinition(
                ref=f"new-depends_on",
                name="new_depends_on_ref",
                namespace=namespace,
                type=stepType,
                input={
                    "dependsOnStatement": "PROCESS('name', 'COMPLETED') OR PROCESS('name', 'TERMINATED') OR PROCESS('name', 'FAILED')",
                    "intervalSeconds": 10
                }
            )
        raise Exception(f"Unable to construct default step definition for type: {getattr(type, 'value', str(type))}")