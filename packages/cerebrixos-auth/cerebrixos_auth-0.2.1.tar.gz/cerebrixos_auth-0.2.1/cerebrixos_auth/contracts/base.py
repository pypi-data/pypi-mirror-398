
class AuthContract:
    def __init__(self, required_scopes=None):
        self.required_scopes = required_scopes or []
    def validate(self, payload):
        for s in self.required_scopes:
            if s not in payload.get("scopes", []):
                raise RuntimeError(f"Missing scope: {s}")
