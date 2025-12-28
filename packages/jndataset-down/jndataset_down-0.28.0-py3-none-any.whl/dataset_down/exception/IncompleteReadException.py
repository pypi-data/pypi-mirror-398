class IncompleteReadException(Exception):
    def __init__(self, file, chunk ,bytes_read, expected_bytes):
        self.file = file
        self.chunk = chunk
        self.bytes_read = bytes_read
        self.expected_bytes = expected_bytes
        super().__init__(f"Incomplete read:{file},chunk:{chunk}, {bytes_read} bytes read, {expected_bytes} bytes expected")
    
    def __str__(self):
        return f"Incomplete read:{self.file},chunk:{self.chunk}, {self.bytes_read} bytes read, {self.expected_bytes} bytes expected"
    
    def __repr__(self):
        return f"IncompleteReadException({self.file},chunk:{self.chunk}, {self.bytes_read} bytes read, {self.expected_bytes} bytes expected)"