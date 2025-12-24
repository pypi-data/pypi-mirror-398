from cs_framework.core.concept import Concept

class User(Concept):
    def __init__(self, name="User"):
        super().__init__(name)
        self._state = {"is_logged_in": False, "username": None}

    def login(self, payload):
        username = payload.get("username")
        self._state["is_logged_in"] = True
        self._state["username"] = username
        self.emit("LoggedIn", {"username": username})

class AuditLog(Concept):
    def __init__(self, name="AuditLog"):
        super().__init__(name)
        self._state = {"logs": []}

    def log_access(self, payload):
        entry = f"User {payload.get('user')} accessed system."
        self._state["logs"].append(entry)
        self.emit("AccessLogged", {"entry": entry})

class Metrics(Concept):
    def __init__(self, name="Metrics"):
        super().__init__(name)
        self._state = {"login_count": 0}

    def increment_counter(self, payload):
        metric = payload.get("metric")
        if metric == "login_count":
            self._state["login_count"] += 1
        self.emit("CounterIncremented", {"metric": metric, "value": self._state["login_count"]})
