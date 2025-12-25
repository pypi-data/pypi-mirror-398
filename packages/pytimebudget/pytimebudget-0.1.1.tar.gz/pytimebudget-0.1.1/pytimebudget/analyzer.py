from statistics import mean
from .storage import fetch_samples
from .warnings import emit_warning

BASELINE_SAMPLES = 10
REGRESSION_FACTOR = 1.3

def analyze(record, warn_only):
    samples = fetch_samples(record["name"])

    if len(samples) < BASELINE_SAMPLES:
        return

    baseline = mean(samples[:-1])
    current = samples[-1]

    if baseline <= 0:
        return

    if current > baseline * REGRESSION_FACTOR:
        emit_warning(
            name=record["name"],
            baseline=baseline,
            current=current,
            warn_only=warn_only,
        )
