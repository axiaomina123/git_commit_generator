from typing import Dict, List, Tuple
from questionary import checkbox

class FileSelector:
    """文件选择器类，用于处理文件选择相关的功能"""
    
    @staticmethod
    def build_file_tree(files: List[str]) -> Dict:
        """将文件列表构建成树形结构
        
        Args:
            files: 文件路径列表
            
        Returns:
            dict: 树形结构的字典
        """
        tree = {}
        for file_path in files:
            parts = file_path.replace('\\', '/').split('/')
            current = tree
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # 文件
                    current[part] = file_path
                else:  # 目录
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        return tree
    
    @staticmethod
    def flatten_tree(tree: Dict, prefix: str = "", result: Dict = {}, choices: List = []) -> Tuple[Dict, List]:
        """将树形结构扁平化为questionary可用的选项列表
        
        Args:
            tree: 树形结构字典
            prefix: 当前路径前缀
            result: 存储文件路径与选项的映射关系
            choices: 存储选项列表
            
        Returns:
            tuple: (result, choices) 文件路径映射和选项列表
        """
        if result is None:
            result = {}
        if choices is None:
            choices = []
            
        for key, value in sorted(tree.items(), key=lambda x: (isinstance(x[1], dict), x[0])):
            if isinstance(value, dict):  # 目录
                dir_path = f"{prefix}{key}/"
                dir_choice = {
                    "name": f"📁 {dir_path}",
                    "value": dir_path,
                    "checked": True  # 默认选中所有目录
                }
                choices.append(dir_choice)
                result[dir_path] = {
                    "is_dir": True,
                    "choice": dir_choice,
                    "files": []
                }
                # 递归处理子目录和文件
                FileSelector.flatten_tree(value, f"{prefix}{key}/", result, choices)
            else:  # 文件
                file_choice = {
                    "name": f"   📄 {key}",
                    "value": value,
                    "checked": True  # 默认选中所有文件
                }
                choices.append(file_choice)
                result[value] = {
                    "is_dir": False,
                    "choice": file_choice
                }
                # 将文件添加到其所在目录的files列表中
                if prefix in result:
                    result[prefix]["files"].append(value)
        return result, choices
    
    @staticmethod
    def on_checkbox_select(selected_values: List[str], file_map: Dict) -> List[str]:
        """实现级联选择功能，当选择或取消某个文件夹时，其下所有文件执行相同操作
        
        Args:
            selected_values: 当前选中的值列表
            file_map: 文件路径映射关系
            
        Returns:
            list: 更新后的选中值列表
        """
        # 创建一个新的选中值列表，避免修改原始列表
        updated_selection = selected_values.copy()
        
        # 处理目录选择状态变化
        for dir_path, dir_info in file_map.items():
            if not dir_info["is_dir"]:
                continue
                
            # 检查目录是否在选中列表中
            dir_selected = dir_path in updated_selection
            
            # 获取该目录下的所有文件和子目录
            child_files = []
            child_dirs = []
            
            for path, info in file_map.items():
                # 检查是否为当前目录的子项
                if path != dir_path and path.startswith(dir_path):
                    if info["is_dir"]:
                        child_dirs.append(path)
                    else:
                        child_files.append(path)
            
            # 更新子文件的选择状态
            for file_path in dir_info["files"]:
                if file_path in file_map and not file_map[file_path]["is_dir"]:
                    file_choice = file_map[file_path]["choice"]
                    
                    # 根据目录选择状态更新文件选择状态
                    if dir_selected and file_path not in updated_selection:
                        updated_selection.append(file_path)
                        file_choice["checked"] = True
                    elif not dir_selected and file_path in updated_selection:
                        updated_selection.remove(file_path)
                        file_choice["checked"] = False
            
            # 更新子目录的选择状态
            for child_dir in child_dirs:
                dir_choice = file_map[child_dir]["choice"]
                
                # 根据父目录选择状态更新子目录选择状态
                if dir_selected and child_dir not in updated_selection:
                    updated_selection.append(child_dir)
                    dir_choice["checked"] = True
                elif not dir_selected and child_dir in updated_selection:
                    updated_selection.remove(child_dir)
                    dir_choice["checked"] = False
        
        return updated_selection