import collections
import random

class TailDropQueue:
    def __init__(self, max_size):
        # deque, hızlı ekleme/çıkarma sağlar
        self.queue = collections.deque()
        self.max_size = max_size
        self.dropped = 0  # atılan paket sayısı

    def enqueue(self, packet):
        """Paketi kuyruğa ekle; kuyruk doluysa at (tail drop)."""
        if len(self.queue) < self.max_size:
            self.queue.append(packet)
        else:
            # Kuyruk dolu: yeni gelen paketi at
            self.dropped += 1
            # dilersen buraya log ekleyebilirsin:
            # print(f"[Tail Drop] Paket atıldı: {packet}")

    def dequeue(self):
        """Kuyruktan bir paket çıkar; boşsa None döner."""
        if self.queue:
            return self.queue.popleft()
        return None

    def stats(self):
        """Anlık kuyruk uzunluğu ve toplam atılan paket sayısı."""
        return {
            'current_queue_length': len(self.queue),
            'total_dropped': self.dropped
        }

# Basit bir simülasyon: rastgele paket gelişleri ve işlemleri
if __name__ == "__main__":
    q = TailDropQueue(max_size=5)
    time_slots = 20

    for t in range(time_slots):
        # Her zaman slotunda 0–3 paket arasında gelir
        arrivals = [f"P{t}-{i}" for i in range(random.randint(0,3))]
        for pkt in arrivals:
            q.enqueue(pkt)

        # Her slotta 0–2 paket işleyelim (çıkış)
        for _ in range(random.randint(0,2)):
            processed = q.dequeue()
            # dilersen işlenen paketleri bastırabilirsin:
            # if processed: print(f"İşlendi: {processed}")

        print(f"Slot {t}: Kuyruk uzunluğu = {q.stats()['current_queue_length']}, "
              f"Toplam atılan = {q.stats()['total_dropped']}")

