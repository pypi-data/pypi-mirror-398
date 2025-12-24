"""
WinNap UI Library v3.1
Auto start first page without welcome screen
"""

from customtkinter import *
import threading
import time
import os
import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Callable, List, Tuple, Dict, Any
import json

# ============================================================================
# WINNAP CORE CLASSES
# ============================================================================

class WinNapTheme:
    """Theme management for WinNap"""
    
    THEMES = {
        "dark": {
            "primary": "#0066FF",
            "primary_light": "#3399FF",  # Lighter version for highlights
            "secondary": "#8B5CF6",
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "background": "#0F172A",
            "surface": "#1E293B",
            "text_primary": "#F1F5F9",
            "text_secondary": "#94A3B8",
            "border": "#334155",
            "accent": "#3B82F6",
        },
        "light": {
            "primary": "#3B82F6",
            "primary_light": "#60A5FA",
            "secondary": "#8B5CF6",
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "background": "#F8FAFC",
            "surface": "#FFFFFF",
            "text_primary": "#0F172A",
            "text_secondary": "#475569",
            "border": "#E2E8F0",
            "accent": "#6366F1",
        },
        "purple": {
            "primary": "#8B5CF6",
            "primary_light": "#A78BFA",
            "secondary": "#EC4899",
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "background": "#1E1B2E",
            "surface": "#2A2540",
            "text_primary": "#F1F5F9",
            "text_secondary": "#C4B5FD",
            "border": "#4C1D95",
            "accent": "#A855F7",
        },
        "cyberpunk": {
            "primary": "#00FF9D",
            "primary_light": "#33FFB1",
            "secondary": "#FF00FF",
            "success": "#00FF9D",
            "warning": "#FF9D00",
            "danger": "#FF006E",
            "background": "#0A0A0F",
            "surface": "#1A1A2E",
            "text_primary": "#FFFFFF",
            "text_secondary": "#8A8DFF",
            "border": "#00FF9D",
            "accent": "#8A8DFF",
        }
    }
    
    @classmethod
    def get_theme(cls, theme_name: str = "dark") -> dict:
        """Get theme configuration"""
        return cls.THEMES.get(theme_name, cls.THEMES["dark"]).copy()
    
    @classmethod
    def list_themes(cls) -> List[str]:
        """List available themes"""
        return list(cls.THEMES.keys())


