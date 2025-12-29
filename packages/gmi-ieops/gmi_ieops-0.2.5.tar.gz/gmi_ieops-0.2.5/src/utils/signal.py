import traceback, signal


def debug(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging."""
    message = "Signal received : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))


def bind_signal(reload):
    # signal.signal(signal.SIGUSR1, debug)  # Register handler
    signal.signal(signal.SIGHUP, reload)
    signal.signal(signal.SIGUSR1, reload)
    signal.signal(signal.SIGTERM, reload)
    signal.signal(signal.SIGQUIT, reload)
    signal.signal(signal.SIGINT, reload)
