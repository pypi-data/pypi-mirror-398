import argparse
import os
import datetime
import re
from pathlib import Path
from importlib.resources import files


def get_all_files_in_directory(directory: Path) -> list[tuple[Path, str]]:
    """
    获取目录下所有文件的相对路径（忽略__pycache__目录）
    返回值: 元组列表 (模板文件路径, 相对目标路径)
    """
    file_mappings = []
    if not directory.exists() or not directory.is_dir():
        return file_mappings

    # 遍历目录下所有文件
    for root, _, files in os.walk(directory):
        # 跳过包含__pycache__的目录
        if "__pycache__" in root:
            continue

        for file in files:
            # 获取文件的绝对路径
            file_path = Path(root) / file
            # 计算相对模板目录的路径
            rel_path = file_path.relative_to(directory)
            # 添加到映射列表
            file_mappings.append((file_path, str(rel_path)))

    return file_mappings


def init_project(project_name: str, project_type: str) -> None:
    """
    初始化项目，自动读取模板文件并替换占位符
    """
    project_path = Path(os.getcwd()) / project_name
    if project_path.exists():
        print(f"❌ 错误：工程 '{project_path}' 已存在")
        return

    template_root = files("command.templates")
    if not template_root.is_dir():
        print("❌ 错误：未找到模板文件目录（command/templates）")
        return

    # 处理项目名称
    short_project_name = project_name.replace("shengye-platform-", "")
    short_project_name_upper = short_project_name.upper()

    # 定义模板变量
    context = {
        "__cli__.project_name": project_name,
        "__cli__.short_project_name": short_project_name,
        "__cli__.short_project_name_upper": short_project_name_upper,
        "__cli__.project_type": project_type,
        "__cli__.create_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "__cli__.author": os.getlogin(),
        "__cli__.default_port": 8080
    }

    # 自动获取基础模板文件和特定类型模板文件
    base_dir = template_root / "base"
    type_dir = template_root / project_type

    base_files = get_all_files_in_directory(base_dir)
    type_specific_files = get_all_files_in_directory(type_dir)

    # 合并所有文件映射
    file_mappings = base_files + type_specific_files
    copied_files = 0

    # 处理每个文件
    for template_file, target_rel_path in file_mappings:
        try:
            # 1. 读取模板内容
            template_content = template_file.read_text(encoding="utf-8")

            # 2. 替换所有占位符（包含花括号）
            rendered_content = template_content
            for key, value in context.items():
                # 精确匹配带有花括号的占位符
                pattern = re.compile(rf'{{\s*{re.escape(key)}\s*}}')
                rendered_content = pattern.sub(str(value), rendered_content)

            # 3. 清理引号（针对YAML键值对格式）
            rendered_content = re.sub(
                r'(\w+)\s*:\s*["\']([^"\']+)["\']',
                r'\1: \2',
                rendered_content
            )

            # 4. 最后检查并移除任何残留的花括号
            for value in context.values():
                rendered_content = re.sub(
                    rf'{{+{re.escape(str(value))}+}}',
                    str(value),
                    rendered_content
                )

            # 5. 处理文件后缀：直接移除.tpl后缀
            if target_rel_path.endswith('.tpl'):
                target_rel_path = target_rel_path[:-4]

            # 6. 写入文件
            target_file = project_path / target_rel_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(rendered_content, encoding="utf-8")

            copied_files += 1
        except Exception as e:
            print(f"❌ 处理模板 {template_file} 失败: {str(e)}")

    if copied_files > 0:
        print(f"✅ 模板{project_type}工程 {project_name} 创建完成！")
        print(f"📁 工程路径：{project_path}")
        print(f"📊 共创建 {copied_files} 个文件")
    else:
        print(f"\n⚠️  未创建任何文件，可能是缺少模板文件或模板路径配置错误")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sycommon",
        description="sycommon 工具集 - 项目初始化工具",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="子命令（当前支持：init）"
    )

    init_parser = subparsers.add_parser(
        "init",
        help="创建Web/Agent类型项目模板",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="示例:\n"
               "  sycommon init web   my_project  # 创建Web类型项目\n"
               "  sycommon init agent my_project  # 创建AI Agent类型项目"
    )
    init_parser.add_argument(
        "project_type",
        choices=["web", "agent"],
        help="项目类型：web - Web服务项目；agent - AI Agent服务项目"
    )
    init_parser.add_argument(
        "project_name",
        help="工程名称（如 my_web_project，将创建同名根目录）"
    )

    try:
        args = parser.parse_args()
        if args.command == "init":
            init_project(args.project_name, args.project_type)
    except argparse.ArgumentError as e:
        print(f"❌ 错误：{e}\n")
        print(
            f"请使用 {parser.prog} {args.command if 'args' in locals() else ''} -h 查看帮助")
    except SystemExit:
        pass


if __name__ == "__main__":
    # uv pip install -e .
    # sycommon init web my_project
    main()
