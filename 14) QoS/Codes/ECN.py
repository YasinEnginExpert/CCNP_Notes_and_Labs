import collections
import random

class ECNREDKuyruk:
    def __init__(self, max_size, min_th, max_th, max_p, w_q=0.002):
        """
        max_size: Kuyruğun alabileceği maksimum paket sayısı
        min_th  : Ortalama kuyruk uzunluğu için düşük eşik
        max_th  : Ortalama için yüksek eşik
        max_p   : Eşikler arasında ulaşılacak en yüksek işaretleme/düşürme olasılığı
        w_q     : EWMA katsayısı (0 < w_q < 1)
        """
        self.kuyruk = collections.deque()
        self.max_size = max_size
        self.min_th = min_th
        self.max_th = max_th
        self.max_p = max_p
        self.w_q = w_q

        # Durum değişkenleri
        self.avg = 0.0
        self.count = -1
        self.marked = 0  # ECN işaretlenen paket sayısı
        self.dropped = 0 # Tail-drop edilen paket sayısı

    def _ortalama_guncelle(self):
        """ Mevcut kuyruk uzunluğuna göre EWMA ortalamayı günceller """
        qlen = len(self.kuyruk)
        self.avg = (1 - self.w_q)*self.avg + self.w_q*qlen

    def enqueue(self, packet):
        """
        packet: {'id':..., 'ecn_capable': True/False, 'ecn': None/'CE'}
        """
        # 1) Ortalama güncelle
        self._ortalama_guncelle()

        # 2) Erken işaretleme/atım bölgesi
        if self.min_th <= self.avg < self.max_th:
            self.count += 1
            p = self.max_p * (self.avg - self.min_th) / (self.max_th - self.min_th)
            pa = p / (1 - self.count * p) if (1 - self.count * p) > 0 else 1.0
            if random.random() < pa:
                # ECN-capable ise işaretle, değilse drop et
                if packet.get('ecn_capable', False):
                    packet['ecn'] = 'CE'
                    self.marked += 1
                    # Kuyruğa yine ekliyoruz; işaretlenmiş paket çıkışı da işlenecek
                    self.kuyruk.append(packet)
                else:
                    self.dropped += 1
                # count sıfırlansın
                self.count = 0
                return

        # 3) Yüksek eşik aşıldıysa tail-drop
        if self.avg >= self.max_th or len(self.kuyruk) >= self.max_size:
            self.dropped += 1
            return

        # 4) Normal ekleme
        self.kuyruk.append(packet)

    def dequeue(self):
        """ Kuyruktan (varsa) bir paket çıkarır """
        if self.kuyruk:
            return self.kuyruk.popleft()
        return None

    def istatistik(self):
        """ Anlık ve toplam işaretleme/atılma sayısı döner """
        return {
            'mevcut_kuyruk': len(self.kuyruk),
            'ortalama_kuyruk': round(self.avg, 2),
            'ecn_isaretlenen': self.marked,
            'tail_drop_edilen': self.dropped
        }

# Basit simülasyon örneği
if __name__ == "__main__":
    # RED+ECN parametreleri
    ecnred = ECNREDKuyruk(max_size=50, min_th=15, max_th=30, max_p=0.1)

    for t in range(1, 501):
        # 0–5 arası yeni paket; yarısı ECN-capable olsun
        for i in range(random.randint(0,5)):
            pkt = {
                'id': f"P{t}-{i}",
                'ecn_capable': (random.random() < 0.5),
                'ecn': None
            }
            ecnred.enqueue(pkt)

        # 0–5 arası paket işleme
        for _ in range(random.randint(0,5)):
            p = ecnred.dequeue()
            # İşlenen paketin ECN bilgisi burada loglanabilir:
            # if p and p['ecn']=='CE': print(f"{p['id']} işaretlendi.")

        if t % 100 == 0:
            print(f"[{t}] {ecnred.istatistik()}")
