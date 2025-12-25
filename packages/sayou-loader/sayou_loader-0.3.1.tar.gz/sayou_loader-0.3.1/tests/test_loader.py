import json
import os
import shutil
import tempfile
import unittest

from sayou.loader.pipeline import LoaderPipeline


class TestLoaderPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = LoaderPipeline()
        self.pipeline.initialize()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_file_writer_json(self):
        """Dict 데이터를 JSON 파일로 저장하는지 확인"""
        data = {"key": "value", "list": [1, 2, 3]}
        dest = os.path.join(self.test_dir, "test.json")

        # 실행
        success = self.pipeline.run(data, dest, strategy="file")
        self.assertTrue(success)

        # 검증
        with open(dest, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)

    def test_jsonl_writer(self):
        """List 데이터를 JSONL(줄바꿈)로 저장하는지 확인"""
        data = [{"id": 1}, {"id": 2}]
        dest = os.path.join(self.test_dir, "test.jsonl")

        # 실행 (전략: jsonl)
        success = self.pipeline.run(data, dest, strategy="jsonl")
        self.assertTrue(success)

        # 검증
        with open(dest, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0]), data[0])

    def test_writer_routing_failure(self):
        """없는 전략을 호출했을 때 에러 처리"""
        with self.assertRaises(Exception):  # WriterError
            self.pipeline.run("data", "dest", strategy="unknown_db")

    def test_empty_data_handling(self):
        """빈 데이터를 보냈을 때 (저장 안 하고 False 반환)"""
        # None
        result = self.pipeline.run(None, "dest", strategy="file")
        self.assertFalse(result)

        # Empty List
        result = self.pipeline.run([], "dest", strategy="file")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
