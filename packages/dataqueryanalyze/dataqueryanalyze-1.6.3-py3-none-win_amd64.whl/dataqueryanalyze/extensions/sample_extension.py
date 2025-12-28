# 示例扩展文件

# 扩展基本信息
MENU_NAME = "示例扩展"
VERSION = "1.0.0"
DESCRIPTION = "示例扩展，展示扩展功能的使用方法"
SERIAL = "sample-001"

# 扩展函数定义
EXTENSION_FUNCTIONS = {
    "process_data": {
        "name": "数据处理示例",
        "description": "对数据进行简单处理"
    },
    "filter_data": {
        "name": "数据筛选示例",
        "description": "筛选数据示例"
    },
    "gui_example": {
        "name": "GUI操作示例",
        "description": "带有图形界面的数据操作"
    },
    "pivot_example": {
        "name": "透视示例",
        "description": "基于3个字段的分组透视（count）"
    }
}

# 导入必要的库
import polars as pl
from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox, QHeaderView
from PySide6.QtCore import Qt


def process_data(data):
    """
    数据处理示例函数
    
    Args:
        data: 输入数据（Polars DataFrame）
        
    Returns:
        处理后的数据（Polars DataFrame）
    """
    # 这里可以添加任意数据处理逻辑
    # 示例：添加一个新列
    result = data.with_columns(
        (pl.col(pl.Int64) + 100).name.suffix("_plus_100")
    )
    return result


def filter_data(data):
    """
    数据筛选示例函数
    
    Args:
        data: 输入数据（Polars DataFrame）
        
    Returns:
        筛选后的数据（Polars DataFrame）
    """
    # 示例：筛选数值列大于100的数据
    result = data
    for col in data.columns:
        if data[col].dtype in [pl.Int64, pl.Float64]:
            result = result.filter(pl.col(col) > 100)
    return result


def gui_example(data):
    """
    GUI操作示例函数
    
    Args:
        data: 输入数据（Polars DataFrame）
        
    Returns:
        处理后的数据（Polars DataFrame）
    """
    # 创建一个对话框用于显示和操作数据
    class DataEditDialog(QDialog):
        def __init__(self, data, parent=None):
            super().__init__(parent)
            self.original_data = data
            self.modified_data = data
            self.setWindowTitle("数据编辑界面")
            self.setGeometry(100, 100, 1000, 600)
            self.init_ui()
        
        def init_ui(self):
            # 创建主布局
            main_layout = QVBoxLayout(self)
            
            # 创建表格
            self.table_widget = QTableWidget()
            self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
            self.table_widget.setSelectionMode(QTableWidget.MultiSelection)
            
            # 设置表头自适应
            header = self.table_widget.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeToContents)
            header.setStretchLastSection(True)
            
            # 填充表格数据
            self.fill_table()
            
            # 创建按钮布局
            button_layout = QHBoxLayout()
            
            # 删除选中行按钮
            self.delete_btn = QPushButton("删除选中行")
            self.delete_btn.clicked.connect(self.delete_selected_rows)
            button_layout.addWidget(self.delete_btn)
            
            # 取消按钮
            self.cancel_btn = QPushButton("取消")
            self.cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(self.cancel_btn)
            
            # 确定按钮
            self.ok_btn = QPushButton("确定")
            self.ok_btn.clicked.connect(self.accept)
            button_layout.addWidget(self.ok_btn)
            
            # 将组件添加到主布局
            main_layout.addWidget(self.table_widget)
            main_layout.addLayout(button_layout)
        
        def fill_table(self):
            """填充表格数据"""
            # 获取数据列名和行数
            columns = self.original_data.columns
            rows = len(self.original_data)
            
            # 设置表格行列数
            self.table_widget.setColumnCount(len(columns))
            self.table_widget.setRowCount(rows)
            
            # 设置列名
            self.table_widget.setHorizontalHeaderLabels(columns)
            
            # 填充数据
            for row in range(rows):
                for col in range(len(columns)):
                    value = self.original_data[row, columns[col]]
                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table_widget.setItem(row, col, item)
        
        def delete_selected_rows(self):
            """删除选中的行"""
            selected_rows = set()
            # 获取所有选中的行
            for item in self.table_widget.selectedItems():
                selected_rows.add(item.row())
            
            if not selected_rows:
                QMessageBox.warning(self, "警告", "请先选择要删除的行")
                return
            
            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 行吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 将选中的行转换为列表并排序（从大到小，避免删除行后索引变化）
                sorted_rows = sorted(selected_rows, reverse=True)
                
                # 更新表格显示
                for row in sorted_rows:
                    self.table_widget.removeRow(row)
                
                # 更新修改后的数据
                remaining_indices = [i for i in range(len(self.original_data)) if i not in selected_rows]
                self.modified_data = self.original_data[remaining_indices]
        
        def get_modified_data(self):
            """获取修改后的数据"""
            return self.modified_data
    
    # 创建并显示对话框
    dialog = DataEditDialog(data)
    if dialog.exec() == QDialog.Accepted:
        # 如果用户点击确定，返回修改后的数据
        return dialog.get_modified_data()
    else:
        # 如果用户点击取消，返回None，不创建新选项卡
        return None


