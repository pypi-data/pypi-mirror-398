import os
import shutil
import sqlite3
import tempfile
import unittest

from sayou.core.schemas import SayouPacket

from sayou.connector.pipeline import ConnectorPipeline


class TestConnectorPipeline(unittest.TestCase):

    def setUp(self):
        """테스트 전 환경 구성"""
        self.pipeline = ConnectorPipeline()
        self.pipeline.initialize()

        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """테스트 후 정리"""
        shutil.rmtree(self.test_dir)

    def test_file_scan_strategy(self):
        """[Integration] 로컬 파일 스캔 및 읽기 테스트"""
        # 1. 테스트 파일 생성
        file_path = os.path.join(self.test_dir, "test.txt")
        with open(file_path, "w") as f:
            f.write("Hello Sayou")

        test_cases = ["file", "auto", None]
        for strategy_input in test_cases:
            with self.subTest(strategy=strategy_input):

                # 2. 파이프라인 실행
                iterator = self.pipeline.run(
                    source=self.test_dir, strategy=strategy_input, extensions=[".txt"]
                )
                packets = list(iterator)

                # 3. 검증
                self.assertEqual(len(packets), 1)
                packet = packets[0]

                self.assertIsInstance(packet, SayouPacket)
                self.assertTrue(packet.success)
                self.assertEqual(packet.data, b"Hello Sayou")
                self.assertEqual(packet.task.source_type, "file")

    def test_sqlite_strategy_pagination(self):
        """[Integration] SQL 페이지네이션 로직 테스트"""
        # 1. 임시 DB 생성
        db_path = os.path.join(self.test_dir, "test.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE data (id INT)")
        # 25개 레코드 삽입
        for i in range(25):
            cur.execute("INSERT INTO data VALUES (?)", (i,))
        conn.commit()
        conn.close()

        test_cases = ["sqlite", "auto", None]
        for strategy_input in test_cases:
            with self.subTest(strategy=strategy_input):

                run_kwargs = {
                    "source": db_path,
                    "query": "SELECT * FROM data",
                    "batch_size": 10,
                }
                if strategy_input:
                    run_kwargs["strategy"] = strategy_input

                # 2. 파이프라인 실행 (Batch Size = 10)
                if strategy_input == "auto" or strategy_input is None:
                    run_kwargs["source"] = f"sqlite:///{db_path}"

                iterator = self.pipeline.run(**run_kwargs)
                packets = list(iterator)

                self.assertEqual(len(packets), 3)
                self.assertEqual(len(packets[0].data), 10)
                self.assertEqual(packets[0].task.meta["offset"], 0)
                self.assertEqual(len(packets[2].data), 5)
                self.assertEqual(packets[2].task.meta["offset"], 20)

    def test_error_handling(self):
        """[Unit] 존재하지 않는 파일 요청 시 에러 핸들링"""
        # 존재하지 않는 경로로 직접 run 시도 (Generator가 아니라 Fetcher 에러 유도)
        # 하지만 Pipeline.run은 Generator를 통해야 하므로,
        # FileGenerator가 없는 파일을 가리키도록 설정할 수는 없음 (Generator가 먼저 거름).
        # 따라서 여기서는 '잘못된 전략' 이름을 테스트

        with self.assertRaises(ValueError):
            list(self.pipeline.run(source=".", strategy="unknown_strategy"))


if __name__ == "__main__":
    unittest.main()
