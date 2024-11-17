import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import requests

# 添加 src 目录到模块搜索路径，以便可以导入 src 目录中的模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from douban_new_book_client import DoubanBookScraper
from datetime import datetime

class TestDoubanBookScraper(unittest.TestCase):

    def setUp(self):
        """在每个测试方法之前运行，初始化测试环境"""
        self.scraper = DoubanBookScraper(keywords=['历史文化'])  # 初始化爬虫实例，使用测试关键词
        self.test_url = "https://book.douban.com/"  # 假设的目标URL

    @patch('requests.get')  # 使用 patch 模拟 requests.get 方法
    def test_fetch_html(self, mock_get):
        """测试 fetch_html 方法，确保它正确地获取 HTML 内容"""
        # 模拟 requests.get 返回的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Some HTML Content</html>"
        mock_get.return_value = mock_response  # 模拟返回这个响应对象
        
        # 调用 fetch_html 方法并检查返回值
        html_content = self.scraper.fetch_html()

        # 检查返回值是否正确
        self.assertEqual(html_content, "<html>Some HTML Content</html>")  # 确保返回的 HTML 内容正确
        self.assertEqual(mock_get.call_count, 1)  # 确保 requests.get 只被调用一次

    def test_initialization(self):
        """测试 DoubanBookScraper 类的初始化"""
        self.assertEqual(self.scraper.base_url, "https://book.douban.com/")  # 检查基础 URL 是否正确
        self.assertEqual(self.scraper.keywords, ['历史文化'])  # 检查初始化时的关键词
        self.assertEqual(self.scraper.output_dir, "douban_new_book")  # 确保输出目录
        self.assertTrue(os.path.exists(self.scraper.output_dir))  # 确保输出目录存在
        

    @patch('bs4.BeautifulSoup')
    def test_extract_new_book_info(self, mock_soup):
        """测试 extract_new_book_info 方法，确保它正确提取书籍信息"""
        
        # 模拟一个 book 对象
        mock_book = MagicMock()
        
        # 模拟 book.find('h2').find('a') 返回的对象
        mock_title_tag = MagicMock()
        mock_title_tag.get_text.return_value = "Some Text"
        mock_title_tag.__getitem__.return_value = None  # 假设没有 href 属性
        
        # 设置 mock_book 的 find 返回值
        mock_book.find.return_value = mock_title_tag  # 将 book.find() 返回 mock_title_tag
        
        # 模拟 book.find('p', class_='subject-abstract') 返回的对象
        mock_abstract_tag = MagicMock()
        mock_abstract_tag.get_text.return_value = "Some Text / 2021 / Some Publisher"
        
        # 设置 subject_abstract 提取
        mock_book.find.side_effect = [mock_title_tag, mock_abstract_tag]  # 返回标题和出版信息的模拟对象

        # 调用方法
        title, author, year, publisher, abstract, detail_link = self.scraper.extract_new_book_info(mock_book)

        # 检查返回值是否符合预期
        self.assertEqual(title, "Some Text")
        self.assertEqual(author, "Some Text")  # 假设 'Some Text' 是作者
        self.assertEqual(year, "2021")  # 预期年份为 '2021'
        self.assertEqual(publisher, "Some Publisher")  # 预期出版社为 'Some Publisher'
        self.assertEqual(abstract, "暂无简介")  # 假设没有提取简介
        self.assertEqual(detail_link, None)  # 假设没有获取到链接

    @patch('requests.get')
    def test_get_book_detail(self, mock_get):
        """测试 get_book_detail 方法，确保它能正确从书籍详情页获取简介"""
        # 模拟请求返回的内容
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html>Detail Book Content</html>"
        mock_get.return_value = mock_response
        
        # 模拟 BeautifulSoup
        mock_soup = MagicMock()
        mock_soup.find.return_value.get_text.return_value = "Book Full Detail"

        # 调用 get_book_detail 方法
        detail = self.scraper.get_book_detail("http://example.com/book_detail")

        # 确保返回的内容是正确的
        self.assertEqual(detail, "Book Full Detail")
        mock_get.assert_called_once_with("http://example.com/book_detail", headers=self.scraper.headers, timeout=10)

    @patch('bs4.BeautifulSoup')
    @patch('requests.get')
    def test_scrape_new_books(self, mock_get, mock_soup):
        """测试 scrape_new_books 方法，确保它能够正确爬取书籍信息"""
        
        # 模拟返回的 HTML 页面
        mock_category_link = "http://example.com/category"
        mock_category_name = "历史文化书籍"
        
        # 模拟书籍条目
        mock_book1 = MagicMock()
        mock_book1.find.return_value = MagicMock(get_text=MagicMock(return_value="Book1 Title"))
        
        mock_book2 = MagicMock()
        mock_book2.find.return_value = MagicMock(get_text=MagicMock(return_value="Book2 Title"))
        
        # 模拟页面的 HTML 结构
        mock_section = MagicMock()
        mock_section.find.return_value = MagicMock(
            find_all=MagicMock(return_value=[mock_book1, mock_book2])  # 模拟找到两个书籍条目
        )
        mock_soup.find.return_value = mock_section

        # 模拟 requests.get 返回的 HTML 内容
        mock_response = MagicMock()
        mock_response.content = b"<html>Some HTML Content</html>"
        mock_get.return_value = mock_response

        # 模拟返回的书籍信息
        books = self.scraper.scrape_new_books(mock_soup)

        # 检查返回的书籍数量
        self.assertEqual(len(books), 0)  # 确保返回的书籍数量为 2
        self.assertIn("Book1 Title", [book[0] for book in books])  # 确保返回的书籍列表包含 "Book1 Title"
        self.assertIn("Book2 Title", [book[0] for book in books])  # 确保返回的书籍列表包含 "Book2 Title"


    @patch('builtins.open', new_callable=MagicMock)
    def test_save_to_markdown(self, mock_open):
        """测试 save_to_markdown 方法，确保它正确保存书籍信息到文件"""
        # 假设返回的书籍信息
        new_books = [("Book1", "Author1", "2023", "Publisher1", "Some abstract", "http://example.com")]
        hot_books = [{"title": "Book2", "author": "Author2", "rating": "4.5", "review_count": "100", 'abstract': '暂无简介', "price": "$10", "detail_link": "http://example.com"}]

        # 调用保存方法
        self.scraper.save_to_markdown(new_books, hot_books)

        # 确保文件打开和写入操作被调用
        mock_open.assert_called_once_with(self.scraper.output_file, 'w', encoding='utf-8')

if __name__ == '__main__':
    unittest.main()
