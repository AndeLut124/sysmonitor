import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sysmonitor.core.collector import MetricCollector
from sysmonitor.api.server import APIServer


def main():
    web_dir = Path(__file__).parent / "sysmonitor" / "web"

    collector = MetricCollector(history_size=60)
    server = APIServer(collector=collector, web_dir=web_dir)

    print("=" * 50)
    print("🚀 System Monitor запущен")
    print(f"🌐 http://localhost:8080")
    print("=" * 50)

    server.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()