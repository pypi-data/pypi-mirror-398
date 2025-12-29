from src.unmeshed.sdk.decorators.worker_function import worker_function


@worker_function(name = "worker2_alt")
def worker2(inp : dict) -> dict:
    return {
        "original_input" : inp,
        "worker": "worker2"
    }