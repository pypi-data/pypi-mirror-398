# guardian/app_state.py
#
# A simple singleton class for managing application-wide state.
# This ensures that all parts of the application can access a single,
# consistent state object.

class AppState:
    """
    Manages a global, application-wide state using the singleton pattern.
    """
    _instance = None
    _state = {}

    def __new__(cls):
        """
        Ensures only a single instance of AppState exists.
        """
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
        return cls._instance

    def set(self, key, value):
        """
        Sets a key-value pair in the global state.
        """
        self._state[key] = value

    def get(self, key, default=None):
        """
        Retrieves a value from the global state.
        """
        return self._state.get(key, default)

    def increment(self, key, value=1):
        """
        Increments a numeric value in the global state.
        
        Args:
            key: The key of the value to increment
            value: The amount to increment by (default: 1)
            
        Returns:
            The new value after incrementing
        """
        current = self._state.get(key, 0)
        if not isinstance(current, (int, float)):
            current = 0
        new_value = current + value
        self._state[key] = new_value
        return new_value

    def decrement(self, key, value=1):
        """
        Decrements a numeric value in the global state.
        
        Args:
            key: The key of the value to decrement
            value: The amount to decrement by (default: 1)
            
        Returns:
            The new value after decrementing
        """
        current = self._state.get(key, 0)
        if not isinstance(current, (int, float)):
            current = 0
        new_value = current - value
        self._state[key] = new_value
        return new_value

    def __repr__(self):
        """
        Provides a string representation of the current state.
        """
        return f"AppState(state={self._state})"
