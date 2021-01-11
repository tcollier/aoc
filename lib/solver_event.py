class SolverEvent:
    MISSING_SRC = "missing-source"
    BUILD_STARTED = "build-started"
    BUILD_FINISHED = "build-finished"
    BUILD_FAILED = "build-failed"
    SOLVE_STARTED = "solve-started"
    SOLVE_FINISHED = "solve-finished"
    SOLVE_ATTEMPTED = "solved-attempted"
    SOLVE_SUCCEEDED = "solve-succeeded"
    SOLVE_FAILED = "solve-failed"
    SOLVE_INCORRECT = "solve-incorrect"
    OUTPUT_SAVED = "output-saved"
    TIMING_STARTED = "timing-started"
    TIMING_SKIPPED = "timing-skipped"
    TIMING_FINISHED = "timing-finished"
    TIMING_FAILED = "timing-failed"
    TERMINATE = "terminate"