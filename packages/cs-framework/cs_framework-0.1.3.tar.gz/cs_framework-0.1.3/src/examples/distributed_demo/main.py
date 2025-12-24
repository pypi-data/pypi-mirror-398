import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from cs_framework.engine.runner import Runner
from cs_framework.core.concept import Concept
from cs_framework.core.event_bridge import EventBridge
from cs_framework.core.transport import LocalTransport
from cs_framework.core.synchronization import Synchronization
from cs_framework.core.event import EventPattern, ActionInvocation

class Pinger(Concept):
    def ping(self, payload):
        self.emit("pinged", {"msg": "Hello"})

class Ponger(Concept):
    def pong(self, payload):
        print(f"Ponger received: {payload}")
        self.emit("ponged", {})

def main():
    transport = LocalTransport()

    # --- Node A ---
    runner_a = Runner()
    pinger = Pinger("Pinger")
    bridge_a = EventBridge("BridgeA", transport, channel="chat")
    
    runner_a.register(pinger)
    runner_a.register(bridge_a)

    # Sync: Pinger.pinged -> BridgeA.send_remote
    sync_a = Synchronization(
        name="SyncA",
        when=EventPattern(pinger, "pinged"),
        then=[ActionInvocation(bridge_a, "send_remote", lambda e: {"event_name": "pinged", "payload": e.payload})]
    )
    runner_a.register(sync_a)

    # --- Node B ---
    runner_b = Runner()
    ponger = Ponger("Ponger")
    bridge_b = EventBridge("BridgeB", transport, channel="chat")

    runner_b.register(ponger)
    runner_b.register(bridge_b)

    # Sync: BridgeB.remote_received -> Ponger.pong
    sync_b = Synchronization(
        name="SyncB",
        when=EventPattern(bridge_b, "remote_received"),
        then=[ActionInvocation(ponger, "pong", lambda e: e.payload.get("payload", {}))]
    )
    runner_b.register(sync_b)

    # --- Execution ---
    print("Starting Node A and Node B...")
    runner_a.start()
    runner_b.start()

    print("Triggering Ping on Node A...")
    runner_a.dispatch(pinger.id, "ping", {})
    
    # Step Node A to process ping -> send_remote
    print("Stepping Node A...")
    runner_a.process_events()

    # At this point, BridgeA has published to transport.
    # BridgeB's callback has been called, so BridgeB has a pending event 'remote_received'.
    
    # Step Node B to process remote_received -> pong
    print("Stepping Node B...")
    runner_b.process_events()

if __name__ == "__main__":
    main()
