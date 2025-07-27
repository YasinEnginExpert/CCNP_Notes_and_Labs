from collections import deque
from typing import List, Dict, Tuple

# Paket sınıfı
class Packet:
    def __init__(self, id, length, acl=None, tcp_port=None, ingress_if=None):
        self.id = id
        self.length = length
        self.acl = acl
        self.tcp_port = tcp_port
        self.ingress_if = ingress_if

    def __repr__(self):
        return f"Pkt({self.id}, {self.length}B)"

# Kuyruk sınıfı
class CustomQueue:
    def __init__(self, limit: int, byte_count: int):
        self.queue = deque()
        self.limit = limit
        self.byte_count = byte_count

    def enqueue(self, pkt: Packet) -> bool:
        if len(self.queue) < self.limit:
            self.queue.append(pkt)
            return True
        return False

    def dequeue(self) -> List[Packet]:
        sent = []
        total_bytes = 0
        while self.queue and total_bytes + self.queue[0].length <= self.byte_count:
            pkt = self.queue.popleft()
            sent.append(pkt)
            total_bytes += pkt.length
        return sent

# CQ Scheduler
class CustomQueuing:
    def __init__(self):
        self.queues: Dict[int, CustomQueue] = {
            1: CustomQueue(limit=40, byte_count=2000),
            2: CustomQueue(limit=40, byte_count=2000),
            3: CustomQueue(limit=40, byte_count=2000)
        }
        self.class_rules = [
            {"type": "acl", "value": 10, "queue": 1},
            {"type": "tcp", "value": 23, "queue": 2},
            {"type": "interface", "value": "Serial0", "queue": 3}
        ]
        self.default_queue = 3
        self.drop_count = 0

    def classify(self, pkt: Packet) -> int:
        for rule in self.class_rules:
            if rule["type"] == "acl" and pkt.acl == rule["value"]:
                return rule["queue"]
            if rule["type"] == "tcp" and pkt.tcp_port == rule["value"]:
                return rule["queue"]
            if rule["type"] == "interface" and pkt.ingress_if == rule["value"]:
                return rule["queue"]
        return self.default_queue

    def receive(self, pkt: Packet) -> str:
        qid = self.classify(pkt)
        success = self.queues[qid].enqueue(pkt)
        if success:
            return f"Enqueued {pkt} -> Q{qid}"
        else:
            self.drop_count += 1
            return f"DROPPED {pkt} -> Q{qid} FULL"

    def serve(self) -> List[str]:
        logs = []
        for qid in sorted(self.queues.keys()):
            sent = self.queues[qid].dequeue()
            for pkt in sent:
                logs.append(f"Sent {pkt} from Q{qid}")
        return logs

# Test senaryosu
if __name__ == "__main__":
    cq = CustomQueuing()

    # Geliş sırasındaki paketler
    packets = [
        Packet(1, 500, acl=10),                  # Q1 (ACL 10)
        Packet(2, 1000, tcp_port=23),            # Q2 (TCP/23)
        Packet(3, 1500, ingress_if="Serial0"),   # Q3 (Interface)
        Packet(4, 1200),                         # Default Q3
        Packet(5, 900, tcp_port=80),             # Default Q3
        Packet(6, 3000),                         # Büyük → DROP olabilir
    ]

    print("📥 Packet Reception:")
    for pkt in packets:
        print(" -", cq.receive(pkt))

    print("\n🚀 Serving Queues:")
    results = cq.serve()
    for line in results:
        print(" -", line)

    print(f"\n❌ Dropped Packets: {cq.drop_count}")
