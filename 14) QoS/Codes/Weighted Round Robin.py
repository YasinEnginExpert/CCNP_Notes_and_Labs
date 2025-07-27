from collections import deque

def weighted_round_robin(flows, weights):
    """
    Basit Weighted Round Robin planlayıcı.
    flows: {flow_id: deque([...])}
    weights: [w0, w1, w2] — her flow için servis hakkı
    """
    schedule = []

    # Kuyruklar boşalana kadar döner
    while any(flows[fid] for fid in flows):
        for fid, weight in enumerate(weights):
            for _ in range(weight):
                if flows[fid]:
                    pkt = flows[fid].popleft()
                    schedule.append((fid, pkt))
    return schedule

def main():
    # 🎯 Flow’lara ait paketler
    flows = {
        0: deque(["f0-p1", "f0-p2", "f0-p3"]),
        1: deque(["f1-p1", "f1-p2", "f1-p3", "f1-p4"]),
        2: deque(["f2-p1", "f2-p2", "f2-p3", "f2-p4", "f2-p5"])
    }

    # ⚖️ Flow ağırlıkları: [1, 2, 3]
    weights = [1, 2, 3]

    # Planlamayı yap
    schedule = weighted_round_robin(flows, weights)

    # 📋 Sonuçları yazdır
    print("\n=== WRR Planlama Sırası ===")
    for i, (fid, pkt) in enumerate(schedule, 1):
        print(f"{i:02d}. Flow {fid} → Packet {pkt}")

if __name__ == "__main__":
    main()
