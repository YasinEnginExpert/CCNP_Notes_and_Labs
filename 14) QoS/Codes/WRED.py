import collections
import random

class WREDKuyruk:
    def __init__(self, max_size, sinif_parametreleri, w_q=0.002):
        """
        max_size          : Kuyruğun alabileceği maksimum paket sayısı
        sinif_parametreleri: Her trafik sınıfı için (min_th, max_th, max_p) sözlüğü
        w_q               : Ortalama hesaplamada EWMA katsayısı (0 < w_q < 1)
        """
        self.kuyruk = collections.deque()
        self.max_size = max_size
        self.sinif_parametreleri = sinif_parametreleri
        self.w_q = w_q

        # Durum takibi
        self.avg = 0.0
        self.count = {sinif: -1 for sinif in sinif_parametreleri}
        self.dropped = {sinif: 0 for sinif in sinif_parametreleri}

    def _ortalama_guncelle(self):
        """ Mevcut kuyruk uzunluğuna göre EWMA ortalamayı günceller """
        qlen = len(self.kuyruk)
        self.avg = (1 - self.w_q) * self.avg + self.w_q * qlen

    def enqueue(self, packet, sinif):
        """
        Paket ve sınıf alır.
        Ortalama min_th ≤ avg < max_th arasında ise rastgele atma;
        avg ≥ max_th ise kesin atma;
        kuyruğa ekleme sırasındaki tail-drop kontrolü.
        """
        self._ortalama_guncelle()

        # Bilinmeyen sınıf için varsayılan kullanabilirsiniz
        if sinif not in self.sinif_parametreleri:
            sinif = next(iter(self.sinif_parametreleri))

        min_th, max_th, max_p = self.sinif_parametreleri[sinif]

        # 1) Erken rastgele atma bölgesi
        if min_th <= self.avg < max_th:
            self.count[sinif] += 1
            p = max_p * (self.avg - min_th) / (max_th - min_th)
            pa = p / (1 - self.count[sinif] * p) if (1 - self.count[sinif] * p) > 0 else 1.0
            if random.random() < pa:
                self.dropped[sinif] += 1
                self.count[sinif] = 0
                return  # paket atıldı

        # 2) Yüksek eşik aşıldıysa kesin atma
        elif self.avg >= max_th:
            self.dropped[sinif] += 1
            self.count[sinif] = 0
            return

        # 3) Kuyruk tamamen doluysa tail-drop
        if len(self.kuyruk) >= self.max_size:
            self.dropped[sinif] += 1
            return

        # 4) Paket kuyruğa girer
        self.kuyruk.append((packet, sinif))

    def dequeue(self):
        """ Kuyruktan (varsa) bir paket çıkarır """
        if self.kuyruk:
            return self.kuyruk.popleft()
        return None

    def istatistik(self):
        """ Anlık ve sınıf bazlı atılan paket sayılarını döner """
        return {
            'mevcut_kuyruk': len(self.kuyruk),
            'ortalama_kuyruk': round(self.avg, 2),
            'toplam_atilan_sinif': dict(self.dropped)
        }


if __name__ == "__main__":
    # Örnek trafik sınıfı parametreleri
    siniflar = {
        'voip':  (10, 20, 0.02),  # düşük eşikler, düşük drop olasılığı
        'video': (20, 40, 0.05),
        'data':  (30, 60, 0.1)    # yüksek eşikler, daha agresif drop
    }

    wred = WREDKuyruk(max_size=100, sinif_parametreleri=siniflar)

    # Basit simülasyon
    for t in range(1, 501):
        # 0–10 arası paket gelişi
        for i in range(random.randint(0, 10)):
            sinif = random.choice(list(siniflar.keys()))
            wred.enqueue(f"P{t}-{i}", sinif)

        # 0–10 arası paket işleme
        for _ in range(random.randint(0, 10)):
            wred.dequeue()

        # Her 100 adımda istatistiği yazdır
        if t % 100 == 0:
            print(f"[{t}] {wred.istatistik()}")
