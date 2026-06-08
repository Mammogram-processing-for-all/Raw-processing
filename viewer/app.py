import sys
from pathlib import Path
from time import perf_counter

import numpy as np
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QImage, QPixmap, QTransform
from PySide6.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

# 엔진 import. `pip install -e ../engine` 로 설치되어 있으면 그대로 import 되고,
# 설치 전(개발 중)이면 엔진 디렉터리를 경로에 추가하는 폴백을 사용한다.
try:
    from main import DEFAULT_PARAMS, PIPELINE_STEPS, basic_pipeline
except ModuleNotFoundError:
    ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"
    if str(ENGINE_DIR) not in sys.path:
        sys.path.insert(0, str(ENGINE_DIR))
    from main import DEFAULT_PARAMS, PIPELINE_STEPS, basic_pipeline  # noqa: E402

DEFAULT_HEIGHT = 3816
DEFAULT_WIDTH = 3048
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "0"


# 파라미터 UI 정의: (key, 라벨, 최소, 최대, 소수자릿수)
# key 는 엔진의 DEFAULT_PARAMS 와 일치하며, 그룹은 파이프라인 단계 기준으로 묶는다.
PARAM_GROUPS: list[tuple[str, list[tuple[str, str, float, float, int]]]] = [
    (
        "Log Inversion",
        [
            ("clip_percent", "Highlight Clip (%)", 80.0, 100.0, 0),
            ("alpha", "Contrast (α)", 1.0, 30.0, 0),
            ("beta", "Midpoint (%)", 5.0, 95.0, 0),
        ],
    ),
    (
        "Denoise",
        [
            ("denoise_sigma", "Denoise Strength", 0.0, 3.0, 2),
        ],
    ),
    (
        "Local Contrast (CLAHE)",
        [
            ("clahe_clip", "Contrast Limit", 1.0, 10.0, 1),
            ("clahe_tile", "Tile Size", 4.0, 32.0, 0),
        ],
    ),
    (
        "Background",
        [
            ("bg_thresh", "Removal Threshold", 0.0, 50.0, 0),
        ],
    ),
    (
        "Edge",
        [
            ("edge_strength", "Edge Enhancement", 0.0, 2.0, 2),
        ],
    ),
]


class ParameterRow(QWidget):
    """슬라이더 + 스핀박스로 실수 파라미터 하나를 조정하는 행."""

    SLIDER_RES = 1000

    def __init__(
        self,
        label: str,
        minimum: float,
        maximum: float,
        value: float,
        decimals: int,
    ) -> None:
        super().__init__()
        self._min = minimum
        self._max = maximum
        self._guard = False

        self.spin = QDoubleSpinBox()
        self.spin.setDecimals(decimals)
        self.spin.setRange(minimum, maximum)
        self.spin.setSingleStep(10 ** -decimals if decimals else 1)
        self.spin.setValue(value)
        self.spin.setFixedWidth(72)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, self.SLIDER_RES)
        self.slider.setValue(self._to_slider(value))

        self.slider.valueChanged.connect(self._on_slider)
        self.spin.valueChanged.connect(self._on_spin)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(label))

        row = QHBoxLayout()
        row.addWidget(self.slider)
        row.addWidget(self.spin)
        layout.addLayout(row)

    def _to_slider(self, value: float) -> int:
        frac = (value - self._min) / (self._max - self._min)
        return round(frac * self.SLIDER_RES)

    def _to_value(self, slider: int) -> float:
        return self._min + (slider / self.SLIDER_RES) * (self._max - self._min)

    def _on_slider(self, slider: int) -> None:
        if self._guard:
            return
        self._guard = True
        self.spin.setValue(self._to_value(slider))
        self._guard = False

    def _on_spin(self, value: float) -> None:
        if self._guard:
            return
        self._guard = True
        self.slider.setValue(self._to_slider(value))
        self._guard = False

    def value(self) -> float:
        return self.spin.value()


class SizeGroup(QGroupBox):
    def __init__(self) -> None:
        super().__init__("Raw size")

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 65535)
        self.height_spin.setValue(DEFAULT_HEIGHT)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 65535)
        self.width_spin.setValue(DEFAULT_WIDTH)

        form = QFormLayout(self)
        form.addRow("Height", self.height_spin)
        form.addRow("Width", self.width_spin)


class ParameterPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        self.size_group = SizeGroup()
        layout.addWidget(self.size_group)

        # PARAM_GROUPS 정의에 따라 파라미터 그룹/행을 생성하고 key 로 보관
        self.rows: dict[str, ParameterRow] = {}
        for title, specs in PARAM_GROUPS:
            box = QGroupBox(title)
            box_layout = QVBoxLayout(box)
            for key, label, minimum, maximum, decimals in specs:
                row = ParameterRow(
                    label, minimum, maximum, DEFAULT_PARAMS[key], decimals
                )
                self.rows[key] = row
                box_layout.addWidget(row)
            layout.addWidget(box)

        layout.addStretch()

        self.process_button = QPushButton("Process")
        layout.addWidget(self.process_button)

        # 처리 소요 시간 표시 (Process 버튼 아래)
        self.time_label = QLabel("")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

    def values(self) -> dict[str, float]:
        """현재 파라미터 값을 엔진 파라미터 딕셔너리 형태로 반환."""
        return {key: row.value() for key, row in self.rows.items()}


class TransformPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        self.rotate_button = QPushButton("Rotate 90° CW")
        self.flip_h_button = QPushButton("Flip Horizontal")
        self.flip_v_button = QPushButton("Flip Vertical")

        layout.addWidget(self.rotate_button)
        layout.addWidget(self.flip_h_button)
        layout.addWidget(self.flip_v_button)
        layout.addStretch()


