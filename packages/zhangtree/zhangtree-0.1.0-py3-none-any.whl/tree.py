#!/usr/bin/env python3

# tree.py - 跨平台 tree 命令，仅显示名称



import os

import sys

import argparse

from datetime import datetime

from pathlib import Path



class TreeGenerator:

    def __init__(self, args):

        self.args = args

        self.exclude_dirs = set(args.exclude_dir) if args.exclude_dir else set()

        # 始终排除 __pycache__ 目录

        self.exclude_dirs.add('__pycache__')

        self.exclude_dirs.add('docs')

        self.exclude_dirs.add('node_modules')

        self.exclude_exts = set(args.exclude_ext) if args.exclude_ext else set()

        # 新增: 排除具体文件

        self.exclude_files = set(args.exclude_file) if args.exclude_file else set()

        self.exclude_files.add('tree.py')

        self.exclude_files.add('diff.md')

        self.exclude_files.add('uv.lock')

        self.output_lines = []



    def format_size(self, size_bytes):

        """格式化文件大小"""

        if size_bytes == 0:

            return "0 B"



        units = ['B', 'KB', 'MB', 'GB', 'TB']

        size = float(size_bytes)

        for unit in units:

            if size < 1024.0 or unit == units[-1]:

                return f"{size:.1f} {unit}"

            size /= 1024.0

        return f"{size:.1f} PB"



    def should_exclude(self, path):

        """检查是否应该排除"""

        name = path.name



        # 检查显式排除 __pycache__ 目录

        if path.is_dir() and name == "__pycache__":

            return True



        # 检查隐藏文件

        if not self.args.all and name.startswith('.'):

            return True



        # 检查排除目录

        if path.is_dir() and name in self.exclude_dirs:

            return True



        # 检查排除扩展名

        if path.is_file():

            ext = path.suffix.lower()

            if ext in self.exclude_exts:

                return True



        # 检查排除具体文件

        if path.is_file() and name in self.exclude_files:

            return True



        return False



    def generate_tree(self, path, prefix="", is_last=True, depth=0):

        """生成目录树"""

        if depth >= self.args.level:

            return



        try:

            # 获取目录内容并排序

            items = []

            for item in path.iterdir():

                if not self.should_exclude(item):

                    items.append(item)



            # 排序：目录在前，文件在后

            items.sort(key=lambda x: (x.is_file(), x.name.lower()))



            for i, item in enumerate(items):

                is_current_last = (i == len(items) - 1)

                connector = "└── " if is_current_last else "├── "



                # 构建显示文本

                if item.is_dir():

                    display = f"{item.name}/"

                    if self.args.dir_only:

                        self.output_lines.append(f"{prefix}{connector}{display}")

                        new_prefix = prefix + ("    " if is_current_last else "│   ")

                        self.generate_tree(item, new_prefix, is_current_last, depth + 1)

                    elif not self.args.dir_only:

                        self.output_lines.append(f"{prefix}{connector}{display}")

                        new_prefix = prefix + ("    " if is_current_last else "│   ")

                        self.generate_tree(item, new_prefix, is_current_last, depth + 1)

                else:

                    if not self.args.dir_only:

                        display = f"{item.name}"

                        if self.args.size:

                            size = item.stat().st_size

                            display += f" ({self.format_size(size)})"

                        if self.args.time:

                            mtime = datetime.fromtimestamp(item.stat().st_mtime)

                            display += f" [{mtime.strftime('%Y-%m-%d %H:%M')}]"

                        self.output_lines.append(f"{prefix}{connector}{display}")



        except PermissionError:

            self.output_lines.append(f"{prefix}└── [权限不足]")

        except Exception as e:

            if self.args.verbose:

                self.output_lines.append(f"{prefix}└── [错误: {e}]")



    def run(self):

        """运行 tree 生成"""

        path = Path(self.args.path).resolve()



        if not path.exists():

            print(f"错误: 路径不存在 - {path}")

            return 1



        # 输出标题

        title = f"目录结构: {path}"

        self.output_lines.append(title)

        self.output_lines.append("=" * len(title))



        # 添加根目录

        if path.is_dir():

            self.output_lines.append(f"{path.name}/")

            self.generate_tree(path, "", True, 0)

        else:

            # 如果是文件，直接显示

            self.output_lines.append(f"{path.name}")



        # 输出结果

        if self.args.output:

            with open(self.args.output, 'w', encoding='utf-8') as f:

                f.write("\n".join(self.output_lines))

            print(f"OK 已保存到: {self.args.output}")

        else:

            for line in self.output_lines:

                print(line)



        # 统计信息

        if self.args.stats:

            print("\n" + "=" * 40)

            print("统计信息:")

            print(f"总行数: {len(self.output_lines) - 2}")



        return 0



def main():

    parser = argparse.ArgumentParser(

        description="增强版 tree 命令 - 类似 Linux 的 tree。此版本只显示名称，不显示任何图标。",

        formatter_class=argparse.RawDescriptionHelpFormatter,

        epilog="""

示例:

  tree                        显示当前目录结构

  tree C:\\Users              显示指定目录

  tree -L 2                  限制深度为2层

  tree -o tree.txt          保存到文件

  tree -s -t                显示大小和修改时间

  tree -d                   只显示目录

  tree -a                   显示隐藏文件

  tree --exclude-dir .git node_modules  排除指定目录

  tree --exclude-file foo.py bar.txt    排除指定文件

  tree --unicode            （已无效，仅保持接口一致）

        """

    )



    parser.add_argument("path", nargs="?", default=".", help="目标目录路径")

    parser.add_argument("-L", "--level", type=int, default=99, help="显示深度限制")

    parser.add_argument("-d", "--dir-only", action="store_true", help="只显示目录")

    parser.add_argument("-a", "--all", action="store_true", help="显示隐藏文件")

    parser.add_argument("-s", "--size", action="store_true", help="显示文件大小")

    parser.add_argument("-t", "--time", action="store_true", help="显示修改时间")

    parser.add_argument("-o", "--output", help="输出到文件")

    parser.add_argument("--stats", action="store_true", help="显示统计信息")

    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")

    parser.add_argument("--exclude-dir", action="append", help="排除目录(可多次使用)")

    parser.add_argument("--exclude-ext", action="append", help="排除扩展名(可多次使用)")

    parser.add_argument("--exclude-file", action="append", help="排除文件(可多次使用)")

    parser.add_argument("--unicode", action="store_true", help="（已无效，仅保持接口一致）")



    args = parser.parse_args()



    generator = TreeGenerator(args)

    return generator.run()



if __name__ == "__main__":

    sys.exit(main())

