METRICS_INTERVAL = 0.5
PREDICT_INTERVAL = 0.5

# Profiled on benchmark and testbed
PRIORITY_TABLE = {
    "Researcher": None,
    "Writer": None,

    "Router": None,
    "MathAgent": None,
    "HistoryAgent": None,
}

PREDICT_TIME_TABLE = {
    "Researcher": None,
    "Writer": None,

    "Router": None,
    "MathAgent": None,
    "HistoryAgent": None,
}

# Max tokens supported by KV Cache
MAX_TOKENS = None
Decode_slop = None
Bias_factor = None # default 1