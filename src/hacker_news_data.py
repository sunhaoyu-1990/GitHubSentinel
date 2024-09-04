import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup

class HackerClient:
    def fetch_hackernews_top_stories(self):
        url = 'https://news.ycombinator.com/'
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        soup = BeautifulSoup(response.text, 'html.parser')
        # 查找包含新闻的所有 <tr> 标签
        stories = soup.find_all('tr', class_='athing')

        top_stories = []
        for story in stories:
            title_tag = story.find('span', class_='titleline').find('a')
            if title_tag:
                title = title_tag.text
                link = title_tag['href']
                top_stories.append({'title': title, 'link': link})

        return top_stories

    def export_hackernews_top_stories(self):
        stories = self.fetch_hackernews_top_stories()
        story_content = ""
        if stories:
            for idx, story in enumerate(stories, start=1):
                story_content += f"{idx}. {story['title']}\n"
                story_content += f"   Link: {story['link']}\n"
        else:
            story_content = "No stories found."
        
        # 获取当前日期
        today = datetime.now().date().isoformat()
        repo_dir = os.path.join('html_progress')  # 构建存储路径
        os.makedirs(repo_dir, exist_ok=True)  # 确保目录存在
        file_path = os.path.join(repo_dir, f'{today}_hackernews.md')  # 构建文件路径
        with open(file_path, 'w') as file:
            file.write(f"# hackernews top _stories of ({today})\n\n")
            file.write(story_content)
        
        return file_path

    def fetch_story_content(url):
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功

        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取网页的正文内容，通常会在 <article> 或 <div> 标签内
        main_content = ""
        
        # 尝试寻找常见的正文标签
        article_tag = soup.find('article')
        if article_tag:
            main_content = article_tag.get_text()
        else:
            div_tag = soup.find('div', {'class': 'post'})
            if div_tag:
                main_content = div_tag.get_text()
            else:
                # 如果没有找到常见标签，提取页面主要部分的文本作为正文
                main_content = soup.get_text()

        return main_content.strip()

# def fetch_pdf_content(pdf_url):
#     response = requests.get(pdf_url)
#     response.raise_for_status()

#     # 将PDF内容存储为二进制流
#     pdf_content = response.content

#     # 使用PyMuPDF读取PDF内容
#     with fitz.open(stream=pdf_content, filetype="pdf") as doc:
#         text = ""
#         for page in doc:
#             text += page.get_text()

#     return text

if __name__ == "__main__":
    hacker = HackerClient()
    hacker.export_hackernews_top_stories()
