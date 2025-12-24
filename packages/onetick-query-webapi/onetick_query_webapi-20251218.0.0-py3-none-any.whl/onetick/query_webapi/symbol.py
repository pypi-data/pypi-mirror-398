class Symbol:
    def __init__(self, name, params=None):
        """Constructs Symbol object from it name and parameters.
		Positional arguments:
		name(String)
			The symbol name
		params({param_name, param_value} dict)
		"""
        self.name = name
        self.params = params

    def __repr__(self):
        """Returns string representation of the object.
		"""
        return self.name

    def __str__(self):
        """Returns string view of the object.
		"""
        if self.params:
            return self.name + ":" + str(self.params)
        else:
            return self.name
