import click
from prompt_toolkit import prompt
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any


@click.command()
@click.option('--name', help='项目的英文名称（用于文件夹和配置）')
@click.option('--display-name', help='项目的中文显示名称')  
@click.option('--description', help='项目的简短描述')
@click.option('--version', help='项目版本号')
@click.option('--author', help='项目作者')
@click.option('--type', 
              type=click.Choice(['kit', 'agent'], case_sensitive=False), 
              help='选择项目类型: kit(表单工具) 或 agent(智能体工具)')
@click.option('--collection', help='知识库名称（仅当启用 RAG 功能时使用）')
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.')
def init(name: str, display_name: str, description: str, version: str, author: str, type: str, collection: str, directory: str):
    """初始化一个新的 Adam 工具项目"""
    while not name:
        name = prompt('项目名称（仅支持字母、数字、连字符，不能有空格）: ')
    while not display_name:
        display_name = prompt('显示名称: ')
    while not description:
        description = prompt('项目描述: ')
    if not version:
        version = prompt('版本号 [1.0.0]: ')
        if not version:
            version = "1.0.0"
    while not author:
        author = prompt('作者: ')

    # 验证项目名称格式
    if not validate_project_name(name):
        click.echo(f"错误: 项目名称 '{name}' 格式不正确")
        click.echo("项目名称只能包含字母、数字和连字符(-)，不能包含空格或其他特殊字符")
        click.echo("示例: my-tool, data-processor, image-analyzer")
        return
    
    # 如果没有提供项目类型，显示选择菜单
    if not type:
        type = select_project_type()
    
    # 如果是 agent 类型，询问是否需要 RAG 功能
    enable_rag = False
    if type == 'agent':
        enable_rag = click.confirm('是否需要启用 RAG 知识库搜索功能？', default=False)
        if enable_rag:
            while not collection:
                collection = prompt('知识库名称: ')
    
    directory_path = Path(directory)
    project_path = directory_path / name
    
    # 检查目录是否已存在
    if project_path.exists():
        click.echo(f"错误: 目录 '{name}' 已存在")
        return
    
    # 创建项目目录
    project_path.mkdir(parents=True, exist_ok=True)
    click.echo(f"创建项目目录: {project_path}")
    
    # 创建config目录
    config_path = project_path / "config"
    config_path.mkdir(parents=True, exist_ok=True)
    
    # 设置Jinja2环境
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # 模板变量
    template_vars = {
        'name': name,
        'display_name': display_name,
        'description': description,
        'version': version,
        'author': author,
        'project_type': type,
        'enable_rag': enable_rag,
        'collection_name': collection if enable_rag else '',
        'class_name': name.replace('-', '_').title(),
        'rag_class_name': name.replace('-', '_').replace('_', '').title() + 'RAG' if enable_rag else ''
    }
    
    # 生成配置文件
    render_and_save(env, 'configure.json.j2', config_path / "configure.json", template_vars)
    click.echo(f"生成配置文件: config/configure.json")
    
    # 生成描述文件
    render_and_save(env, 'long_description.md.j2', config_path / "long_description.md", template_vars)
    click.echo(f"生成描述文件: config/long_description.md")
    
    # 生成描述文件 (英文版本)
    render_and_save(env, 'long_description_en.md.j2', config_path / "long_description_en.md", template_vars)
    click.echo(f"生成描述文件 (英文): config/long_description_en.md")
    
    if type == 'kit':
        generate_kit_files(env, project_path, config_path, template_vars)
    else:  # agent
        generate_agent_files(env, project_path, config_path, template_vars)
        # 如果启用了 RAG 功能，额外生成 RAG 文件
        if enable_rag:
            generate_rag_files(env, project_path, config_path, template_vars)
    
    # 生成 Makefile
    render_and_save(env, 'Makefile.j2', project_path / "Makefile", template_vars)
    click.echo(f"生成构建脚本: Makefile")
    
    # 生成 README 文件
    if type == 'kit':
        render_and_save(env, 'README_kit.md.j2', project_path / "README.md", template_vars)
    else:  # agent
        render_and_save(env, 'README_agent.md.j2', project_path / "README.md", template_vars)
    click.echo(f"生成项目文档: README.md")
    
    click.echo(f"\n✅ 项目 '{name}' 初始化完成!")
    click.echo(f"📁 项目路径: {project_path}")
    click.echo("\n📋 后续步骤:")
    click.echo("1. 📖 阅读 README.md 了解详细的开发指南")
    click.echo("2. 🔧 根据需要修改 Python 代码实现")
    if type == 'kit':
        click.echo("3. 📝 自定义 config/input.json 表单配置")
    else:
        click.echo("3. 🤖 自定义 config/initial_system_prompt.md 和 config/initial_assistant_message.md")
        if enable_rag:
            click.echo("4. 🔍 根据需要修改 RAG 知识库搜索功能")
    click.echo(f"{4 if type == 'kit' else 5}. 📄 完善 config/long_description.md 描述文档")
    click.echo(f"{5 if type == 'kit' else 6}. ⚙️ 运行 'make parse' 生成 functions.json")
    click.echo(f"{6 if type == 'kit' else 7}. 📦 运行 'make build' 打包项目")
    click.echo(f"\n💡 详细的开发指南请查看: https://sidereus-ai.feishu.cn/wiki/FVMowiyGCi4qYGkr131cPNzVnQd")


