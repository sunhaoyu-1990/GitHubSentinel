import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

class DoubanBookScraper:
    def __init__(self, keywords=['历史文化']):
        """
        初始化豆瓣爬虫类
        :param base_url: 目标网站URL
        :param keywords: 图书类型关键词列表
        """
        self.base_url = "https://book.douban.com/"
        self.keywords = keywords
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
        }
        self.output_dir = "douban_new_book"
        os.makedirs(self.output_dir, exist_ok=True)
        self.today = datetime.today().strftime('%Y-%m-%d')
        self.output_file = os.path.join(self.output_dir, f"{self.today}.md")

    def fetch_html(self):
        """从豆瓣网站获取HTML内容"""
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(response.text[:500])  # 打印前500个字符进行调试
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None

    def extract_new_book_info(self, book):
        """从书籍条目中提取信息"""
        try:
            title_tag = book.find('h2').find('a')
            title = title_tag.get_text(strip=True)
            detail_link = title_tag['href'] if title_tag else None

            # 获取作者和出版信息
            subject_abstract = book.find('p', class_='subject-abstract').get_text(strip=True)
            parts = subject_abstract.split('/')
            if len(parts) >= 4:
                author = parts[0].strip()
                year = parts[1].strip()
                publisher = parts[2].strip()
            else:
                author, year, publisher = "未知作者", "未知年份", "未知出版社"

            # 获取简介
            abstract = "暂无简介"

            return title, author, year, publisher, abstract, detail_link
        except Exception as e:
            print(f"解析书籍信息时出错: {e}")
            return None, None, None, None, None, None

    def extract_hot_book_info(self, book):
        """从热门图书列表项中提取书籍信息"""
        try:
            # 提取书籍标题和链接
            title_tag = book.find('h2', class_='clearfix').find('a')
            title = title_tag.text.strip() if title_tag else "未知标题"
            detail_link = title_tag['href'] if title_tag else None

            # 提取封面链接
            cover_tag = book.find('div', class_='media__img').find('img')
            cover_url = cover_tag['src'] if cover_tag else None

            # 提取作者信息
            author_tag = book.find('p', class_='subject-abstract color-gray')
            author = author_tag.text.strip() if author_tag else "未知作者"

            # 提取评分
            rating_tag = book.find('span', class_='font-small color-red fleft')
            rating = rating_tag.text.strip() if rating_tag else "暂无评分"

            # 提取评价人数
            review_tag = book.find('span', class_='fleft ml8 color-gray')
            review_count = review_tag.text.strip().strip('()') if review_tag else "0"

            # 提取纸质版价格
            price_tag = book.find('span', class_='buy-info')
            price = price_tag.text.strip() if price_tag else "未知价格"

            # 提取电子书链接（如果有）
            ebook_tag = book.find('div', class_='ebook-link')
            ebook_link = ebook_tag.find('a')['href'] if ebook_tag else None

            # 提取书籍简介
            abstract = "暂无简介"

            return {
                "title": title,
                "author": author,
                "rating": rating,
                "review_count": review_count,
                "price": price,
                "detail_link": detail_link,
                "cover_url": cover_url,
                "ebook_link": ebook_link,
                "abstract": abstract
            }

        except Exception as e:
            print(f"解析热门图书信息时出错: {e}")
            return None

    def get_book_detail(self, detail_url):
        """从书籍详情页获取完整简介"""
        try:
            time.sleep(1)  # 添加延迟，避免被封禁
            response = requests.get(detail_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            detail_soup = BeautifulSoup(response.content, 'html.parser')
            desc_tag = detail_soup.find('div', id='link-report')
            if desc_tag:
                return desc_tag.get_text(strip=True)
        except requests.RequestException as e:
            print(f"访问书籍详情页失败: {e}")
        return "暂无详细简介"

    def get_books_from_section(self, section, type_url):
        """从具体类型下抓取书籍信息"""
        books = []
        # 找到所有书籍列表项
        for book in section.find_all('li'):
            title, author, rating, abstract, detail_link = self.extract_book_info(book)
            
            # 如果简介为空，尝试从详情页获取
            if abstract == "暂无简介" and detail_link:
                abstract = self.get_book_detail(detail_link)
            
            books.append((title, author, rating, abstract))
        return books

    def extract_category_links(self, section):
        """从新书速递板块提取分类标签及其链接"""
        categories = {}
        category_tags = section.find('div', class_='tags').find_all('span', class_='item')
        for tag in category_tags:
            category_name = tag.get_text(strip=True)
            category_link = tag.get('data-tag', None)
            categories[category_name] = f"https://book.douban.com/latest?subcat={category_link}" if category_link else None
        return categories

    def extract_hot_category_links(self, hot_books_section):
        """从‘一周热门图书榜’板块提取分类链接"""
        categories = {}
        tags_section = hot_books_section.find('span', class_='tags')
        if tags_section:
            for tag in tags_section.find_all('a', href=True):
                category = tag.get_text(strip=True)
                link = "https://book.douban.com" + tag['href']
                categories[category] = link
        return categories

    def get_book_type(self, section):
        """获取模块下的图书类型，并返回类型和链接"""
        types = {}
        type_tags = section.find('span', class_='tags').find_all('a')
        for tag in type_tags:
            type_name = tag.get_text(strip=True)
            type_url = tag['href'] if 'href' in tag.attrs else None
            types[type_name] = type_url
        return types

    def scrape_new_books(self, soup):
        """爬取“新书速递”板块下符合关键词的书籍信息"""
        new_books_section = soup.find('div', class_='section books-express')
        if not new_books_section:
            print("未找到新书速递内容")
            return []

        # 提取分类
        categories = self.extract_category_links(new_books_section)
        books = []

        # 根据关键词筛选分类并抓取书籍信息
        for category, link in categories.items():
            if any(keyword in category for keyword in self.keywords):
                print(f"正在爬取新书分类: {category}")

                # 循环抓取每一页的数据
                current_page = 1

                # 获取分类页面的 HTML
                while link:
                    print(f"正在爬取分类 {category} 第 {current_page} 页...")
                    response = requests.get(link, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    category_soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 找到书籍列表
                    books_list = category_soup.find('ul', class_='chart-dashed-list')
                    if not books_list:
                        # 如果 'chart-dashed-list' 没有找到，尝试其他可能的 class
                        books_list = category_soup.find('ul', class_='list-col list-col2 list-summary')

                    if not books_list:
                        print(f"未找到 {category} 分类的书籍列表")
                        break

                    # 提取书籍信息
                    for i, book in enumerate(books_list.find_all('li', class_='media clearfix')):
                        # if i > 1:
                        #     break
                        try:
                            title, author, year, publisher, abstract, detail_link = self.extract_new_book_info(book)
                            if abstract == "暂无简介" and detail_link:
                                abstract = self.get_book_detail(detail_link)
                            books.append((title, author, year, publisher, abstract, detail_link))
                        except Exception as e:
                            print(f"解析书籍信息时出错: {e}")

                    # 检查是否有“下一页”
                    link = self.get_next_page_link(category_soup)
                    current_page += 1
        
        return books

    def scrape_hot_books(self, soup):
        """爬取“一周热门图书榜”板块的书籍信息"""
        hot_books_section = soup.find('div', class_='section popular-books')
        if not hot_books_section:
            print("未找到一周热门图书榜内容")
            return []

        # 提取分类及其链接
        categories = self.extract_hot_category_links(hot_books_section)
        books = []
        
        # 根据关键词筛选分类并抓取书籍信息
        for category, link in categories.items():
            if any(keyword in category for keyword in self.keywords):
                print(f"正在爬取热门分类: {category}")

                # 循环抓取每一页的数据
                current_page = 1
                while link:
                    print(f"正在爬取分类 {category} 第 {current_page} 页...")
                    response = requests.get(link, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    category_soup = BeautifulSoup(response.content, 'html.parser')

                    # 找到书籍列表
                    books_list = category_soup.find('ul', class_='chart-dashed-list')
                    if not books_list:
                        print(f"未找到 {category} 分类的书籍列表")
                        break

                    # 提取书籍信息
                    for i, book in enumerate(books_list.find_all('li')):
                        # if i > 2:
                        #     break
                        try:
                            book_info = self.extract_hot_book_info(book)
                            # 如果简介为空，则尝试从详情页获取
                            if book_info['abstract'] == "暂无简介" and book_info['detail_link']:
                                book_info['abstract'] = self.get_book_detail(book_info['detail_link'])
                            books.append(book_info)
                        except Exception as e:
                            print(f"解析书籍信息时出错: {e}")

                    # 检查是否有“下一页”
                    link = self.get_next_page_link(category_soup)
                    current_page += 1
        return books

    def save_to_markdown(self, new_books, hot_books):
        """将爬取结果保存为 Markdown 文件"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            # 保存新书信息
            f.write(f"# 豆瓣{'、'.join(self.keywords)}新书 ({self.today})\n\n")
            for idx, book in enumerate(new_books, 1):
                title, author, year, publisher, abstract, detail_link = book
                f.write(f"## {idx}. 《{title}》\n")
                f.write(f"- 作者: {author}\n")
                f.write(f"- 出版日期: {year}\n")
                f.write(f"- 出版社: {publisher}\n")
                f.write(f"- 简介: {abstract}\n")
                f.write(f"- 详情链接: [{detail_link}]({detail_link})\n")
                f.write("\n")
            
            # 保存一周热门图书榜信息
            f.write(f"\n# 豆瓣{'、'.join(self.keywords)}一周热门图书榜 ({self.today})\n\n")
            for idx, book in enumerate(hot_books, 1):
                f.write(f"## {idx}. 《{book['title']}》\n")
                f.write(f"- 作者: {book['author']}\n")
                f.write(f"- 评分: {book['rating']} （{book['review_count']}人评价）\n")
                f.write(f"- 价格: {book.get('price', '未知')}\n")
                f.write(f"- 简介: {book['abstract']}\n")
                f.write(f"- 详情链接: [{book['detail_link']}]({book['detail_link']})\n")
                if book.get('ebook_link'):
                    f.write(f"- 电子书链接: [{book['ebook_link']}]({book['ebook_link']})\n")
                if book.get('cover_url'):
                    f.write(f"![封面图片]({book['cover_url']})\n")
                f.write("\n")

        print(f"已成功保存到 {self.output_file}")
        return self.output_file

    def get_next_page_link(self, soup):
        """从分页器中提取“下一页”链接"""
        paginator = soup.find('div', class_='paginator')
        if paginator:
            next_page = paginator.find('span', class_='next')
            if next_page and next_page.find('a'):
                return "https://book.douban.com" + next_page.find('a')['href']
        return None

    def run(self):
        # 判断是否已经存在self.output_file文件，如果存在则直接返回
        if os.path.exists(self.output_file):
            print(f"文件 {self.output_file} 已存在")
            return self.output_file
        """执行爬虫任务"""
        html_content = self.fetch_html()
        if not html_content:
            print("获取网页内容失败")
            return
        
        soup = BeautifulSoup(html_content, 'html.parser')
        new_books = self.scrape_new_books(soup)
        hot_books = self.scrape_hot_books(soup)
        return self.save_to_markdown(new_books, hot_books)


# 使用示例
if __name__ == "__main__":
    # 设置目标URL和关键词
    keywords = ["文学"]

    # 实例化爬虫类并执行
    scraper = DoubanBookScraper(keywords)
    scraper.run()
