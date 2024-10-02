import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, \
    QCheckBox, QLineEdit, QFileDialog, QMessageBox, QTabWidget, QGridLayout, QComboBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from functools import partial

# 模拟OCR识别结果
ocr_result = """大般若波羅蜜多經卷第一二天
大唐三藏聖教序太宗文皇帝製
盖聞二儀有像顯覆載以含生四時
無形潜寒暑以化物是以窺天鑑地
庸愚皆識其端眀隂洞陽贒哲罕窮
其數然而天地苞乎隂陽而易識者
以其有像也隂陽䖏乎天地而難窮"""

# 将OCR结果按行分割
lines = ocr_result.splitlines()

# 存储每个汉字的注释状态和备注，包括新加的属性
annotation_states = {}

# 全局变量存储选中的汉字索引
selected_char_index = 0
selected_line_index = 0

# 全局变量存储图片路径
uploaded_image_path = ""

class OCRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR识别与文字校对工具")

        # 主窗口布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 创建选项卡
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # 分栏1：上传图片并进行OCR识别
        self.tab1 = QWidget()
        self.tab_widget.addTab(self.tab1, "上传与OCR识别")
        self.tab1_layout = QVBoxLayout(self.tab1)

        self.upload_button = QPushButton("上传图片")
        self.upload_button.clicked.connect(self.upload_image)
        self.tab1_layout.addWidget(self.upload_button)

        # 分栏1：用于显示上传的图片，使用水平布局居中显示
        self.image_layout_tab1 = QHBoxLayout()  # 创建水平布局
        self.image_layout_tab1.setAlignment(Qt.AlignCenter)  # 设置居中对齐

        self.image_label_tab1 = QLabel()
        self.image_label_tab1.setFixedSize(300, 300)
        self.image_layout_tab1.addWidget(self.image_label_tab1)  # 将图片标签添加到水平布局

        self.tab1_layout.addLayout(self.image_layout_tab1)  # 将水平布局添加到分栏1的布局中

        # 路径选择编辑框
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择保存路径")
        self.tab1_layout.addWidget(self.path_input)

        self.path_button = QPushButton("选择路径")
        self.path_button.clicked.connect(self.select_path)
        self.tab1_layout.addWidget(self.path_button)

        # OCR引擎选择
        self.ocr_engine_label = QLabel("选择OCR识别引擎：")
        self.tab1_layout.addWidget(self.ocr_engine_label)

        # 下拉选择框：选择OCR引擎
        self.ocr_engine_combo = QComboBox()
        self.ocr_engine_combo.addItems(["引擎1", "引擎2", "引擎3"])
        self.tab1_layout.addWidget(self.ocr_engine_combo)

        # 进行OCR识别按钮
        self.perform_ocr_button = QPushButton("执行OCR识别")
        self.perform_ocr_button.clicked.connect(self.perform_ocr)
        self.tab1_layout.addWidget(self.perform_ocr_button)

        self.tab1.setLayout(self.tab1_layout)

        # 分栏2：OCR结果与校对
        self.tab2 = QWidget()
        self.tab_widget.addTab(self.tab2, "校对")
        self.tab2_layout = QGridLayout(self.tab2)

        # 左上角：显示上传的图片
        self.image_label_tab2 = QLabel()
        self.image_label_tab2.setFixedSize(200, 200)
        self.image_label_tab2.setAlignment(Qt.AlignCenter)
        self.tab2_layout.addWidget(self.image_label_tab2, 0, 0)

        # 右上角：显示OCR识别的汉字
        self.char_grid = QGridLayout()
        self.tab2_layout.addLayout(self.char_grid, 0, 1)

        # 左下角：当前选中的字符大框图
        self.current_char_display = QLabel("")
        self.current_char_display.setStyleSheet("font-size: 48px;")
        self.current_char_display.setFixedSize(200, 100)
        self.current_char_display.setAlignment(Qt.AlignCenter)
        self.tab2_layout.addWidget(self.current_char_display, 1, 0)

        # 右下角：注释与文字选项
        self.annotation_frame = QVBoxLayout()
        self.tab2_layout.addLayout(self.annotation_frame, 1, 1)

        self.annotation_label = QLabel("注释选项：")
        self.annotation_frame.addWidget(self.annotation_label)

        self.uncertain_checkbox = QCheckBox("不确定字符")
        self.annotation_frame.addWidget(self.uncertain_checkbox)

        self.strokes_checkbox = QCheckBox("笔画残缺")
        self.annotation_frame.addWidget(self.strokes_checkbox)

        self.variant_checkbox = QCheckBox("异体字")
        self.annotation_frame.addWidget(self.variant_checkbox)

        # 额外备注
        self.notes_label = QLabel("额外备注：")
        self.annotation_frame.addWidget(self.notes_label)

        # 创建备注编辑框，使用 setPlaceholderText 设置占位符
        self.notes_entry = QLineEdit()  # 创建空的 QLineEdit
        self.notes_entry.setPlaceholderText("备注，如果有的话")  # 设置占位符
        self.annotation_frame.addWidget(self.notes_entry)

        # 文字选项
        self.text_label = QLabel("文字选项：")
        self.annotation_frame.addWidget(self.text_label)

        self.text_frame = QHBoxLayout()
        self.annotation_frame.addLayout(self.text_frame)

        # 初始文字（锁定，不能被修改）
        self.initial_text_label = QLabel("初始文字")
        self.text_frame.addWidget(self.initial_text_label)

        # 编辑框，可以修改的文字
        self.current_text_entry = QLineEdit()
        self.current_text_entry.textChanged.connect(self.update_current_text_content)
        self.text_frame.addWidget(self.current_text_entry)

        # 保存按钮
        self.save_button = QPushButton("保存结果")
        self.save_button.clicked.connect(self.save_results)
        self.annotation_frame.addWidget(self.save_button)

        # 初始状态：隐藏汉字区域
        self.hide_character_grid()

        # 用于存储按钮对象以便更新按钮文字
        self.char_buttons = {}

    def hide_character_grid(self):
        """隐藏汉字区域"""
        for i in reversed(range(self.char_grid.count())):
            widget_to_remove = self.char_grid.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.hide()

    def show_character_grid(self):
        """显示汉字区域"""
        for i in range(self.char_grid.count()):
            widget = self.char_grid.itemAt(i).widget()
            if widget is not None:
                widget.show()

    def create_character_widgets(self):
        """创建汉字按钮"""
        for line_index, line in enumerate(lines):
            for index, char in enumerate(line):
                # 初始化每个字符的状态，char_value 为 OCR 识别得到的初始值
                annotation_states[(line_index, index)] = {
                    "char_value": char,  # 新增属性：char_value 存储当前字符的值
                    "uncertain": False,
                    "strokes": False,
                    "variant": False,
                    "note": ""
                }

                # 创建按钮，显示初始的 OCR 识别值
                char_button = QPushButton(char)
                char_button.setFixedSize(30, 30)

                # 使用 functools.partial 确保每个按钮传递独立的索引参数
                char_button.clicked.connect(partial(self.on_char_click, index, line_index))
                self.char_grid.addWidget(char_button, line_index, index)

                # 存储按钮对象
                self.char_buttons[(line_index, index)] = char_button

    def upload_image(self):
        global uploaded_image_path
        file_path, _ = QFileDialog.getOpenFileName(self, "上传图片", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            pixmap = QPixmap(file_path)

            # 在分栏1中显示图片
            self.image_label_tab1.setPixmap(pixmap.scaled(self.image_label_tab1.size(), Qt.KeepAspectRatio))

            # 在分栏2中也显示图片
            self.image_label_tab2.setPixmap(pixmap.scaled(self.image_label_tab2.size(), Qt.KeepAspectRatio))

            uploaded_image_path = file_path  # 保存上传的图片路径
            QMessageBox.information(self, "图片上传", f"已上传 {file_path}")

    def select_path(self):
        directory = QFileDialog.getExistingDirectory(self, "选择保存路径", "")
        if directory:
            self.path_input.setText(directory)

    def perform_ocr(self):
        """OCR识别后显示汉字"""
        selected_engine = self.ocr_engine_combo.currentText()
        QMessageBox.information(self, "OCR识别", f"OCR识别已执行，使用的引擎是：{selected_engine}")
        self.create_character_widgets()
        self.show_character_grid()

    def save_results(self):
        # 获取保存路径
        save_directory = self.path_input.text().strip()

        if not save_directory:
            # 如果没有选择路径，则使用图片的路径
            save_directory = os.path.dirname(uploaded_image_path)

        # 获取图片文件名
        image_filename = os.path.basename(uploaded_image_path)
        image_name_without_extension = os.path.splitext(image_filename)[0]

        # 保存文件的路径
        save_path = os.path.join(save_directory, f"{image_name_without_extension}_校正结果.txt")

        # 将每个按钮的文字按行排列保存到文件中
        with open(save_path, "w", encoding="utf-8") as f:
            for line_index, line in enumerate(lines):
                line_result = ''.join(
                    annotation_states[(line_index, index)]["char_value"] for index in range(len(line))
                )
                f.write(line_result + "\n")

        QMessageBox.information(self, "保存", f"结果已成功保存到 {save_path}")

    def update_annotation_state(self):
        global selected_char_index, selected_line_index
        # 更新当前字符的注释状态和文字选项（char_value）
        annotation_states[(selected_line_index, selected_char_index)] = {
            "uncertain": self.uncertain_checkbox.isChecked(),
            "strokes": self.strokes_checkbox.isChecked(),
            "variant": self.variant_checkbox.isChecked(),
            "note": self.notes_entry.text(),
            "char_value": self.current_text_entry.text()  # 更新 char_value
        }

    def on_char_click(self, index, line_index):
        global selected_char_index, selected_line_index

        # 先保存上一个字符的状态，确保保存的是上一个按钮的内容
        if (selected_line_index, selected_char_index) in annotation_states:
            self.update_annotation_state()

        # 再更新当前选择的字符索引
        selected_char_index = index
        selected_line_index = line_index

        # 更新当前字符显示
        current_char = annotation_states[(line_index, index)]["char_value"]
        self.current_char_display.setText(current_char)

        # 锁定显示初始文字
        self.initial_text_label.setText(lines[line_index][index])

        # 获取当前字符的注释状态
        state = annotation_states.get((line_index, index), {})

        # 恢复保存的注释状态和备注
        self.uncertain_checkbox.setChecked(state.get("uncertain", False))
        self.strokes_checkbox.setChecked(state.get("strokes", False))
        self.variant_checkbox.setChecked(state.get("variant", False))
        self.notes_entry.setText(state.get("note", ""))

        # 恢复保存的文字选项（char_value）
        self.current_text_entry.setText(state.get("char_value", current_char))

    def update_current_text_content(self):
        global selected_char_index, selected_line_index
        if (selected_line_index, selected_char_index) in annotation_states:
            # 实时保存当前字符的修改，更新 char_value
            annotation_states[(selected_line_index, selected_char_index)]["char_value"] = self.current_text_entry.text()

            # 更新按钮显示的文字为修改后的文字
            self.char_buttons[(selected_line_index, selected_char_index)].setText(self.current_text_entry.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ocr_app = OCRApp()
    ocr_app.show()
    sys.exit(app.exec_())
