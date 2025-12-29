class TermSignalInterruptionException(Exception):
    def __init__(self):
        self.message = "Stopping consumer due to TERM Signal, subscriber had not yet started processing the event"
        super(TermSignalInterruptionException, self).__init__(self.message)