class WinNapWindow:
    """
    Main window class with modern styling and features
    Auto starts with first page - NO WELCOME SCREEN
    """
    
    def __init__(
        self,
        title: str = "WinNap App",
        width: int = 900,
        height: int = 600,
        theme: str = "dark",
        topmost: bool = True,
        resizable: bool = True,
        center: bool = True
    ):
        """
        Initialize WinNap window
        """
        self.title = title
        self.width = width
        self.height = height
        self.theme_name = theme
        self.theme = WinNapTheme.get_theme(theme)
        self.topmost = topmost
        
        # Create main window
        self.root = CTk()
        
        # Configure appearance
        set_appearance_mode("dark" if "dark" in theme else "light")
        set_default_color_theme("blue")
        
        # Set window properties
        if center:
            self.center_window()
        else:
            self.x = 100
            self.y = 100
        
        self.root.title(title)
        self.root.geometry(f"{width}x{height}+{self.x}+{self.y}")
        self.root.overrideredirect(True)
        if topmost:
            self.root.attributes("-topmost", True)
        
        if not resizable:
            self.root.resizable(False, False)
        
        # Configure colors
        self.root.configure(fg_color=self.theme["background"])
        
        # Draggable window
        self.root.x = None
        self.root.y = None
        self.root.bind("<ButtonPress-1>", self._start_move)
        self.root.bind("<B1-Motion>", self._on_move)
        
        # Close with Escape
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        
        # Track components
        self.components = {}
        self.sidebar_buttons = {}
        self.pages = {}
        self.current_page = None
        
        # Track first page
        self.first_page_added = False
        self.first_page_name = None
        
        # Initialize UI
        self._setup_grid()
        self._create_title_bar()
        self._create_sidebar()
        self._create_main_area()
        self._create_status_bar()
        
        # Active page tracking
        self.active_page_name = None
        
        # Track active popups
        self.active_popups = []
    
    def center_window(self):
        """Center window on screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.x = (screen_width // 2) - (self.width // 2)
        self.y = (screen_height // 2) - (self.height // 2)
    
    def _start_move(self, event):
        """Start window movement"""
        self.root.x = event.x
        self.root.y = event.y
    
    def _on_move(self, event):
        """Handle window movement"""
        x = self.root.winfo_x() + (event.x - self.root.x)
        y = self.root.winfo_y() + (event.y - self.root.y)
        self.root.geometry(f"+{x}+{y}")
    
    def _setup_grid(self):
        """Setup grid layout"""
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
    
    def _create_title_bar(self):
        """Create modern title bar"""
        # Title bar container
        self.title_bar = CTkFrame(
            self.root,
            height=40,
            fg_color=self.theme["surface"],
            corner_radius=0
        )
        self.title_bar.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.title_bar.grid_columnconfigure(1, weight=1)
        
        # Drag area for moving window
        drag_area = CTkFrame(self.title_bar, fg_color="transparent")
        drag_area.grid(row=0, column=0, padx=(15, 0), sticky="w")
        
        # App icon and title
        icon_label = CTkLabel(
            drag_area,
            text="⚡",
            font=("Segoe UI", 18),
            text_color=self.theme["primary"]
        )
        icon_label.pack(side="left", padx=(0, 8))
        
        self.title_label = CTkLabel(
            drag_area,
            text=self.title,
            font=("Segoe UI", 14, "bold"),
            text_color=self.theme["text_primary"]
        )
        self.title_label.pack(side="left")
        
        # Window controls
        controls_frame = CTkFrame(self.title_bar, fg_color="transparent")
        controls_frame.grid(row=0, column=2, padx=(0, 5), sticky="e")
        
        # Close button
        CTkButton(
            controls_frame,
            text="✕",
            width=30,
            height=30,
            command=self.root.destroy,
            fg_color="transparent",
            hover_color=self.theme["danger"],
            text_color=self.theme["text_secondary"],
            font=("Segoe UI", 12, "bold"),
            corner_radius=6
        ).pack(side="left", padx=2)
    
    def _create_sidebar(self):
        """Create sidebar navigation"""
        # Sidebar container
        self.sidebar = CTkFrame(
            self.root,
            width=200,
            fg_color=self.theme["surface"],
            corner_radius=0
        )
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # ลบส่วน App branding ทั้งหมดออก
        # ไม่สร้าง brand_frame แล้ว
        
        # Separator - เริ่มจากเส้นคั่นได้เลย
        CTkFrame(
            self.sidebar,
            height=1,
            fg_color=self.theme["border"]
        ).pack(fill="x", pady=15, padx=15)
        
        # Navigation label
        CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=("Segoe UI", 10, "bold"),
            text_color=self.theme["text_secondary"]
        ).pack(pady=(0, 8), padx=15, anchor="w")
        
        # Navigation buttons container
        self.nav_container = CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            height=350
        )
        self.nav_container.pack(fill="both", expand=True, padx=8, pady=5)
    
    def _create_main_area(self):
        """Create main content area"""
        self.main_area = CTkFrame(
            self.root,
            fg_color=self.theme["background"]
        )
        self.main_area.grid(row=1, column=1, sticky="nsew")
        
        # NO DEFAULT WELCOME PAGE - we'll show first page automatically
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_bar = CTkFrame(
            self.root,
            height=25,
            fg_color=self.theme["surface"]
        )
        self.status_bar.grid(row=2, column=0, columnspan=2, sticky="nsew")
        
        # Status label
        self.status_label = CTkLabel(
            self.status_bar,
            text="Ready",
            font=("Segoe UI", 9),
            text_color=self.theme["text_secondary"]
        )
        self.status_label.pack(side="left", padx=12)
        
        # Version info
        CTkLabel(
            self.status_bar,
            text="WinNap v3.1",
            font=("Segoe UI", 9),
            text_color=self.theme["text_secondary"]
        ).pack(side="right", padx=12)
    
    # ==================== PUBLIC API ====================
    
    def add_page(
        self,
        name: str,
        title: str,
        icon: Optional[str] = None
    ) -> 'WinNapPage':
        """
        Add a new page to the application
        Auto switches to first page added
        """
        # Create page frame
        page_frame = CTkScrollableFrame(
            self.main_area,
            fg_color="transparent",
            border_width=0
        )
        page_frame.pack_forget()  # Hide initially
        
        # Store page
        page = WinNapPage(name, title, page_frame, self.theme)
        self.pages[name] = page
        
        # Create sidebar button
        self._add_sidebar_button(name, title, icon)
        
        # If this is the first page added, switch to it automatically
        if not self.first_page_added:
            self.first_page_added = True
            self.first_page_name = name
            # Switch to first page after a short delay
            self.root.after(100, lambda: self._auto_switch_first_page(name))
        
        return page
    
    def _auto_switch_first_page(self, page_name: str):
        """Automatically switch to first page after UI is ready"""
        if page_name in self.pages:
            self.switch_page(page_name)
    
    def _add_sidebar_button(self, page_name: str, title: str, icon: Optional[str]):
        """Add button to sidebar"""
        # Create button text
        if icon:
            button_text = f"  {icon}  {title}"
        else:
            button_text = f"  {title}"
        
        # Create button
        button = CTkButton(
            self.nav_container,
            text=button_text,
            anchor="w",
            height=40,
            fg_color="transparent",
            hover_color=self.theme["border"],
            text_color=self.theme["text_secondary"],
            font=("Segoe UI", 13),
            command=lambda pn=page_name: self.switch_page(pn),
            corner_radius=6
        )
        button.pack(fill="x", padx=4, pady=1)
        
        self.sidebar_buttons[page_name] = button
    
    def switch_page(self, page_name: str):
        """
        Switch to a different page
        """
        # Reset previous active button
        if self.active_page_name and self.active_page_name in self.sidebar_buttons:
            self.sidebar_buttons[self.active_page_name].configure(
                fg_color="transparent",
                text_color=self.theme["text_secondary"]
            )
        
        # Hide current page
        if self.current_page and self.current_page in self.pages:
            self.pages[self.current_page].frame.pack_forget()
        
        # Show new page
        if page_name in self.pages:
            page = self.pages[page_name]
            page.frame.pack(expand=True, fill="both", padx=20, pady=20)
            
            # Highlight button for active page
            if page_name in self.sidebar_buttons:
                self.sidebar_buttons[page_name].configure(
                    fg_color=self.theme["primary_light"],
                    text_color=self.theme["text_primary"]
                )
            
            # Update title
            self.title_label.configure(text=f"{self.title} - {page.title}")
            
            # Set current page
            self.current_page = page_name
            self.active_page_name = page_name
            
            # Update status
            self.set_status(f"Viewing {page.title}")
    
    def set_status(self, message: str):
        """
        Set status bar message
        """
        self.status_label.configure(text=message)
    
    def show_notification(self, message: str, duration: int = 3):
        """
        Show a notification
        """
        WinNapNotification(self.root, message, duration, self.theme)
    
    def show_popup(self, message: str, title: str = "", ok_text: str = "OK", 
                  cancel_text: str = "CANCEL", on_ok: Callable = None, 
                  on_cancel: Callable = None, width: int = 400, 
                  height: int = 220, icon: str = None, 
                  input_mode: bool = False, default_value: str = "",
                  input_type: str = "text") -> 'WinNapPopup':
        """
        Show a popup dialog with OK and CANCEL buttons
        
        Args:
            message: Message to display
            title: Popup title (optional)
            ok_text: Text for OK button
            cancel_text: Text for CANCEL button
            on_ok: Callback when OK is clicked
            on_cancel: Callback when CANCEL is clicked
            width: Popup width
            height: Popup height
            icon: Icon to display (optional)
            input_mode: Enable input field
            default_value: Default value for input field
            input_type: Type of input ("text", "password", "number")
        
        Returns:
            WinNapPopup instance
        """
        popup = WinNapPopup(
            self.root, 
            message=message,
            title=title,
            ok_text=ok_text, 
            cancel_text=cancel_text, 
            on_ok=on_ok, 
            on_cancel=on_cancel,
            width=width,
            height=height,
            icon=icon,
            input_mode=input_mode,
            default_value=default_value,
            input_type=input_type,
            theme=self.theme
        )
        self.active_popups.append(popup)
        return popup
    
    def show_alert(self, message: str, title: str = "Alert", 
                  on_ok: Callable = None) -> 'WinNapPopup':
        """
        Show an alert dialog with only OK button
        
        Returns:
            WinNapPopup instance
        """
        return self.show_popup(
            message=message,
            title=title,
            ok_text="OK",
            cancel_text=None,
            on_ok=on_ok,
            on_cancel=None,
            height=200
        )
    
    def show_confirm(self, message: str, title: str = "Confirm",
                    on_confirm: Callable = None, on_cancel: Callable = None) -> 'WinNapPopup':
        """
        Show a confirmation dialog
        
        Returns:
            WinNapPopup instance
        """
        return self.show_popup(
            message=message,
            title=title,
            ok_text="CONFIRM",
            cancel_text="CANCEL",
            on_ok=on_confirm,
            on_cancel=on_cancel,
            height=220
        )
    
    def show_input(self, message: str, title: str = "Input",
                  default_value: str = "", ok_text: str = "OK",
                  cancel_text: str = "CANCEL", on_submit: Callable = None,
                  input_type: str = "text") -> 'WinNapPopup':
        """
        Show an input dialog with text entry
        
        Args:
            message: Message to display
            title: Dialog title
            default_value: Default value for input
            ok_text: Text for OK button
            cancel_text: Text for CANCEL button
            on_submit: Callback when submitted (receives input value)
            input_type: Type of input ("text", "password", "number")
        
        Returns:
            WinNapPopup instance with get_value() method
        """
        popup = WinNapPopup(
            self.root,
            message=message,
            title=title,
            ok_text=ok_text,
            cancel_text=cancel_text,
            on_ok=on_submit,
            on_cancel=None,
            input_mode=True,
            default_value=default_value,
            input_type=input_type,
            theme=self.theme,
            height=240
        )
        self.active_popups.append(popup)
        return popup
    
    def close_all_popups(self):
        """Close all active popups"""
        for popup in self.active_popups[:]:
            if hasattr(popup, 'popup') and popup.popup.winfo_exists():
                popup.popup.destroy()
                if popup in self.active_popups:
                    self.active_popups.remove(popup)
    
    def run(self):
        """Run the application"""
        self.root.mainloop()
    
    def get_root(self):
        """Get the root window"""
        return self.root


class WinNapPopup:
    """
    Popup dialog with OK and CANCEL buttons - FIXED RENDERING VERSION
    """
    
    def __init__(
        self,
        parent,
        message: str,
        title: str = "",
        ok_text: str = "OK",
        cancel_text: str = "CANCEL",
        on_ok: Callable = None,
        on_cancel: Callable = None,
        width: int = 400,
        height: int = 220,
        icon: str = None,
        input_mode: bool = False,
        default_value: str = "",
        input_type: str = "text",
        theme: dict = None
    ):
        self.parent = parent
        self.message = message
        self.title = title
        self.ok_text = ok_text
        self.cancel_text = cancel_text
        self.on_ok = on_ok
        self.on_cancel = on_cancel
        self.width = width
        self.height = height
        self.icon = icon
        self.input_mode = input_mode
        self.default_value = default_value
        self.input_type = input_type
        self.theme = theme or WinNapTheme.get_theme("dark")
        self.result = None
        self.input_value = None
        self.callback_executed = False
        self._content_created = False
        
        # Create popup window
        self.popup = CTkToplevel(parent)
        
        # Remove window title bar
        self.popup.overrideredirect(True)
        
        # Configure colors
        self.popup.configure(fg_color=self.theme["surface"])
        
        # Set size - ใช้ min size ก่อน
        self.popup.geometry(f"{width}x{height}")
        self.popup.resizable(False, False)
        
        # Handle window close
        self.popup.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # ทำให้อยู่ด้านบน
        self.popup.attributes("-topmost", True)
        
        # สร้าง content ทันที
        self._create_content()
        
        # Center popup on parent
        self._center_on_parent()
        
        # Bind Enter and Escape keys
        self._bind_keys()
        
        # Update และ force rendering
        self._update_and_focus()
    
    def _update_and_focus(self):
        """Update window and force focus"""
        if self.popup.winfo_exists():
            # อัพเดทหน้าต่าง
            self.popup.update_idletasks()
            self.popup.update()
            
            # ให้ focus
            self.popup.focus_force()
            
            # ถ้ามี input field ให้ focus ที่ input
            if hasattr(self, 'input_entry') and self.input_entry.winfo_exists():
                self.input_entry.focus_set()
                self.input_entry.icursor("end")  # เลื่อนเคอร์เซอร์ไปท้ายสุด
    
    def _center_on_parent(self):
        """Center popup on parent window"""
        if not self.parent.winfo_exists():
            # ถ้า parent ไม่มีอยู่แล้ว ให้ center บนหน้าจอ
            screen_width = self.popup.winfo_screenwidth()
            screen_height = self.popup.winfo_screenheight()
            x = (screen_width // 2) - (self.width // 2)
            y = (screen_height // 2) - (self.height // 2)
        else:
            parent_x = self.parent.winfo_rootx()
            parent_y = self.parent.winfo_rooty()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()
            
            x = parent_x + (parent_width // 2) - (self.width // 2)
            y = parent_y + (parent_height // 2) - (self.height // 2)
        
        self.popup.geometry(f"{self.width}x{self.height}+{x}+{y}")
    
    def _create_content(self):
        """Create popup content"""
        if self._content_created:
            return
            
        self._content_created = True
        
        # Main content frame
        content_frame = CTkFrame(self.popup, fg_color="transparent")
        content_frame.pack(expand=True, fill="both", padx=25, pady=20)
        
        # Header frame for icon and title
        header_frame = CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        # Icon (if provided) - smaller size
        if self.icon:
            icon_label = CTkLabel(
                header_frame,
                text=self.icon,
                font=("Segoe UI", 28),
                text_color=self.theme["primary"]
            )
            icon_label.pack(side="left", padx=(0, 10))
        
        # Title (only if provided)
        if self.title:
            title_label = CTkLabel(
                header_frame,
                text=self.title,
                font=("Segoe UI", 18, "bold"),
                text_color=self.theme["text_primary"]
            )
            title_label.pack(side="left", fill="x", expand=True)
        else:
            # ถ้าไม่มี title ให้ไอคอนอยู่ตรงกลาง
            if self.icon:
                icon_label.pack(side="left", expand=True)
        
        # Message - ใช้ wraplength ที่เหมาะสม
        message_label = CTkLabel(
            content_frame,
            text=self.message,
            font=("Segoe UI", 14),
            text_color=self.theme["text_secondary"],
            wraplength=self.width - 60,
            justify="left"
        )
        message_label.pack(fill="x", pady=(0, 20) if not self.input_mode else (0, 15))
        
        # Input field (if input mode)
        if self.input_mode:
            input_frame = CTkFrame(content_frame, fg_color="transparent")
            input_frame.pack(fill="x", pady=(0, 20))
            
            # กำหนด placeholder และ show option ตาม input_type
            placeholder = ""
            show_char = None
            
            if self.input_type == "password":
                placeholder = "Enter password..."
                show_char = "•"
            elif self.input_type == "number":
                placeholder = "Enter number..."
            else:
                placeholder = "Enter value..."
            
            self.input_entry = CTkEntry(
                input_frame,
                placeholder_text=placeholder,
                height=40,
                font=("Segoe UI", 13),
                fg_color=self.theme["background"],
                text_color=self.theme["text_primary"],
                border_color=self.theme["border"],
                corner_radius=6,
                show=show_char
            )
            self.input_entry.pack(fill="x")
            if self.default_value:
                self.input_entry.insert(0, self.default_value)
            
            # Validate number input
            if self.input_type == "number":
                def validate_number_input(new_value):
                    if new_value == "" or new_value == "-":
                        return True
                    try:
                        float(new_value)
                        return True
                    except ValueError:
                        return False
                
                # Register validation
                vcmd = (self.popup.register(validate_number_input), '%P')
                self.input_entry.configure(validate="key", validatecommand=vcmd)
        
        # Buttons frame
        buttons_frame = CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(5, 0))
        
        # Add spacer to center buttons
        left_spacer = CTkFrame(buttons_frame, fg_color="transparent", width=20)
        left_spacer.pack(side="left", expand=True)
        
        # CANCEL Button (if cancel_text is provided)
        if self.cancel_text:
            cancel_button = CTkButton(
                buttons_frame,
                text=self.cancel_text,
                width=100,
                height=36,
                command=self._on_cancel_clicked,
                fg_color=self.theme["surface"],
                hover_color=self.theme["border"],
                text_color=self.theme["text_primary"],
                font=("Segoe UI", 13),
                border_color=self.theme["border"],
                border_width=1,
                corner_radius=6
            )
            cancel_button.pack(side="left", padx=(0, 10))
        
        # OK Button
        ok_button = CTkButton(
            buttons_frame,
            text=self.ok_text,
            width=100,
            height=36,
            command=self._on_ok_clicked,
            fg_color=self.theme["primary"],
            hover_color=self.theme["accent"],
            font=("Segoe UI", 13),
            corner_radius=6
        )
        ok_button.pack(side="left")
        
        # Right spacer
        right_spacer = CTkFrame(buttons_frame, fg_color="transparent", width=20)
        right_spacer.pack(side="left", expand=True)
    
    def _bind_keys(self):
        """Bind keyboard shortcuts"""
        self.popup.bind("<Return>", lambda e: self._on_ok_clicked())
        if self.cancel_text:
            self.popup.bind("<Escape>", lambda e: self._on_cancel_clicked())
        else:
            self.popup.bind("<Escape>", lambda e: self._on_ok_clicked())
    
    def _on_ok_clicked(self):
        """Handle OK button click"""
        if self.callback_executed:
            return
            
        self.callback_executed = True
        
        if self.input_mode and hasattr(self, 'input_entry'):
            self.input_value = self.input_entry.get()
        
        self.result = True
        
        # Execute callback
        if self.on_ok:
            try:
                if self.input_mode:
                    self.on_ok(self.input_value)
                else:
                    self.on_ok()
            except Exception as e:
                print(f"Error in popup callback: {e}")
        
        # Destroy popup
        if self.popup.winfo_exists():
            self.popup.destroy()
    
    def _on_cancel_clicked(self):
        """Handle CANCEL button click"""
        if self.callback_executed:
            return
            
        self.callback_executed = True
        
        self.result = False
        
        # Execute callback
        if self.on_cancel:
            try:
                self.on_cancel()
            except Exception as e:
                print(f"Error in popup callback: {e}")
        
        # Destroy popup
        if self.popup.winfo_exists():
            self.popup.destroy()
    
    def _on_close(self):
        """Handle window close event"""
        if self.cancel_text:
            self._on_cancel_clicked()
        else:
            self._on_ok_clicked()
    
    def get_value(self):
        """Get input value (only for input mode)"""
        return self.input_value if self.input_mode else None
    
    def wait_for_result(self):
        """Wait for popup result (blocking)"""
        if self.popup.winfo_exists():
            self.popup.wait_window()
        return self.result
    
    def destroy(self):
        """Destroy the popup"""
        if hasattr(self, 'popup') and self.popup.winfo_exists():
            self.popup.destroy()


class WinNapPage:
    """
    Page container for organizing content
    """
    
    def __init__(self, name: str, title: str, frame: CTkFrame, theme: dict):
        self.name = name
        self.title = title
        self.frame = frame
        self.theme = theme
        self.components = []
    
    def add_header(self, text: str, subtitle: str = None) -> Tuple[CTkLabel, Optional[CTkLabel]]:
        """
        Add header to page
        """
        header = CTkLabel(
            self.frame,
            text=text,
            font=("Segoe UI", 24, "bold"),
            text_color=self.theme["text_primary"]
        )
        header.pack(pady=(0, 8), anchor="w")
        
        subtitle_label = None
        if subtitle:
            subtitle_label = CTkLabel(
                self.frame,
                text=subtitle,
                font=("Segoe UI", 12),
                text_color=self.theme["text_secondary"]
            )
            subtitle_label.pack(pady=(0, 20), anchor="w")
        
        self.components.append(header)
        if subtitle_label:
            self.components.append(subtitle_label)
        
        return header, subtitle_label
    
    def add_card(
        self,
        title: str,
        content: Any = None,
        width: int = None,
        height: int = None
    ) -> 'WinNapCard':
        """
        Add a card container
        """
        card = WinNapCard(self.frame, title, self.theme, width, height)
        card.pack(pady=12, fill="x")
        
        if content:
            if isinstance(content, str):
                card.add_label(content)
        
        self.components.append(card)
        return card
    
    def add_section(self, title: str, description: str = None) -> CTkFrame:
        """
        Add a section
        """
        section = CTkFrame(self.frame, fg_color="transparent")
        section.pack(pady=15, fill="x")
        
        # Section title
        title_label = CTkLabel(
            section,
            text=title,
            font=("Segoe UI", 18, "bold"),
            text_color=self.theme["text_primary"]
        )
        title_label.pack(anchor="w")
        
        # Section description
        if description:
            desc_label = CTkLabel(
                section,
                text=description,
                font=("Segoe UI", 12),
                text_color=self.theme["text_secondary"],
                wraplength=600
            )
            desc_label.pack(anchor="w", pady=(3, 12))
        
        self.components.append(section)
        return section
    
    def add_button(
        self,
        text: str,
        command: Callable = None,
        **kwargs
    ) -> CTkButton:
        """
        Add a button
        """
        # Default style
        btn_kwargs = {
            "text": text,
            "command": command,
            "height": 40,
            "font": ("Segoe UI", 13),
            "fg_color": self.theme["primary"],
            "hover_color": self.theme["accent"],
            "corner_radius": 8
        }
        
        # Override with custom
        btn_kwargs.update(kwargs)
        
        button = CTkButton(self.frame, **btn_kwargs)
        button.pack(pady=8, fill="x")
        
        self.components.append(button)
        return button
    
    def add_switch(
        self,
        text: str,
        command: Callable = None,
        default: bool = False
    ) -> CTkSwitch:
        """
        Add a switch
        """
        switch_frame = CTkFrame(self.frame, fg_color="transparent")
        switch_frame.pack(pady=6, fill="x")
        
        switch = CTkSwitch(
            switch_frame,
            text=text,
            command=command,
            progress_color=self.theme["primary"],
            font=("Segoe UI", 13),
            text_color=self.theme["text_primary"]
        )
        switch.pack(side="left")
        
        if default:
            switch.select()
        
        self.components.append(switch)
        return switch
    
    def add_label(
        self,
        text: str,
        **kwargs
    ) -> CTkLabel:
        """
        Add a label
        """
        # Default style
        label_kwargs = {
            "text": text,
            "font": ("Segoe UI", 13),
            "text_color": self.theme["text_primary"]
        }
        
        # Override with custom
        label_kwargs.update(kwargs)
        
        label = CTkLabel(self.frame, **label_kwargs)
        label.pack(pady=4, anchor="w")
        
        self.components.append(label)
        return label
    
    def add_entry(
        self,
        placeholder: str = "",
        **kwargs
    ) -> CTkEntry:
        """
        Add an entry field
        """
        # Default style
        entry_kwargs = {
            "placeholder_text": placeholder,
            "height": 40,
            "font": ("Segoe UI", 13),
            "border_color": self.theme["border"],
            "fg_color": self.theme["surface"],
            "text_color": self.theme["text_primary"],
            "corner_radius": 6
        }
        
        # Override with custom
        entry_kwargs.update(kwargs)
        
        entry = CTkEntry(self.frame, **entry_kwargs)
        entry.pack(pady=8, fill="x")
        
        self.components.append(entry)
        return entry
    
    def add_slider(
        self,
        from_: int = 0,
        to: int = 100,
        **kwargs
    ) -> CTkSlider:
        """
        Add a slider
        """
        # Default style
        slider_kwargs = {
            "from_": from_,
            "to": to,
            "progress_color": self.theme["primary"],
            "button_color": self.theme["primary"],
            "button_hover_color": self.theme["accent"],
        }
        
        # Override with custom
        slider_kwargs.update(kwargs)
        
        slider = CTkSlider(self.frame, **slider_kwargs)
        slider.pack(pady=12, fill="x")
        
        self.components.append(slider)
        return slider
    
    def add_progressbar(self, **kwargs) -> CTkProgressBar:
        """
        Add a progress bar
        """
        # Default style
        pb_kwargs = {
            "progress_color": self.theme["primary"],
            "fg_color": self.theme["surface"],
            "height": 6,
            "corner_radius": 3
        }
        
        # Override with custom
        pb_kwargs.update(kwargs)
        
        pb = CTkProgressBar(self.frame, **pb_kwargs)
        pb.pack(pady=12, fill="x")
        
        self.components.append(pb)
        return pb
    
    def add_combobox(
        self,
        values: List[str],
        **kwargs
    ) -> CTkComboBox:
        """
        Add a combobox
        """
        # Default style
        cb_kwargs = {
            "values": values,
            "height": 40,
            "font": ("Segoe UI", 13),
            "fg_color": self.theme["surface"],
            "button_color": self.theme["primary"],
            "button_hover_color": self.theme["accent"],
            "text_color": self.theme["text_primary"],
            "dropdown_fg_color": self.theme["surface"],
            "dropdown_text_color": self.theme["text_primary"],
            "corner_radius": 6
        }
        
        # Override with custom
        cb_kwargs.update(kwargs)
        
        cb = CTkComboBox(self.frame, **cb_kwargs)
        cb.pack(pady=8, fill="x")
        
        self.components.append(cb)
        return cb
    
    def clear(self):
        """Clear all components from page"""
        for component in self.components:
            component.destroy()
        self.components.clear()


class WinNapCard(CTkFrame):
    """
    Card container for grouping related content
    """
    
    def __init__(
        self,
        parent,
        title: str,
        theme: dict,
        width: int = None,
        height: int = None
    ):
        super().__init__(
            parent,
            fg_color=theme["surface"],
            border_color=theme["border"],
            border_width=1,
            corner_radius=10
        )
        
        self.theme = theme
        self.title = title
        self.components = []
        
        # Title
        self.title_label = CTkLabel(
            self,
            text=title,
            font=("Segoe UI", 16, "bold"),
            text_color=theme["text_primary"]
        )
        self.title_label.pack(pady=(12, 8), padx=15, anchor="w")
        
        # Content area
        self.content_frame = CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    def add_label(self, text: str, **kwargs) -> CTkLabel:
        """Add label to card"""
        label_kwargs = {
            "text": text,
            "font": ("Segoe UI", 12),
            "text_color": self.theme["text_secondary"]
        }
        label_kwargs.update(kwargs)
        
        label = CTkLabel(self.content_frame, **label_kwargs)
        label.pack(pady=4, anchor="w")
        
        self.components.append(label)
        return label
    
    def add_button(self, text: str, command: Callable = None, **kwargs) -> CTkButton:
        """Add button to card"""
        btn_kwargs = {
            "text": text,
            "command": command,
            "height": 36,
            "font": ("Segoe UI", 12),
            "fg_color": self.theme["primary"],
            "corner_radius": 6
        }
        btn_kwargs.update(kwargs)
        
        button = CTkButton(self.content_frame, **btn_kwargs)
        button.pack(pady=6, fill="x")
        
        self.components.append(button)
        return button
    
    def add_switch(self, text: str, command: Callable = None, default: bool = False) -> CTkSwitch:
        """Add switch to card"""
        switch = CTkSwitch(
            self.content_frame,
            text=text,
            command=command,
            progress_color=self.theme["primary"],
            font=("Segoe UI", 12),
            text_color=self.theme["text_primary"]
        )
        switch.pack(pady=6, anchor="w")
        
        if default:
            switch.select()
        
        self.components.append(switch)
        return switch


class WinNapNotification(CTkToplevel):
    """
    Modern notification window
    """
    
    def __init__(self, parent, message: str, duration: int = 3, theme: dict = None):
        super().__init__(parent)
        
        self.message = message
        self.duration = duration
        self.theme = theme or WinNapTheme.get_theme("dark")
        self.opacity = 0.0
        
        # Configure window
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", self.opacity)
        
        # Styling
        self.configure(fg_color=self.theme["surface"])
        
        # Content
        self.label = CTkLabel(
            self,
            text=message,
            text_color=self.theme["text_primary"],
            font=("Segoe UI", 13)
        )
        self.label.pack(padx=20, pady=15)
        
        # Position at bottom right
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = self.winfo_reqwidth()
        win_h = self.winfo_reqheight()
        
        x = screen_w - win_w - 30
        y = screen_h - win_h - 50
        self.geometry(f"+{x}+{y}")
        
        # Force update
        self.update()
        
        # Start fade animation
        threading.Thread(target=self._fade_effect, daemon=True).start()
    
    def _fade_effect(self):
        """Fade in and out animation"""
        # Fade in
        for i in range(20):
            self.opacity = i * 0.05
            self.attributes("-alpha", self.opacity)
            time.sleep(0.02)
        
        # Wait
        time.sleep(self.duration)
        
        # Fade out
        for i in range(20, -1, -1):
            self.opacity = i * 0.05
            self.attributes("-alpha", self.opacity)
            time.sleep(0.02)
        
        self.destroy()


app = WinNapWindow("Onyx Hub", 600, 300, "dark")

home = app.add_page("home", "Dashboard", "🏠")
home.add_header("Dashboard", "หน้าหลักของระบบ")

user_data = {"name": None}

def save_name(value):
    user_data["name"] = value
    app.show_notification(f"บันทึกชื่อแล้ว: {value}")
    app.show_alert(f"บันทึกข้อมูลสำเร็จ {value}")

home.add_button(
    "ตั้งชื่อ",
    lambda: app.show_input(
        "กรุณากรอกชื่อ",
        on_submit=save_name
    )
)

setting = app.add_page("setting", "Setting", "✔")
setting.add_header("Setting", "หน้าต่างเมนู")


app.run()