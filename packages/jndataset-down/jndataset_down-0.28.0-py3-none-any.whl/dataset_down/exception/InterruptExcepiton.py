class InterruptException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self._format_message())
    
    def _format_message(self):
        return f"Interrupt happened, message: {self.message}"
    
    def __str__(self):
        return self._format_message()
    
    def __repr__(self):
        return f"InterruptException({self.message})"