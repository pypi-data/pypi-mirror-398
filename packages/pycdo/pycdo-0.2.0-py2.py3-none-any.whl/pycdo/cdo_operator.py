class CdoOperator:
    def __init__(self, command, n_input=1, n_output=1, params=None):
        """
        Represents a CDO operator.

        :param command: Name of the CDO operator (e.g., 'add', 'sub', 'timmean')
        :param n_input: Number of input files required
        :param n_output: Number of output files produced
        :param params: List of parameter names this operator accepts
        """
        self.command = command
        self.n_input = n_input
        self.n_output = n_output
        self.params = params or []

    def __repr__(self):
        return (f"CdoOperator(command='{self.command}', "
                f"n_input={self.n_input}, "
                f"n_output={self.n_output}, "
                f"params={self.params})")

