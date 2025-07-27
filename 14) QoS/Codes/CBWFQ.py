from collections import deque
from typing import List, Tuple, Optional, Dict

# ——— Paket Yapısı ———
class Packet:
    def __init__(self, id: int, length: int,
                 acl: Optional[int] = None,
                 tcp_port: Optional[int] = None,
                 ingress_if: Optional[str] = None):
        self.id = id
        self.length = length
        self.acl = acl
        self.tcp_port = tcp_port
        self.ingress_if = ingress_if

    def __repr__(self):
        return f"Pkt({self.id},len={self.length})"

# ——— CBWFQ Scheduler (DRR tabanlı) ———
class CBWFQScheduler:
    def __init__(self,
                 class_limits: Dict[int, int],
                 class_quantums: Dict[int, int],
                 classification_rules: List[dict],
                 default_class: int):
        # Her sınıfa ait FIFO kuyruk
        self.queues: Dict[int, deque] = {cls: deque() for cls in class_limits}
        self.limits = class_limits
        self.quantums = class_quantums
        self.rules = classification_rules
        self.default_class = default_class
        # DRR için deficit sayacı ve son hizmet verilen sınıf
        self.deficits: Dict[int, int] = {cls: 0 for cls in class_limits}
        self.last_class = default_class

    def classify(self, pkt: Packet) -> int:
        # ACL / TCP port / interface kurallarıyla sınıflandır
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
        return False, cls  # Tail-drop

    def get_next_packet(self) -> Optional[Tuple[int, Packet]]:
        # DRR turu: her sınıfa quantum ekle, yeterse bir paket çıkar
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

# ——— Simülasyon ve Raporlama ———
def simulate_cbwfq(arrivals: List[Tuple[float, Packet]], service_interval: float):
    # Parametreleri tanımla
    class_limits   = {1: 40,    2: 40,    3: 40}
    class_quantums = {1: 2000,  2: 2000,  3: 2000}
    rules = [
        {"type": "acl",       "value": 10,        "class": 1},
        {"type": "tcp_port",  "value": 23,        "class": 2},
        {"type": "interface", "value": "Serial0", "class": 3},
    ]
    default_class = 3

    sched = CBWFQScheduler(class_limits, class_quantums, rules, default_class)
    events = []
    t = 0.0
    idx = 0
    total = len(arrivals)

    # Event-driven döngü
    while idx < total or any(sched.queues.values()):
        next_arr = arrivals[idx][0] if idx < total else float('inf')
        next_srv = t + service_interval if any(sched.queues.values()) else float('inf')
        t = min(next_arr, next_srv)

        # ► Arrival
        if idx < total and t == next_arr:
            _, pkt = arrivals[idx]
            before = len(sched.queues[sched.classify(pkt)])
            ok, cls = sched.enqueue(pkt)
            after = len(sched.queues[cls])
            events.append((t, "arrival",   pkt.id, cls, before, after, 0 if ok else 1))
            idx += 1
        else:
            # ► Departure
            res = sched.get_next_packet()
            if res:
                cls, pkt = res
                after = len(sched.queues[cls])
                events.append((t, "departure", pkt.id, cls, None, after, 0))

    # Raporu yazdır
    print(f"{'t(s)':>6} | {'evt':>9} | {'pkt':>3} | {'cls':>3} | {'bef':>3}→{'aft':>3} | dropped")
    print("-"*64)
    for t, evt, pid, cls, bef, aft, dr in events:
        bef_str = f"{bef}" if bef is not None else ""
        print(f"{t:6.3f} | {evt:>9} | {pid:3d} | {cls:3d} | {bef_str:3}→{aft:3} | {dr:7d}")

# ——— Örnek Çalıştırma ———
if __name__ == "__main__":
    arrivals = [
        (0.00, Packet(1, length=500,  acl=10)),
        (0.00, Packet(2, length=1500, tcp_port=23)),
        (0.05, Packet(3, length=600,  ingress_if="Serial0")),
        (0.10, Packet(4, length=1200, acl=10)),
        (0.15, Packet(5, length=800,  tcp_port=80)),
    ]
    simulate_cbwfq(arrivals, service_interval=0.01)
