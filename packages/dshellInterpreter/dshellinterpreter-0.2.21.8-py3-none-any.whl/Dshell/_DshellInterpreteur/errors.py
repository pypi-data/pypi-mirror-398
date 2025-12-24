
class DshellInterpreterError(Exception):
    """Base class for exceptions in this module."""
    pass

class DshellInterpreterStopExecution(DshellInterpreterError):
    """Exception raised to stop the execution of the interpreter."""
    pass