def render_and_save(env: Environment, template_name: str, output_path: Path, template_vars: Dict[str, Any]):
    """渲染模板并保存到文件"""
    template = env.get_template(template_name)
    content = template.render(**template_vars)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_kit_files(env: Environment, project_path: Path, config_path: Path, template_vars: Dict[str, Any]):
    """生成 kit 项目的特定文件"""
    
    # 生成 input.json 表单配置
    render_and_save(env, 'input.json.j2', config_path / "input.json", template_vars)
    click.echo(f"生成表单配置: config/input.json")
    
    # 生成主要的Python实现文件
    python_filename = f"{template_vars['name'].replace('-', '_')}.py"
    render_and_save(env, 'kit_python.py.j2', project_path / python_filename, template_vars)
    click.echo(f"生成主要实现文件: {python_filename}")


def generate_agent_files(env: Environment, project_path: Path, config_path: Path, template_vars: Dict[str, Any]):
    """生成 agent 项目的特定文件"""
    
    # 生成 initial_system_prompt.md
    render_and_save(env, 'initial_system_prompt.md.j2', config_path / "initial_system_prompt.md", template_vars)
    click.echo(f"生成系统提示文件: config/initial_system_prompt.md")
    
    # 生成 initial_system_prompt_en.md (英文版本)
    render_and_save(env, 'initial_system_prompt_en.md.j2', config_path / "initial_system_prompt_en.md", template_vars)
    click.echo(f"生成系统提示文件 (英文): config/initial_system_prompt_en.md")
    
    # 生成 initial_assistant_message.md
    render_and_save(env, 'initial_assistant_message.md.j2', config_path / "initial_assistant_message.md", template_vars)
    click.echo(f"生成助手消息文件: config/initial_assistant_message.md")
    
    # 生成 initial_assistant_message_en.md (英文版本)
    render_and_save(env, 'initial_assistant_message_en.md.j2', config_path / "initial_assistant_message_en.md", template_vars)
    click.echo(f"生成助手消息文件 (英文): config/initial_assistant_message_en.md")
    
    # 生成主要的Python实现文件
    python_filename = f"{template_vars['name'].replace('-', '_')}.py"
    render_and_save(env, 'agent_python.py.j2', project_path / python_filename, template_vars)
    click.echo(f"生成主要实现文件: {python_filename}")


def generate_rag_files(env: Environment, project_path: Path, config_path: Path, template_vars: Dict[str, Any]):
    """生成 RAG 功能的额外文件"""
    
    # 生成 RAG 功能的 Python 实现文件
    rag_filename = f"{template_vars['name'].replace('-', '_')}_rag.py"
    render_and_save(env, 'rag_python.py.j2', project_path / rag_filename, template_vars)
    click.echo(f"生成 RAG 功能文件: {rag_filename}")


def select_project_type() -> str:
    """显示项目类型选择菜单"""
    click.echo("\n请选择项目类型:")
    click.echo("1. kit (表单工具)")
    click.echo("2. agent (智能体工具)")
    
    while True:
        choice = prompt("请输入选项编号 (1 或 2)：")
        if choice == '1':
            return 'kit'
        elif choice == '2':
            return 'agent'
        else:
            click.echo("❌ 无效选择，请输入 1 或 2")


def validate_project_name(name: str) -> bool:
    """验证项目名称格式"""
    # 项目名称只能包含字母、数字和连字符，不能有空格
    pattern = r'^[a-zA-Z0-9-]+$'
    if not re.match(pattern, name):
        return False
    
    # 不能以连字符开始或结束
    if name.startswith('-') or name.endswith('-'):
        return False
    
    # 不能有连续的连字符
    if '--' in name:
        return False
    
    # 长度限制
    if len(name) < 1 or len(name) > 50:
        return False
    
    return True