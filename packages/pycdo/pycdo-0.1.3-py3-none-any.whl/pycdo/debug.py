import os 

class MockResult:
    def __init__(self, output, returncode = 0):
        self.output = output
        self.returncode = returncode

def skip_run(skip = True):
    if skip:
        os.environ["_DEBUG_SKIP_RUN"] = "true"
    else:
        os.environ["_DEBUG_SKIP_RUN"] = "false"