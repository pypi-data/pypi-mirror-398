class SumUseCase:
    """Use case for mathematical sum operations."""
    
    async def execute(self, a: float, b: float) -> float:
        """
        Sum two numbers.
        
        Args:
            a: First number
            b: Second number
            
        Returns:
            The sum of a and b
        """
        return a + b