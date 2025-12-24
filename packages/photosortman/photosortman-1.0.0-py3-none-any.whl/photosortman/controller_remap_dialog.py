#!/usr/bin/env python3
"""
Controller Remapping Dialog for Photosortman
Allows users to customize game controller button mappings
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QMessageBox, QScrollArea, QWidget, QApplication
)
from PyQt6.QtCore import Qt, QTimer
import pygame


class ControllerRemapDialog(QDialog):
    """Dialog for remapping controller buttons"""
    
    def __init__(self, parent, controller, current_mapping, colors):
        super().__init__(parent)
        self.controller = controller
        self.current_mapping = current_mapping.copy()
        self.colors = colors
        self.capturing = False
        self.capture_action = None
        self.remap_buttons = {}
        
        # Controller navigation state
        self.current_focus_index = 0
        self.action_list = []  # Will be populated after UI creation
        self.last_lt_value = 0
        self.last_rt_value = 0
        self.last_a_pressed = False
        self.navigation_triggered = False  # Flag to skip A button after navigation trigger
        
        self.setWindowTitle('🎮 Controller Remapping')
        self.setModal(True)
        self.setMinimumSize(600, 700)
        
        self.init_ui()
        
        # Timer for button capture - start immediately for RB+B close
        self.capture_timer = QTimer()
        self.capture_timer.timeout.connect(self.check_button_press)
        self.capture_timer.start(16)  # Always running for RB+B close
        
    def init_ui(self):
        """Initialize UI layout"""
        main_layout = QVBoxLayout()
        
        # Instruction label
        inst_label = QLabel('💡 Click "Remap" next to an action, then press the desired controller button\nRB+A to Save  |  RB+B to Cancel')
        inst_label.setStyleSheet('''
            QLabel {
                font-weight: bold;
                padding: 10px;
                background-color: #2a2a2a;
                border-radius: 5px;
                color: #00f0ff;
            }
        ''')
        inst_label.setWordWrap(True)
        main_layout.addWidget(inst_label)
        
        # Scroll area for mappings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Navigation section
        nav_group = self.create_section('🎯 Navigation', [
            ('nav_prev', 'Previous Photo'),
            ('nav_next', 'Next Photo'),
        ])
        scroll_layout.addWidget(nav_group)
        
        # Categorization section
        cat_group = self.create_section('⭐ Categorization', [
            ('cat_best', 'Best'),
            ('cat_standard', 'Standard'),
            ('cat_bad', 'Bad'),
        ])
        scroll_layout.addWidget(cat_group)
        
        # Actions section
        act_group = self.create_section('🎬 Actions', [
            ('action_folder', 'Select Folder'),
            ('action_analysis', 'Start Analysis'),
            ('toggle_sound', 'Toggle Sound'),
        ])
        scroll_layout.addWidget(act_group)
        
        # LB Combos section
        lb_group = self.create_section('🅻 LB + D-Pad Combos', [
            ('lb_cpu_dec', 'CPU Workers -'),
            ('lb_cpu_inc', 'CPU Workers +'),
            ('lb_sound', 'Toggle Sound'),
            ('lb_gpu', 'Toggle GPU'),
        ])
        scroll_layout.addWidget(lb_group)
        
        # RB Combos section
        rb_group = self.create_section('🆁 RB Combos', [
            ('rb_about', 'RB + About'),
            ('rb_reconnect', 'RB + Reconnect'),
            ('rb_close_dialog', 'RB+B + Close Dialog'),
            ('rb_copy', 'RB + Toggle Copy'),
            ('rb_theme', 'RB + Toggle Theme'),
        ])
        scroll_layout.addWidget(rb_group)
        
        # D-Pad Navigation section
        dpad_group = self.create_section('🎮 D-Pad Navigation', [
            ('dpad_nav_up', 'Navigate Up'),
            ('dpad_nav_down', 'Navigate Down'),
            ('dpad_nav_left', 'Navigate Left'),
            ('dpad_nav_right', 'Navigate Right'),
        ])
        scroll_layout.addWidget(dpad_group)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Build action list for navigation (in order of appearance)
        self.action_list = list(self.remap_buttons.keys())
        
        # Set initial focus on first action
        if self.action_list:
            self.update_focus_highlight()
        
        # Store scroll area reference for auto-scrolling
        self.scroll_area = scroll
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton('🔄 Reset to Default')
        reset_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5252;
            }
        ''')
        reset_btn.clicked.connect(self.reset_to_default)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton('❌ Cancel')
        cancel_btn.setStyleSheet('''
            QPushButton {
                background-color: #666666;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        ''')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton('💾 Save')
        save_btn.setStyleSheet('''
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        ''')
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # Apply dark theme
        self.setStyleSheet('''
            QDialog {
                background-color: #1a1a2e;
                color: #e0e0ff;
            }
            QGroupBox {
                border: 2px solid #00f0ff;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
                font-weight: bold;
                color: #00f0ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #e0e0ff;
            }
        ''')
    
    def create_section(self, title, actions):
        """Create a section group with actions"""
        group = QGroupBox(title)
        grid = QGridLayout()
        grid.setSpacing(10)
        
        for i, (action_key, action_name) in enumerate(actions):
            # Action label
            label = QLabel(action_name + ':')
            label.setStyleSheet('font-weight: normal; padding: 5px;')
            grid.addWidget(label, i, 0)
            
            # Current mapping display
            mapping_label = QLabel(self.get_mapping_display(action_key))
            mapping_label.setStyleSheet('''
                QLabel {
                    padding: 8px 12px;
                    background-color: #2a2a3e;
                    border: 1px solid #00f0ff;
                    border-radius: 5px;
                    font-family: monospace;
                    font-weight: bold;
                    color: #00f0ff;
                }
            ''')
            mapping_label.setMinimumWidth(150)
            grid.addWidget(mapping_label, i, 1)
            
            # Remap button
            remap_btn = QPushButton('🔧 Remap')
            remap_btn.setStyleSheet('''
                QPushButton {
                    background-color: #16213e;
                    color: #00f0ff;
                    border: 1px solid #00f0ff;
                    padding: 6px 12px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1f2937;
                }
            ''')
            remap_btn.clicked.connect(lambda checked, key=action_key: self.start_capture(key))
            grid.addWidget(remap_btn, i, 2)
            
            # Store references
            self.remap_buttons[action_key] = (mapping_label, remap_btn)
        
        group.setLayout(grid)
        return group
    
    def get_mapping_display(self, action_key):
        """Get display string for current mapping"""
        mapping = self.current_mapping.get(action_key)
        if not mapping:
            return '❌ Not set'
        
        map_type, value = mapping
        if map_type == 'trigger':
            trigger_name = 'LT' if value == 2 else 'RT' if value == 5 else f'Trigger {value}'
            return f'🎯 {trigger_name}'
        elif map_type == 'trigger_combo':
            modifier, axis = value
            mod_str = '🅻 LB' if modifier == 'lb' else '🆁 RB'
            trigger_name = 'LT' if axis == 2 else 'RT' if axis == 5 else f'Trigger {axis}'
            return f'{mod_str} + 🎯 {trigger_name}'
        elif map_type == 'button':
            button_names = {0: 'A', 1: 'B', 2: 'X', 3: 'Y', 6: 'Select', 7: 'Start'}
            btn_name = button_names.get(value, f'Button {value}')
            return f'🔘 {btn_name}'
        elif map_type == 'button_combo':
            modifier, btn = value
            mod_str = '🅻 LB' if modifier == 'lb' else '🆁 RB'
            button_names = {0: 'A', 1: 'B', 2: 'X', 3: 'Y', 6: 'Select', 7: 'Start'}
            btn_name = button_names.get(btn, f'Button {btn}')
            return f'{mod_str} + 🔘 {btn_name}'
        elif map_type == 'hat':
            x, y = value
            if y == 1: return '⬆️ D-Pad Up'
            elif y == -1: return '⬇️ D-Pad Down'
            elif x == -1: return '⬅️ D-Pad Left'
            elif x == 1: return '➡️ D-Pad Right'
        elif map_type == 'hat_combo':
            modifier, x, y = value
            mod_str = '🅻 LB' if modifier == 'lb' else '🆁 RB'
            if y == 1: return f'{mod_str} + ⬆️'
            elif y == -1: return f'{mod_str} + ⬇️'
            elif x == -1: return f'{mod_str} + ⬅️'
            elif x == 1: return f'{mod_str} + ➡️'
        
        return str(value)
    
    def start_capture(self, action_key):
        """Start capturing button press for action"""
        self.capturing = True
        self.capture_action = action_key
        
        # Update button text and style
        mapping_label, remap_btn = self.remap_buttons[action_key]
        remap_btn.setText('⏺️ Press button...')
        remap_btn.setStyleSheet('''
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: 2px solid #ff5252;
                padding: 6px 12px;
                border-radius: 5px;
                font-weight: bold;
            }
        ''')
        
        # Start capture timer
        self.capture_timer.start(16)  # 60 FPS
    
    def check_button_press(self):
        """Check for button press during capture"""
        if not self.controller:
            return
        
        try:
            pygame.event.pump()
            
            # Check for RB+B to close dialog (works even when not capturing)
            rb_pressed = self.controller.get_button(5) if self.controller.get_numbuttons() > 5 else False
            b_pressed = self.controller.get_button(1) if self.controller.get_numbuttons() > 1 else False
            a_pressed = self.controller.get_button(0) if self.controller.get_numbuttons() > 0 else False
            
            if rb_pressed and b_pressed:
                self.reject()
                return
            
            # Check for RB+A to save and close dialog
            if rb_pressed and a_pressed:
                self.accept()
                return
        except:
            pass
        
        # Only continue if capturing
        if not self.capturing:
            # Controller navigation (only when not capturing)
            try:
                # LT/RT for navigation
                lt_value = self.controller.get_axis(2) if self.controller.get_numaxes() > 2 else 0
                rt_value = self.controller.get_axis(5) if self.controller.get_numaxes() > 5 else 0
                
                # LT - Previous action (trigger threshold 0.5)
                if lt_value > 0.5 and self.last_lt_value <= 0.5:
                    self.navigate_previous()
                self.last_lt_value = lt_value
                
                # RT - Next action (trigger threshold 0.5)
                if rt_value > 0.5 and self.last_rt_value <= 0.5:
                    self.navigate_next()
                self.last_rt_value = rt_value
                
                # A button - Trigger remap on focused action
                a_pressed = self.controller.get_button(0) if self.controller.get_numbuttons() > 0 else False
                if a_pressed and not self.last_a_pressed:
                    self.trigger_focused_remap()
                self.last_a_pressed = a_pressed
                
            except:
                pass
            return
        
        try:
            pygame.event.pump()
            
            # Check if LB or RB is pressed (for combos)
            lb_pressed = self.controller.get_button(4) if self.controller.get_numbuttons() > 4 else False
            rb_pressed = self.controller.get_button(5) if self.controller.get_numbuttons() > 5 else False
            
            # Check triggers
            for axis_idx in [2, 5]:  # LT and RT
                if self.controller.get_numaxes() > axis_idx:
                    value = self.controller.get_axis(axis_idx)
                    if value > 0.5:
                        if lb_pressed:
                            self.assign_mapping(('trigger_combo', ('lb', axis_idx)))
                        elif rb_pressed:
                            self.assign_mapping(('trigger_combo', ('rb', axis_idx)))
                        else:
                            self.assign_mapping(('trigger', axis_idx))
                        return
            
            # Check buttons (skip LB/RB themselves)
            for btn_idx in range(self.controller.get_numbuttons()):
                if btn_idx in [4, 5]:  # Skip LB and RB
                    continue
                
                # Skip A button (0) if triggered by navigation
                if btn_idx == 0 and self.navigation_triggered:
                    # Only clear flag if A is not pressed (released)
                    if not self.controller.get_button(0):
                        self.navigation_triggered = False
                    continue
                
                if self.controller.get_button(btn_idx):
                    if lb_pressed:
                        self.assign_mapping(('button_combo', ('lb', btn_idx)))
                    elif rb_pressed:
                        self.assign_mapping(('button_combo', ('rb', btn_idx)))
                    else:
                        self.assign_mapping(('button', btn_idx))
                    return
            
            # Check D-Pad
            if self.controller.get_numhats() > 0:
                hat = self.controller.get_hat(0)
                if hat != (0, 0):
                    if lb_pressed:
                        self.assign_mapping(('hat_combo', ('lb', hat[0], hat[1])))
                    elif rb_pressed:
                        self.assign_mapping(('hat_combo', ('rb', hat[0], hat[1])))
                    else:
                        self.assign_mapping(('hat', hat))
                    return
        
        except Exception as e:
            print(f"Capture error: {e}")
    
    def find_duplicate_mapping(self, new_mapping):
        """Find if this mapping is already used by another action"""
        for action_key, mapping in self.current_mapping.items():
            if action_key == self.capture_action:
                continue
            if mapping == new_mapping:
                return action_key
        return None
    
    def assign_mapping(self, new_mapping):
        """Assign new mapping to action with duplicate detection"""
        # Check for duplicates
        duplicate_action = self.find_duplicate_mapping(new_mapping)
        
        if duplicate_action:
            # Show warning dialog
            action_names = {
                'nav_prev': 'Previous Photo',
                'nav_next': 'Next Photo',
                'cat_best': 'Best',
                'cat_bad': 'Bad',
                'cat_standard': 'Standard',
                'action_folder': 'Select Folder',
                'action_analysis': 'Start Analysis',
                'toggle_sound': 'Toggle Sound',
                'lb_cpu_dec': 'LB + CPU Workers -',
                'lb_cpu_inc': 'LB + CPU Workers +',
                'lb_sound': 'LB + Toggle Sound',
                'lb_gpu': 'LB + Toggle GPU',
                'rb_about': 'RB + About',
                'rb_reconnect': 'RB + Reconnect',
                'rb_close_dialog': 'RB+B + Close Dialog',
                'rb_copy': 'RB + Toggle Copy',
                'rb_theme': 'RB + Toggle Theme',
                'dpad_nav_up': 'D-Pad Navigate Up',
                'dpad_nav_down': 'D-Pad Navigate Down',
                'dpad_nav_left': 'D-Pad Navigate Left',
                'dpad_nav_right': 'D-Pad Navigate Right',
            }
            
            duplicate_name = action_names.get(duplicate_action, duplicate_action)
            mapping_display = self.get_mapping_display_from_value(new_mapping)
            
            # Create message box
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('⚠️ Duplicate Mapping')
            msg_box.setText(f'This button ({mapping_display}) is already assigned to:\n\n'
                           f'"{duplicate_name}"\n\n'
                           f'Do you want to unset the old mapping and use it here?\n\n'
                           f'A = Yes  |  B = No')
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            
            # Show non-blocking and poll controller
            msg_box.show()
            
            # Poll controller for A (Yes) or B (No)
            while msg_box.isVisible():
                pygame.event.pump()
                
                try:
                    a_pressed = self.controller.get_button(0) if self.controller.get_numbuttons() > 0 else False
                    b_pressed = self.controller.get_button(1) if self.controller.get_numbuttons() > 1 else False
                    
                    if a_pressed:
                        msg_box.done(QMessageBox.StandardButton.Yes)
                        break
                    elif b_pressed:
                        msg_box.done(QMessageBox.StandardButton.No)
                        break
                except:
                    pass
                
                # Process Qt events
                QApplication.processEvents()
            
            reply = msg_box.result()
            
            if reply == QMessageBox.StandardButton.Yes:
                # Unset the old mapping
                self.current_mapping[duplicate_action] = None
                # Update old mapping display
                if duplicate_action in self.remap_buttons:
                    old_label, _ = self.remap_buttons[duplicate_action]
                    old_label.setText('❌ Not set')
            else:
                # Cancel this assignment
                self.stop_capturing()
                return
        
        # Assign the new mapping
        self.current_mapping[self.capture_action] = new_mapping
        
        # Update display
        mapping_label, remap_btn = self.remap_buttons[self.capture_action]
        mapping_label.setText(self.get_mapping_display(self.capture_action))
        
        self.stop_capturing()
    
    def stop_capturing(self):
        """Stop capturing and reset button state"""
        if self.capture_action and self.capture_action in self.remap_buttons:
            _, remap_btn = self.remap_buttons[self.capture_action]
            remap_btn.setText('🔧 Remap')
            remap_btn.setStyleSheet('''
                QPushButton {
                    background-color: #16213e;
                    color: #00f0ff;
                    border: 1px solid #00f0ff;
                    padding: 6px 12px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1f2937;
                }
            ''')
        
        self.capturing = False
        self.capture_action = None
    
    def get_mapping_display_from_value(self, mapping):
        """Get display string from mapping value (for duplicate warning)"""
        if not mapping:
            return 'Not set'
        
        map_type, value = mapping
        if map_type == 'trigger':
            trigger_name = 'LT' if value == 2 else 'RT' if value == 5 else f'Trigger {value}'
            return trigger_name
        elif map_type == 'trigger_combo':
            modifier, axis = value
            mod_str = 'LB' if modifier == 'lb' else 'RB'
            trigger_name = 'LT' if axis == 2 else 'RT' if axis == 5 else f'Trigger {axis}'
            return f'{mod_str} + {trigger_name}'
        elif map_type == 'button':
            button_names = {0: 'A', 1: 'B', 2: 'X', 3: 'Y', 6: 'Select', 7: 'Start'}
            return button_names.get(value, f'Button {value}')
        elif map_type == 'button_combo':
            modifier, btn = value
            mod_str = 'LB' if modifier == 'lb' else 'RB'
            button_names = {0: 'A', 1: 'B', 2: 'X', 3: 'Y', 6: 'Select', 7: 'Start'}
            btn_name = button_names.get(btn, f'Button {btn}')
            return f'{mod_str} + {btn_name}'
        elif map_type == 'hat':
            x, y = value
            if y == 1: return 'D-Pad Up'
            elif y == -1: return 'D-Pad Down'
            elif x == -1: return 'D-Pad Left'
            elif x == 1: return 'D-Pad Right'
        elif map_type == 'hat_combo':
            modifier, x, y = value
            mod_str = 'LB' if modifier == 'lb' else 'RB'
            if y == 1: return f'{mod_str} + D-Pad Up'
            elif y == -1: return f'{mod_str} + D-Pad Down'
            elif x == -1: return f'{mod_str} + D-Pad Left'
            elif x == 1: return f'{mod_str} + D-Pad Right'
        
        return str(value)
    
    def reset_to_default(self):
        """Reset all mappings to default"""
        from photoman import DEFAULT_CONTROLLER_MAPPING
        
        reply = QMessageBox.question(
            self,
            'Reset to Default',
            'Are you sure you want to reset all mappings to default?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_mapping = DEFAULT_CONTROLLER_MAPPING.copy()
            
            # Update all displays
            for action_key, (mapping_label, _) in self.remap_buttons.items():
                mapping_label.setText(self.get_mapping_display(action_key))
    
    def navigate_previous(self):
        """Navigate to previous action"""
        if not self.action_list:
            return
        self.current_focus_index = (self.current_focus_index - 1) % len(self.action_list)
        self.update_focus_highlight()
    
    def navigate_next(self):
        """Navigate to next action"""
        if not self.action_list:
            return
        self.current_focus_index = (self.current_focus_index + 1) % len(self.action_list)
        self.update_focus_highlight()
    
    def trigger_focused_remap(self):
        """Trigger remap for currently focused action"""
        if not self.action_list or self.current_focus_index >= len(self.action_list):
            return
        focused_action = self.action_list[self.current_focus_index]
        self.navigation_triggered = True  # Set flag to skip A button in next capture
        self.start_capture(focused_action)
    
    def update_focus_highlight(self):
        """Update visual highlight for focused action"""
        for i, action_key in enumerate(self.action_list):
            if action_key in self.remap_buttons:
                mapping_label, remap_btn = self.remap_buttons[action_key]
                
                if i == self.current_focus_index:
                    # Highlight focused action
                    remap_btn.setStyleSheet(f'''
                        QPushButton {{
                            background-color: #00f0ff;
                            color: #000;
                            border: 2px solid #00f0ff;
                            padding: 6px 12px;
                            border-radius: 5px;
                            font-weight: bold;
                        }}
                        QPushButton:hover {{
                            background-color: #00d0df;
                        }}
                    ''')
                else:
                    # Normal style
                    remap_btn.setStyleSheet('''
                        QPushButton {
                            background-color: #16213e;
                            color: #00f0ff;
                            border: 1px solid #00f0ff;
                            padding: 6px 12px;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #1f2937;
                        }
                    ''')
        
        # Auto-scroll to focused action
        if hasattr(self, 'scroll_area') and self.action_list:
            focused_action = self.action_list[self.current_focus_index]
            if focused_action in self.remap_buttons:
                _, remap_btn = self.remap_buttons[focused_action]
                self.scroll_area.ensureWidgetVisible(remap_btn)
    
    def get_mappings(self):
        """Get the current mapping"""
        return self.current_mapping
