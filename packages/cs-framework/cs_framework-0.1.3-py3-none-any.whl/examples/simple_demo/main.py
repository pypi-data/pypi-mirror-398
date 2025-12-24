import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from cs_framework.core.synchronization import Synchronization
from cs_framework.core.event import EventPattern, ActionInvocation
from cs_framework.engine.runner import Runner
from cs_framework.logging.logger import RDFLogger
from concepts import User, AuditLog, Metrics

def main():
    # Create Concepts
    user = User("User")
    audit = AuditLog("Audit")
    metrics = Metrics("Metrics")

    # Define Sync
    sync = Synchronization(
        name="LogAccessOnLogin",
        when=EventPattern(source_concept=user, event_name="LoggedIn"),
        where=lambda state: state[user.id]["is_logged_in"] is True,
        then=[
            ActionInvocation(
                target_concept=audit,
                action_name="log_access",
                payload_mapper=lambda event: {"user": event.payload["username"]}
            ),
            ActionInvocation(
                target_concept=metrics,
                action_name="increment_counter",
                payload_mapper=lambda event: {"metric": "login_count"}
            )
        ]
    )

    # Setup Runner with Logger
    logger = RDFLogger(log_file="execution.ttl", console_output=True)
    runner = Runner(logger=logger)
    
    runner.register(user)
    runner.register(audit)
    runner.register(metrics)
    runner.register(sync)

    print("Starting C-S Framework Demo...")
    
    # Trigger Action
    runner.dispatch(user.id, "login", {"username": "alice"})
    
    print("Execution finished. Log saved to execution.ttl")

if __name__ == "__main__":
    main()
