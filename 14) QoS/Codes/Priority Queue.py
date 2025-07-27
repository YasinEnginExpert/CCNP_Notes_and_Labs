from collections import deque
from typing import List, Tuple

# Paket yapısı
class Packet:
    def __init__(self, pkt_id: int, priority: int, arrival_time: float):
        self.id = pkt_id
        self.priority = priority  # 0 = en yüksek, 3 = en düşük
        self.arrival_time = arrival_time

    def __repr__(self):
        return f"Pkt(id={self.id}, prio={self.priority})"

# 4-FIFO Priority Queue simülasyonu
def simulate_priority_queues(
    arrivals: List[Tuple[float, Packet]],
    service_interval: float
):
    """
    arrivals: List of (arrival_time, Packet)
    service_interval: sabit servis aralığı (saniye)
    """
    # Dört FIFO kuyruk
    queues = [deque() for _ in range(4)]
    events = []
    t = 0.0
    idx = 0
    total = len(arrivals)

    # Event-driven döngü
    while idx < total or any(queues):
        next_arrival = arrivals[idx][0] if idx < total else float('inf')
        next_service = t + service_interval if any(queues) else float('inf')
        t = min(next_arrival, next_service)

        # ► Paket geliş (arrival)
        if idx < total and t == next_arrival:
            _, pkt = arrivals[idx]
            queues[pkt.priority].append(pkt)
            total_len = sum(len(q) for q in queues)
            events.append((t, "arrival", pkt.id, pkt.priority, total_len))
            idx += 1
        else:
            # ► Paket servisi (departure) — en yüksek öncelikten başla
            for prio in range(4):
                if queues[prio]:
                    pkt = queues[prio].popleft()
                    total_len = sum(len(q) for q in queues)
                    events.append((t, "departure", pkt.id, prio, total_len))
                    break

    # Sonuçları yazdır
    print(f"{'t(s)':>6} | {'event':>9} | {'pkt':>3} | {'prio':>4} | {'q_total':>7}")
    print("-" * 40)
    for t, evt, pid, prio, qtot in events:
        print(f"{t:6.3f} | {evt:>9} | {pid:3d} | {prio:4d} | {qtot:7d}")

# Örnek Kullanım
if __name__ == "__main__":
    arrivals = [
        (0.00, Packet(1, priority=2, arrival_time=0.00)),
        (0.10, Packet(2, priority=0, arrival_time=0.10)),
        (0.20, Packet(3, priority=3, arrival_time=0.20)),
        (0.30, Packet(4, priority=1, arrival_time=0.30)),
        (0.40, Packet(5, priority=0, arrival_time=0.40)),
    ]
    simulate_priority_queues(arrivals, service_interval=0.05)
