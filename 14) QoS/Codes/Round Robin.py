import time
import random
from collections import deque
from typing import NamedTuple, Optional, Tuple

class Packet(NamedTuple):
    id: int
    flow_id: int
    arrival_time: float

class RoundRobinScheduler:
    def __init__(self, num_flows: int, capacity: int, service_rate: float):
        """
        num_flows   : Toplam akış (flow) sayısı
        capacity    : Her akış kuyruğunun maksimum uzunluğu (paket sayısı)
        service_rate: İşleme hızı (paket/saniye)
        """
        self.queues = [deque() for _ in range(num_flows)]
        self.capacity = capacity
        self.service_rate = service_rate
        self.next_departure = 0.0
        self.current_idx = 0
        self.dropped = 0

    def enqueue(self, pkt: Packet) -> bool:
        """Tail-Drop: Kuyruk doluysa paketi düşür."""
        q = self.queues[pkt.flow_id]
        if len(q) < self.capacity:
            q.append(pkt)
            return True
        else:
            self.dropped += 1
            return False

    def dequeue(self, current_time: float) -> Optional[Tuple[Packet,int]]:
        """
        Round Robin: Sıradaki akış kuyruğunu kontrol et.
        Eğer o kuyrukta paket varsa al ve zamanlayıcıyı ilerlet.
        """
        if current_time < self.next_departure:
            return None

        n = len(self.queues)
        for _ in range(n):
            q = self.queues[self.current_idx]
            if q:
                pkt = q.popleft()
                # Bir sonraki çıkış zamanını belirle
                self.next_departure = current_time + 1.0/self.service_rate
                served_flow = self.current_idx
                # Sonraki akışa geç
                self.current_idx = (self.current_idx + 1) % n
                return pkt, served_flow
            # Kuyruk boşsa, diğer akışa geç
            self.current_idx = (self.current_idx + 1) % n

        return None

def simulate_round_robin(num_flows: int,
                         arrival_interval: float,
                         service_rate: float,
                         capacity: int,
                         total_arrivals: int):
    """
    num_flows       : Kaç ayrı flow olacak?
    arrival_interval: Paket geliş hızı (saniye başına; sabit aralık)
    service_rate    : Scheduler servis hızı (paket/saniye)
    capacity        : Her flow kuyruğu kapasitesi (paket sayısı)
    total_arrivals  : Simülasyonda üretilen paket sayısı
    """
    sched = RoundRobinScheduler(num_flows, capacity, service_rate)
    t_next_arr = arrival_interval
    t_next_srv = 0.0
    arrivals = 0
    stats = []

    while arrivals < total_arrivals or any(sched.queues):
        # Hangi olay daha erken?
        if arrivals < total_arrivals and t_next_arr <= t_next_srv:
            t = t_next_arr
            t_next_arr += arrival_interval
            # Flow ID: rastgele seçelim
            flow_id = random.randrange(num_flows)
            pkt = Packet(id=arrivals+1, flow_id=flow_id, arrival_time=t)

            # Kuyruğa ekleme
            before = len(sched.queues[flow_id])
            ok = sched.enqueue(pkt)
            after = len(sched.queues[flow_id])

            stats.append({
                "time": round(t,3),
                "event": "arrival",
                "pkt": pkt.id,
                "flow": flow_id,
                "before": before,
                "after": after,
                "dropped": sched.dropped
            })
            arrivals += 1

        else:
            t = t_next_srv
            if t_next_srv == 0.0:
                # İlk servis hemen mümkün olsun
                t_next_srv = 0.0
            t_next_srv += 1.0/service_rate

            result = sched.dequeue(t)
            if result:
                pkt, flow_id = result
                before = len(sched.queues[flow_id]) + 1
                after = len(sched.queues[flow_id])
                stats.append({
                    "time": round(t,3),
                    "event": "departure",
                    "pkt": pkt.id,
                    "flow": flow_id,
                    "before": before,
                    "after": after,
                    "dropped": sched.dropped
                })

    # Raporu yazdır
    print(f"{'t(s)':>6} | {'olay':>10} | {'pkt':>3} | {'flow':>4} | {'önce':>5} → {'sonra':>5} | dropped")
    print("-"*70)
    for s in stats:
        print(f"{s['time']:6.3f} | {s['event']:>10} | {s['pkt']:3d} | {s['flow']:4d} |"
              f" {s['before']:5d} → {s['after']:5d} | {s['dropped']:7d}")

if __name__ == "__main__":
    # Örnek parametreler
    NUM_FLOWS        = 10      # 3 ayrı trafik sınıfı
    ARRIVAL_INTERVAL = 0.04   # Her 40 ms’de 1 paket (25 pkt/s)
    SERVICE_RATE     = 15     # Saniyede 15 paket işlenir
    QUEUE_CAPACITY   = 4      # Her sınıf kuyruğu en fazla 4 paket
    TOTAL_PACKETS    = 30     # Toplam 30 paket üretilecek

    simulate_round_robin(NUM_FLOWS,
                         ARRIVAL_INTERVAL,
                         SERVICE_RATE,
                         QUEUE_CAPACITY,
                         TOTAL_PACKETS)
