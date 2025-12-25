class BaseClient:

    def set_properties(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def check_properties(self, *args):
        for arg in args:
            if not hasattr(self, arg):
                raise AttributeError(f"Missing required property: {arg}")

    def check_required_properties(self, *args):
        for arg in args:
            if not hasattr(self, arg):
                raise AttributeError(f"Missing required property: {arg}")
            if getattr(self, arg) is None:
                raise AttributeError(f"Required property cannot be None: {arg}")

