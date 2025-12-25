import os 
from pathlib import Path

class MockOutput():
    def __init__(self, output = None):
        self.output = output

mockoutput = MockOutput("test_output")

class MockResult:
    def __init__(self, file_output = None, text_output = None, returncode = 0):
        
        if file_output is not None:
            output = file_output
            if isinstance(file_output, list):
                [Path(file).touch() for file in file_output]
            else:
                Path(file_output).touch()

        if text_output is not None:
            output = text_output
            self.stdout = text_output

        self.output = output
        self.returncode = returncode


def skip_run(skip = True):
    if skip:
        os.environ["_DEBUG_SKIP_RUN"] = "true"
    else:
        os.environ["_DEBUG_SKIP_RUN"] = "false"