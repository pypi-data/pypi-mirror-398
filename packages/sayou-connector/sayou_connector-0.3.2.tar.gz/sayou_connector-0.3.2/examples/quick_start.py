import logging
import os
import sqlite3

from sayou.connector.pipeline import ConnectorPipeline

try:
    from sayou.visualizer.pipeline import VisualizerPipeline
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


# --- Helper: 더미 DB 생성 ---
def create_dummy_db(path="examples/user_demo.db"):
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (id INTEGER, name TEXT, role TEXT)")
    for i in range(25):
        role = "admin" if i % 5 == 0 else "user"
        cur.execute("INSERT INTO users VALUES (?, ?, ?)", (i, f"User_{i}", role))
    conn.commit()
    conn.close()
    return path


# --- Helper: 더미 파일 생성 ---
def create_dummy_files(root="test_docs"):
    if not os.path.exists(root):
        os.makedirs(root)
    with open(f"{root}/report_q1.txt", "w", encoding="utf-8") as f:
        f.write("2024 Q1 Financial Report...")
    with open(f"{root}/report_q2.txt", "w", encoding="utf-8") as f:
        f.write("2024 Q2 Financial Report...")
    return root


def run_demo():
    print(">>> Initializing Sayou Connector Brain...")
    pipeline = ConnectorPipeline()
    pipeline.initialize()

    if VISUALIZER_AVAILABLE:
        print("[Demo] Visualizer detected! Attaching pipeline...")
        viz = VisualizerPipeline()
        viz.attach_to(pipeline)

    # ---------------------------------------------------------
    # Scenario 1: Local File Scan
    # ---------------------------------------------------------
    print("\n=== [1] Local File Scan Demo ===")
    file_root = create_dummy_files()

    # strategy="file" 사용
    packets = pipeline.run(
        source=file_root,
        # strategy="file",
        extensions=[".txt"],
        recursive=True
    )

    for i, packet in enumerate(packets):
        # SayouPacket 구조 활용
        if packet.success:
            content = packet.data.decode("utf-8")
            print(f"[{i}] File: {packet.task.meta['filename']}")
            print(f"    Content: {content[:20]}...")
        else:
            print(f"[{i}] Error: {packet.error}")

    if VISUALIZER_AVAILABLE:
        viz.report("examples/visualizer_file_demo.html")
        print(f"[Demo] Report generated: visualizer_file_demo.html")

    # ---------------------------------------------------------
    # Scenario 2: SQLite DB Fetching (Pagination)
    # ---------------------------------------------------------
    print("\n=== [2] SQLite DB Demo ===")
    db_path = create_dummy_db()

    # strategy="sqlite" 사용
    # 배치 사이즈 10 -> 총 25개이므로 3번(10, 10, 5) Fetch 발생 예상
    db_packets = pipeline.run(
        source=db_path,
        # strategy="sqlite",
        query="SELECT * FROM users",
        batch_size=10
    )

    for i, packet in enumerate(db_packets):
        if packet.success:
            rows = packet.data  # List[Dict]
            offset = packet.task.meta.get("offset")
            print(f"Batch {i+1} (Offset {offset}): Fetched {len(rows)} rows.")
            if rows:
                print(f"    Sample: {rows[0]}")
        else:
            print(f"Batch {i+1} Failed: {packet.error}")

    if VISUALIZER_AVAILABLE:
        viz.report("examples/visualizer_sqlite_demo.html")
        print(f"[Demo] Report generated: visualizer_sqlite_demo.html")

    # ---------------------------------------------------------
    # Scenario 3: Web Crawling (Real World)
    # ---------------------------------------------------------
    print("\n=== [3] Web Crawling Demo ===")

    target_url = "https://news.daum.net/tech"
    link_pattern = r"https://v\.daum\.net/v/\d+"

    try:
        web_packets = pipeline.run(
            source=target_url,
            # strategy="requests",
            link_pattern=link_pattern,
            selectors={
                "title": ".head_view",
                "content": ".article_view",
            },
            max_depth=1,
        )

        count = 0
        for packet in web_packets:
            if not packet.success:
                continue

            data = packet.data
            display_data = {
                k: v[:30] + "..." for k, v in data.items() if not k.startswith("__")
            }

            if display_data.get("title"):
                print(f"[{count}] URL: {packet.task.uri}")
                print(f"    Data: {display_data}")
                count += 1
                if count >= 3:
                    print("    ... (Stopping demo after 3 articles)")
                    break

    except Exception as e:
        print(f"Skipping Web Demo: {e}")

    if VISUALIZER_AVAILABLE:
        viz.report("examples/visualizer_requests_demo.html")
        print(f"[Demo] Report generated: visualizer_requests_demo.html")

    # Cleanup
    if os.path.exists("test_users.db"):
        os.remove("test_users.db")
    import shutil

    if os.path.exists("test_docs"):
        shutil.rmtree("test_docs")


if __name__ == "__main__":
    run_demo()
