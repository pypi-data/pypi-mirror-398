from contextvars import ContextVar

# used to save all viewed messages in the current scoop
dshell_cached_messages = ContextVar('dshell_cached_messages')