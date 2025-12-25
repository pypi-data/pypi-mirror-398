"""
LolaDB Python Client - Pure Python implementation using pyarrow.flight
"""

import pyarrow.flight as flight


class LolaDbClient:
    """
    LolaDB Flight Client
    
    A pure Python client that uses pyarrow.flight directly to communicate
    with the LolaDB server. This avoids extra copies by working directly
    with Arrow data structures.
    
    Args:
        addr (str): Address of the Flight server (e.g., "localhost:2711" or "grpc://localhost:2711")
    
    Example:
        >>> import loladb
        >>> client = loladb.LolaDbClient("grpc://localhost:2711")
        >>> client.get_simple_tensor()
        Tensor shape: [100,100,100]
        Total elements received: 1000000
    """
    
    def __init__(self, addr: str):
        """Connect to a LolaDB Flight server"""
        # Ensure the address has a scheme
        if not addr.startswith(('grpc://', 'grpc+tcp://', 'http://', 'https://')):
            # Default to grpc:// if no scheme provided
            addr = f"grpc://{addr}"
        
        self.client = flight.FlightClient(addr)
    
    def get_simple_tensor(self):
        """
        Get a simple 3D tensor from the server and print its shape.
        
        This method directly receives Arrow data without any extra copies,
        making it more efficient than the Rust PyO3 implementation.
        
        Returns:
            None (prints tensor shape and element count)
        
        Example:
            >>> client.get_simple_tensor()
            Tensor shape: [100,100,100]
            Total elements received: 1000000
        """
        # Create ticket
        ticket = flight.Ticket(b"simple_tensor")
        
        # Get flight stream
        flight_stream = self.client.do_get(ticket)
        
        # Read the stream - this gives us a FlightStreamReader
        # which directly exposes Arrow data without extra copies
        reader = flight_stream.to_reader()
        
        # Get schema with tensor shape metadata
        schema = reader.schema
        if schema.metadata and b'tensor_shape' in schema.metadata:
            tensor_shape = schema.metadata[b'tensor_shape'].decode('utf-8')
            print(f"Tensor shape: [{tensor_shape}]")
        
        # Count total elements by reading all batches
        # The data stays in Arrow format - no unnecessary copies
        total_elements = 0
        for batch in reader:
            total_elements += batch.num_rows
        
        print(f"Total elements received: {total_elements}")
    
    def __repr__(self):
        return "LolaDbClient()"

