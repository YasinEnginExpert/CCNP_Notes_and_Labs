import collections
import random

class REDKuyruk:
    def __init__(self, max_size, min_th, max_th, max_p, w_q=0.002):
        """
        max_size: Kuyruğun alabileceği maksimum paket sayısı
        min_th  : Ortalama kuyruk uzunluğu için düşük eşik
        max_th  : Ortalama kuyruk uzunluğu için yüksek eşik
        max_p   : min_th ile max_th arasında ulaşılan en yüksek drop olasılığı
        w_q     : Ortalama hesaplamada EWMA katsayısı (0 < w_q < 1)
        """
        self.kuyruk = collections.deque()
        self.max_size = max_size
        self.min_th = min_th
        self.max_th = max_th
        self.max_p = max_p
        self.w_q = w_q

        # İç durum
        self.avg = 0.0     # EWMA ile izlenen ortalama kuyruk uzunluğu
        self.count = -1    # Eşikler arasında geçen paket sayısı
        self.dropped = 0   # Toplam atılan paket sayısı

    def _ortalama_guncelle(self):
        """ Mevcut kuyruk uzunluğuna göre EWMA ortalamayı günceller """
        qlen = len(self.kuyruk)
        self.avg = (1 - self.w_q) * self.avg + self.w_q * qlen

    def enqueue(self, packet):
        """
        Kuyruğa paket eklemeye çalışır.
        Ortalama min_th ≤ avg < max_th arasındaysa rastgele atma,
        avg ≥ max_th ise kesin atma,
        aksi halde kuyruğa ekleme.
        """
        # Önce ortalamayı güncelle
        self._ortalama_guncelle()

        # 1) Erken rastgele atma bölgesi
        if self.min_th <= self.avg < self.max_th:
            self.count += 1
            # Anlık drop olasılığı
            p = self.max_p * (self.avg - self.min_th) / (self.max_th - self.min_th)
            # Düzeltilmiş Pa
            pa = p / (1 - self.count * p) if (1 - self.count * p) > 0 else 1.0
            if random.random() < pa:
                # Paket atıldı
                self.dropped += 1
                self.count = 0
                return

        # 2) Yüksek eşik aşıldıysa mutlaka at
        elif self.avg >= self.max_th:
            self.dropped += 1
            self.count = 0
            return

        # 3) Kuyruk tamamen doluysa tail-drop
        if len(self.kuyruk) >= self.max_size:
            self.dropped += 1
            return

        # 4) Paket kuyruğa girer
        self.kuyruk.append(packet)

    def dequeue(self):
        """ Kuyruktan (varsa) bir paket çıkartır """
        if self.kuyruk:
            return self.kuyruk.popleft()
        return None

    def istatistik(self):
        """ Anlık ve toplam istatistikleri dict olarak döner """
        return {
            'mevcut_kuyruk': len(self.kuyruk),
            'ortalama_kuyruk': round(self.avg, 2),
            'toplam_atilan': self.dropped
        }


if __name__ == "__main__":
    # Parametreler: max_size=50, min_th=15, max_th=30, max_p=0.1
    red = REDKuyruk(max_size=50, min_th=15, max_th=30, max_p=0.1)

    # 1000 zaman dilimlik basit simülasyon
    for zaman in range(1, 1001):
        # Her zaman biriminde 0–5 arası yeni paket
        for i in range(random.randint(0, 5)):
            red.enqueue(f"P{zaman}-{i}")

        # Her zaman biriminde 0–5 arası paket işleme (çıkış)
        for _ in range(random.randint(0, 5)):
            red.dequeue()

        # Her 100 adımda bir durumu yazdır
        if zaman % 100 == 0:
            stats = red.istatistik()
            print(f"[{zaman}] Kuyruk: {stats['mevcut_kuyruk']}, "
                  f"Ort. Kuyruk: {stats['ortalama_kuyruk']}, "
                  f"Toplam Atılan: {stats['toplam_atilan']}")

