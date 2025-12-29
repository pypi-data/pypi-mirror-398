from datetime import datetime
import unittest
from langchain_anthropic import ChatAnthropic
import pytz
import requests
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from trustcall import create_extractor
from botrun_flow_lang.langgraph_agents.agents.util.local_files import (
    upload_and_get_tmp_public_url,
)
from pathlib import Path


class ValidationResult(BaseModel):
    """Pydantic model for the validation result"""

    pass_: bool = Field(
        description="Whether the validation passes (true) or fails (false), If all conditions are met, return true, otherwise return false"
    )
    reason: str = Field(
        description="Detailed explanation of why validation passed or failed"
    )


class TestAPIFunctionality(unittest.TestCase):
    """Test class for REST API functionality tests"""

    def setUp(self):
        """Setup method that runs before each test"""
        # Default base URL, can be overridden by setting the class attribute
        if not hasattr(self, "base_url"):
            self.base_url = "http://localhost:8080"
            # self.base_url = (
            #     "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app"
            # )

        # Common headers
        self.headers = {"Content-Type": "application/json"}

        # Initialize LLM and extractor
        # self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.llm = ChatAnthropic(model="claude-3-5-haiku-latest", temperature=0)
        self.validator = create_extractor(
            self.llm, tools=[ValidationResult], tool_choice="ValidationResult"
        )
        local_tz = pytz.timezone("Asia/Taipei")
        self.local_time = datetime.now(local_tz)

    def api_post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to make POST requests to the API

        Args:
            endpoint: The API endpoint path (without base URL)
            data: The request payload as a dictionary

        Returns:
            The JSON response as a dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, headers=self.headers, json=data)

        # Raise an exception if the response was unsuccessful
        response.raise_for_status()

        return response.json()

    def validate_with_llm(
        self, response_content: str, validation_criteria: str
    ) -> Dict[str, Any]:
        """Use trustcall with GPT-4o-mini to validate the response content

        Args:
            response_content: The content to validate
            validation_criteria: Validation criteria description

        Returns:
            Dictionary with 'pass' (boolean) and 'reason' (string)
        """
        prompt = f"""
        你是一個專業的API回應驗證員。請評估以下API回應是否符合所有指定條件。
        
        === 驗證條件 ===
        {validation_criteria}
        
        === API回應內容 ===
        {response_content}
        
        請評估API回應是否符合所有驗證條件。詳細說明評估原因，若不符合條件，請明確指出哪些條件未達成。
        """

        try:
            # Use trustcall extractor to validate
            result = self.validator.invoke(
                {"messages": [{"role": "user", "content": prompt}]}
            )

            # Extract the validated response
            validation_result = result["responses"][0]

            # Convert to the expected format
            return {"pass": validation_result.pass_, "reason": validation_result.reason}

        except Exception as e:
            return {"pass": False, "reason": f"Error during validation: {str(e)}"}

    def test_langgraph_news_joke_emoji(self):
        """測試是否會抓到今天的新聞，檢查重點：
        1. 是否會抓到今天的新聞
        2. 是否會列出來源網址
        3. 是否會講個笑話，並加上 emoji
        """
        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "幫我搜尋今天的新聞是什麼？一一列出來，並給我參考來源網址。",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            validation_criteria = f"""
            1. 是否包含今天 {self.local_time.strftime("%Y-%m-%d")} 日期的新聞資訊，沒有列出日期測試算失敗
            2. 是否列出每則新聞的來源網址
            3. 是否在回答結尾包含一個笑話
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

        except Exception as e:
            print(f"test_langgraph_news_joke_emoji: Test failed with error: {str(e)}")
            raise

    def test_langgraph_multinode_news_dall_e(self):
        """測試多節點處理流程，檢查重點：
        1. 是否會抓到今天的新聞
        2. 是否有評分新聞 (1-10分)
        3. 是否有產出一張圖片，並帶有 URL
        """
        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "好。 我們現在就是跟那個Bert人講多個節點,那它裡面它就會用多個節點的方式直接去工作,比如說第一個節點就是請Bert人上網去搜尋今天的新聞。 然後第二個節點呢,請你把這個新聞,打分,一分到十分,哪個新聞最可愛。 然後第三個節點呢,請你根據分數最高的那一個新聞,你幫我呼叫達利畫一張跟那個新聞相關的圖片,那我們就用這個來示範一下,來。",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria based on the test requirements
            validation_criteria = f"""
            1. 是否會抓到今天 {self.local_time.strftime("%Y-%m-%d")} 日期的新聞
            2. 是否有評分新聞 (1-10分)
            3. 是否有產出一張圖片，並帶有 URL
            4. 是否在回答結尾包含一個笑話
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

        except Exception as e:
            print(
                f"test_langgraph_multinode_news_dall_e: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_future_date_news(self):
        """測試未來日期的新聞搜尋，檢查重點：
        1. 是否是指定時間的 2025/2/10 的新聞，回覆內容要有這個時間
        2. 不能回應說這個時間在未來，所以無法回答，可以說 "截至2025年2月10日，相關的新聞如下："。
        """
        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "請你幫我找2025/2/10全球災難新聞",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria based on the test requirements
            validation_criteria = """
            1. 是否包含指定時間 2025/2/10 的新聞資訊，回覆內容中必須有出現「2025/2/10」或類似的日期格式
            2. 不能包含任何提到該日期在未來、無法預測未來、尚未發生等類似的說明
            3. 是否在回答結尾包含一個笑話
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

        except Exception as e:
            print(f"test_langgraph_future_date_news: Test failed with error: {str(e)}")
            raise

    def test_langgraph_pdf_analysis(self):
        """測試PDF分析功能，檢查重點：
        1. 是否能正確解析PDF檔案中的「表 4.3-1 環境敏感地區調查表-第一級環境敏感地區」
        2. 是否能列出所有項目的「查詢結果及限制內容」（是或否）
        3. 回傳結果是否符合預期的敏感區域結果
        """
        # 使用pathlib構建正確的檔案路徑

        current_dir = Path(__file__).parent
        pdf_path = (
            current_dir
            / "test_files"
            / "1120701A海廣離岸風力發電計畫環境影響說明書-C04.PDF"
        )

        # 確保檔案存在
        self.assertTrue(pdf_path.exists(), f"Test file not found at {pdf_path}")
        # 將絕對路徑轉為字串
        pdf_path_str = str(pdf_path)
        # 上傳檔案到 tmp_public_url
        tmp_public_url = upload_and_get_tmp_public_url(
            pdf_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )

        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": f"幫我分析 {tmp_public_url} 這個檔案，請你幫我找出在報告書中的「表 4.3-1 環境敏感地區調查表-第一級環境敏感地區」表格中的所有項目的「查詢結果及限制內容」幫我列出是或否？請全部列出來，不要遺漏",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria based on existing test_pdf_analyzer.py
            validation_criteria = """
            請確認回應是否包含以下項目的查詢結果（是或否），所有項目都必須存在：
            1. 活動斷層兩側一定範圍: 否
            2. 特定水土保持區: 否
            3. 河川區域: 否
            4. 洪氾區一級管制區及洪水平原一級管制區: 否
            5. 區域排水設施範圍: 是
            6. 國家公園區內之特別景觀區、生態保護區: 否
            7. 自然保留區: 否
            8. 野生動物保護區: 否
            9. 野生動物重要棲息環境: 是
            10. 自然保護區: 否
            11. 一級海岸保護區: 是
            12. 國際級重要濕地、國家級重要濕地之核心保育區及生態復育區: 否
            13. 古蹟保存區: 否
            14. 考古遺址: 否
            15. 重要聚落建築群: 否
            
            所有項目都必須正確列出，且其中：
            - 區域排水設施範圍應為「是」
            - 野生動物重要棲息環境應為「是」
            - 一級海岸保護區應為「是」
            
            如果有遺漏任何一項或者結果不符合預期，則視為測試失敗。
            如果結果有超過，沒有關係。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

        except Exception as e:
            print(f"test_langgraph_pdf_analysis: Test failed with error: {str(e)}")
            raise

    def test_langgraph_pdf_attendance_analysis(self):
        """測試PDF分析功能，檢查重點：
        1. 是否能正確解析PDF檔案中的「目錄4」的出席名單
        2. 回答中是否有包含「德懷師父」、「德宸師父」、「德倫師父」
        """

        current_dir = Path(__file__).parent
        pdf_path = (
            current_dir
            / "test_files"
            / "(溫馨成果 行政請示匯總)20250210向 上人報告簡報 (1).pdf"
        )

        # 確保檔案存在
        self.assertTrue(pdf_path.exists(), f"Test file not found at {pdf_path}")

        # 將絕對路徑轉為字串
        pdf_path_str = str(pdf_path)

        # 上傳檔案到 tmp_public_url
        tmp_public_url = upload_and_get_tmp_public_url(
            pdf_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )

        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": f"幫我分析 {tmp_public_url} 這個檔案，你幫我看「目錄4」，告訴我有哪些師父和講者、執辦、主管有出席",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria
            validation_criteria = """
            請確認回應是否包含以下師父的名字，所有名字都必須存在：
            1. 德懷師父
            2. 德宸師父
            3. 德倫師父
            
            此外，回應應該提供「目錄4」中出席的師父、講者、執辦和主管的完整列表。
            如果缺少上述任一師父的名字，則視為測試失敗。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

        except Exception as e:
            print(
                f"test_langgraph_pdf_attendance_analysis: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_image_analysis_generation(self):
        """測試圖片分析與生成功能，檢查重點：
        1. 是否能正確分析圖片並識別出「佛教」相關元素
        2. 是否產生一張相同意境的圖片並提供URL
        """

        current_dir = Path(__file__).parent
        image_path = current_dir / "test_files" / "d5712343.jpg"

        # 確保檔案存在
        self.assertTrue(image_path.exists(), f"Test file not found at {image_path}")

        # 將絕對路徑轉為字串
        image_path_str = str(image_path)

        # 上傳檔案到 tmp_public_url
        tmp_public_url = upload_and_get_tmp_public_url(
            image_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )

        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": f"{tmp_public_url} 幫我分析這張圖裡的元素，然後幫我創作一張相同意境的圖片",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria
            validation_criteria = """
            請確認回應是否符合以下條件：
            1. 分析結果中有提到「佛教」相關的元素（如佛像、和尚、寺廟、佛教符號等）
            2. 回應中包含一個圖片的URL（通常是以http或https開頭的網址，並包含在圖片的描述旁）
            3. 是否在回答結尾包含一個笑話
            
            所有條件都必須滿足，尤其是必須確認分析中有提到佛教元素，並且有生成一張新的圖片和提供其URL。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

        except Exception as e:
            print(
                f"test_langgraph_image_analysis_generation: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_spot_difference(self):
        """測試圖片比對功能，檢查重點：
        1. 是否能正確分析兩張找不同遊戲的圖片
        2. 是否能找出並明確描述出兩張圖片的不同之處
        """

        current_dir = Path(__file__).parent
        image1_path = current_dir / "test_files" / "spot_difference_1.png"
        image2_path = current_dir / "test_files" / "spot_difference_2.png"

        # 確保檔案存在
        self.assertTrue(image1_path.exists(), f"Test file not found at {image1_path}")
        self.assertTrue(image2_path.exists(), f"Test file not found at {image2_path}")

        # 將絕對路徑轉為字串
        image1_path_str = str(image1_path)
        image2_path_str = str(image2_path)

        # 上傳檔案到 tmp_public_url
        tmp_public_url_1 = upload_and_get_tmp_public_url(
            image1_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        tmp_public_url_2 = upload_and_get_tmp_public_url(
            image2_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )

        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": f"這是一個找不同的遊戲，幫我分析兩張圖有幾處不同？ {tmp_public_url_1}，{tmp_public_url_2}",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria
            validation_criteria = """
            請確認回應是否符合以下條件：
            1. 回應中有具體指出並描述兩張圖片之間的不同之處
            2. 必須明確描述出不同的位置、形狀、顏色或其他特徵差異
            3. 不能只回應「無法處理」、「無法比較」或類似的無能力陳述
            4. 是否在回答結尾包含一個笑話
            
            關鍵是要確保系統能夠實際找出差異並清楚描述，而不是迴避任務或宣稱無法完成。
            如果回應只是說明系統不支援圖片比較功能，則測試視為失敗。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

        except Exception as e:
            print(f"test_langgraph_spot_difference: Test failed with error: {str(e)}")
            raise

    def test_langgraph_platform_images_analysis(self):
        """測試分析多張車站月台圖片功能，檢查重點：
        1. 是否能正確分析多張車站月台圖片
        2. 是否能根據圖片提供清晰的月台指引和理由
        3. 回覆中是否包含「月台」相關的特定字眼
        """

        current_dir = Path(__file__).parent
        image1_path = current_dir / "test_files" / "ImportedPhoto.760363950.029251.jpeg"
        image2_path = current_dir / "test_files" / "ImportedPhoto.760363950.031127.jpeg"
        image3_path = current_dir / "test_files" / "ImportedPhoto.760363950.030446.jpeg"

        # 確保檔案存在
        self.assertTrue(image1_path.exists(), f"Test file not found at {image1_path}")
        self.assertTrue(image2_path.exists(), f"Test file not found at {image2_path}")
        self.assertTrue(image3_path.exists(), f"Test file not found at {image3_path}")

        # 將絕對路徑轉為字串
        image1_path_str = str(image1_path)
        image2_path_str = str(image2_path)
        image3_path_str = str(image3_path)

        # 上傳檔案到 tmp_public_url
        tmp_public_url_1 = upload_and_get_tmp_public_url(
            image1_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        tmp_public_url_2 = upload_and_get_tmp_public_url(
            image2_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )
        tmp_public_url_3 = upload_and_get_tmp_public_url(
            image3_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )

        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "system",
                    "content": "妳是臺灣人，回答要用臺灣繁體中文正式用語，需要的時候也可以用英文，可以親切、俏皮、幽默，但不能隨便輕浮。在使用者合理的要求下請盡量配合他的需求，不要隨便拒絕。",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"以下為使用者上傳的圖片，請參考這些圖片回答使用者的問題：\n\n{tmp_public_url_1}\n{tmp_public_url_2}\n{tmp_public_url_3}\n\n使用者問題：\n\n我要去哪個月台，為什麼？",
                        }
                    ],
                },
            ],
            "config": {
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria
            validation_criteria = """
            請確認回應是否符合以下條件：
            1. 回應中有明確提及「月台」、「站台」或「platform」等相關詞彙
            2. 回應中有具體指出一個明確的月台方向或號碼，尤其應該包含以下月台號碼其中之一：
               - 5 A-C
               - 5 D-F
               - 5-A-C
               - 5-A/C
               - 5-D-F
               - 5-D/F
            3. 回應中提供了選擇該月台的理由或依據（例如目的地、車次、方向等）
            4. 回應使用了臺灣繁體中文正式用語
            
            回應必須能清楚指引使用者應該前往哪個月台，以及為什麼要去那個月台。如果回應中缺少明確的月台指引或理由，則視為測試失敗。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

            # Additional check for specific platform numbers
            possible_platforms = ["5 A-C", "5 D-F", "5-A-C", "5-A/C", "5-D-F", "5-D/F"]
            platform_found = False

            for platform in possible_platforms:
                if platform in response_content:
                    platform_found = True
                    print(f"Found expected platform: {platform}")
                    break

            self.assertTrue(
                platform_found,
                f"Response does not contain any of the expected platform numbers: {possible_platforms}, but get {response_content}",
            )

        except Exception as e:
            print(
                f"test_langgraph_platform_images_analysis: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_population_analysis(self):
        """測試PDF人口分析與圖表生成功能，檢查重點：
        1. 是否能正確分析PDF中各縣市的人口數據
        2. 是否生成相關的比較圖表並提供Google Storage URL
        """

        current_dir = Path(__file__).parent
        pdf_path = (
            current_dir
            / "test_files"
            / "11206_10808人口數(3段年齡組+比率)天下雜誌1.pdf"
        )

        # 確保檔案存在
        self.assertTrue(pdf_path.exists(), f"Test file not found at {pdf_path}")

        # 將絕對路徑轉為字串
        pdf_path_str = str(pdf_path)
        tmp_public_url = upload_and_get_tmp_public_url(
            pdf_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )

        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": f"{tmp_public_url} 幫我分析這個檔案，做深度的人口狀況分析，然後產出一個相關的比較圖表給我看。",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria
            validation_criteria = """
            請確認回應是否符合以下條件：
            1. 回應中有包含各縣市的人口數據分析，至少提及三個以上的縣市名稱及其人口狀況
            2. 回應中包含至少一個以 "https://storage.googleapis.com" 開頭的URL，這個URL應該指向一個生成的圖表
            3. 分析內容應該涵蓋人口結構的深度分析，例如年齡分布、老化指數、人口增減等
            4. 是否在回答結尾包含一個笑話
            
            所有條件都必須滿足，特別是必須有各縣市的人口分析並含有Google Storage的圖表URL。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

            # Additional check for Google Storage URL
            self.assertTrue(
                "https://storage.googleapis.com" in response_content,
                "Response does not contain a Google Storage URL",
            )

        except Exception as e:
            print(
                f"test_langgraph_population_analysis: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_wind_power_flowchart(self):
        """測試風力發電計畫PDF分析與流程圖生成功能，檢查重點：
        1. 是否能正確分析PDF中的風力發電計畫內容
        2. 是否生成相關的流程圖並提供Google Storage URL
        """

        current_dir = Path(__file__).parent
        pdf_path = (
            current_dir
            / "test_files"
            / "1120701A海廣離岸風力發電計畫環境影響說明書-C04.PDF"
        )

        # 確保檔案存在
        self.assertTrue(pdf_path.exists(), f"Test file not found at {pdf_path}")

        # 將絕對路徑轉為字串
        pdf_path_str = str(pdf_path)
        tmp_public_url = upload_and_get_tmp_public_url(
            pdf_path_str,
            "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "sebastian.hsu@gmail.com",
        )

        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": f"{tmp_public_url} 幫我分析這個檔案，針對風力發電計畫，生成一張流程圖給我。",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria
            validation_criteria = """
            請確認回應是否符合以下條件：
            1. 回應中有包含風力發電計畫的分析內容，例如計畫目標、執行步驟、環境影響等
            2. 回應中包含至少一個以 "https://storage.googleapis.com" 開頭的URL，這個URL應該指向一個生成的流程圖
            3. 分析內容應該專注於風力發電計畫的程序或流程，而非僅是一般性描述
            4. 是否在回答結尾包含一個笑話
            
            所有條件都必須滿足，特別是必須有風力發電計畫的分析並含有Google Storage的流程圖URL。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

            # Additional check for Google Storage URL
            self.assertTrue(
                "https://storage.googleapis.com" in response_content,
                "Response does not contain a Google Storage URL",
            )

        except Exception as e:
            print(
                f"test_langgraph_wind_power_flowchart: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_oauth_flow_diagram(self):
        """測試OAuth流程圖生成功能，檢查重點：
        1. 是否能正確生成OAuth認證流程圖
        2. 是否提供Google Storage URL連結到生成的圖表
        """
        # Test payload based on the curl command
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "我想做一個 oauth 的流程，幫我生出一個流程表",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria
            validation_criteria = """
            請確認回應是否符合以下條件：
            1. 回應中有詳細描述OAuth認證流程的步驟，必須包含關鍵步驟如授權請求、令牌交換等
            2. 回應中包含至少一個以 "https://storage.googleapis.com" 開頭的URL，這個URL應該指向一個生成的流程圖
            3. 回應應該提供清晰的OAuth流程解釋，包括不同參與者（如用戶、客戶端應用、授權伺服器等）之間的互動
            4. 是否在回答結尾包含一個笑話
            
            所有條件都必須滿足，特別是必須有OAuth流程的詳細描述，並含有Google Storage的流程圖URL。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

            # Additional check for Google Storage URL
            self.assertTrue(
                "https://storage.googleapis.com" in response_content,
                "Response does not contain a Google Storage URL",
            )

        except Exception as e:
            print(
                f"test_langgraph_oauth_flow_diagram: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_moda_news_dall_e(self):
        """測試多節點處理數位發展部新聞流程，檢查重點：
        1. 是否會抓到今天日期，或截至今天日期的數位發展部相關新聞
        2. 是否有評分新聞 (1-10分)，並標示出「最可愛」的新聞
        3. 是否有產出一張圖片，並帶有 URL
        """
        # Test payload based on the curl command
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "好，那個你幫我那個啟動幾個多個節點,然後第一個節點請你幫我上網搜尋。 上網搜尋今天那個我們那個數位發展部的夥伴,或者最近一個禮拜數位發展部的那個夥伴有沒有什麼新聞好。 然後第二個節點,你幫我做一件事,你幫我做幫我把這些新聞評分數,評分一到十分。 那哪個新聞你覺得最可愛。 然後第三個節點,你幫我做一件事。 就是你把這個分數最可愛的那一個新聞挑出來以後,你幫我生成一個prompt,這個prompt是我要把你丟進打理畫圖用的prompt。那第四個節點你才真的呼叫打理把那個圖給畫出來,你幫我依序執行這個這個工作流程好不好,謝謝。",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria based on the test requirements
            validation_criteria = f"""
            請確認回應是否符合以下條件：
            1. 回應中有包含今天({self.local_time.strftime("%Y-%m-%d")})或最近一週內的數位發展部相關新聞資訊
            2. 回應中有對新聞進行1-10分的評分，並明確指出哪則新聞「最可愛」或分數最高
            3. 回應中包含至少一個圖片URL（通常是以http或https開頭的網址）
            4. 是否在回答結尾包含一個笑話
            
            所有條件都必須滿足，特別是必須有數位發展部相關新聞、評分結果以及最終生成的圖片URL。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

            # Additional check for an image URL
            self.assertTrue(
                "http" in response_content.lower()
                and (
                    "jpg" in response_content.lower()
                    or "png" in response_content.lower()
                    or "https://storage.googleapis.com" in response_content
                ),
                "Response does not contain a valid image URL",
            )

        except Exception as e:
            print(f"test_langgraph_moda_news_dall_e: Test failed with error: {str(e)}")
            raise

    def test_langgraph_global_disaster_news(self):
        """測試深度研究災難新聞流程，檢查重點：
        1. 是否有收集全球災難新聞
        2. 是否以表格方式呈現災難資料
        3. 是否提供新聞來源
        """
        # Test payload based on the curl command
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "請幫我進行深度研究，深度研究時請遵循以下三個步驟\n第一步驟：\n身為一個專業的全球新聞蒐集分析人員，請透過網路幫我收集Google News、路透社、美聯社、CNN、BBC、法新社、歐洲傳媒應急中心、公共透視網路、台灣聯合報及東森新聞，不使用不可信賴媒體及模擬資料，盡力確保可收集到全球的災難新聞。產生的研究報告文件名稱請以「xxxx年xx月xx日 全球災難新聞收集與追蹤」這樣的格式生成。收集時間請以UTC+8時區為基準，收集從2025年2月24日15:00到2025年2月25日15:00 的24 小時內，全球在時區內發生的災難事件及發生時間，包括大型自然災害或人為災難的人數統計，包括「傷亡」、「失蹤」、「受影響」、「流離失所」、「避難」等。自然災難類型包括但不限於地震、風災、火山爆發、寒流、大雪、冰雹、雪崩、土石流、野火、山火之類的極端氣候災難，人為災害包括 空難、戰爭、大型交通事故、海難、建物倒塌、疫情、中毒等並整理成表格，以繁體中文輸出，表格名請加上當天的年月日，格式為「xxxx年xx月xx日」並按照亞洲、歐洲、美洲、大洋洲、非洲等五大洲排列，後面要加上國家、省市別做完整地點呈現\n第二個表格請搜集以2025年2月24日為基準過去 96 小時的全球新聞中的災難報導。請確認事件發生時間在區間內，若是非區間內發生，請在說明欄清楚說明原因。並再三確認報導更新時間是否在區間內，也就是從前三天到當天，四天中發生的災難後續報導。\n第三個表格請就第一和第二個表格中收集到的災難事件中，逐條就每個災難進行250字的災難摘要及資料來源連結。並收集有關房屋（棟）的損壞統計，包括「受損」、「毁損」等。請務必以表格呈現，不要逐條展示。\n第二步驟：\n我要復盤上述資料都來自於可信賴的國際或台灣新聞媒體即時新聞報導，並且要找到三個不同的資訊來源，交差比對確認災難真實發生的時間點。第一個表格要有詳細的災難發生地點，每條災難收集的時間條件是指災難發生時間而非新聞發布時間在時間區間內，若災難發生時間不在時間區間內，請移到第二個表格。第二個表格是在過去96個小時不重複第一個表格的時間區間中新聞媒體對於災難的後續報導，第三個部份也請用表格呈現，而不是條列式。請檢視每個表格的災難資料，並合併相同的災難事件，確保每條事件只有一筆， 我很怕你使用到不可信的網路媒體資料，如：維基百科或是災難預言、天氣預警、模擬訊息或是你預訓練的資料Youtube及專題報導等。 若無傷亡或防屋毀損實際統計數據，請勿收集。\n第三步驟：\n請將下列附加檔案的表格一和表格二匯的每條災難事件透過網路可信賴媒體交叉比對時間和真實性後，匯整到原有的表格一和二中並合併相同的災難資訊，重新整理完整的表格三。再重新檢查每筆資料都符合各表格的時間區間及規範，重新盤點100遍，幫我整理出最完整的表格一到三。每筆資料請幫我再三搜尋可信賴媒體進行交差比對，務求每條事件都在真實世界中發生，地點明確，發生時間可驗證，若無傷亡資料就不收集。要確認表格一加上表格二的條目，能完整在表格三中呈現，不可多也不可少。",
                }
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Extract the content field from the response
            if "content" in response:
                response_content = response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # Define validation criteria based on the test requirements
            validation_criteria = """
            請確認回應是否符合以下條件：
            1. 回應中包含災難新聞信息（至少提到了一些具體災難事件）
            2. 回應中有表格呈現（HTML表格標籤或是文字表格形式呈現災難數據）
            3. 回應中提供了新聞來源（至少包含一個可識別的媒體來源名稱如CNN、BBC、路透社等）
            4. 回應中有提及災難事件的類型（自然災害或人為災害）
            5. 回應中有提及災難事件的地理位置（國家、城市等）
            6. 回應中是否在結尾包含一個笑話
            
            所有條件都必須滿足，特別是必須有災難新聞、表格呈現方式及新聞來源引用。
            """

            # Validate with LLM
            validation_result = self.validate_with_llm(
                response_content, validation_criteria
            )

            # Assert that the validation passed
            self.assertTrue(
                validation_result["pass"],
                f"LLM validation failed in {self._testMethodName}: {validation_result['reason']}, LLM response: {response_content}",
            )

            # Additional checks for tables and sources
            self.assertTrue(
                "|" in response_content
                or "<table" in response_content.lower()
                or "表格" in response_content,
                "Response does not appear to contain any tables",
            )

            # # Check for news sources
            # news_sources = [
            #     "CNN",
            #     "BBC",
            #     "路透社",
            #     "美聯社",
            #     "法新社",
            #     "聯合報",
            #     "東森",
            # ]
            # sources_found = any(source in response_content for source in news_sources)
            # self.assertTrue(
            #     sources_found,
            #     "Response does not reference any recognizable news sources",
            # )

        except Exception as e:
            print(
                f"test_langgraph_global_disaster_news: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_date_time_comparison(self):
        """測試日期時間比較功能，檢查重點：
        1. 當使用者僅指定日期時間而未明確要求比較時，agent 是否能自動使用 current_date_time 工具獲取當前時間
        2. agent 是否能自動使用 compare_date_time 工具比較指定時間與當前時間
        3. agent 是否能正確判斷指定時間是過去還是未來並提供解釋
        """
        # 共用的系統提示
        system_prompt = "如果使用者的問題中有指定日期時間，不要預設它是未來或過去，一定要先使用 current_date_time 和 compare_date_time 這兩個工具，以取得現在的日期時間並判斷使用者指定的日期時間是過去或未來，然後再進行後續的動作。"

        # 共用的配置
        base_config = {
            "system_prompt": system_prompt,
            "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
            "user_id": "sebastian.hsu@gmail.com",
        }

        # 測試過去時間
        past_payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "2020年1月1日發生了什麼重要事件？",
                }
            ],
            "config": base_config,
        }

        # 測試未來時間
        future_payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "2030年12月31日會有什麼重要活動？",
                }
            ],
            "config": base_config,
        }

        # 測試端點
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            # 測試過去時間
            print("Testing past date comparison...")
            past_response = self.api_post(endpoint, past_payload)
            self.assertIsNotNone(past_response)

            if "content" in past_response:
                past_response_content = past_response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # 定義過去時間的驗證標準
            past_validation_criteria = """
            請確認回應是否符合以下條件：
            1. 回應中是否提到或暗示 2020年1月1日 是過去的時間
            2. 回應中是否有跡象表明 agent 使用了 current_date_time 工具獲取當前時間（例如提到「根據當前時間」、「現在是...」等）
            3. 回應中是否有跡象表明 agent 使用了 compare_date_time 工具比較時間（例如提到「比較結果」、「早於當前時間」等）
            4. 回應中是否包含關於 2020年1月1日 發生的重要事件的資訊
            """

            # 使用 LLM 驗證
            past_validation_result = self.validate_with_llm(
                past_response_content, past_validation_criteria
            )

            # 驗證結果
            self.assertTrue(
                past_validation_result["pass"],
                f"LLM validation failed for past date in {self._testMethodName}: {past_validation_result['reason']}, LLM response: {past_response_content}",
            )

            # 測試未來時間
            print("Testing future date comparison...")
            future_response = self.api_post(endpoint, future_payload)
            self.assertIsNotNone(future_response)

            if "content" in future_response:
                future_response_content = future_response["content"]
            else:
                self.fail("Response does not contain 'content' field")

            # 定義未來時間的驗證標準
            future_validation_criteria = """
            請確認回應是否符合以下條件：
            1. 回應中是否提到或暗示 2030年12月31日 是未來的時間
            2. 回應中是否有跡象表明 agent 使用了 current_date_time 工具獲取當前時間（例如提到「根據當前時間」、「現在是...」等）
            3. 回應中是否有跡象表明 agent 使用了 compare_date_time 工具比較時間（例如提到「比較結果」、「晚於當前時間」等）
            4. 回應中是否適當地處理了關於未來日期的問題（例如表明無法預測未來具體事件，但可能提供一些合理的推測或建議）
            """

            # 使用 LLM 驗證
            future_validation_result = self.validate_with_llm(
                future_response_content, future_validation_criteria
            )

            # 驗證結果
            self.assertTrue(
                future_validation_result["pass"],
                f"LLM validation failed for future date in {self._testMethodName}: {future_validation_result['reason']}, LLM response: {future_response_content}",
            )

        except Exception as e:
            print(
                f"test_langgraph_date_time_comparison: Test failed with error: {str(e)}"
            )
            raise

    def test_langgraph_react_agent_business_flow(self):
        """Test the langgraph_react_agent with a business flow example."""
        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "我想要請你 給我 一個業務流的範例,我只要三個節點,然後我還要針對這個業務流範例當中的其中中間的一個工作流程,然後來 進行示意,然後我那個工作流程也只需要三個節點,那原因是因為我要做成簡報,這樣子比較清晰容易看懂,那業務流 他是人如何工作的,的,的一個重點,記錄人員互動、決策跟情緒體驗,那也因此在業務流的時候呢,我需要請你幫我畫成使用者旅程地圖,裡面有酷酷點跟笑笑點,對不起,那請你節點幫我增加為五個好,然後再來工作流程的地方,它則是聚焦在任務跟文件,還有系統間的流動,它是一個操作的程序跟規則,那我,我也需要,我要修改前面的說法,要改成五個節點,那業務流是使用使用者旅程庫庫地圖,那工作流程的話,我希望它是一個,也許是一個工作流程程圖,或者是時序圖,然後看你覺得哪一個的表現比較明確,那這個內容呢,我需要以內政部的任何一個轄下的任何一個業務來進行舉例,然後我我想要請你幫我現在畫出來。",
                },
                {
                    "role": "assistant",
                    "content": "**我瞭解您需要一個業務流程的範例，特別是以內政部的業務為例，包含：**\n1. **一個使用者旅程地圖（業務流）- 5個節點，記錄人員互動、決策和情緒體驗**\n2. **一個工作流程程圖或時序圖 - 5個節點，聚焦在任務、文件和系統間的流動**\n**我會先幫您創建這兩個圖表。讓我們以內政部戶政司的「結婚登記」業務為例。**\n**首先，讓我建立使用者旅程地圖（業務流）：**",
                },
                {
                    "role": "user",
                    "content": "等一下，你在第二個跟第三個給我的連結啊，裡面都是亂買，你到底在幹什麼？你重新確認一下。",
                },
                {"role": "assistant", "content": ""},
                {"role": "user", "content": "你還好嗎？你有沒有在動作？"},
            ],
            "config": {
                "system_prompt": "回答後你都會在結尾講個笑話，並加上 emoji",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Check for error response format
            if "detail" in response:
                error_message = response["detail"]
                # Fail if the error is about empty message content
                self.assertNotIn(
                    "messages.3: all messages must have non-empty content except for the optional final assistant message",
                    error_message,
                    f"API returned expected error about empty content: {error_message}",
                )
                print(
                    f"API returned an error, but not the empty content error: {error_message}"
                )
            # Check for successful response format
            else:
                # For successful responses, verify content key exists at the top level
                self.assertIn("content", response, "Response missing 'content' field")
                print(f"Response received successfully with content!")

        except Exception as e:
            self.fail(f"Error testing API: {str(e)}")

    def test_auth_token_verify_api(self):
        """測試 auth token verification API，檢查重點：
        1. 有效 token 的驗證
        2. 無效 token 的錯誤處理
        3. 缺少 token 參數的錯誤處理
        """
        # Test with valid-looking token
        endpoint = "/api/auth/token_verify"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            # Test case 1: Valid token format (though may not be valid in backend)
            valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
            
            # Use form data for POST request
            import requests
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, data={"access_token": valid_token})
            
            # Expect either 200 (valid) or 401 (invalid token) or 500 (service unavailable)
            self.assertIn(response.status_code, [200, 401, 500], 
                         f"Unexpected status code: {response.status_code}")
            
            if response.status_code == 200:
                json_response = response.json()
                self.assertIn("is_success", json_response)
                print(f"Token verification succeeded: {json_response}")
            elif response.status_code == 401:
                json_response = response.json()
                self.assertIn("detail", json_response)
                self.assertIn("Invalid", json_response["detail"])
                print(f"Token verification failed as expected: {json_response}")
            elif response.status_code == 500:
                # Service might not be configured
                json_response = response.json()
                print(f"Service unavailable (expected in dev): {json_response}")

            # Test case 2: Missing token parameter
            response_missing = requests.post(url, data={})
            self.assertEqual(response_missing.status_code, 422, 
                           "Missing token should return 422 validation error")
            
            json_response_missing = response_missing.json()
            self.assertIn("detail", json_response_missing)
            print(f"Missing token handled correctly: {json_response_missing}")

            # Test case 3: Empty token
            response_empty = requests.post(url, data={"access_token": ""})
            self.assertIn(response_empty.status_code, [400, 401, 500], 
                         "Empty token should return 400, 401, or 500")
            print(f"Empty token handled with status: {response_empty.status_code}")

        except Exception as e:
            print(f"test_auth_token_verify_api: Test failed with error: {str(e)}")
            raise

    def test_langgraph_react_agent_social_housing(self):
        """Test the langgraph_react_agent with social housing application analysis."""
        # Test payload
        payload = {
            "graph_name": "langgraph_react_agent",
            "messages": [
                {
                    "role": "user",
                    "content": "幫我分析這分申請資料，我的檔案已經在你的system prompt裡面了，不需要再做其他的處理，直接使用system prompt裡的資料進行分析",
                }
            ],
            "config": {
                "system_prompt": "<Context>\n您是一位非常細心且專業的中華民國內政部審查社宅入住資格的資深審查員\n</Context>\n\n<Objective>\n您的目標是在審查使用者是否符合社宅入住資格\n</Objective>\n\n<Style>\n請保持中立及客觀，以精煉的方式分析資料，確保過程簡潔明瞭。\n</Style>\n\n<Tone>\n專業且耐心的語氣。\n</Tone>\n\n<Audience>\n此流程設計專門供機關內的相關同仁使用，他們需清楚知道哪些是合格的資料，哪些不是，以便後續決策。\n<Audience>\n\n<第一步驟>\n<審查規則>\n1. 年滿18歲(含)以上之中華民國國民\n2. 有於北北基桃設籍、就學、就業任一需求者\n3. 於北北基桃無自有住宅者或個別持有小於40平方公尺\n4. 家庭成員每人每月平均所得不超過新臺幣59,150元（舉例：新臺幣60,000元就是超過59,150元）\n</審查規則>\n\n<Response>\n1. 請幫我列出完整的審查結果，通過打Ｖ，不通過打Ｘ，並且列出不通過的原因\n2. 幫我把上面的內容產出一個表格回傳給我\n</Response>\n</第一步驟>\n\n<第二步驟>\n幫我依照<第一步驟>產生的結果，生產一個html的頁面報告，html頁面裡面要顯示以下資訊，你不要直接給我html的程式\n1. 請幫我畫一張圓餅圖分析年齡分佈\n2. 請幫我把原始審查資料跟<第一步驟>的產出做合併\n3. 請幫我做一個搜尋工具快速搜尋審查資料\n</第二步驟>\n\n\n\n\n\n以下為附加檔案內容：\n\n檔名：\n社宅申請模擬資料.csv\n檔案內容：\n申請人姓名,性別,出生年月日,婚姻狀況,身分證字號,電話,電子郵件,職業,戶籍地址,戶籍地址是否承租,通訊地址,通訊地址是否承租,緊急聯絡人,稱謂,緊急聯絡人電話,申請類別,申請戶類型,家具承租方案,配偶姓名,配偶身分證字號,家庭成員數量,持有住宅平方公尺數,平均家庭成員月收入\n林志明,男,1985-06-12,已婚,A123456789,0912-345-678,zhiming.lin@example.com,軟體工程師,新北市板橋區文化路一段100號5樓,是,新北市板橋區文化路一段100號5樓,是,林志豪,兄弟,0922-123-456,設籍,一般戶,同步租,王美玲,B234567890,3,0,45000\n陳雅婷,女,2001-05-06,未婚,B287654321,0933-876-543,yating.chen@example.com,學生,台北市信義區松仁路50號12樓,否,新北市新莊區中正路200號3樓,是,陳大明,父親,0955-987-654,就學,一般戶,買斷,,,1,0,38000\n張家豪,男,1978-11-30,已婚,C198765432,0977-654-321,jiahao.zhang@example.com,公務員,台北市大安區和平東路二段106號7樓,是,台北市大安區和平東路二段106號7樓,是,張明德,父親,0910-234-567,設籍,現職警消人員,同步租,李佩珊,D123456789,4,0,52000\n黃麗華,女,1965-08-15,喪偶,E234567890,0988-765-432,lihua.huang@example.com,退休教師,新北市三重區重新路一段88號4樓,否,新北市三重區重新路一段88號4樓,否,黃志成,兒子,0923-456-789,設籍,65歲以上老人,同步租,,,1,0,25000\n吳建志,男,1982-04-20,已婚,F123456789,0932-123-456,jianzhih.wu@example.com,銀行經理,台北市中山區南京東路三段25號9樓,是,台北市中山區南京東路三段25號9樓,是,吳大維,父親,0912-876-543,就業,一般戶,買斷,林美琪,G234567890,5,15,60000\n李小芳,女,1992-12-05,已婚,H123456789,0956-789-123,xiaofang.li@example.com,設計師,基隆市中正區中正路100號3樓,是,台北市松山區民生東路四段133號6樓,是,李大中,父親,0933-222-111,就業,未成年子女三人以上,同步租,王大明,I234567890,5,0,42000\n王俊傑,男,1988-07-15,未婚,J123456789,0978-456-123,junjie.wang@example.com,工程師,桃園市中壢區中央西路二段30號5樓,否,新北市新店區北新路三段100號7樓,是,王大華,父親,0910-876-543,就業,身心障礙,買斷,,,1,0,35000\n蔡美玲,女,1975-09-28,離婚,K123456789,0933-789-456,meiling.tsai@example.com,會計師,新北市永和區永和路一段50號4樓,是,新北市永和區永和路一段50號4樓,是,蔡明哲,兄弟,0922-333-444,就業,特殊境遇家庭,同步租,,,2,0,40000\n鄭志偉,男,1980-02-14,已婚,L123456789,0955-123-789,zhiwei.zheng@example.com,教師,台北市文山區木柵路一段100號3樓,否,台北市文山區木柵路一段100號3樓,否,鄭大勇,父親,0912-345-678,就業,一般戶,買斷,陳美美,M234567890,3,20,48000\n林美華,女,2003-01-03,未婚,N123456789,0978-789-123,meihua.lin@example.com,學生,新北市汐止區大同路一段150號5樓,是,新北市汐止區大同路一段150號5樓,是,林大明,父親,0933-456-789,就學,一般戶,同步租,,,1,0,36000\n張大為,男,1972-06-30,已婚,O123456789,0910-234-567,dawei.zhang@example.com,建築師,台北市大安區復興南路一段200號7樓,否,台北市大安區復興南路一段200號7樓,否,張小明,兒子,0922-123-456,設籍,一般戶,買斷,王麗麗,P234567890,3,25,65000\n陳俊宏,男,1990-08-12,未婚,Q123456789,0933-222-111,junhong.chen@example.com,軍職人員,桃園市龜山區文化一路100號5樓,是,桃園市龜山區文化一路100號5樓,是,陳大勇,父親,0955-123-456,就業,軍職人員,同步租,,,1,0,42000\n楊雅琪,女,1987-04-15,已婚,R123456789,0978-456-789,yaqi.yang@example.com,行銷經理,新北市中和區中和路100號6樓,是,新北市中和區中和路100號6樓,是,楊大明,父親,0912-345-678,設籍,一般戶,買斷,李志明,S234567890,2,0,55000\n劉大偉,男,1968-12-25,已婚,T123456789,0955-789-123,dawei.liu@example.com,計程車司機,基隆市安樂區安樂路二段50號3樓,否,基隆市安樂區安樂路二段50號3樓,否,劉小明,兒子,0933-456-789,設籍,低收入戶,同步租,張美美,U234567890,4,0,28000\n高美玲,女,1993-03-08,未婚,V123456789,0910-123-456,meiling.gao@example.com,設計師,台北市內湖區內湖路一段300號8樓,是,台北市內湖區內湖路一段300號8樓,是,高大明,父親,0922-789-123,就業,一般戶,買斷,,,1,0,38000\n鄭美美,女,1983-09-18,離婚,W123456789,0933-789-123,meimei.zheng@example.com,餐廳經理,新北市新莊區新莊路100號4樓,是,新北市新莊區新莊路100號4樓,是,鄭大勇,父親,0955-456-789,設籍,特殊境遇家庭,同步租,,,2,0,32000\n林志豪,男,1991-05-20,未婚,X123456789,0978-123-456,zhihao.lin@example.com,工程師,台北市士林區士林路100號5樓,否,台北市士林區士林路100號5樓,否,林大明,父親,0912-789-123,就業,一般戶,買斷,,,1,0,45000\n王美玲,女,1979-11-12,已婚,Y123456789,0955-123-456,meiling.wang@example.com,會計師,新北市板橋區民生路100號6樓,是,新北市板橋區民生路100號6樓,是,王大明,父親,0933-123-456,設籍,一般戶,同步租,李大偉,Z234567890,3,0,50000\n陳志明,男,1960-02-28,已婚,A234567891,0910-789-456,zhiming.chen@example.com,退休公務員,台北市北投區石牌路一段100號3樓,否,台北市北投區石牌路一段100號3樓,否,陳小明,兒子,0922-456-789,設籍,65歲以上老人,同步租,林美美,B234567891,2,0,30000\n莊雅婷,女,2002-08-08,未婚,C234567891,0933-456-123,yating.zhuang@example.com,學生,桃園市桃園區中正路100號5樓,是,桃園市桃園區中正路100號5樓,是,莊大明,父親,0955-789-456,就學,原住民,買斷,,,1,0,37000",
                "botrun_flow_lang_url": "https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app",
                "user_id": "sebastian.hsu@gmail.com",
            },
        }

        # Make the request
        endpoint = "/api/langgraph/invoke"
        print(f"\nTesting API: {self.base_url}{endpoint}")
        print("-" * 50)

        try:
            response = self.api_post(endpoint, payload)

            # Basic assertions to verify the response
            self.assertIsNotNone(response)

            # Validation criteria for social housing application analysis
            validation_criteria = """
            請驗證回應是否包含以下內容：
            1. 完整的社宅申請審查結果，包括通過/不通過標記
            2. 以Markdown格式顯示的審查結果表格（應包含 | 字符作為表格格式）
            3. 一個以"https://storage.googleapis.com"開頭的HTML頁面URL
            4. 基於提供的人口統計數據的分析
            """

            # Validate the response with LLM
            if "content" in response:
                validation_result = self.validate_with_llm(
                    response["content"], validation_criteria
                )

                # Additionally, directly check for markdown table and storage URL
                content = response["content"]
                has_markdown_table = "|" in content and "-|-" in content
                has_storage_url = "https://storage.googleapis.com" in content

                # Custom assertions for specific requirements
                self.assertTrue(has_markdown_table, "回應中不包含Markdown表格")
                self.assertTrue(
                    has_storage_url,
                    "回應中不包含Google Cloud Storage網址",
                )

                # Assert that validation passed
                self.assertTrue(
                    validation_result.get("pass", False),
                    f"驗證失敗：{validation_result.get('reason', '未提供原因')}",
                )

                print(f"回應驗證成功：{validation_result.get('reason', '')}")
            else:
                self.fail("Response does not contain 'content' field")

        except Exception as e:
            self.fail(f"Error testing API: {str(e)}")


def run_with_base_url(base_url=None):
    """Run the tests with an optional custom base URL

    Args:
        base_url: Optional base URL to override the default
    """
    # If a base URL is provided, set it as a class attribute
    if base_url:
        TestAPIFunctionality.base_url = base_url

    # Run the tests
    unittest.main(argv=["first-arg-is-ignored"], exit=False)


if __name__ == "__main__":
    unittest.main()
    # single test test_langgraph_multinode_news_dall_e
    # run_with_base_url("https://botrun-flow-lang-fastapi-dev-36186877499.asia-east1.run.app")
    # test_suite = unittest.TestSuite()
    # test_suite.addTest(TestAPIFunctionality("test_langgraph_multinode_news_dall_e"))
    # runner = unittest.TextTestRunner()
    # runner.run(test_suite)
