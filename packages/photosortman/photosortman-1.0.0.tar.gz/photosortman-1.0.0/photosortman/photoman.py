#!/usr/bin/env python3
"""
Photosortman - Aplikasi desktop untuk mensortir foto ke kategori
Best, Standard, dan Bad dengan keyboard shortcuts dan game controller.
"""

import sys
import os
import shutil
import subprocess
import multiprocessing
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QStatusBar, QMessageBox,
    QScrollArea, QGridLayout, QProgressBar, QCheckBox, QGroupBox,
    QSpinBox, QDialog
)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QUrl, QTimer, QSettings
from PyQt6.QtGui import QPixmap, QKeySequence, QShortcut, QImage
from PyQt6.QtMultimedia import QSoundEffect

# Import controller remap dialog
from .controller_remap_dialog import ControllerRemapDialog

# Import pygame for game controller support
try:
    import pygame
    PYGAME_AVAILABLE = True
    from .controller_remap_dialog import ControllerRemapDialog
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available. Game controller support disabled.")

# Import pillow for HEIC support
from PIL import Image
import pillow_heif

# Import OpenCV for blur detection
import cv2
import numpy as np

# Import CuPy for GPU acceleration (optional)
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False
    cp = None

# Import quality analysis modules
from .quality_analysis import CPUAnalyzer, GPUAnalyzer, QualityMetrics

# Cyberpunk color scheme - Neon & Dark
CYBERPUNK_COLORS = {
    # Neon accents
    'neon_cyan': '#00f0ff',
    'neon_magenta': '#ff00ff',
    'neon_purple': '#b026ff',
    'neon_pink': '#ff006e',
    'neon_green': '#39ff14',
    
    # Dark backgrounds
    'bg_darkest': '#0a0a0f',
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#1f2937',
    
    # Text
    'text': '#e0e0ff',
    'text_muted': '#8b8baa',
    
    # Glows (for box-shadow)
    'glow_cyan': 'rgba(0, 240, 255, 0.5)',
    'glow_magenta': 'rgba(255, 0, 255, 0.5)',
    'glow_purple': 'rgba(176, 38, 255, 0.5)',
    'glow_green': 'rgba(57, 255, 20, 0.5)',
}

# Alias for backward compatibility
MODERN_COLORS = {
    'primary': CYBERPUNK_COLORS['neon_cyan'],
    'primary_hover': CYBERPUNK_COLORS['neon_purple'],
    'secondary': CYBERPUNK_COLORS['neon_magenta'],
    'success': CYBERPUNK_COLORS['neon_green'],
    'danger': CYBERPUNK_COLORS['neon_pink'],
    'bg_dark': CYBERPUNK_COLORS['bg_darkest'],
    'bg_medium': CYBERPUNK_COLORS['bg_dark'],
    'bg_light': CYBERPUNK_COLORS['bg_medium'],
    'text': CYBERPUNK_COLORS['text'],
    'text_muted': CYBERPUNK_COLORS['text_muted'],
}

# Casual/Professional color scheme - Monochrome with colored quality indicators
CASUAL_COLORS = {
    # All UI colors are gray/white (monochrome)
    'neon_cyan': '#e6e6e6',      # Gray for UI
    'neon_magenta': '#e6e6e6',   # Gray for UI
    'neon_purple': '#e6e6e6',    # Gray for UI
    'neon_pink': '#e6e6e6',      # Gray for UI
    'neon_green': '#e6e6e6',     # Gray for UI
    # Dark backgrounds (same as cyberpunk)
    'bg_darkest': '#0a0a0f',
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#1f2937',
    # Text - white/gray only
    'text': '#e0e0ff',
    'text_muted': '#8b8baa',
    # No glows in casual theme
    'glow_cyan': 'rgba(136, 136, 136, 0.2)',
    'glow_magenta': 'rgba(136, 136, 136, 0.2)',
    'glow_purple': 'rgba(136, 136, 136, 0.2)',
    'glow_green': 'rgba(136, 136, 136, 0.2)',
}

# Quality indicator colors (used only for photo borders)
QUALITY_COLORS = {
    'best': '#4CAF50',      # Green
    'standard': '#9C27B0',  # Purple
    'bad': '#E91E63',       # Pink
}

# Default controller mapping (optimized for Xbox controllers)
# NOTE: PS controllers use different axis indices for triggers:
#   - PS: LT=axis 3, RT=axis 4
#   - Xbox: LT=axis 2, RT=axis 5
# Use the "Remap Controller" feature to customize for your controller
DEFAULT_CONTROLLER_MAPPING = {
    # Navigation
    'nav_prev': ('trigger', 2),      # Left Trigger (Xbox: axis 2, PS: use axis 3)
    'nav_next': ('trigger', 5),      # Right Trigger (Xbox: axis 5, PS: use axis 4)
    # Categorization
    'cat_best': ('button', 0),       # Button A
    'cat_bad': ('button', 1),        # Button B
    'cat_standard': ('button', 2),   # Button X
    # Actions
    'action_folder': ('button', 3),  # Button Y
    'action_analysis': ('button', 7), # Start
    'toggle_sound': ('button', 6),   # Select
    # LB combos
    'lb_cpu_dec': ('hat_combo', ('lb', 0, 1)),      # LB + D-Pad Up
    'lb_cpu_inc': ('hat_combo', ('lb', 0, -1)),     # LB + D-Pad Down
    'lb_sound': ('hat_combo', ('lb', -1, 0)),       # LB + D-Pad Left
    'lb_gpu': ('hat_combo', ('lb', 1, 0)),          # LB + D-Pad Right
    # RB combos
    'rb_copy': ('hat_combo', ('rb', 0, 1)),         # RB + D-Pad Up
    'rb_theme': ('hat_combo', ('rb', 0, -1)),       # RB + D-Pad Down
    'rb_remap': ('hat_combo', ('rb', -1, 0)),       # RB + D-Pad Left
    'rb_about': ('hat_combo', ('rb', 1, 0)),        # RB + D-Pad Right
    'rb_reconnect': ('button_combo', ('rb', 3)),    # RB + Y (default)
    'rb_close_dialog': ('button_combo', ('rb', 1)), # RB + B (system combo)
    # D-Pad navigation (no modifier)
    'dpad_nav_up': ('hat', (0, 1)),
    'dpad_nav_down': ('hat', (0, -1)),
    'dpad_nav_left': ('hat', (-1, 0)),
    'dpad_nav_right': ('hat', (1, 0)),
}

# Current theme (will be updated based on settings)
CURRENT_COLORS = CYBERPUNK_COLORS.copy()


