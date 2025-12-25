import unittest

from sayou.refinery.pipeline import RefineryPipeline


class TestRefineryPipeline(unittest.TestCase):

    def setUp(self):
        # 테스트 전 레지스트리가 로드되었는지 확인 (혹은 process 내부에서 로드됨)
        pass

    def test_doc_markdown_normalization_with_dict(self):
        """
        [Normalizer] Document 스키마를 가진 Dict가 Markdown 블록으로 변환되는지 확인 (Duck Typing)
        """
        # Document 객체 대신 Raw Dictionary 사용 (Refinery의 독립성 검증)
        raw_doc = {
            "doc_type": "pdf",
            "pages": [
                {
                    "elements": [
                        {
                            "type": "text",
                            "text": "Contact: test@test.com",
                            "meta": {"semantic_type": "heading"},
                        }
                    ]
                }
            ],
        }

        # [1-Line Magic] 생성+실행
        # strategy="standard_doc" -> DocMarkdownNormalizer 강제 선택
        blocks = RefineryPipeline.process(raw_doc, strategy="standard_doc")

        print(f"\n[Test 1] Generated Blocks: {blocks}")

        self.assertTrue(len(blocks) > 0)
        self.assertEqual(blocks[0].type, "md")
        self.assertIn("Contact:", blocks[0].content)

    def test_deduplication_processor(self):
        """
        [Processor] 중복 제거 프로세서가 명시적으로 호출되어 작동하는지 확인
        """
        raw_doc = {
            "pages": [
                {
                    "elements": [
                        {"type": "text", "text": "Unique Line"},
                        {"type": "text", "text": "Dup Line"},
                        {"type": "text", "text": "Dup Line"},  # 중복
                    ]
                }
            ]
        }

        # [Fix] processors=["Deduplicator"] 명시
        blocks = RefineryPipeline.process(
            raw_doc, strategy="standard_doc", processors=["Deduplicator"]
        )

        # 3개 입력 -> 2개 출력 (중복 제거 성공)
        self.assertEqual(len(blocks), 2)

        content_list = [b.content for b in blocks]
        self.assertEqual(content_list.count("Dup Line"), 1)

    def test_record_processing_chain(self):
        """
        [Chain] JSON 레코드 -> (결측치 채우기) -> (이상치 제거) 체인 테스트
        """
        raw_records = [
            {"id": 1, "category": None, "score": 50},  # Imputation 대상
            {"id": 2, "category": "A", "score": 200},  # Outlier 대상 (max: 100)
            {"id": 3, "category": "B", "score": 90},  # 정상
        ]

        # [Config] 런타임 설정 주입
        config = {
            "imputation_rules": {"category": "General"},  # None -> 'General'
            "outlier_rules": {"score": {"max": 100, "action": "drop"}},  # 100 초과 삭제
        }

        # [Execution]
        blocks = RefineryPipeline.process(
            raw_records,
            strategy="json",  # RecordNormalizer 선택
            processors=["Imputer", "OutlierHandler"],  # 순서대로 실행
            **config,  # 설정 주입
        )

        # 3개 입력 -> 2개 출력 (id:2 제거됨)
        self.assertEqual(len(blocks), 2)

        # Imputer 결과 확인 (None -> General)
        block1_data = blocks[0].content  # RecordNormalizer는 dict를 content로 가짐
        self.assertEqual(block1_data["category"], "General")

        # Outlier 결과 확인 (id:2 없음)
        ids = [b.content["id"] for b in blocks]
        self.assertNotIn(2, ids)
        self.assertIn(3, ids)

    def test_auto_routing_html(self):
        """
        [Auto] strategy 미지정 시 HTML 감지 확인
        """
        raw_html = "<html><body><div>Hello World</div></body></html>"

        # strategy="auto" (기본값)
        blocks = RefineryPipeline.process(raw_html)

        # HtmlTextNormalizer가 선택되어 텍스트를 추출했어야 함
        self.assertTrue(len(blocks) > 0)
        self.assertEqual(blocks[0].type, "text")
        self.assertIn("Hello World", blocks[0].content)


if __name__ == "__main__":
    unittest.main()
