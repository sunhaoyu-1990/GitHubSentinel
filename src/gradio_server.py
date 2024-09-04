import gradio as gr  # 导入gradio库用于创建GUI
from datetime import datetime  # 导入datetime库用于获取当前时间

from config import Config  # 导入配置管理模块
from github_client import GitHubClient  # 导入用于GitHub API操作的客户端
from hacker_news_data import HackerClient  # 导入HackerNews客户端类，处理HackerNews API请求
from report_generator import ReportGenerator  # 导入报告生成器模块
from llm import LLM  # 导入可能用于处理语言模型的LLM类
from subscription_manager import SubscriptionManager  # 导入订阅管理器
from logger import LOG  # 导入日志记录器

# 创建各个组件的实例
config = Config()
github_client = GitHubClient(config.github_token)
llm = LLM()
report_generator = ReportGenerator(llm)
subscription_manager = SubscriptionManager(config.subscriptions_file)
llm_hackernews = LLM('hackernews')  # 创建语言模型实例
report_generator_hackernews = ReportGenerator(llm_hackernews)  # 创建报告生成器实例
hacknews_client = HackerClient()

def export_progress_by_date_range(repo, days):
    # 定义一个函数，用于导出和生成指定时间范围内项目的进展报告
    raw_file_path = github_client.export_progress_by_date_range(repo, days)  # 导出原始数据文件路径
    report, report_file_path = report_generator.generate_report_by_date_range(raw_file_path, days)  # 生成并获取报告内容及文件路径

    return report, report_file_path  # 返回报告内容和报告文件路径

def export_hackernews_progress():
    # 定义一个函数，用于导出和生成HackerNews的进展报告
    raw_file_path = hacknews_client.export_hackernews_top_stories()  # 导出原始数据文件路径
    report, report_file_path = report_generator_hackernews.generate_daily_report(raw_file_path)  # 生成并获取报告内容及文件路径

    return report, report_file_path  # 返回报告内容和报告文件路径

def update_subscription_list():
    # 定义一个函数，用于更新订阅列表
    return subscription_manager.list_subscriptions()

def add_subscription(new_repo):
    # 定义一个函数，用于添加新的订阅项目
    response_str = ''
    if new_repo:
        if subscription_manager.add_subscription(new_repo):
            now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            LOG.info(f'{now_time} 添加新项目：{new_repo}')
            response_str = new_repo + '添加成功'
        else:
            response_str = new_repo + '添加失败'
    else:
        response_str = '请输入要添加的项目名称'
    return response_str, gr.update(choices=update_subscription_list()), gr.update(choices=update_subscription_list()), gr.update(value=None)

def remove_subscription(selected_repos):
    # 定义一个函数，用于删除订阅项目
    response_str = ''
    if selected_repos:
        for selected_repo in selected_repos:
            if subscription_manager.remove_subscription(selected_repo):
                now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                LOG.info(f'{now_time} 添加新项目：{new_repo}')
                response_str += selected_repo + '删除成功\n\n'
            else:
                response_str += selected_repo + '删除失败\n\n'
    else:
        response_str = '请选择要删除的项目'
    return response_str, gr.update(choices=update_subscription_list()), gr.update(choices=update_subscription_list()), gr.update(value=[])

# 创建Gradio界面
with gr.Blocks() as demo:
    gr.HTML("""
    <style>
        /* 修改Button的hover效果 */
        button:hover {
            background-color: #4CAF50;
        }
    </style>
    """)
    gr.HTML("<h1 style='text-align: center; font-family: Arial, sans-serif; font-size: 36px; color: #4CAF50;'>GitHubSentinel</h1>")
    with gr.Tab("github_report"):
        # Dropdown里的内容实时更新，用于选择要生成报告的GitHub项目
        repo = gr.Dropdown(subscription_manager.list_subscriptions(), label="选择项目", info="选择要生成报告的GitHub项目")
        days = gr.Slider(value=2, minimum=1, maximum=7, step=1, label="报告周期", info="生成项目过去一段时间进展，单位：天")
        button = gr.Button("生成报告")
        output = gr.Markdown()
        download = gr.File(label="下载报告")
    with gr.Tab("github_setting"):
        with gr.Group():
            gr.Markdown("## 添加项目")
            new_repo = gr.Textbox(label="项目名称", placeholder="输入项目名称")
            button_add = gr.Button("添加")
        with gr.Group():
            gr.Markdown("## 删除项目")
            selected_repos = gr.Dropdown(
                subscription_manager.list_subscriptions(), label="项目名称", info="请选择要删除的项目名称，可以多选",multiselect=True,
            )
            button_remove = gr.Button("删除")
        # 显示操作日志的
        show = gr.Markdown("操作日志", height=100)
    with gr.Tab("hackernews_report"):
        # Dropdown里的内容实时更新，用于选择要生成报告的GitHub项目
        button_hacker = gr.Button("生成当前报告")
        output_hacker = gr.Markdown()
        download_hacker = gr.File(label="下载报告")

    button.click(
        export_progress_by_date_range,
        inputs=[repo, days],
        outputs=[output, download]
    )
    # 生成项目名称添加功能按钮的点击事件，成功后，刷新下拉框
    button_add.click(add_subscription, inputs=new_repo, outputs=[show, repo, selected_repos, new_repo])
    # 删除项目名称添加功能按钮的点击事件，成功后，刷新下拉框
    button_remove.click(remove_subscription, inputs=selected_repos, outputs=[show, repo, selected_repos, selected_repos])
    button_hacker.click(
        export_hackernews_progress,
        inputs=[repo, days],
        outputs=[output_hacker, download_hacker]
    )


if __name__ == "__main__":
    demo.launch(share=True, server_name="0.0.0.0")  # 启动界面并设置为公共可访问
    # 可选带有用户认证的启动方式
    # demo.launch(share=True, server_name="0.0.0.0", auth=("django", "1234"))