class QualityAnalyzer(QThread):
    """Thread untuk analisis kualitas komprehensif pada semua foto"""
    progress_update = pyqtSignal(int, int)  # current, total
    analysis_complete = pyqtSignal(str)  # result message
    quality_result = pyqtSignal(int, dict, str)  # index, metrics_dict, recommendation
    
    def __init__(self, photos, output_file, cpu_workers=1, use_gpu=False):
        super().__init__()
        self.photos = photos
        self.output_file = output_file
        self.cpu_workers = cpu_workers
        self.use_gpu = use_gpu
        self.stop_requested = False  # Flag for stop button
        
    def run(self):
        """Analyze quality for all photos"""
        results = []
        
        if self.cpu_workers > 1 and not self.use_gpu:
            # Use multiprocessing for parallel analysis
            results = self.analyze_parallel()
        else:
            # Sequential analysis (single CPU or GPU)
            results = self.analyze_sequential()
        
        # Save results to file
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write("Nama File; Blur (%); Exposure (%); Contrast (%); Noise (%); Saturation (%); Overall (%); Rekomendasi\n")
                for name, metrics, rec in results:
                    if metrics:
                        f.write(f"{name}; {metrics.get('blur', 0)}%; {metrics.get('exposure', 0)}%; "
                               f"{metrics.get('contrast', 0)}%; {metrics.get('noise', 0)}%; "
                               f"{metrics.get('saturation', 0)}%; {metrics.get('overall', 0)}%; {rec}\n")
                    else:
                        f.write(f"{name}; Error; Error; Error; Error; Error; Error; Error\n")
            
            self.analysis_complete.emit(f"Analisis selesai! {len(results)} foto dianalisis.\nHasil disimpan di: {self.output_file}")
        except Exception as e:
            self.analysis_complete.emit(f"Error menyimpan hasil: {str(e)}")
    
    def analyze_sequential(self):
        """Analyze photos sequentially (single thread)"""
        results = []
        
        for idx, photo_path in enumerate(self.photos):
            # Check if stop requested
            if self.stop_requested:
                print("Analysis stopped by user")
                break
            
            try:
                # Load image
                img = self.load_image(photo_path)
                if img is None:
                    results.append((photo_path.name, {}, "Error"))
                    continue
                
                # Calculate all metrics
                metrics = self.analyze_single_image(img)
                
                # Generate recommendation
                recommendation = self.get_recommendation(metrics['overall'], metrics)
                
                results.append((photo_path.name, metrics, recommendation))
                self.quality_result.emit(idx, metrics, recommendation)
                self.progress_update.emit(idx + 1, len(self.photos))
                
            except Exception as e:
                print(f"Error analyzing {photo_path}: {e}")
                results.append((photo_path.name, {}, "Error"))
        
        return results
    
    def analyze_parallel(self):
        """Analyze photos in parallel using multiprocessing"""
        from multiprocessing import Pool
        import functools
        
        results = []
        
        # Create a pool of workers
        with Pool(processes=self.cpu_workers) as pool:
            # Map analyze_photo_worker to all photos
            # The worker function needs to be a top-level function for pickling
            photo_data = [(idx, str(photo)) for idx, photo in enumerate(self.photos)]
            
            # Process in chunks and emit progress
            chunk_size = max(1, len(self.photos) // (self.cpu_workers * 4))
            for idx, result in enumerate(pool.imap(analyze_photo_worker, photo_data, chunksize=chunk_size)):
                photo_idx, name, metrics, recommendation = result
                results.append((name, metrics, recommendation))
                
                if metrics:
                    self.quality_result.emit(photo_idx, metrics, recommendation)
                
                self.progress_update.emit(idx + 1, len(self.photos))
        
        return results
    
    def analyze_single_image(self, img):
        """Analyze a single image and return all metrics"""
        # Use GPU if enabled and available
        if self.use_gpu and GPUAnalyzer.is_available():
            try:
                return GPUAnalyzer.analyze_image(img)
            except Exception as e:
                print(f"GPU analysis failed, falling back to CPU: {e}")
        
        # CPU analysis
        return CPUAnalyzer.analyze_image(img)
    
    def get_recommendation(self, overall_score, metrics):
        """Get recommendation based on overall score and metrics"""
        return QualityMetrics.get_recommendation(overall_score, metrics)
    
    def load_image(self, image_path):
        """Load image with OpenCV"""
        try:
            img = cv2.imread(str(image_path))
            if img is None:
                # Fallback for HEIC and other formats
                pil_img = Image.open(str(image_path))
                pil_img = pil_img.convert('RGB')
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return img
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            return None
    
    def analyze_blur(self, img):
        """Analyze blur using Laplacian variance (0% = sharp, 100% = blurry)"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Convert to blur percentage (inverted)
            if laplacian_var > 200:
                blur_percent = 0
            elif laplacian_var < 10:
                blur_percent = 100
            else:
                blur_percent = max(0, min(100, int(100 - (laplacian_var / 200) * 100)))
            
            return blur_percent
        except:
            return 50
    
    def analyze_exposure(self, img):
        """Analyze exposure/brightness (0% = bad, 100% = good)"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calculate mean brightness (0-255)
            mean_brightness = np.mean(gray)
            
            # Check for overexposure and underexposure
            overexposed = np.sum(gray > 250) / gray.size
            underexposed = np.sum(gray < 5) / gray.size
            
            # Ideal brightness is around 110-145 (middle-bright)
            # Penalize overexposure and underexposure
            if mean_brightness < 50:  # Too dark
                exposure_score = mean_brightness / 50 * 50
            elif mean_brightness > 200:  # Too bright
                exposure_score = (255 - mean_brightness) / 55 * 50
            else:  # Good range
                # Best at 127, scale to 100%
                distance_from_ideal = abs(mean_brightness - 127)
                exposure_score = max(50, 100 - (distance_from_ideal / 127 * 50))
            
            # Penalize heavy clipping
            if overexposed > 0.1 or underexposed > 0.1:
                exposure_score *= 0.7
            
            return int(max(0, min(100, exposure_score)))
        except:
            return 50
    
    def analyze_contrast(self, img):
        """Analyze contrast (0% = low contrast, 100% = good contrast)"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Calculate standard deviation (measure of contrast)
            std_dev = np.std(gray)
            
            # Good contrast typically has std > 40
            # Low contrast has std < 20
            if std_dev > 60:
                contrast_score = 100
            elif std_dev < 15:
                contrast_score = 0
            else:
                contrast_score = int((std_dev / 60) * 100)
            
            return max(0, min(100, contrast_score))
        except:
            return 50
    
    def analyze_noise(self, img):
        """Analyze noise level (0% = clean, 100% = noisy)"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Use high-frequency analysis to detect noise
            # Apply Gaussian blur and subtract from original
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            noise = cv2.absdiff(gray, blurred)
            
            # Calculate noise level
            noise_level = np.mean(noise)
            
            # Typical range: clean < 5, noisy > 15
            if noise_level < 3:
                noise_percent = 0
            elif noise_level > 20:
                noise_percent = 100
            else:
                noise_percent = int((noise_level / 20) * 100)
            
            return max(0, min(100, noise_percent))
        except:
            return 50
    
    def analyze_saturation(self, img):
        """Analyze color saturation (0% = desaturated, 100% = well saturated)"""
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Get saturation channel
            saturation = hsv[:, :, 1]
            
            # Calculate mean saturation
            mean_sat = np.mean(saturation)
            
            # Good saturation is around 80-150 (out of 255)
            # Too low = washed out, too high = oversaturated
            if mean_sat < 30:  # Very desaturated
                sat_score = (mean_sat / 30) * 30
            elif mean_sat > 180:  # Oversaturated
                sat_score = ((255 - mean_sat) / 75) * 30
            else:  # Good range
                # Best around 100-120
                distance_from_ideal = abs(mean_sat - 110)
                sat_score = max(30, 100 - (distance_from_ideal / 110 * 70))
            
            return int(max(0, min(100, sat_score)))
        except:
            return 50
    
    def calculate_overall_quality(self, metrics):
        """Calculate weighted overall quality score"""
        # Adjusted weights - blur is most critical
        weights = {
            'blur': 0.45,       # Increased from 0.35 - most important
            'exposure': 0.20,   # Reduced from 0.25
            'contrast': 0.15,   # Same
            'noise': 0.12,      # Reduced from 0.15
            'saturation': 0.08  # Reduced from 0.10
        }
        
        # Invert blur and noise (lower is better for these)
        blur_score = 100 - metrics.get('blur', 50)
        noise_score = 100 - metrics.get('noise', 50)
        
        overall = (
            blur_score * weights['blur'] +
            metrics.get('exposure', 50) * weights['exposure'] +
            metrics.get('contrast', 50) * weights['contrast'] +
            noise_score * weights['noise'] +
            metrics.get('saturation', 50) * weights['saturation']
        )
        
        return int(max(0, min(100, overall)))




# Global worker function for multiprocessing (must be at module level for pickling)
def analyze_photo_worker(photo_data):
    """Worker function to analyze a single photo (for multiprocessing)"""
    idx, photo_path = photo_data
    
    try:
        # Load image
        img = cv2.imread(photo_path)
        if img is None:
            # Fallback for HEIC and other formats
            from PIL import Image
            import pillow_heif
            pillow_heif.register_heif_opener()
            pil_img = Image.open(photo_path)
            pil_img = pil_img.convert('RGB')
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        if img is None:
            return (idx, Path(photo_path).name, {}, "Error")
        
        # Use CPU analyzer (multiprocessing already uses multiple cores)
        from .quality_analysis import CPUAnalyzer, QualityMetrics
        metrics = CPUAnalyzer.analyze_image(img)
        recommendation = QualityMetrics.get_recommendation(metrics['overall'], metrics)
        
        return (idx, Path(photo_path).name, metrics, recommendation)
        
    except Exception as e:
        print(f"Error in worker analyzing {photo_path}: {e}")
        return (idx, Path(photo_path).name, {}, "Error")


class ThumbnailLoader(QThread):
    """Thread untuk load thumbnails secara async"""
    thumbnail_loaded = pyqtSignal(int, QPixmap)
    
    def __init__(self, photos, thumbnail_size):
        super().__init__()
        self.photos = photos
        self.thumbnail_size = thumbnail_size
        
    def run(self):
        for idx, photo_path in enumerate(self.photos):
            try:
                pixmap = self.load_image(photo_path, self.thumbnail_size)
                if pixmap:
                    self.thumbnail_loaded.emit(idx, pixmap)
            except Exception as e:
                print(f"Error loading thumbnail {photo_path}: {e}")
    
    def load_image(self, path, size):
        """Load image with HEIC support"""
        try:
            # Try Qt first for common formats
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                return pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation)
            
            # If Qt fails, try Pillow (for HEIC)
            img = Image.open(str(path))
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            # Convert PIL Image to QPixmap
            img = img.convert('RGB')
            data = img.tobytes('raw', 'RGB')
            qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
            return QPixmap.fromImage(qimage)
            
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None


