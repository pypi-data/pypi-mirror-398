#!/usr/bin/env python3
"""
한국투자증권 API 문서 크롤링 스크립트

이 스크립트는 한국투자증권 Open API 포털에서 API 명세를 크롤링하여
로컬 마크다운 파일로 저장합니다.

각 API 페이지의 전체 내용을 HTML에서 마크다운으로 변환합니다.
"""

import asyncio
import argparse
import logging
import random
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
import html2text

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 상수 정의
BASE_URL = "https://apiportal.koreainvestment.com"
OUTPUT_DIR = Path("docs/api")
REQUEST_DELAY_MIN_MS = 1000  # 서버 부하 방지를 위한 최소 요청 간격 (밀리초)
REQUEST_DELAY_MAX_MS = 2000  # 서버 부하 방지를 위한 최대 요청 간격 (밀리초)


class APIDocsCrawler:
    """API 문서 크롤링 클래스"""

    def __init__(self, output_dir: Path = OUTPUT_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # html2text 설정
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.ignore_emphasis = False
        self.html_converter.body_width = 0  # 줄바꿈 없음
        self.html_converter.unicode_snob = True  # 유니코드 유지

    async def get_api_list_from_menu(self, page: Page) -> List[Tuple[str, str, str]]:
        """
        왼쪽 메뉴에서 모든 API 목록 추출

        Returns:
            (카테고리, API 이름, API 경로) 튜플 리스트
        """
        logger.info("API 메뉴 목록 추출 중...")

        await page.goto(f"{BASE_URL}/apiservice-summary")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)  # 동적 콘텐츠 로딩 대기

        api_list = []

        # 왼쪽 메뉴의 모든 링크 추출
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # onclick 속성에서 goLeftMenuUrl 패턴 찾기
        clickable_elements = soup.select("[onclick*='goLeftMenuUrl']")

        # 카테고리 추출을 위해 부모 요소도 확인
        current_category = "기타"

        for elem in clickable_elements:
            onclick = elem.get("onclick", "")
            text = elem.get_text(strip=True)

            # onclick에서 API 경로 추출: goLeftMenuUrl('/path/to/api')
            match = re.search(r"goLeftMenuUrl\(['\"]([^'\"]+)['\"]\)", onclick)
            if match:
                api_path = match.group(1)

                # 카테고리 추출 (부모 요소에서)
                parent = elem.find_parent("ul") or elem.find_parent("div")
                if parent:
                    # 이전 형제 요소에서 카테고리 제목 찾기
                    prev = parent.find_previous_sibling()
                    if prev and prev.get_text(strip=True):
                        cat_text = prev.get_text(strip=True)
                        if "[" in cat_text:
                            current_category = cat_text.strip("[]").split("]")[0]

                api_list.append((current_category, text, api_path))

        logger.info(f"발견된 API 수: {len(api_list)}")
        return api_list

    async def crawl_api_page(self, page: Page, api_path: str, api_name: str) -> Optional[str]:
        """
        API 상세 페이지를 클릭하여 콘텐츠를 마크다운으로 변환

        Args:
            page: Playwright Page 객체
            api_path: API 경로 (goLeftMenuUrl의 인자)
            api_name: API 이름

        Returns:
            마크다운 형식의 문자열
        """
        try:
            # JavaScript 함수 호출로 API 페이지 로드
            await page.evaluate(f"goLeftMenuUrl('{api_path}')")
            await asyncio.sleep(1.5)  # 콘텐츠 로딩 대기

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # 메인 콘텐츠 영역 찾기 (오른쪽 API 문서 영역)
            content_element = None

            # 한국투자증권 API 포털의 콘텐츠 영역 선택자 (우선순위대로)
            content_selectors = [
                ".contents",  # 실제 API 문서 콘텐츠 영역
                ".api-content",
                ".main-content",
                "main",
            ]

            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element and len(content_element.get_text(strip=True)) > 100:
                    break

            # 콘텐츠를 찾지 못하면 content-wrap에서 사이드바 제외
            if not content_element:
                content_element = soup.select_one(".content-wrap")
                if content_element:
                    # 사이드바(lnb-wrap) 제거
                    for sidebar in content_element.select(".lnb-wrap, .sidebar, .side-menu, nav"):
                        sidebar.decompose()

            if not content_element:
                logger.warning(f"콘텐츠를 찾을 수 없음: {api_name}")
                return None

            # 불필요한 요소 제거
            for tag in content_element.select("script, style, header, footer"):
                tag.decompose()

            # HTML을 마크다운으로 변환
            html_content = str(content_element)
            markdown_content = self.html_converter.handle(html_content)

            # 마크다운 정리
            markdown_content = self._clean_markdown(markdown_content)

            # API 이름과 경로 정보 추가
            header = f"# {api_name}\n\n"
            header += f"> API 경로: `{api_path}`\n\n---\n\n"
            markdown_content = header + markdown_content

            return markdown_content

        except Exception as e:
            logger.error(f"페이지 크롤링 중 오류 ({api_name}): {e}")
            return None

    def _clean_markdown(self, content: str) -> str:
        """
        마크다운 내용 정리 - 네비게이션 요소 제거

        Args:
            content: 원본 마크다운

        Returns:
            정리된 마크다운
        """
        # 1. 브레드크럼 네비게이션 제거 (짧은 네비게이션 항목만)
        content = re.sub(r'^\s*\d+\.\s*HOME\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s*API 문서\s*$', '', content, flags=re.MULTILINE)
        # 카테고리 브레드크럼: "  3. OAuth인증" 또는 "  3. [국내주식] 시세분석" 형태 (짧은 것만)
        content = re.sub(r'^\s*\d+\.\s*\[.+?\]\s*.{0,20}\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\s*\d+\.\s*OAuth인증\s*$', '', content, flags=re.MULTILINE)

        # 2. API 가이드 목록 메뉴 제거 (긴 메뉴 라인)
        content = re.sub(
            r'^API 가이드 목록.+$',
            '', content, flags=re.MULTILINE
        )

        # 3. API 선택 목록 제거 (모든 카테고리 포함)
        # [인증-XXX], [국내주식-XXX], [해외주식-XXX], [실시간-XXX] 등
        content = re.sub(
            r'^API 선택.+?\[.+?-\d+\].*$',
            '', content, flags=re.MULTILINE
        )
        content = re.sub(
            r'^API .+?\[.+?-\d+\].+?\[.+?-\d+\].*$',
            '', content, flags=re.MULTILINE
        )

        # 4. 카테고리 헤더 제거 (단독 라인 - OAuth인증, [국내주식] 시세분석 등)
        content = re.sub(r'^OAuth인증\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^\[.+?\]\s+.+?(분석|계좌|시세|기타|정보)\s*$', '', content, flags=re.MULTILINE)

        # 5. 다운로드/버튼 텍스트 제거
        content = re.sub(r'^카테고리 다운로드\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^개별문서 다운로드\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^호출테스트\s*$', '', content, flags=re.MULTILINE)

        # 6. 연속된 빈 줄 제거 (3개 이상 -> 2개로)
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 7. 앞뒤 공백 제거
        content = content.strip()

        return content

    def save_markdown(self, category: str, filename: str, content: str) -> Path:
        """
        마크다운 파일 저장

        Args:
            category: 카테고리 이름
            filename: 파일명
            content: 마크다운 내용

        Returns:
            저장된 파일 경로
        """
        # 파일명 정리 (특수문자 제거)
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe_filename = safe_filename.replace(' ', '_')

        # 카테고리 디렉토리 정리
        safe_category = re.sub(r'[<>:"/\\|?*]', '_', category) if category else "기타"

        category_dir = self.output_dir / safe_category
        category_dir.mkdir(parents=True, exist_ok=True)

        file_path = category_dir / f"{safe_filename}.md"
        file_path.write_text(content, encoding="utf-8")

        logger.info(f"저장 완료: {file_path}")
        return file_path

    def generate_index(self, saved_files: Dict[str, List[str]]):
        """
        README.md 인덱스 생성

        Args:
            saved_files: 카테고리별 저장된 파일명 딕셔너리
        """
        index_content = """# 한국투자증권 Open API 문서

이 문서는 한국투자증권 API 포털에서 크롤링한 API 명세입니다.

## API 카테고리

"""
        total_count = 0
        for category, files in sorted(saved_files.items()):
            if not files:
                continue
            index_content += f"\n### {category} ({len(files)}개)\n\n"
            for filename in sorted(files):
                api_name = filename.replace(".md", "").replace("_", " ")
                safe_category = re.sub(r'[<>:"/\\|?*]', '_', category)
                index_content += f"- [{api_name}]({safe_category}/{filename})\n"
            total_count += len(files)

        index_content += f"\n---\n\n**총 API 수**: {total_count}개\n\n"
        index_content += "## 참조\n\n"
        index_content += "- [한국투자증권 API 포털](https://apiportal.koreainvestment.com/apiservice-summary)\n"

        index_path = self.output_dir / "README.md"
        index_path.write_text(index_content, encoding="utf-8")

        logger.info(f"인덱스 생성 완료: {index_path} (총 {total_count}개 API)")

    async def run(self, specific_category: Optional[str] = None, limit: Optional[int] = None):
        """
        크롤링 실행

        Args:
            specific_category: 특정 카테고리만 크롤링 (None이면 전체)
            limit: 크롤링할 API 개수 제한 (테스트용)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # API 목록 가져오기
            api_list = await self.get_api_list_from_menu(page)

            # 카테고리 필터링
            if specific_category:
                api_list = [(cat, name, path) for cat, name, path in api_list
                           if specific_category in cat]
                logger.info(f"'{specific_category}' 카테고리 필터링: {len(api_list)}개")

            # 개수 제한 (테스트용)
            if limit:
                api_list = api_list[:limit]
                logger.info(f"테스트 모드: {limit}개로 제한")

            saved_files: Dict[str, List[str]] = {}
            success_count = 0
            fail_count = 0

            for i, (category, api_name, api_path) in enumerate(api_list, 1):
                logger.info(f"[{i}/{len(api_list)}] 크롤링: {api_name}")

                # 페이지 크롤링 (JavaScript 함수 호출 방식)
                markdown_content = await self.crawl_api_page(page, api_path, api_name)

                if markdown_content:
                    # 파일 저장
                    self.save_markdown(category, api_name, markdown_content)

                    if category not in saved_files:
                        saved_files[category] = []
                    saved_files[category].append(f"{api_name.replace(' ', '_')}.md")
                    success_count += 1
                else:
                    fail_count += 1

                # 요청 간격 대기 (랜덤 1000~2000ms)
                delay_ms = random.randint(REQUEST_DELAY_MIN_MS, REQUEST_DELAY_MAX_MS)
                await asyncio.sleep(delay_ms / 1000)

            await browser.close()

            # 인덱스 생성
            if saved_files:
                self.generate_index(saved_files)

            logger.info(f"크롤링 완료! 성공: {success_count}, 실패: {fail_count}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="한국투자증권 API 문서 크롤링 (HTML → Markdown 변환)"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="특정 카테고리만 크롤링 (예: 국내주식, OAuth)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help=f"출력 디렉토리 (기본값: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="크롤링할 API 개수 제한 (테스트용)"
    )

    args = parser.parse_args()

    crawler = APIDocsCrawler(output_dir=args.output)
    asyncio.run(crawler.run(specific_category=args.category, limit=args.limit))


if __name__ == "__main__":
    main()