class ImageView(QLabel):
    def __init__(self) -> None:
        super().__init__()
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: white;")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(1, 1)
        self._source: QPixmap | None = None

    def set_source(self, pixmap: QPixmap) -> None:
        self._source = pixmap
        self._rescale()

    def _apply_transform(self, transform: QTransform) -> None:
        if self._source is None:
            return
        self._source = self._source.transformed(transform, Qt.SmoothTransformation)
        self._rescale()

    def rotate_cw(self) -> None:
        self._apply_transform(QTransform().rotate(90))

    def flip_horizontal(self) -> None:
        self._apply_transform(QTransform().scale(-1, 1))

    def flip_vertical(self) -> None:
        self._apply_transform(QTransform().scale(1, -1))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rescale()

    def _rescale(self) -> None:
        if self._source is None:
            return
        scaled = self._source.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        super().setPixmap(scaled)


class PipelineWorker(QObject):
    """백그라운드 스레드에서 파이프라인을 실행하는 워커."""

    progress = Signal(int, int, str)
    finished = Signal(object, float)
    failed = Signal(str)

    def __init__(self, raw_array: np.ndarray, params: dict[str, float]) -> None:
        super().__init__()
        self._raw = raw_array
        self._params = params

    def run(self) -> None:
        try:
            start = perf_counter()
            result = basic_pipeline(
                self._raw,
                self._params,
                progress=lambda i, total, label: self.progress.emit(i, total, label),
            )
            self.finished.emit(result, perf_counter() - start)
        except Exception as exc:  # noqa: BLE001 — UI 로 오류 전달
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Viewer")
        self.resize(1024, 768)

        self._raw_array: np.ndarray | None = None
        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None
        self._progress: QProgressDialog | None = None

        file_menu = self.menuBar().addMenu("File")
        load_action = QAction("Load", self)
        load_action.triggered.connect(self._on_load)
        file_menu.addAction(load_action)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.panel = ParameterPanel()
        self.image_view = ImageView()
        self.transform_panel = TransformPanel()

        root.addWidget(self.panel, 4)
        root.addWidget(self.image_view, 10)
        root.addWidget(self.transform_panel, 2)

        self.panel.process_button.clicked.connect(self._process)
        self.transform_panel.rotate_button.clicked.connect(self.image_view.rotate_cw)
        self.transform_panel.flip_h_button.clicked.connect(
            self.image_view.flip_horizontal
        )
        self.transform_panel.flip_v_button.clicked.connect(
            self.image_view.flip_vertical
        )

        self.setCentralWidget(central)

    # ----- 파일 로드 -----
    def _on_load(self) -> None:
        start_dir = str(DEFAULT_DATA_DIR) if DEFAULT_DATA_DIR.exists() else ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load raw image",
            start_dir,
            "Raw files (*.raw);;All files (*)",
        )
        if not path:
            return

        height = self.panel.size_group.height_spin.value()
        width = self.panel.size_group.width_spin.value()

        try:
            self._raw_array = self._read_raw_array(Path(path), height, width)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Load failed", str(exc))
            return

        # 로드 직후 기본 파라미터로 자동 처리
        self._process()

    @staticmethod
    def _read_raw_array(path: Path, height: int, width: int) -> np.ndarray:
        expected = height * width * 2
        raw_bytes = path.read_bytes()
        if len(raw_bytes) < expected:
            raise ValueError(
                f"File size {len(raw_bytes)} smaller than {height}x{width}x2 = {expected}"
            )
        return (
            np.frombuffer(raw_bytes[:expected], dtype=np.uint16)
            .reshape(height, width)
            .copy()
        )

    # ----- 처리 실행 -----
    def _process(self) -> None:
        if self._raw_array is None or self._thread is not None:
            return

        params = self.panel.values()
        self.panel.process_button.setEnabled(False)

        self._progress = QProgressDialog(
            "Processing...", None, 0, len(PIPELINE_STEPS), self
        )
        self._progress.setWindowTitle("Processing")
        self._progress.setWindowModality(Qt.WindowModal)
        self._progress.setCancelButton(None)  # 취소 버튼 제거
        self._progress.setMinimumDuration(0)
        self._progress.setAutoClose(False)
        self._progress.setAutoReset(False)
        self._progress.setValue(0)
        self._progress.show()

        self._thread = QThread()
        self._worker = PipelineWorker(self._raw_array, params)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._thread.start()

    def _on_progress(self, step: int, total: int, label: str) -> None:
        if self._progress is None:
            return
        self._progress.setMaximum(total)
        self._progress.setValue(step)
        self._progress.setLabelText(f"{label} ({step}/{total})")

    def _on_finished(self, result: np.ndarray, elapsed: float) -> None:
        self.image_view.set_source(self._to_pixmap(result))
        self.panel.time_label.setText(f"처리 시간: {elapsed:.2f} s")
        self._teardown_processing()

    def _on_failed(self, message: str) -> None:
        self._teardown_processing()
        QMessageBox.critical(self, "Processing failed", message)

    def _teardown_processing(self) -> None:
        if self._progress is not None:
            self._progress.close()
            self._progress = None
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait()
            self._worker = None
            self._thread = None
        self.panel.process_button.setEnabled(True)

    @staticmethod
    def _to_pixmap(arr: np.ndarray) -> QPixmap:
        arr = np.ascontiguousarray(arr.astype(np.uint8))
        height, width = arr.shape
        image = QImage(
            arr.data, width, height, width, QImage.Format_Grayscale8
        ).copy()
        return QPixmap.fromImage(image)


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