class ThumbnailWidget(QWidget):
    """Widget untuk menampilkan satu thumbnail"""
    clicked = pyqtSignal(int)
    
    def __init__(self, index, photo_path):
        super().__init__()
        self.index = index
        self.photo_path = photo_path
        self.is_selected = False
        
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(layout)
        
        # Thumbnail label
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(120, 120)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                border: 2px solid #34495e;
                
            }
        """)
        self.thumb_label.setText("...")
        layout.addWidget(self.thumb_label)
        
        
        # Filename label
        name_label = QLabel(photo_path.name[:15] + "..." if len(photo_path.name) > 15 else photo_path.name)
        name_label.setStyleSheet(f"""
            QLabel {{
                font-size: 10px;
                color: {CURRENT_COLORS['text_muted']};
                background-color: transparent;
                border: none;
                padding: 2px;
            }}
        """)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        self.setFixedSize(130, 150)
        
    def set_thumbnail(self, pixmap):
        """Set thumbnail image"""
        self.thumb_label.setPixmap(pixmap)
        
    def set_selected(self, selected):
        """Highlight selected thumbnail"""
        self.is_selected = selected
        if selected:
            self.thumb_label.setStyleSheet("""
                QLabel {
                    background-color: #2c3e50;
                    border: 3px solid #3498db;
                    
                }
            """)
        else:
            self.thumb_label.setStyleSheet("""
                QLabel {
                    background-color: #2c3e50;
                    border: 2px solid #34495e;
                    
                }
            """)
    
    def mousePressEvent(self, event):
        """Handle click"""
        self.clicked.emit(self.index)


class PhotoSorterApp(QMainWindow):
    """Main application window untuk Photosortman"""
    
    def __init__(self):
        super().__init__()
        self.photos = []  # List of photo file paths
        self.current_index = 0
        self.source_folder = None
        self.categories = ['Best', 'Standard', 'Bad']
        self.thumbnail_widgets = []
        
        # Initialize settings FIRST before loading values
        self.settings = QSettings('Photosortman', 'PhotoSorter')
        self.use_cyberpunk_theme = self.settings.value('theme/cyberpunk', True, type=bool)
        
        # Load settings from QSettings
        self.use_copy = self.settings.value('processing/copy_mode', True, type=bool)
        self.quality_data = {}  # Store quality analysis results {index: (metrics, recommendation)}
        
        # Performance settings
        self.use_gpu = False
        # CPU workers for parallel processing (load from settings)
        self.cpu_workers = self.settings.value('processing/cpu_workers', multiprocessing.cpu_count(), type=int)
        self.sound_enabled = self.settings.value('sound/enabled', True, type=bool)
        
        # Supported image extensions (including HEIC)
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif'}
        
        # Register HEIC opener
        pillow_heif.register_heif_opener()
        
        # Load controller mapping
        self.controller_mapping = self.load_controller_mapping()
        
        # Apply theme
        global CURRENT_COLORS
        if self.use_cyberpunk_theme:
            CURRENT_COLORS = CYBERPUNK_COLORS.copy()
        else:
            CURRENT_COLORS = CASUAL_COLORS.copy()
        
        # Initialize sound effects
        self.sounds = {}
        resources_dir = Path(__file__).parent / 'assets' / 'resources'
        
        sound_files = {
            'best': resources_dir / 'best.wav',
            'standard': resources_dir / 'standar.wav',
            'bad': resources_dir / 'bad.wav',
            'select': resources_dir / 'select.wav'
        }
        
        for name, path in sound_files.items():
            if path.exists():
                sound = QSoundEffect()
                sound.setSource(QUrl.fromLocalFile(str(path)))
                sound.setVolume(0.5)  # 50% volume
                self.sounds[name] = sound
        
        self.init_ui()
        self.setup_shortcuts()
        
        # Initialize game controller (after UI is ready)
        self.controller = None
        self.controller_name = None
        self.last_trigger_left = 0
        self.last_trigger_right = 0
        # Button state tracking for debounce
        self.last_button_states = {}
        self.dialog_in_progress = False  # Prevent multiple dialog calls
        if PYGAME_AVAILABLE:
            self.init_controller()
            # Initialize controller polling
        if self.controller:
            self.controller_timer = QTimer()
            self.controller_timer.timeout.connect(self.poll_controller)
            self.controller_timer.start(16)  # ~60 FPS
        
        # Load last folder if it exists (after UI is initialized)
        last_folder = self.settings.value('folder/last_path', '', type=str)
        if last_folder and Path(last_folder).exists():
            self.source_folder = Path(last_folder)
            # Update folder info label
            folder_name = self.source_folder.name
            folder_path_str = str(self.source_folder)
            if len(folder_path_str) > 40:
                folder_path_str = '...' + folder_path_str[-37:]
            self.folder_info_label.setText(f'{folder_name}\n{folder_path_str}')
            # Auto-load photos from last folder
            self.load_photos()
        
    def get_border_style(self, element_type='panel', color_key='neon_cyan'):
        """Get border style based on current theme"""
        if self.use_cyberpunk_theme:
            # Cyberpunk: thick, colorful borders
            if element_type == 'panel':
                return f"""
                    border-left: 5px solid {CURRENT_COLORS[color_key]};
                    border-right: 2px solid {CURRENT_COLORS[color_key]};
                    border-top: 2px solid {CURRENT_COLORS[color_key]};
                    border-bottom: 2px solid {CURRENT_COLORS[color_key]};
                """
            elif element_type == 'photo':
                return f"border: 3px solid {CURRENT_COLORS[color_key]};"
            else:
                return f"border: 2px solid {CURRENT_COLORS[color_key]};"
        else:
            # Casual: thin, monochrome (except photos)
            if element_type == 'photo':
                return f"border: 2px solid {CURRENT_COLORS[color_key]};"
            else:
                return f"border: 1px solid {CURRENT_COLORS['text_muted']};"
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('Photosortman')
        
        # Make window responsive to screen size
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # Account for title bar (~30px) and taskbar (~40-50px) = ~80px total
        # Set window size to 85% width, 75% height with larger buffer for small screens
        window_width = min(int(screen_width * 0.85), 1600)
        window_height = min(int(screen_height * 0.75) - 100, 850)  # More aggressive height reduction
        window_width = max(window_width, 950)
        window_height = max(window_height, 500)  # Lower minimum height
        
        # Center window on screen
        x = (screen_width - window_width) // 2
        y = max(10, (screen_height - window_height - 50) // 2)  # Leave more space for taskbar
        
        self.setGeometry(x, y, window_width, window_height)
        
        # Enable window resizing
        self.setMinimumSize(950, 500)  # Set minimum size but allow resize
        
        # Apply cyberpunk styling to main window
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {CURRENT_COLORS['bg_darkest']};
            }}
            QLabel {{
                color: {CURRENT_COLORS['text']};
                font-family: 'Rajdhani', 'Orbitron', 'Exo 2', 'Segoe UI', monospace;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QGroupBox {{
                background-color: {CURRENT_COLORS['bg_dark']};
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
                
                margin-top: 16px;
                padding: 20px;
                font-weight: 700;
                color: {CURRENT_COLORS['neon_cyan']};
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 12px;
                background-color: {CURRENT_COLORS['bg_darkest']};
            }}
        """)
        
        # Central widget
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {CURRENT_COLORS['bg_darkest']};")
        self.setCentralWidget(central_widget)
        
        # Main layout - 3 columns with spacing
        main_layout = QHBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        central_widget.setLayout(main_layout)
        
        # ========== LEFT PANEL: Thumbnails + Stats ==========
        left_panel_content = QWidget()
        left_panel_content.setStyleSheet(f"""
            QWidget {{
                background-color: {CURRENT_COLORS['bg_dark']};
                border-left: 5px solid {CURRENT_COLORS['neon_cyan']};
                border-right: 3px solid {CURRENT_COLORS['neon_cyan']};
                border-top: 2px solid {CURRENT_COLORS['neon_cyan']};
                border-bottom: 2px solid {CURRENT_COLORS['neon_cyan']};
                
            }}
        """)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(12, 12, 8, 12)  # Less right margin for scrollbar space
        left_layout.setSpacing(10)
        left_panel_content.setLayout(left_layout)
        
        # Set size policy to allow proper scrolling
        from PyQt6.QtWidgets import QSizePolicy
        left_panel_content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        # Wrap left panel in scroll area
        self.left_scroll_area = QScrollArea()
        self.left_scroll_area.setWidget(left_panel_content)
        self.left_scroll_area.setWidgetResizable(True)
        self.left_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.left_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.left_scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {CURRENT_COLORS['bg_dark']};
                padding-left: 5px;
            }}
            QScrollBar:vertical {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                width: 12px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {CURRENT_COLORS['neon_purple']};
                border: 1px solid {CURRENT_COLORS['bg_darkest']};
                border-radius: 5px;
                min-height: 20px;
                margin: 0px 2px;  /* Center in track */
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {CURRENT_COLORS['neon_magenta']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Panel header
        thumb_header = QLabel("/// PHOTO GRID ///")
        thumb_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_header.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 900;
                padding: 12px;
                color: {CURRENT_COLORS['neon_cyan']};
                background-color: {CURRENT_COLORS['bg_darkest']};
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
                
                letter-spacing: 3px;
                text-transform: uppercase;
            }}
        """)
        left_layout.addWidget(thumb_header)
        
        # Statistics section
        stats_container = QWidget()
        stats_container.setStyleSheet(f"""
            QWidget {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                border: 1px solid {CURRENT_COLORS['neon_cyan']};
                
                padding: 6px;
                border-radius: 5px;
            }}
        """)
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(6)
        stats_container.setLayout(stats_layout)
        
        self.total_photos_label = QLabel("TOTAL: 0")
        self.total_photos_label.setStyleSheet(f"""
            color: {CURRENT_COLORS['text']};
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 1px;
        """)
        
        self.best_count_label = QLabel("++ BEST: 0")
        self.best_count_label.setStyleSheet(f"""
            color: {CURRENT_COLORS['neon_green']};
            font-size: 12px;
            font-weight: 600;
        """)
        
        self.standard_count_label = QLabel(">> STANDARD: 0")
        self.standard_count_label.setStyleSheet(f"""
            color: {CURRENT_COLORS['neon_cyan']};
            font-size: 12px;
            font-weight: 600;
        """)
        
        self.bad_count_label = QLabel("<< BAD: 0")
        self.bad_count_label.setStyleSheet(f"""
            color: {CURRENT_COLORS['neon_magenta']};
            font-size: 12px;
            font-weight: 600;
        """)
        
        stats_layout.addWidget(self.total_photos_label)
        stats_layout.addWidget(self.best_count_label)
        stats_layout.addWidget(self.standard_count_label)
        stats_layout.addWidget(self.bad_count_label)
        
        left_layout.addWidget(stats_container)
        
        # Thumbnails scroll area
        self.thumbnail_scroll = QScrollArea()
        self.thumbnail_scroll.setWidgetResizable(True)
        self.thumbnail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumbnail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.thumbnail_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {CURRENT_COLORS['neon_purple']};
                border-radius: 4px;
                margin: 0px 2px;
                border: 1px solid {CURRENT_COLORS['bg_darkest']};
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {CURRENT_COLORS['neon_magenta']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        self.thumbnail_container = QWidget()
        self.thumbnail_container.setStyleSheet(f"background-color: {CURRENT_COLORS['bg_darkest']};")
        self.thumbnail_grid = QGridLayout()
        self.thumbnail_grid.setSpacing(8)
        self.thumbnail_container.setLayout(self.thumbnail_grid)
        self.thumbnail_scroll.setWidget(self.thumbnail_container)
        
        left_layout.addWidget(self.thumbnail_scroll)
        
        # Folder info and open button
        
        # Folder info and open button
        self.folder_info_label = QLabel('NO FOLDER')
        self.folder_info_label.setWordWrap(True)
        self.folder_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.folder_info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                color: {CURRENT_COLORS['text_muted']};
                border: 1px solid {CURRENT_COLORS['neon_cyan']};
                padding: 8px 12px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
        """)
        left_layout.addWidget(self.folder_info_label)
        
        
        # ========== CENTER PANEL: Photo Display ==========
        center_panel = QWidget()
        center_panel.setStyleSheet(f"""
            QWidget {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                border-left: 6px solid {CURRENT_COLORS['neon_magenta']};
                border-right: 6px solid {CURRENT_COLORS['neon_purple']};
                border-top: 3px solid {CURRENT_COLORS['neon_magenta']};
                border-bottom: 3px solid {CURRENT_COLORS['neon_purple']};
                
            }}
        """)
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(12, 12, 12, 12)
        center_layout.setSpacing(12)
        center_panel.setLayout(center_layout)
        
        # Panel header
        viewer_header = QLabel(">> VIEWER <<")
        viewer_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        viewer_header.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 900;
                padding: 12px;
                color: {CURRENT_COLORS['neon_magenta']};
                background-color: {CURRENT_COLORS['bg_dark']};
                border: 2px solid {CURRENT_COLORS['neon_magenta']};
                
                letter-spacing: 3px;
                text-transform: uppercase;
            }}
        """)
        center_layout.addWidget(viewer_header)
        
        # Image display area
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: #000;
                border: 2px solid {CURRENT_COLORS['neon_purple']};
                
                min-height: 500px;
                color: {CURRENT_COLORS['text_muted']};
                font-size: 16px;
            }}
        """)
        self.image_label.setText('PILIH FOLDER UNTUK MEMULAI')
        center_layout.addWidget(self.image_label, stretch=1)
        
        # File info label
        self.file_info_label = QLabel('BELUM ADA FOLDER DIPILIH')
        self.file_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_info_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {CURRENT_COLORS['neon_cyan']};
                background-color: {CURRENT_COLORS['bg_dark']};
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
                padding: 12px 16px;
                
                font-family: 'Rajdhani', 'Orbitron', monospace;
                font-weight: 600;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }}
        """)
        center_layout.addWidget(self.file_info_label)
        
        # Category buttons - horizontal layout
        category_layout = QHBoxLayout()
        category_layout.setSpacing(8)
        category_layout.setContentsMargins(0, 0, 0, 0)
        
        self.best_btn = self.create_category_button('++ BEST ++', CURRENT_COLORS['neon_green'], 0)
        self.standard_btn = self.create_category_button('>> STANDARD', CURRENT_COLORS['neon_cyan'], 1)
        self.bad_btn = self.create_category_button('<< BAD', CURRENT_COLORS['neon_magenta'], 2)
        
        category_layout.addWidget(self.best_btn)
        category_layout.addWidget(self.standard_btn)
        category_layout.addWidget(self.bad_btn)
        
        center_layout.addLayout(category_layout)
        
        # Folder action buttons
        folder_buttons_layout = QHBoxLayout()
        folder_buttons_layout.setSpacing(10)
        
        # Select folder button
        select_folder_btn = QPushButton('📁 SELECT FOLDER')
        select_folder_btn.clicked.connect(self.select_folder)
        select_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {CURRENT_COLORS['bg_dark']};
                color: {CURRENT_COLORS['neon_cyan']};
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 700;
                border-radius: 5px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {CURRENT_COLORS['neon_cyan']};
                color: #000;
            }}
        """)
        folder_buttons_layout.addWidget(select_folder_btn)
        
        # Open folder button
        self.open_folder_btn = QPushButton('📂 SHOW DIRECTORY')
        self.open_folder_btn.clicked.connect(self.open_in_file_manager)
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {CURRENT_COLORS['bg_dark']};
                color: {CURRENT_COLORS['neon_purple']};
                border: 2px solid {CURRENT_COLORS['neon_purple']};
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 700;
                border-radius: 5px;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {CURRENT_COLORS['neon_purple']};
                color: #000;
            }}
            QPushButton:disabled {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                color: {CURRENT_COLORS['text_muted']};
                border-color: {CURRENT_COLORS['bg_light']};
            }}
        """)
        folder_buttons_layout.addWidget(self.open_folder_btn)
        
        center_layout.addLayout(folder_buttons_layout)
        
        # Navigation hint
        nav_hint = QLabel('← PREV  |  → NEXT  |  1:BEST  2:STD  3:BAD')
        nav_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_hint.setStyleSheet(f"""
            QLabel {{
                color: {CURRENT_COLORS['text_muted']};
                font-size: 11px;
                padding: 8px;
                letter-spacing: 1px;
            }}
        """)
        center_layout.addWidget(nav_hint)
        
        # ========== RIGHT PANEL: Quality Info + Settings ==========
        right_panel_content = QWidget()
        right_panel_content.setStyleSheet(f"""
            QWidget {{
                background-color: {CURRENT_COLORS['bg_dark']};
                border-left: 3px solid {CURRENT_COLORS['neon_green']};
                border-top: 2px solid {CURRENT_COLORS['neon_green']};
                border-bottom: 2px solid {CURRENT_COLORS['neon_green']};
                border-right: 5px solid {CURRENT_COLORS['neon_green']};
                
            }}
        """)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(12, 12, 8, 12)  # Less right margin for scrollbar space
        right_layout.setSpacing(12)
        right_panel_content.setLayout(right_layout)
        
        # Set size policy to allow proper scrolling
        right_panel_content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        # Wrap right panel in scroll area
        self.right_scroll_area = QScrollArea()
        self.right_scroll_area.setWidget(right_panel_content)
        self.right_scroll_area.setWidgetResizable(True)
        self.right_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.right_scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {CURRENT_COLORS['bg_dark']};
                padding-left: 5px;
            }}
            QScrollBar:vertical {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                width: 12px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {CURRENT_COLORS['neon_purple']};
                border: 1px solid {CURRENT_COLORS['bg_darkest']};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {CURRENT_COLORS['neon_magenta']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        # Panel header
        analysis_header = QLabel("++ ANALYSIS ++")
        analysis_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        analysis_header.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: 900;
                padding: 12px;
                color: {CURRENT_COLORS['neon_green']};
                background-color: {CURRENT_COLORS['bg_darkest']};
                border: 2px solid {CURRENT_COLORS['neon_green']};
                
                letter-spacing: 3px;
                text-transform: uppercase;
            }}
        """)
        right_layout.addWidget(analysis_header)
        
        # Quality metrics display
        metrics_container = QWidget()
        metrics_container.setStyleSheet(f"""
            QWidget {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                border: 1px solid {CURRENT_COLORS['neon_green']};
                
                padding: 8px;
            }}
        """)
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(6)
        metrics_container.setLayout(metrics_layout)
        
        # Create metric displays (single line format)
        self.blur_label = self.create_metric_label(metrics_layout, "BLUR", CURRENT_COLORS['neon_pink'])
        self.exposure_label = self.create_metric_label(metrics_layout, "EXPOSURE", CURRENT_COLORS['neon_cyan'])
        self.contrast_label = self.create_metric_label(metrics_layout, "CONTRAST", CURRENT_COLORS['neon_purple'])
        self.noise_label = self.create_metric_label(metrics_layout, "NOISE", CURRENT_COLORS['neon_magenta'])
        self.saturation_label = self.create_metric_label(metrics_layout, "SATURATION", CURRENT_COLORS['neon_green'])
        
        # Separator line
        separator = QLabel()
        separator.setStyleSheet(f"""
            QLabel {{
                background-color: {CURRENT_COLORS['neon_cyan']};
                max-height: 2px;
                margin: 8px 0px;
            }}
        """)
        metrics_layout.addWidget(separator)
        
        # Overall score (larger display)
        overall_container = QWidget()
        overall_layout = QHBoxLayout()
        overall_layout.setContentsMargins(0, 0, 0, 0)
        overall_container.setLayout(overall_layout)
        
        overall_title = QLabel("OVERALL")
        overall_title.setStyleSheet(f"""
            color: {CURRENT_COLORS['neon_cyan']};
            font-weight: 900;
            font-size: 14px;
            letter-spacing: 2px;
        """)
        overall_layout.addWidget(overall_title)
        overall_layout.addStretch()
        
        self.overall_label = QLabel("0%")
        self.overall_label.setStyleSheet(f"""
            color: {CURRENT_COLORS['neon_cyan']};
            font-size: 20px;
            font-weight: 900;
            padding: 4px;
        """)
        overall_layout.addWidget(self.overall_label)
        
        metrics_layout.addWidget(overall_container)
        
        # Recommendation label
        self.recommendation_label = QLabel("NO DATA")
        self.recommendation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recommendation_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 900;
                padding: 10px;
                color: {CURRENT_COLORS['text_muted']};
                background-color: {CURRENT_COLORS['bg_dark']};
                border: 2px solid {CURRENT_COLORS['text_muted']};
                
                letter-spacing: 2px;
            }}
        """)
        metrics_layout.addWidget(self.recommendation_label)
        
        right_layout.addWidget(metrics_container)
        
        # Quality analysis button
        self.quality_btn = QPushButton('/// ANALISIS KUALITAS ///')
        self.quality_btn.clicked.connect(self.start_quality_analysis)
        self.quality_btn.setEnabled(False)
        self.quality_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #000;
                color: {CURRENT_COLORS['neon_green']};
                border: none;
                border-left: 6px solid {CURRENT_COLORS['neon_green']};
                border-right: 2px solid {CURRENT_COLORS['neon_cyan']};
                padding: 14px 20px;
                font-size: 13px;
                font-weight: 900;
                letter-spacing: 3px;
                text-transform: uppercase;
                font-family: 'Rajdhani', 'Orbitron', monospace;
            }}
            QPushButton:hover {{
                background-color: {CURRENT_COLORS['neon_green']};
                color: #000;
            }}
            QPushButton:disabled {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                color: {CURRENT_COLORS['text_muted']};
                border-left-color: {CURRENT_COLORS['bg_light']};
                border-right-color: {CURRENT_COLORS['bg_light']};
            }}
        """)
        right_layout.addWidget(self.quality_btn)
        
        # Stop button
        self.stop_btn = QPushButton('<< STOP >>')
        self.stop_btn.clicked.connect(self.stop_analysis)
        self.stop_btn.setVisible(False)
        self.stop_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #000;
                color: {CURRENT_COLORS['neon_pink']};
                border: none;
                border-left: 6px solid {CURRENT_COLORS['neon_pink']};
                border-right: 2px solid {CURRENT_COLORS['neon_magenta']};
                padding: 14px 20px;
                font-size: 13px;
                font-weight: 900;
                letter-spacing: 3px;
                text-transform: uppercase;
                font-family: 'Rajdhani', 'Orbitron', monospace;
            }}
            QPushButton:hover {{
                background-color: {CURRENT_COLORS['neon_pink']};
                color: #000;
            }}
        """)
        right_layout.addWidget(self.stop_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
                
                text-align: center;
                background-color: #000;
                color: {CURRENT_COLORS['neon_cyan']};
                font-weight: bold;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {CURRENT_COLORS['neon_cyan']};
                
            }}
        """)
        self.progress_bar.hide()
        right_layout.addWidget(self.progress_bar)
        
        
        # Settings panel (collapsible)
        self.settings_panel = QGroupBox("⚙️ PENGATURAN")
        settings_layout = QVBoxLayout()
        
        # CPU workers
        cpu_layout = QHBoxLayout()
        cpu_label = QLabel("CPU Workers:")
        cpu_label.setStyleSheet(f"color: {CURRENT_COLORS['text']}; padding: 4px;")
        cpu_layout.addWidget(cpu_label)
        
        self.cpu_workers_spin = QSpinBox()
        self.cpu_workers_spin.setMinimum(1)
        self.cpu_workers_spin.setMaximum(multiprocessing.cpu_count())
        self.cpu_workers_spin.setValue(self.cpu_workers)
        self.cpu_workers_spin.setToolTip(f"Jumlah CPU cores (Max: {multiprocessing.cpu_count()})")
        self.cpu_workers_spin.valueChanged.connect(self.on_cpu_workers_changed)
        self.cpu_workers_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                color: {CURRENT_COLORS['text']};
                border: 1px solid {CURRENT_COLORS['neon_cyan']};
                padding: 4px;
                
            }}
        """)
        cpu_layout.addWidget(self.cpu_workers_spin)
        cpu_layout.addStretch()
        settings_layout.addLayout(cpu_layout)
        
        # GPU checkbox
        self.gpu_checkbox = QCheckBox("Gunakan GPU (CUDA)")
        # Load GPU preference from settings
        use_gpu = self.settings.value('processing/use_gpu', False, type=bool)
        self.gpu_checkbox.setChecked(use_gpu if CUPY_AVAILABLE else False)
        
        if not CUPY_AVAILABLE:
            self.gpu_checkbox.setEnabled(False)
            self.gpu_checkbox.setToolTip("CUDA tidak tersedia")
        else:
            self.gpu_checkbox.setToolTip("Gunakan GPU NVIDIA untuk akselerasi")
        self.gpu_checkbox.stateChanged.connect(self.on_gpu_mode_changed)
        gpu_style = """
            QCheckBox {{
                color: {text_color};
                padding: 4px;
                font-weight: 600;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {purple};
                background-color: {bg_dark};
            }}
            QCheckBox::indicator:checked {{
                background-color: {purple};
                border: 2px solid {purple};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {green};
            }}
            QCheckBox::indicator:disabled {{
                border-color: {muted};
            }}
        """.format(
            text_color=CURRENT_COLORS.get('text', '#fff'),
            purple=CURRENT_COLORS.get('neon_purple', '#a855f7'),
            bg_dark=CURRENT_COLORS.get('bg_darkest', '#0a0a0a'),
            green=CURRENT_COLORS.get('neon_green', '#10b981'),
            muted=CURRENT_COLORS.get('text_muted', '#666')
        )
        self.gpu_checkbox.setStyleSheet(gpu_style)
        settings_layout.addWidget(self.gpu_checkbox)
        
        # Copy mode checkbox
        self.copy_checkbox = QCheckBox("Salin (bukan pindahkan)")
        self.copy_checkbox.setChecked(self.use_copy)  # Load from settings
        self.copy_checkbox.setToolTip("Salin file ke folder kategori (default: pindahkan)")
        self.copy_checkbox.stateChanged.connect(self.on_copy_mode_changed)
        self.copy_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {CURRENT_COLORS['text']};
                padding: 4px;
                font-weight: 600;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
                background-color: {CURRENT_COLORS['bg_darkest']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {CURRENT_COLORS['neon_cyan']};
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {CURRENT_COLORS['neon_green']};
            }}
        """)
        settings_layout.addWidget(self.copy_checkbox)
        
        # Sound effects checkbox
        self.sound_checkbox = QCheckBox("Sound Effects")
        self.sound_checkbox.setChecked(self.sound_enabled)  # Load from settings
        self.sound_checkbox.stateChanged.connect(self.on_sound_mode_changed)
        self.sound_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {CURRENT_COLORS['text']};
                padding: 4px;
                font-weight: 600;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {CURRENT_COLORS['neon_green']};
                background-color: {CURRENT_COLORS['bg_darkest']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {CURRENT_COLORS['neon_green']};
                border: 2px solid {CURRENT_COLORS['neon_green']};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
            }}
        """)
        settings_layout.addWidget(self.sound_checkbox)
        
        # Theme toggle checkbox
        self.theme_checkbox = QCheckBox("Cyberpunk Theme")
        self.theme_checkbox.setChecked(self.use_cyberpunk_theme)
        self.theme_checkbox.stateChanged.connect(self.on_theme_changed)
        self.theme_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {CURRENT_COLORS['text']};
                padding: 4px;
                font-weight: 600;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {CURRENT_COLORS['neon_purple']};
                background-color: {CURRENT_COLORS['bg_darkest']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {CURRENT_COLORS['neon_purple']};
                border: 2px solid {CURRENT_COLORS['neon_purple']};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {CURRENT_COLORS['neon_cyan']};
            }}
        """)
        settings_layout.addWidget(self.theme_checkbox)
        
        # Controller status label
        controller_layout = QHBoxLayout()
        controller_layout.setSpacing(8)
        
        self.controller_status_label = QLabel('🎮 No Controller')
        self.controller_status_label.setStyleSheet(f"""
            QLabel {{
                color: {CURRENT_COLORS['text_muted']};
                font-size: 10px;
                padding: 4px;
                font-weight: 600;
            }}
        """)
        controller_layout.addWidget(self.controller_status_label, stretch=1)
        
        # Reconnect Controller button (50% width)
        if PYGAME_AVAILABLE:
            reconnect_btn = QPushButton('🔄 Reconnect')
            reconnect_btn.setToolTip('Reconnect Controller')
            reconnect_btn.clicked.connect(self.reconnect_controller)
            reconnect_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {CURRENT_COLORS['bg_dark']};
                    color: {CURRENT_COLORS['neon_green']};
                    border: 1px solid {CURRENT_COLORS['neon_green']};
                    padding: 4px;
                    font-size: 14px;
                    border-radius: 3px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background-color: {CURRENT_COLORS['neon_green']};
                    color: #000;
                }}
            """)
            controller_layout.addWidget(reconnect_btn, stretch=1)
        
        settings_layout.addLayout(controller_layout)
        
        # Remap Controller button (moved here, before About button)
        self.remap_btn = QPushButton("🎮 Remap Controller")
        self.remap_btn.clicked.connect(self.open_remap_dialog)
        self.remap_btn.setEnabled(False)  # Disabled until controller is initialized
        self.remap_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {CURRENT_COLORS['bg_dark']};
                color: {CURRENT_COLORS['neon_purple']};
                border: 1px solid {CURRENT_COLORS['neon_purple']};
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 700;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                border: 1px solid {CURRENT_COLORS['neon_purple']};
            }}
            QPushButton:disabled {{
                background-color: {CURRENT_COLORS['bg_dark']};
                color: #555555;
                border: 1px solid #555555;
            }}
        """)
        settings_layout.addWidget(self.remap_btn)
        
        # About button
        about_btn = QPushButton('ℹ️ About')
        about_btn.clicked.connect(self.show_about_dialog)
        about_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {CURRENT_COLORS['bg_dark']};
                color: {CURRENT_COLORS['neon_cyan']};
                border: 1px solid {CURRENT_COLORS['neon_cyan']};
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 700;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                border: 1px solid {CURRENT_COLORS['neon_purple']};
            }}
        """)
        settings_layout.addWidget(about_btn)
        
        self.settings_panel.setLayout(settings_layout)
        self.settings_panel.setStyleSheet(f"""
            QGroupBox {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                border: 2px solid {CURRENT_COLORS['neon_purple']};
                
                margin-top: 8px;
                padding: 10px;
                color: {CURRENT_COLORS['neon_purple']};
                font-weight: 700;
                font-size: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        right_layout.addWidget(self.settings_panel)
        
        right_layout.addStretch()
        
        # Add panels to main layout with proportions
        main_layout.addWidget(self.left_scroll_area, stretch=1)  # Left panel with scroll
        main_layout.addWidget(center_panel, stretch=2)
        main_layout.addWidget(self.right_scroll_area, stretch=1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {CURRENT_COLORS['bg_dark']};
                color: {CURRENT_COLORS['text']};
                border-top: 1px solid {CURRENT_COLORS['neon_cyan']};
            }}
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('SYSTEM READY')
        
        # Disable category buttons initially
        self.set_buttons_enabled(False)
        
    def toggle_settings(self):
        """Toggle settings panel visibility"""
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
        else:
            self.settings_panel.show()
    
    def on_copy_mode_changed(self, state):
        """Handle copy mode checkbox change"""
        self.use_copy = (state == Qt.CheckState.Checked.value)
        self.settings.setValue('processing/copy_mode', self.use_copy)
        mode = "Salin" if self.use_copy else "Pindahkan"
        self.status_bar.showMessage(f'Mode: {mode} file', 2000)
    
    def on_cpu_workers_changed(self, value):
        """Handle CPU workers spinbox change"""
        self.cpu_workers = value
        self.settings.setValue('processing/cpu_workers', value)
        self.status_bar.showMessage(f'CPU Workers: {value}', 2000)
        # Disable GPU if using multiple CPU workers
        if value > 1 and self.gpu_checkbox.isChecked():
            self.gpu_checkbox.setChecked(False)
            self.status_bar.showMessage('GPU disabled (incompatible with multi-CPU)', 2000)
    
    def on_gpu_mode_changed(self, state):
        """Handle GPU mode checkbox change"""
        use_gpu = (state == Qt.CheckState.Checked.value)
        self.settings.setValue('processing/use_gpu', use_gpu)
        # Disable multi-CPU if GPU is enabled
        if use_gpu and self.cpu_workers_spin.value() > 1:
            self.cpu_workers_spin.setValue(1)
            self.status_bar.showMessage('CPU workers set to 1 (GPU mode)', 2000)
        
        if use_gpu:
            self.status_bar.showMessage('🚀 GPU Acceleration: ON', 2000)
        else:
            self.status_bar.showMessage('💻 GPU Acceleration: OFF', 2000)
    
    def on_sound_mode_changed(self, state):
        """Handle sound effects toggle"""
        self.sound_enabled = (state == Qt.CheckState.Checked.value)
        self.settings.setValue('sound/enabled', self.sound_enabled)
        if self.sound_enabled:
            self.status_bar.showMessage('🔊 Sound Effects: ON', 2000)
        else:
            self.status_bar.showMessage('🔇 Sound Effects: OFF', 2000)
    
    def on_theme_changed(self, state):
        """Handle theme toggle"""
        self.use_cyberpunk_theme = (state == Qt.CheckState.Checked.value)
        self.settings.setValue('theme/cyberpunk', self.use_cyberpunk_theme)
        
        # Update global theme
        global CURRENT_COLORS
        if self.use_cyberpunk_theme:
            CURRENT_COLORS = CYBERPUNK_COLORS.copy()
            self.status_bar.showMessage('🎨 Theme: Cyberpunk', 2000)
        else:
            CURRENT_COLORS = CASUAL_COLORS.copy()
            self.status_bar.showMessage('🎨 Theme: Casual', 2000)
        
        # Recreate UI with new theme
        self.init_ui()
        self.status_bar.showMessage(f'✓ Theme changed to {"Cyberpunk" if self.use_cyberpunk_theme else "Casual"}', 3000)
    
    def load_controller_mapping(self):
        """Load controller mapping from QSettings"""
        mapping = {}
        for key in DEFAULT_CONTROLLER_MAPPING.keys():
            saved_value = self.settings.value(f'controller/{key}')
            if saved_value:
                # Parse saved value back to tuple
                mapping[key] = eval(saved_value) if isinstance(saved_value, str) else saved_value
            else:
                mapping[key] = DEFAULT_CONTROLLER_MAPPING[key]
        return mapping
    
    def save_controller_mapping(self):
        """Save controller mapping to QSettings"""
        for key, value in self.controller_mapping.items():
            self.settings.setValue(f'controller/{key}', str(value))
    
    def open_remap_dialog(self):
        """Open controller remapping dialog"""
        if not PYGAME_AVAILABLE or not self.controller:
            QMessageBox.warning(
                self,
                'Controller Not Available',
                'No game controller detected. Please connect a controller and restart the application.'
            )
            return
        
        dialog = ControllerRemapDialog(
            self,
            self.controller,
            self.controller_mapping,
            DEFAULT_CONTROLLER_MAPPING
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save new mapping
            self.controller_mapping = dialog.get_mapping()
            self.save_controller_mapping()
            self.status_bar.showMessage('✓ Controller mapping saved!', 3000)
    
    def show_about_dialog(self):
        """Show about dialog"""
        # Close any existing about dialog
        if hasattr(self, 'about_dialog') and self.about_dialog:
            self.about_dialog.close()
            self.about_dialog = None
        
        # Load and scale icon
        icon_path = Path(__file__).parent / 'resources' / 'icon.png'
        icon_html = ""
        if icon_path.exists():
            icon_html = f"<p align='center'><img src='{icon_path}' width='80' height='80'/></p>"
        
        about_text = f"""
        {icon_html}
        <h2 style='color: #00f0ff; text-align: center;'>🎮 Photosortman</h2>
        <p style='color: #e0e0ff; text-align: center;'><b>by Rania Amina</b></p>
        
        <p style='color: #8b8baa; margin-top: 20px; text-align: center;'>
        A simple photo sorting and quality analysis tool<br/>
        with game controller support. Sort your photos<br/>
        efficiently using keyboard shortcuts or game<br/>
        controller, with basic and simple quality analysis<br/>
        and cyberpunk-themed UI.
        </p>
        
        <p style='color: #e0e0ff; margin-top: 20px; text-align: center;'>
        <b>GitHub:</b><br/>
        <a href='https://github.com/raniaamina/photosortman' style='color: #00f0ff;'>
        github.com/raniaamina/photosortman</a>
        </p>
        
        <p style='color: #8b8baa; margin-top: 20px; font-size: 10px; text-align: center;'>
        Version 1.0 • Built with PyQt6 & Python
        </p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle('About Photosortman')
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        
        # Set custom button text
        close_button = msg.addButton('Close', QMessageBox.ButtonRole.AcceptRole)
        
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {CURRENT_COLORS['bg_dark']};
            }}
            QLabel {{
                color: {CURRENT_COLORS['text']};
                min-width: 450px;
                max-width: 500px;
            }}
            QPushButton {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                color: {CURRENT_COLORS['neon_cyan']};
                border: 1px solid {CURRENT_COLORS['neon_cyan']};
                padding: 8px 30px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {CURRENT_COLORS['bg_medium']};
            }}
            QDialogButtonBox {{
                qproperty-centerButtons: true;
            }}
        """)
        
        # Store reference for RB+B close
        self.about_dialog = msg
        
        # Use show() instead of exec() to allow controller polling to continue
        msg.show()
    
    def open_remap_dialog(self):
        """Open controller remapping dialog"""
        if not self.controller:
            QMessageBox.warning(
                self,
                'No Controller',
                'No controller detected. Please connect a controller first.'
            )
            return
        
        # Set flag to block main controller polling
        self.remap_dialog_open = True
        
        # Pause main controller polling
        if hasattr(self, 'controller_timer'):
            self.controller_timer.stop()
        
        # Open dialog
        dialog = ControllerRemapDialog(
            self,
            self.controller,
            self.controller_mapping,
            CURRENT_COLORS
        )
        
        result = dialog.exec()
        
        # Clear flag
        self.remap_dialog_open = False
        
        # Resume controller polling
        if hasattr(self, 'controller_timer'):
            self.controller_timer.start(16)
        
        # If user saved, update mappings
        if result == QDialog.DialogCode.Accepted:
            self.controller_mapping = dialog.get_mappings()
            self.save_controller_mapping()
            # Reload mappings to ensure they're applied
            self.controller_mapping = self.load_controller_mapping()
            self.status_bar.showMessage('✓ Controller mappings saved', 3000)
        else:
            self.status_bar.showMessage('Controller remapping cancelled', 2000)
    
    def check_cuda_available(self):
        """Check if CUDA is available (check for NVIDIA GPU)"""
        try:
            # Check if nvidia-smi is available (indicates NVIDIA GPU present)
            result = subprocess.run(['nvidia-smi'], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=2)
            if result.returncode == 0:
                # NVIDIA GPU detected - enable GPU option
                # Note: Actual CUDA usage requires OpenCV with CUDA support
                return True
            return False
        except:
            return False
    
    def stop_analysis(self):
        """Stop ongoing quality analysis"""
        if hasattr(self, 'quality_analyzer') and self.quality_analyzer.isRunning():
            self.quality_analyzer.stop_requested = True
            self.stop_btn.setEnabled(False)
            self.stop_btn.setText('⛔ STOPPING...')
            self.status_bar.showMessage('Menghentikan analisis...')
    
    
    def create_metric_label(self, layout, label, color):
        """Create a single-line quality metric display (label on left, value on right)"""
        container = QWidget()
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(h_layout)
        
        # Label on left
        title = QLabel(label)
        title.setStyleSheet(f"""
            color: {color};
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 1px;
        """)
        h_layout.addWidget(title)
        h_layout.addStretch()
        
        # Value on right
        value_label = QLabel("0%")
        value_label.setStyleSheet(f"""
            color: {color};
            font-weight: 900;
            font-size: 13px;
            letter-spacing: 1px;
        """)
        h_layout.addWidget(value_label)
        
        layout.addWidget(container)
        return value_label
    
    
    def update_quality_display(self, index):
        """Update quality metrics display for current photo"""
        if index in self.quality_data:
            metrics, recommendation = self.quality_data[index]
            
            # Update each metric label
            self.blur_label.setText(f"{metrics.get('blur', 0)}%")
            self.exposure_label.setText(f"{metrics.get('exposure', 0)}%")
            self.contrast_label.setText(f"{metrics.get('contrast', 0)}%")
            self.noise_label.setText(f"{metrics.get('noise', 0)}%")
            self.saturation_label.setText(f"{metrics.get('saturation', 0)}%")
            self.overall_label.setText(f"{metrics.get('overall', 0)}%")
            
            # Update recommendation badge with color
            self.recommendation_label.setText(recommendation)
            if recommendation == "Best":
                color = CURRENT_COLORS['neon_green']
            elif recommendation == "Standard":
                color = CURRENT_COLORS['neon_cyan']
            elif recommendation == "Bad":
                color = CURRENT_COLORS['neon_pink']
            else:
                color = CURRENT_COLORS['text_muted']
            
            self.recommendation_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 14px;
                    font-weight: 900;
                    padding: 10px;
                    color: {color};
                    background-color: {CURRENT_COLORS['bg_dark']};
                    border: 2px solid {color};
                    
                    letter-spacing: 2px;
                }}
            """)
        else:
            # Clear metrics if not analyzed yet
            self.clear_quality_display()
    
    def clear_quality_display(self):
        """Clear quality metrics display"""
        self.blur_label.setText("0%")
        self.exposure_label.setText("0%")
        self.contrast_label.setText("0%")
        self.noise_label.setText("0%")
        self.saturation_label.setText("0%")
        self.overall_label.setText("0%")
        self.recommendation_label.setText("NO DATA")
        self.recommendation_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                font-weight: 900;
                padding: 10px;
                color: {CURRENT_COLORS['text_muted']};
                background-color: {CURRENT_COLORS['bg_dark']};
                border: 2px solid {CURRENT_COLORS['text_muted']};
                
                letter-spacing: 2px;
            }}
        """)
    
    
    def update_stats_display(self):
        """Update statistics display in left panel"""
        total = len(self.photos)
        self.total_photos_label.setText(f"TOTAL: {total}")
        
        # Count photos in each category folder
        best_count = 0
        standard_count = 0
        bad_count = 0
        
        if self.source_folder:
            best_folder = self.source_folder / 'Best'
            standard_folder = self.source_folder / 'Standard'
            bad_folder = self.source_folder / 'Bad'
            
            if best_folder.exists():
                best_count = len([f for f in best_folder.iterdir() if f.suffix.lower() in self.image_extensions])
            if standard_folder.exists():
                standard_count = len([f for f in standard_folder.iterdir() if f.suffix.lower() in self.image_extensions])
            if bad_folder.exists():
                bad_count = len([f for f in bad_folder.iterdir() if f.suffix.lower() in self.image_extensions])
        
        self.best_count_label.setText(f"++ BEST: {best_count}")
        self.standard_count_label.setText(f">> STANDARD: {standard_count}")
        self.bad_count_label.setText(f"<< BAD: {bad_count}")
        
    def create_category_button(self, text, color, category_index):
        """Create a styled category button with cyberpunk design and diagonal cuts"""
        btn = QPushButton(text)
        btn.setMinimumHeight(60)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Cyberpunk button styling - diagonal cuts effect
        # Using linear-gradient to create diagonal cut illusion
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #000, stop:0.05 #000, 
                    stop:0.05 {color}, stop:0.95 {color},
                    stop:0.95 #000, stop:1 #000);
                color: #000;
                border: none;
                border-left: 6px solid {color};
                border-right: 2px solid {color};
                border-top: 2px solid {color};
                border-bottom: 2px solid {color};
                font-size: 18px;
                font-weight: 900;
                letter-spacing: 3px;
                text-transform: uppercase;
                font-family: 'Rajdhani', 'Orbitron', monospace;
            }}
            QPushButton:hover {{
                background: {color};
                color: #000;
            }}
            QPushButton:pressed {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                color: {color};
            }}
            QPushButton:disabled {{
                background-color: {CURRENT_COLORS['bg_darkest']};
                color: {CURRENT_COLORS['text_muted']};
                border-left-color: {CURRENT_COLORS['bg_light']};
                border-right-color: {CURRENT_COLORS['bg_light']};
            }}
        """)
        
        # Store category index for later use
        btn.clicked.connect(lambda: self.categorize_photo(category_index))
        
        return btn
    
    def darken_color(self, hex_color, factor=0.15):
        """Darken a hex color"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Category shortcuts
        QShortcut(QKeySequence('1'), self).activated.connect(lambda: self.categorize_photo(0))
        QShortcut(QKeySequence('2'), self).activated.connect(lambda: self.categorize_photo(1))
        QShortcut(QKeySequence('3'), self).activated.connect(lambda: self.categorize_photo(2))
        
        # Navigation shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Left), self).activated.connect(self.previous_photo)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self).activated.connect(self.next_photo)
    
    def init_controller(self):
        """Initialize game controller"""
        try:
            pygame.init()
            pygame.joystick.init()
            
            if pygame.joystick.get_count() > 0:
                self.controller = pygame.joystick.Joystick(0)
                self.controller.init()
                self.controller_name = self.controller.get_name()
                print(f"🎮 Controller connected: {self.controller_name}")
                self.status_bar.showMessage(f'🎮 Controller connected: {self.controller_name}', 3000)
                
                # Enable remap button now that controller is available
                if hasattr(self, 'remap_btn'):
                    self.remap_btn.setEnabled(True)
                
                # Update controller status label
                if hasattr(self, 'controller_status_label'):
                    self.controller_status_label.setText(f'🎮 {self.controller_name}')
                    self.controller_status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {CURRENT_COLORS['neon_green']};
                            font-size: 10px;
                            padding: 4px;
                            font-weight: 600;
                        }}
                    """)
                
                # Add controller hints to button tooltips
                self.quality_btn.setToolTip('⚡ Analisis Kualitas (🎮 Start Button)')
                
                # Add hints to category buttons
                if hasattr(self, 'best_btn'):
                    self.best_btn.setToolTip('Best (🎮 A Button)')
                if hasattr(self, 'standard_btn'):
                    self.standard_btn.setToolTip('Standard (🎮 X Button)')
                if hasattr(self, 'bad_btn'):
                    self.bad_btn.setToolTip('Bad (🎮 B Button)')
                
                # Add hints to settings controls
                if hasattr(self, 'copy_checkbox'):
                    self.copy_checkbox.setToolTip('Salin/Pindahkan file (🎮 D-Pad Down)')
                if hasattr(self, 'gpu_checkbox'):
                    self.gpu_checkbox.setToolTip('Toggle GPU CUDA (🎮 D-Pad Up)')
                if hasattr(self, 'sound_checkbox'):
                    self.sound_checkbox.setToolTip('Toggle Sound Effects (🎮 Select Button)')
                if hasattr(self, 'cpu_workers_spin'):
                    self.cpu_workers_spin.setToolTip('CPU Workers (🎮 LB/RB untuk ±)')
                
            else:
                print("No game controller detected")
        except Exception as e:
            print(f"Error initializing controller: {e}")
    
    def reconnect_controller(self):
        """Reconnect/rescan for game controller"""
        try:
            # Stop existing controller timer if running
            if hasattr(self, 'controller_timer') and self.controller_timer:
                self.controller_timer.stop()
            
            # Show scanning message
            self.status_bar.showMessage('🔍 Scanning for controllers...', 10000)
            
            # Quit and reinitialize pygame joystick
            if PYGAME_AVAILABLE:
                pygame.joystick.quit()
                pygame.joystick.init()
                
                # Check for controllers
                joystick_count = pygame.joystick.get_count()
                
                if joystick_count > 0:
                    self.controller = pygame.joystick.Joystick(0)
                    self.controller.init()
                    self.controller_name = self.controller.get_name()
                    
                    # Update status label
                    self.controller_status_label.setText(f'🎮 {self.controller_name}')
                    self.controller_status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {CURRENT_COLORS['neon_green']};
                            font-size: 10px;
                            padding: 4px;
                            font-weight: 600;
                        }}
                    """)
                    
                    # Restart controller timer
                    self.controller_timer = QTimer()
                    self.controller_timer.timeout.connect(self.poll_controller)
                    self.controller_timer.start(16)  # ~60 FPS
                    
                    # Show success notification
                    QMessageBox.information(
                        self,
                        '✓ Controller Connected',
                        f'Successfully connected to:\n\n{self.controller_name}\n\nYou can now use your controller to navigate and sort photos.'
                    )
                    self.status_bar.showMessage(f'✓ Controller connected: {self.controller_name}', 3000)
                else:
                    self.controller = None
                    self.controller_status_label.setText('🎮 No Controller')
                    self.controller_status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {CURRENT_COLORS['text_muted']};
                            font-size: 10px;
                            padding: 4px;
                            font-weight: 600;
                        }}
                    """)
                    
                    # Show failure notification
                    QMessageBox.warning(
                        self,
                        '⚠️ No Controller Found',
                        'No game controller detected.\n\nPlease:\n1. Connect your controller\n2. Make sure it\'s powered on\n3. Click "Reconnect Controller" again'
                    )
                    self.status_bar.showMessage('⚠️ No controller detected', 3000)
        
        except Exception as e:
            print(f"Error reconnecting controller: {e}")
            QMessageBox.critical(
                self,
                '❌ Controller Error',
                f'Failed to reconnect controller:\n\n{str(e)}'
            )
            self.status_bar.showMessage(f'❌ Controller error: {e}', 3000)
    
    def check_mapping_pressed(self, action_key):
        """Check if the mapped button/trigger for an action is pressed"""
        if not self.controller or action_key not in self.controller_mapping:
            return False
        
        mapping = self.controller_mapping[action_key]
        if not mapping:
            return False
        
        map_type, value = mapping
        
        try:
            # Check if RB or LB modifiers are pressed
            lb_pressed = self.controller.get_button(4) if self.controller.get_numbuttons() > 4 else False
            rb_pressed = self.controller.get_button(5) if self.controller.get_numbuttons() > 5 else False
            modifier_active = lb_pressed or rb_pressed
            
            if map_type == 'button':
                btn_idx = value
                if self.controller.get_numbuttons() > btn_idx:
                    button_pressed = self.controller.get_button(btn_idx)
                    # Special case: block button B (button 1) when RB is pressed (for RB+B dialog close)
                    if rb_pressed and btn_idx == 1 and button_pressed:
                        return False
                    return button_pressed
            
            elif map_type == 'trigger':
                axis_idx = value
                if self.controller.get_numaxes() > axis_idx:
                    # PS controllers: triggers go from -1 (not pressed) to 1 (fully pressed)
                    # Xbox controllers: triggers go from 0 (not pressed) to 1 (fully pressed)
                    # Check for positive value > 0.1 to handle both
                    axis_value = self.controller.get_axis(axis_idx)
                    return axis_value > 0.1
            
            elif map_type == 'trigger_combo':
                modifier, axis_idx = value
                lb_pressed = self.controller.get_button(4) if self.controller.get_numbuttons() > 4 else False
                rb_pressed = self.controller.get_button(5) if self.controller.get_numbuttons() > 5 else False
                mod_pressed = lb_pressed if modifier == 'lb' else rb_pressed
                if mod_pressed and self.controller.get_numaxes() > axis_idx:
                    axis_value = self.controller.get_axis(axis_idx)
                    return axis_value > 0.1
            
            elif map_type == 'button_combo':
                modifier, btn_idx = value
                lb_pressed = self.controller.get_button(4) if self.controller.get_numbuttons() > 4 else False
                rb_pressed = self.controller.get_button(5) if self.controller.get_numbuttons() > 5 else False
                mod_pressed = lb_pressed if modifier == 'lb' else rb_pressed
                if mod_pressed and self.controller.get_numbuttons() > btn_idx:
                    return self.controller.get_button(btn_idx)
            
            elif map_type == 'hat':
                x, y = value
                if self.controller.get_numhats() > 0:
                    hat = self.controller.get_hat(0)
                    return hat == (x, y)
            
            elif map_type == 'hat_combo':
                modifier, x, y = value
                lb_pressed = self.controller.get_button(4) if self.controller.get_numbuttons() > 4 else False
                rb_pressed = self.controller.get_button(5) if self.controller.get_numbuttons() > 5 else False
                mod_pressed = lb_pressed if modifier == 'lb' else rb_pressed
                if mod_pressed and self.controller.get_numhats() > 0:
                    hat = self.controller.get_hat(0)
                    return hat == (x, y)
        
        except Exception as e:
            print(f"Error checking mapping for {action_key}: {e}")
        
        return False
    
    def poll_controller(self):
        """Poll controller input every frame"""
        if not self.controller:
            return
        
        # Don't process controller input if remap dialog is open
        if hasattr(self, 'remap_dialog_open') and self.remap_dialog_open:
            return
        
        try:
            pygame.event.pump()  # Process event queue
            
            # RB+B - Close dialog (direct button check, not using check_mapping_pressed)
            rb_pressed = self.controller.get_button(5) if self.controller.get_numbuttons() > 5 else False
            b_pressed = self.controller.get_button(1) if self.controller.get_numbuttons() > 1 else False
            rb_b_combo = rb_pressed and b_pressed
            
            if rb_b_combo and not self.last_button_states.get('rb_b_close', False):
                # Check for stored about dialog first
                if hasattr(self, 'about_dialog') and self.about_dialog and self.about_dialog.isVisible():
                    self.about_dialog.close()
                    self.about_dialog = None
                    self.status_bar.showMessage('✓ Dialog closed', 1000)
                    self.last_button_states['rb_b_close'] = rb_b_combo
                    return
                
                # Find any open QMessageBox or QDialog
                dialog_to_close = None
                
                # Check all top level widgets for QMessageBox or QDialog
                for widget in QApplication.topLevelWidgets():
                    if widget != self and widget.isVisible():
                        # Check if it's a QMessageBox or QDialog
                        if isinstance(widget, (QMessageBox, QDialog)):
                            dialog_to_close = widget
                            break
                
                if dialog_to_close:
                    # Close the dialog
                    dialog_to_close.close()
                    self.status_bar.showMessage('✓ Dialog closed', 1000)
                    self.last_button_states['rb_b_close'] = rb_b_combo
                    return  # Return early to prevent other actions
            self.last_button_states['rb_b_close'] = rb_b_combo
            
            # RB+A - Prevent categorization when pressed (check early)
            a_pressed = self.controller.get_button(0) if self.controller.get_numbuttons() > 0 else False
            rb_a_combo = rb_pressed and a_pressed
            if rb_a_combo:
                # Just track state, don't do anything (prevents categorization)
                self.last_button_states['rb_a_block'] = True
                return  # Return early to prevent categorization
            else:
                self.last_button_states['rb_a_block'] = False
            
            # Navigation using custom mappings
            # Previous photo
            
            # Next photo
            if self.check_mapping_pressed('nav_next') and not self.last_button_states.get('nav_next', False):
                self.next_photo()
            self.last_button_states['nav_next'] = self.check_mapping_pressed('nav_next')
            
            # Categorization using custom mappings
            # Best
            if self.check_mapping_pressed('cat_best') and not self.last_button_states.get('cat_best', False):
                self.categorize_photo(0)
            self.last_button_states['cat_best'] = self.check_mapping_pressed('cat_best')
            
            # Bad
            if self.check_mapping_pressed('cat_bad') and not self.last_button_states.get('cat_bad', False):
                self.categorize_photo(2)
            self.last_button_states['cat_bad'] = self.check_mapping_pressed('cat_bad')
            
            # Standard
            if self.check_mapping_pressed('cat_standard') and not self.last_button_states.get('cat_standard', False):
                self.categorize_photo(1)
            self.last_button_states['cat_standard'] = self.check_mapping_pressed('cat_standard')
            
            # Select folder
            if self.check_mapping_pressed('action_folder') and not self.last_button_states.get('action_folder', False):
                self.last_button_states['action_folder'] = True
                QTimer.singleShot(50, self.select_folder)
            elif not self.check_mapping_pressed('action_folder'):
                self.last_button_states['action_folder'] = False
            
            # Start analysis
            if self.check_mapping_pressed('action_analysis') and not self.last_button_states.get('action_analysis', False):
                self.start_quality_analysis()
            self.last_button_states['action_analysis'] = self.check_mapping_pressed('action_analysis')
            
            # Toggle sound
            if self.check_mapping_pressed('toggle_sound') and not self.last_button_states.get('toggle_sound', False):
                self.sound_checkbox.setChecked(not self.sound_checkbox.isChecked())
            self.last_button_states['toggle_sound'] = self.check_mapping_pressed('toggle_sound')
            
            
            # LB combos using custom mappings
            if self.check_mapping_pressed('lb_cpu_dec') and not self.last_button_states.get('lb_cpu_dec', False):
                current = self.cpu_workers_spin.value()
                if current > 1:
                    self.cpu_workers_spin.setValue(current - 1)
            self.last_button_states['lb_cpu_dec'] = self.check_mapping_pressed('lb_cpu_dec')
            
            if self.check_mapping_pressed('lb_cpu_inc') and not self.last_button_states.get('lb_cpu_inc', False):
                current = self.cpu_workers_spin.value()
                max_val = self.cpu_workers_spin.maximum()
                if current < max_val:
                    self.cpu_workers_spin.setValue(current + 1)
            self.last_button_states['lb_cpu_inc'] = self.check_mapping_pressed('lb_cpu_inc')
            
            if self.check_mapping_pressed('lb_sound') and not self.last_button_states.get('lb_sound', False):
                self.sound_checkbox.setChecked(not self.sound_checkbox.isChecked())
            self.last_button_states['lb_sound'] = self.check_mapping_pressed('lb_sound')
            
            if self.check_mapping_pressed('lb_gpu') and not self.last_button_states.get('lb_gpu', False):
                self.gpu_checkbox.setChecked(not self.gpu_checkbox.isChecked())
            self.last_button_states['lb_gpu'] = self.check_mapping_pressed('lb_gpu')
            
            # RB combos using custom mappings
            if self.check_mapping_pressed('rb_copy') and not self.last_button_states.get('rb_copy', False):
                self.copy_checkbox.setChecked(not self.copy_checkbox.isChecked())
            self.last_button_states['rb_copy'] = self.check_mapping_pressed('rb_copy')
            
            if self.check_mapping_pressed('rb_theme') and not self.last_button_states.get('rb_theme', False):
                self.theme_checkbox.setChecked(not self.theme_checkbox.isChecked())
            self.last_button_states['rb_theme'] = self.check_mapping_pressed('rb_theme')
            
            if self.check_mapping_pressed('rb_remap') and not self.last_button_states.get('rb_remap', False):
                self.open_remap_dialog()
            self.last_button_states['rb_remap'] = self.check_mapping_pressed('rb_remap')
            
            if self.check_mapping_pressed('rb_about') and not self.last_button_states.get('rb_about', False):
                self.show_about_dialog()
            self.last_button_states['rb_about'] = self.check_mapping_pressed('rb_about')
            
            if self.check_mapping_pressed('rb_reconnect') and not self.last_button_states.get('rb_reconnect', False):
                self.reconnect_controller()
            self.last_button_states['rb_reconnect'] = self.check_mapping_pressed('rb_reconnect')
            
            # D-Pad navigation using custom mappings
            if self.check_mapping_pressed('dpad_nav_up') and not self.last_button_states.get('dpad_nav_up', False):
                if self.current_index > 0:
                    self.current_index -= 1
                    self.display_current_photo()
            self.last_button_states['dpad_nav_up'] = self.check_mapping_pressed('dpad_nav_up')
            
            if self.check_mapping_pressed('dpad_nav_down') and not self.last_button_states.get('dpad_nav_down', False):
                if self.current_index < len(self.photos) - 1:
                    self.current_index += 1
                    self.display_current_photo()
            self.last_button_states['dpad_nav_down'] = self.check_mapping_pressed('dpad_nav_down')
            
            if self.check_mapping_pressed('dpad_nav_left') and not self.last_button_states.get('dpad_nav_left', False):
                self.previous_photo()
            self.last_button_states['dpad_nav_left'] = self.check_mapping_pressed('dpad_nav_left')
            
            if self.check_mapping_pressed('dpad_nav_right') and not self.last_button_states.get('dpad_nav_right', False):
                self.next_photo()
            self.last_button_states['dpad_nav_right'] = self.check_mapping_pressed('dpad_nav_right')
            
            # Analog stick scrolling for panels
            # Xbox 360 mapping: Left stick (0,1), Right stick (3,4), Triggers (2,5)
            if self.controller.get_numaxes() >= 5:
                # Left stick Y-axis (axis 1) for thumbnail grid scroll
                left_stick_y = self.controller.get_axis(1)
                if abs(left_stick_y) > 0.3:  # Deadzone
                    scroll_amount = int(left_stick_y * 20)  # Scroll speed
                    if hasattr(self, 'thumbnail_scroll'):
                        scrollbar = self.thumbnail_scroll.verticalScrollBar()
                        old_val = scrollbar.value()
                        new_val = max(0, min(scrollbar.maximum(), old_val + scroll_amount))
                        if new_val != old_val:
                            scrollbar.setValue(new_val)
                
                # Right stick Y-axis (axis 4) for right panel scroll
                right_stick_y = self.controller.get_axis(4)
                if abs(right_stick_y) > 0.3:  # Deadzone
                    scroll_amount = int(right_stick_y * 20)  # Scroll speed
                    if hasattr(self, 'right_scroll_area'):
                        scrollbar = self.right_scroll_area.verticalScrollBar()
                        old_val = scrollbar.value()
                        new_val = max(0, min(scrollbar.maximum(), old_val + scroll_amount))
                        if new_val != old_val:
                            scrollbar.setValue(new_val)
                
        except Exception as e:
            print(f"Controller error: {e}")
            self.status_bar.showMessage(f'❌ Controller error: {e}', 3000)
    
    def select_folder(self):
        """Open folder selection dialog (native KDE dialog via kdialog)"""
        # Prevent multiple simultaneous dialog calls
        if self.dialog_in_progress:
            print("Dialog already in progress, ignoring")
            return
        
        self.dialog_in_progress = True
        print("select_folder called")
        
        # Pause controller polling during dialog
        if hasattr(self, 'controller_timer') and self.controller_timer:
            self.controller_timer.stop()
        
        try:
            try:
                result = subprocess.run(
                    ['kdialog', '--getexistingdirectory', str(Path.home())],
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise on non-zero exit (includes cancel)
                )
                
                # Check if user selected a folder (not cancelled)
                if result.returncode == 0 and result.stdout.strip():
                    folder = result.stdout.strip()
                    self.source_folder = Path(folder)
                    
                    # Update folder info label
                    folder_name = self.source_folder.name
                    folder_path_str = str(self.source_folder)
                    if len(folder_path_str) > 35:
                        folder_display = f"...{folder_path_str[-32:]}"
                    else:
                        folder_display = folder_path_str
                    
                    self.folder_info_label.setText(f"📁 {folder_name}\n{folder_display}")
                    self.folder_info_label.setStyleSheet(f"""
                        QLabel {{
                            background-color: {CURRENT_COLORS['bg_darkest']};
                            color: {CURRENT_COLORS['neon_cyan']};
                            border: 1px solid {CURRENT_COLORS['neon_cyan']};
                            padding: 8px 12px;
                            font-size: 10px;
                            font-weight: 600;
                            letter-spacing: 0.5px;
                        }}
                    """)
                    
                    # Enable file manager button
                    self.open_folder_btn.setEnabled(True)
                    
                    self.load_photos()
                    return
                
                # If cancelled (returncode != 0) or empty, just return
                if result.returncode != 0:
                    return  # User cancelled, don't show fallback
                    
            except FileNotFoundError:
                # kdialog not found, use Qt dialog
                pass
            
            # Fallback: Use Qt's file dialog (only if kdialog not available)
            options = QFileDialog.Option(0)
            folder = QFileDialog.getExistingDirectory(
                self,
                'Pilih Folder Berisi Foto',
                str(Path.home()),
                options
            )
            
            if folder:
                self.source_folder = Path(folder)
                
                # Save folder path to settings
                self.settings.setValue('folder/last_path', str(self.source_folder))
                
                # Update folder info label
                folder_name = self.source_folder.name
                folder_path_str = str(self.source_folder)
                if len(folder_path_str) > 40:
                    folder_display = f"...{folder_path_str[-37:]}"
                else:
                    folder_display = folder_path_str
                
                self.folder_info_label.setText(f"📁 {folder_name}\n{folder_display}")
                self.folder_info_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {CURRENT_COLORS['bg_darkest']};
                        color: {CURRENT_COLORS['neon_cyan']};
                        border: 1px solid {CURRENT_COLORS['neon_cyan']};
                        padding: 8px 12px;
                        font-size: 11px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    }}
                """)
                
                # Enable file manager button
                self.open_folder_btn.setEnabled(True)
                
                self.load_photos()
        finally:
            # Always reset the dialog flag and restart controller
            self.dialog_in_progress = False
            if hasattr(self, 'controller_timer') and self.controller_timer:
                self.controller_timer.start(16)  # Resume polling
            print("Dialog flag reset, controller resumed")
    
    def open_in_file_manager(self):
        """Open current folder in file manager"""
        if not self.source_folder or not self.source_folder.exists():
            return
        
        try:
            # Try xdg-open (works on most Linux)
            subprocess.Popen(['xdg-open', str(self.source_folder)])
        except FileNotFoundError:
            try:
                # Fallback to dolphin (KDE)
                subprocess.Popen(['dolphin', str(self.source_folder)])
            except FileNotFoundError:
                try:
                    # Fallback to nautilus (GNOME)
                    subprocess.Popen(['nautilus', str(self.source_folder)])
                except FileNotFoundError:
                    QMessageBox.warning(
                        self,
                        'Error',
                        'Tidak dapat membuka file manager'
                    )
            
    def load_photos(self):
        """Load photos from selected folder"""
        if not self.source_folder:
            return
        
        # Find all image files
        self.photos = []
        for ext in self.image_extensions:
            self.photos.extend(self.source_folder.glob(f'*{ext}'))
            self.photos.extend(self.source_folder.glob(f'*{ext.upper()}'))
        
        # Sort by name
        self.photos = sorted(self.photos)
        
        if not self.photos:
            QMessageBox.warning(
                self,
                'Tidak Ada Foto',
                'Tidak ditemukan foto di folder yang dipilih.'
            )
            return
        
        # Create category folders
        for category in self.categories:
            category_path = self.source_folder / category
            category_path.mkdir(exist_ok=True)
        
        # Setup progress bar
        self.progress_bar.setMaximum(len(self.photos))
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # Clear old thumbnails
        for widget in self.thumbnail_widgets:
            widget.deleteLater()
        self.thumbnail_widgets.clear()
        
        # Create thumbnail widgets
        for idx, photo in enumerate(self.photos):
            thumb_widget = ThumbnailWidget(idx, photo)
            thumb_widget.clicked.connect(self.on_thumbnail_clicked)
            self.thumbnail_widgets.append(thumb_widget)
            
            row = idx // 2
            col = idx % 2
            self.thumbnail_grid.addWidget(thumb_widget, row, col)
        
        # Load thumbnails in background
        self.thumbnail_loader = ThumbnailLoader(self.photos, 120)
        self.thumbnail_loader.thumbnail_loaded.connect(self.on_thumbnail_loaded)
        self.thumbnail_loader.start()
        
        # Reset index and display first photo
        self.current_index = 0
        self.display_current_photo()
        self.set_buttons_enabled(True)
        
        # Enable quality analysis button
        self.quality_btn.setEnabled(True)
        self.quality_data.clear()
        
        # Auto-load quality info if exists
        quality_file = self.source_folder / 'quality-info.txt'
        if quality_file.exists():
            try:
                loaded_count = 0
                with open(quality_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                # Skip header line
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse CSV line: Nama File; Blur; Exposure; Contrast; Noise; Saturation; Overall; Rekomendasi
                    parts = [p.strip() for p in line.split(';')]
                    if len(parts) < 8:
                        continue
                    
                    filename = parts[0]
                    # Remove % signs and convert to int
                    blur = int(parts[1].replace('%', ''))
                    exposure = int(parts[2].replace('%', ''))
                    contrast = int(parts[3].replace('%', ''))
                    noise = int(parts[4].replace('%', ''))
                    saturation = int(parts[5].replace('%', ''))
                    overall = int(parts[6].replace('%', ''))
                    recommendation = parts[7]
                    
                    # Find photo index by filename
                    for idx, photo in enumerate(self.photos):
                        if photo.name == filename:
                            metrics = {
                                'blur': blur,
                                'exposure': exposure,
                                'contrast': contrast,
                                'noise': noise,
                                'saturation': saturation,
                                'overall': overall
                            }
                            self.quality_data[idx] = (metrics, recommendation)
                            loaded_count += 1
                            break
                
                # Update display for current photo
                if self.current_index in self.quality_data:
                    self.update_quality_display(self.current_index)
                
                self.status_bar.showMessage(
                    f'✓ Loaded {len(self.photos)} foto + {loaded_count} quality info dari {self.source_folder.name}',
                    3000
                )
            except Exception as e:
                print(f"Warning: Could not load quality-info.txt: {e}")
                self.status_bar.showMessage(f'Loaded {len(self.photos)} foto dari {self.source_folder.name}')
        else:
            self.status_bar.showMessage(f'Loaded {len(self.photos)} foto dari {self.source_folder.name}')
        
    def on_thumbnail_loaded(self, index, pixmap):
        """Handle thumbnail loaded"""
        try:
            if index < len(self.thumbnail_widgets):
                widget = self.thumbnail_widgets[index]
                # Check if widget still exists and hasn't been deleted
                if widget and hasattr(widget, 'thumb_label'):
                    widget.set_thumbnail(pixmap)
        except (RuntimeError, AttributeError) as e:
            # Widget was deleted, ignore
            pass
    
    def on_thumbnail_clicked(self, index):
        """Handle thumbnail click"""
        if index < len(self.photos):
            # Play select sound
            if self.sound_enabled and 'select' in self.sounds:
                self.sounds['select'].play()
            
            self.current_index = index
            self.display_current_photo()
            
    def display_current_photo(self):
        """Display the current photo"""
        if not self.photos or self.current_index >= len(self.photos):
            self.image_label.clear()
            self.image_label.setText('SEMUA FOTO SUDAH DIKATEGORIKAN! 🎉')
            self.file_info_label.setText('SELESAI')
            self.set_buttons_enabled(False)
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.clear_quality_display()
            return
        
        current_photo = self.photos[self.current_index]
        
        # Load image with HEIC support
        pixmap = self.load_full_image(current_photo)
        if not pixmap:
            self.next_photo()
            return
        
        # Scale to fit label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        
        # Update file info
        self.file_info_label.setText(f'[{self.current_index + 1}/{len(self.photos)}] {current_photo.name}')
        
        # Update quality display if available
        self.update_quality_display(self.current_index)
        
        # Update photo border color based on quality
        border_color = CURRENT_COLORS['neon_purple']  # Default
        if self.current_index in self.quality_data:
            _, recommendation = self.quality_data[self.current_index]
            if recommendation == "Best":
                border_color = CURRENT_COLORS['neon_green']
            elif recommendation == "Standard":
                border_color = CURRENT_COLORS['neon_cyan']
            elif recommendation == "Bad":
                border_color = CURRENT_COLORS['neon_pink']
        
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: #000;
                border: 4px solid {border_color};
                min-height: 500px;
                color: {CURRENT_COLORS['text_muted']};
                font-size: 16px;
            }}
        """)
        
        # Update progress
        categorized = self.progress_bar.maximum() - len(self.photos)
        self.progress_bar.setValue(categorized)
        
        # Highlight selected thumbnail
        for idx, widget in enumerate(self.thumbnail_widgets):
            widget.set_selected(idx == self.current_index)
    
    def load_full_image(self, path):
        """Load full-size image with HEIC support"""
        try:
            # Try Qt first
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                return pixmap
            
            # Try Pillow for HEIC
            img = Image.open(str(path))
            img = img.convert('RGB')
            data = img.tobytes('raw', 'RGB')
            qimage = QImage(data, img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
            return QPixmap.fromImage(qimage)
            
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return None
        
    def categorize_photo(self, category_index):
        """Copy or move current photo to category folder"""
        if not self.photos or self.current_index >= len(self.photos):
            return
        
        current_photo = self.photos[self.current_index]
        category = self.categories[category_index]
        destination = self.source_folder / category / current_photo.name
        
        try:
            # Copy or move file based on settings
            if self.use_copy:
                shutil.copy2(str(current_photo), str(destination))
                action = "Disalin"
            else:
                shutil.move(str(current_photo), str(destination))
                action = "Dipindahkan"
            
            # Remove from list and thumbnail
            self.photos.pop(self.current_index)
            if self.current_index < len(self.thumbnail_widgets):
                widget = self.thumbnail_widgets.pop(self.current_index)
                self.thumbnail_grid.removeWidget(widget)
                widget.deleteLater()
            
            # Play sound effect based on category
            sound_map = {0: 'best', 1: 'standard', 2: 'bad'}
            sound_name = sound_map.get(category_index)
            if self.sound_enabled and sound_name and sound_name in self.sounds:
                self.sounds[sound_name].play()
            
            # Show feedback
            self.status_bar.showMessage(f'✓ {action} ke {category}', 2000)
            
            # Update statistics
            self.update_stats_display()
            
            # Display next photo (index stays same since we removed current)
            if self.current_index >= len(self.photos) and self.current_index > 0:
                self.current_index -= 1
            
            self.display_current_photo()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Gagal memproses file: {str(e)}'
            )
    
    def next_photo(self):
        """Go to next photo"""
        if self.photos and self.current_index < len(self.photos) - 1:
            # Play select sound
            if self.sound_enabled and 'select' in self.sounds:
                self.sounds['select'].play()
            
            self.current_index += 1
            self.display_current_photo()
    
    def previous_photo(self):
        """Go to previous photo"""
        if self.photos and self.current_index > 0:
            # Play select sound
            if self.sound_enabled and 'select' in self.sounds:
                self.sounds['select'].play()
            
            self.current_index -= 1
            self.display_current_photo()
    
    def set_buttons_enabled(self, enabled):
        """Enable or disable category buttons"""
        self.best_btn.setEnabled(enabled)
        self.standard_btn.setEnabled(enabled)
        self.bad_btn.setEnabled(enabled)
    
    def start_quality_analysis(self):
        """Start comprehensive quality analysis on all photos"""
        if not self.photos or not self.source_folder:
            return
        
        # Toggle buttons: hide quality, show stop
        self.quality_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.stop_btn.setEnabled(True)
        self.stop_btn.setText('⏹ Stop')
        
        # Clear previous quality data
        self.quality_data.clear()
        
        # Output file path
        output_file = self.source_folder / 'quality-info.txt'
        
        # Start analyzer thread with performance settings
        self.quality_analyzer = QualityAnalyzer(
            self.photos, 
            str(output_file),
            cpu_workers=self.cpu_workers,
            use_gpu=self.use_gpu
        )
        self.quality_analyzer.progress_update.connect(self.on_quality_progress)
        self.quality_analyzer.quality_result.connect(self.on_quality_result)
        self.quality_analyzer.analysis_complete.connect(self.on_quality_complete)
        self.quality_analyzer.start()
        
        mode_info = f"GPU (CUDA)" if self.use_gpu else f"CPU ({self.cpu_workers} workers)"
        self.status_bar.showMessage(f'Memulai analisis kualitas ({mode_info})...')
    
    def on_quality_progress(self, current, total):
        """Update progress bar during quality analysis"""
        progress_text = f'Analisis kualitas: {current}/{total}'
        self.status_bar.showMessage(progress_text)
    
    def on_quality_result(self, index, metrics, recommendation):
        """Store quality result for a photo"""
        self.quality_data[index] = (metrics, recommendation)
        
        # Update current photo display if it's the one being shown
        if index == self.current_index:
            self.update_quality_display(index)
    
    def on_quality_complete(self, message):
        """Handle quality analysis completion"""
        # Reset buttons: show quality, hide stop
        self.quality_btn.setVisible(True)
        self.quality_btn.setEnabled(True)
        self.quality_btn.setText('⚡ ANALISIS KUALITAS')
        self.stop_btn.setVisible(False)
        
        QMessageBox.information(
            self,
            'Analisis Selesai',
            message
        )
        
        # Update display to show quality info for current photo
        if self.photos and self.current_index < len(self.photos):
            self.update_quality_display(self.current_index)
    
    
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        # Redisplay current photo to rescale
        if self.photos and self.current_index < len(self.photos):
            self.display_current_photo()


def main():
    """Main entry point"""
    # Set attribute to use native dialogs BEFORE creating QApplication
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, False)
    
    app = QApplication(sys.argv)
    app.setApplicationName('Photosortman')
    app.setOrganizationName('Photosortman')
    
    # Force platform integration for KDE
    app.setDesktopFileName('photoman')
    
    window = PhotoSorterApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

