from collections import deque
from typing import Deque, Dict, Optional, Tuple, List

# ——— Paket Yapısı ———
class Packet:
    def __init__(self, id: int, length: int, priority_flag: bool = False,
                 acl: Optional[int] = None, tcp_port: Optional[int] = None,
                 ingress_if: Optional[str] = None):
        self.id = id
        self.length = length
        self.priority_flag = priority_flag
        self.acl = acl
        self.tcp_port = tcp_port
        self.ingress_if = ingress_if

    def __repr__(self):
        return f"Pkt({self.id},len={self.length},prio={self.priority_flag})"

# ——— CBWFQ Scheduler (DRR tabanlı) ———
class CBWFQScheduler:
    def __init__(self,
                 class_limits: Dict[int, int],
                 class_quantums: Dict[int, int],
                 classification_rules: List[dict],
                 default_class: int):
        self.queues: Dict[int, Deque[Packet]] = {cls: deque() for cls in class_limits}
        self.limits = class_limits
        self.quantums = class_quantums
        self.rules = classification_rules
        self.default_class = default_class
        self.deficits: Dict[int, int] = {cls: 0 for cls in class_limits}
        self.last_class = default_class

    def classify(self, pkt: Packet) -> int:
        for rule in self.rules:
            if rule["type"] == "acl" and pkt.acl == rule["value"]:
                return rule["class"]
            if rule["type"] == "tcp_port" and pkt.tcp_port == rule["value"]:
                return rule["class"]
            if rule["type"] == "interface" and pkt.ingress_if == rule["value"]:
                return rule["class"]
        return self.default_class

    def enqueue(self, pkt: Packet) -> Tuple[bool,int]:
        cls = self.classify(pkt)
        q = self.queues[cls]
        if len(q) < self.limits[cls]:
            q.append(pkt)
            return True, cls
        return False, cls

    def get_next_packet(self) -> Optional[Tuple[int, Packet]]:
        classes = list(self.queues.keys())
        n = len(classes)
        start = classes.index(self.last_class)
        for i in range(1, n+1):
            cls = classes[(start + i) % n]
            self.deficits[cls] += self.quantums[cls]
            q = self.queues[cls]
            if q and q[0].length <= self.deficits[cls]:
                pkt = q.popleft()
                self.deficits[cls] -= pkt.length
                self.last_class = cls
                return cls, pkt
        return None

# ——— LLQ Scheduler ———
class LLQScheduler:
    """
    Low Latency Queuing: strict priority + CBWFQ for other traffic.
    """
    def __init__(self,
                 priority_limit: int,
                 cbwfq_sched: CBWFQScheduler):
        self.priority_queue: Deque[Packet] = deque()
        self.priority_limit = priority_limit
        self.cbwfq = cbwfq_sched

    def enqueue(self, pkt: Packet) -> bool:
        """
        priority_flag=True ise LLQ kuyruğuna ekler (strict priority).
        Diğer paketler CBWFQScheduler'a yönlendirilir.
        """
        if pkt.priority_flag:
            if len(self.priority_queue) < self.priority_limit:
                self.priority_queue.append(pkt)
                return True
            else:
                return False
        ok, _ = self.cbwfq.enqueue(pkt)
        return ok

    def dequeue(self) -> Optional[Packet]:
        """
        Önce high-priority kuyruğunu boşaltır (strict priority).
        Ardından CBWFQ'den bir paket alır.
        """
        if self.priority_queue:
            return self.priority_queue.popleft()
        res = self.cbwfq.get_next_packet()
        if res:
            _, pkt = res
            return pkt
        return None

# ——— Örnek Kullanım ———
if __name__ == "__main__":
    # CBWFQ parametreleri
    class_limits = {1:40, 2:40, 3:40}
    class_quantums = {1:2000, 2:2000, 3:2000}
    rules = [
        {"type":"acl", "value":10, "class":1},
        {"type":"tcp_port", "value":23, "class":2},
        {"type":"interface", "value":"Serial0", "class":3},
    ]
    default_class = 3

    cbwfq = CBWFQScheduler(class_limits, class_quantums, rules, default_class)
    llq = LLQScheduler(priority_limit=10, cbwfq_sched=cbwfq)

    # Örnek paketler
    packets = [
        Packet(1, length=200, priority_flag=True),
        Packet(2, length=500, acl=10),
        Packet(3, length=1500, tcp_port=23),
        Packet(4, length=300, ingress_if="Serial0"),
        Packet(5, length=250, priority_flag=True),
    ]

    # Kuyruğa al, sonra sırayla çıkar
    print("=== Enqueue Results ===")
    for pkt in packets:
        print(f"Enqueue {pkt} -> {llq.enqueue(pkt)}")

    print("\n=== Dequeue Order ===")
    pkt = llq.dequeue()
    while pkt:
        print("Sent", pkt)
        pkt = llq.dequeue()
