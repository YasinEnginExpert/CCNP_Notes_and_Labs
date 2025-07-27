import time
from collections import deque
from typing import NamedTuple, Optional

class Packet(NamedTuple):
    id: int
    arrival_time: float

class FIFOQueue:
    def __init__(self, capacity: int, service_rate: float):
        """
        capacity    : Kuyruğun paket cinsinden maksimum uzunluğu
        service_rate: İşleme hızı (paket/saniye)
        """
        self.capacity = capacity
        self.queue = deque()           # paket kuyruğu
        self.service_rate = service_rate
        self.next_departure = 0.0      # bir sonraki çıkış zamanı
        self.dropped = 0               # düşen paket sayısı

    def enqueue(self, pkt: Packet) -> bool:
        """Tail-drop: Kuyruk doluysa paketi düşür."""
        if len(self.queue) < self.capacity:
            self.queue.append(pkt)
            return True
        else:
            self.dropped += 1
            return False

    def dequeue(self, current_time: float) -> Optional[Packet]:
        """
        Eğer hizmet zamanı geldiyse bir paket çıkar.
        Hizmet aralığı = 1 / service_rate saniye.
        """
        if self.queue and current_time >= self.next_departure:
            pkt = self.queue.popleft()
            # bir sonraki çıkış zamanı belirle
            self.next_departure = current_time + 1.0 / self.service_rate
            return pkt
        return None

def simulate_fifo(arrival_interval: float,
                  service_rate: float,
                  capacity: int,
                  total_packets: int):
    """
    arrival_interval: paketler arası zaman (saniye)
    service_rate    : işleme hızı (paket/saniye)
    capacity        : kuyruk kapasitesi (paket sayısı)
    total_packets   : simüle edilecek toplam paket sayısı
    """
    q = FIFOQueue(capacity, service_rate)
    t = 0.0
    stats = []

    for pkt_id in range(1, total_packets + 1):
        # 1) Paket geliş zamanı
        t += arrival_interval
        pkt = Packet(id=pkt_id, arrival_time=t)

        # 2) Enqueue öncesi kuyruk uzunluğu
        before_enq = len(q.queue)
        success = q.enqueue(pkt)
        after_enq = len(q.queue)

        stats.append({
            "time":         round(t, 3),
            "event":        "arrival",
            "pkt_id":       pkt_id,
            "queue_before": before_enq,
            "queue_after":  after_enq,
            "dropped":      q.dropped
        })

        # 3) Aynı anda bir dequeue dene
        departed = q.dequeue(t)
        if departed:
            # Dequeue öncesi/sonrası
            before_deq = after_enq
            after_deq = len(q.queue)
            stats.append({
                "time":         round(t, 3),
                "event":        "departure",
                "pkt_id":       departed.id,
                "queue_before": before_deq,
                "queue_after":  after_deq,
                "dropped":      q.dropped
            })

    # 4) Raporu yazdır
    print(f"{'t(s)':>6} | {'event':>9} | {'pkt':>3} | {'before':>6} → {'after':>5} | dropped")
    print("-" * 60)
    for s in stats:
        print(f"{s['time']:6.3f} | {s['event']:>9} | {s['pkt_id']:3d} |"
              f" {s['queue_before']:6d} → {s['queue_after']:5d} | {s['dropped']:7d}")

if __name__ == "__main__":
    arrival_interval = 0.05   # 50 ms’de 1 paket gelir
    service_rate     = 10     # saniyede 10 paket işlenir
    capacity         = 20      # kuyruk en fazla 3 paket
    total_packets    = 20     # 12 paket simüle et

    simulate_fifo(arrival_interval, service_rate, capacity, total_packets)
