from framework.trace.trace import RequestGenerator



def get_trace_file(rate):
    return f"/state/trace/{rate}_trace.csv"

__all__ = [
    "RequestGenerator",
    ]