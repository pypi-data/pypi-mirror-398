import os
import shutil

class FileOper:
    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.PREFIX = "│  "
        self.BRANCH = "├─"
        self.LAST_BRANCH = "└─"

        # 树状图符号定义
        self.BRANCH = "├─"  # 非最后一项分支
        self.LAST_BRANCH = "└─"  # 最后一项分支
        self.VERTICAL = "│  "  # 有子项的竖线
        self.BLANK = "   "  # 无子项的空白占位
        self.DIR_ICON = "📂 "  # 目录图标
        self.FILE_ICON = "📄 "  # 文件图标

    def list_dir(self):
        try:
            dir_contents = os.listdir(self.dir_path)
            for item in dir_contents:
                item_path = os.path.join(self.dir_path, item)
                if os.path.isdir(item_path):
                    print(f"  [目录] {item}")
                else:
                    print(f"  [文件] {item}")
        except FileNotFoundError:
            print(f"错误：目录 {self.dir_path} 不存在")
        except PermissionError:
            print(f"错误：没有权限访问目录 {self.dir_path}")

    def del_dir(self):
        try:
            shutil.rmtree(self.dir_path)
        except FileNotFoundError:
            print(f"错误：目录 {self.dir_path} 不存在")
        except PermissionError:
            print(f"错误：没有权限访问目录 {self.dir_path}")
        except Exception as e:
            print(f"删除 {self.dir_path} 失败，错误信息: {e}")

    def del_file(self):
        try:
            os.remove(self.dir_path)
        except FileNotFoundError:
            print(f"错误：文件 {self.dir_path} 不存在")
        except PermissionError:
            print(f"错误：没有权限访问文件 {self.dir_path}")
        except Exception as e:
            print(f"删除 {self.dir_path} 失败，错误信息: {e}")
            return self

    def del_file_or_dir(self):
        if os.path.isdir(self.dir_path):
            print(f"路径 {self.dir_path} 是目录，开始删除...")
            self.del_dir()
        elif os.path.isfile(self.dir_path):
            print(f"路径 {self.dir_path} 是文件，开始删除...")
            self.del_file()
        else:
            print(f"路径 {self.dir_path} 既不是目录也不是文件")

    def mkdir(self):
        try:
            os.makedirs(self.dir_path)
            print(f"成功创建单层目录: {self.dir_path}")
        except FileExistsError:
            print(f"目录已存在: {self.dir_path}, 尝试删除后重新创建")
            self.del_dir()
            self.mkdir()
        except FileNotFoundError:
            print(f"上级目录不存在，请使用 os.makedirs 创建多级目录")
        except PermissionError:
            print(f"没有权限创建目录: {self.dir_path}")

    def curr_file_dir(self):
        try:
            curr_dir = os.getcwd()
            print(f"当前工作目录：{curr_dir}")
        except Exception as e:
            print(f"获取当前工作目录失败，错误信息: {e}")



    def print_subdirs(self):
        try:
            # 获取根目录的绝对路径，用于计算层级
            root_abs = os.path.abspath(self.dir_path)
            # 打印根目录
            print(f"[{os.path.basename(root_abs)}]")
            # 遍历目录树
            for root, dirs, _ in os.walk(root_abs):
                # 计算当前目录的层级（根目录层级为0）
                level = root.replace(root_abs, "").count(os.sep)
                # 生成层级缩进
                indent = self.PREFIX * (level - 1) if level > 0 else ""
                # 遍历当前目录下的子目录
                for idx, dir_name in enumerate(dirs):
                    # 判断是否是当前目录下的最后一个子目录
                    is_last = idx == len(dirs) - 1
                    branch = self.LAST_BRANCH if is_last else self.BRANCH
                    # 拼接并打印树状结构
                    print(f"{indent}{branch} {dir_name}")
        except Exception as e:
            print(f"打印所有下游目录失败，错误信息: {e}")

    def _get_indent(self, level_marks):
        """根据层级标记生成缩进"""
        return "".join([self.VERTICAL if mark else self.BLANK for mark in level_marks])

    def print_tree(self):
        try:
            root_abs = os.path.abspath(self.dir_path)
            root_name = os.path.basename(root_abs)
            print(f"{self.DIR_ICON}{root_name}")

            # 递归遍历目录树（改用递归，更精准控制层级标记）
            def _recursive_walk(current_path, parent_level_marks, is_last):
                # 获取当前路径下的所有目录和文件，分开排序
                entries = sorted(os.scandir(current_path), key=lambda e: (not e.is_dir(), e.name))
                dirs = [e for e in entries if e.is_dir()]
                files = [e for e in entries if e.is_file()]
                all_items = dirs + files

                for idx, item in enumerate(all_items):
                    # 判断当前项是否为同级最后一项
                    item_is_last = idx == len(all_items) - 1
                    # 生成当前项的层级标记：父级标记 + 当前是否非最后一项（用于子项缩进）
                    current_level_marks = parent_level_marks + [not item_is_last]
                    # 生成缩进
                    indent = self._get_indent(current_level_marks[:-1])
                    # 选择分支符号
                    branch = self.LAST_BRANCH if item_is_last else self.BRANCH

                    if item.is_dir():
                        # 打印目录
                        print(f"{indent}{branch}{self.DIR_ICON}{item.name}")
                        # 递归遍历子目录
                        _recursive_walk(item.path, current_level_marks, item_is_last)
                    else:
                        # 打印文件
                        print(f"{indent}{branch}{self.FILE_ICON}{item.name}")

            # 启动递归：根目录的子项，父级标记为空，是否最后一项为True（不影响根目录）
            _recursive_walk(root_abs, [], True)

        except PermissionError:
            print(f"权限不足，无法访问目录: {self.dir_path}")
        except FileNotFoundError:
            print(f"目录不存在: {self.dir_path}")
        except Exception as e:
            print(f"打印目录树失败，错误信息: {e}")