def pivot_example(data):
    """
    透视示例函数，带有3个下拉选择框的GUI界面，用于基于选择的字段进行分组透视（count）
    
    Args:
        data: 输入数据（Polars DataFrame）
        
    Returns:
        处理后的数据（Polars DataFrame），包含一个特殊属性selected_cols用于双击溯源
    """
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel, QMessageBox
    from PySide6.QtCore import Qt
    
    # 创建透视对话框
    class PivotDialog(QDialog):
        def __init__(self, data, parent=None):
            super().__init__(parent)
            self.data = data
            self.columns = data.columns
            self.selected_columns = [None, None, None]
            
            self.setWindowTitle("透视示例")
            self.setGeometry(300, 300, 600, 200)
            self.setStyleSheet("""
                QDialog {
                    background-color: #333333;
                    color: white;
                }
                QLabel {
                    color: white;
                    font-weight: bold;
                }
                QComboBox {
                    background-color: #444444;
                    color: white;
                    border: 1px solid #555555;
                    padding: 5px;
                    border-radius: 4px;
                }
                QComboBox::drop-down {
                    background-color: #555555;
                    border: none;
                    border-radius: 0 4px 4px 0;
                }
                QComboBox QAbstractItemView {
                    background-color: #444444;
                    color: white;
                    border: 1px solid #555555;
                }
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            
            self.init_ui()
        
        def init_ui(self):
            """初始化UI界面"""
            # 创建主布局
            main_layout = QVBoxLayout(self)
            
            # 创建选择区域
            select_layout = QVBoxLayout()
            
            # 创建3个下拉选择框
            self.combos = []
            for i in range(3):
                row_layout = QHBoxLayout()
                
                # 标签
                label = QLabel(f"选择字段 {i+1}:")
                label.setFixedWidth(100)
                row_layout.addWidget(label)
                
                # 下拉选择框
                combo = QComboBox()
                combo.addItem("请选择字段")
                for col in self.columns:
                    combo.addItem(col)
                combo.currentIndexChanged.connect(lambda idx, i=i: self.on_combo_changed(idx, i))
                self.combos.append(combo)
                row_layout.addWidget(combo)
                
                select_layout.addLayout(row_layout)
            
            # 创建按钮布局
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            # 取消按钮
            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(cancel_btn)
            
            # 确定按钮
            ok_btn = QPushButton("确定")
            ok_btn.clicked.connect(self.accept)
            button_layout.addWidget(ok_btn)
            
            # 将组件添加到主布局
            main_layout.addLayout(select_layout)
            main_layout.addLayout(button_layout)
        
        def on_combo_changed(self, idx, combo_index):
            """下拉选择框变化事件处理"""
            if idx > 0:
                self.selected_columns[combo_index] = self.columns[idx - 1]
            else:
                self.selected_columns[combo_index] = None
        
        def get_selected_columns(self):
            """获取选择的字段"""
            # 过滤掉None值
            return [col for col in self.selected_columns if col is not None]
    
    # 创建并显示对话框
    dialog = PivotDialog(data)
    if dialog.exec() == QDialog.Accepted:
        selected_cols = dialog.get_selected_columns()
        
        if len(selected_cols) < 1:
            QMessageBox.warning(None, "警告", "请至少选择一个字段进行透视")
            return None
        
        try:
            # 执行透视操作
            result = data.group_by(selected_cols).agg(pl.len().alias("count"))
            
            # 为结果添加selected_cols属性，用于双击溯源
            # 这样主程序就知道只使用这些列进行双击筛选
            result.selected_cols = selected_cols
            
            # 确保新选项卡能双击溯源，返回结果时添加溯源信息
            return result
        except Exception as e:
            QMessageBox.critical(None, "错误", f"透视操作失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    else:
        # 如果用户点击取消，返回None，不创建新选项卡
        return None