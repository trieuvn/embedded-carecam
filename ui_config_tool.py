"""
UI Configuration Tool for CareCam Button Positions
Allows user to configure mic and speaker button positions on the camera app
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Tuple
import pyautogui
import pygetwindow as gw

# Default configuration file path
CONFIG_FILE = "position_config.json"

# Default button positions (fallback values)
DEFAULT_CONFIG = {
    "mic_button_x": 960,
    "mic_button_y": 1000,
    "speaker_button_x": 800,
    "speaker_button_y": 1000
}


class UIConfigTool:
    """GUI tool for configuring button positions"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CareCam UI Configuration Tool")
        self.root.geometry("600x600")
        self.root.resizable(True, True)
        self.root.minsize(600, 600)
        
        # Configuration data
        self.config = self._load_config()
        
        # Capture mode flags
        self.capturing_mic = False
        self.capturing_speaker = False
        
        # Setup UI
        self._setup_ui()
        
        # Bind escape key to cancel capture
        self.root.bind('<Escape>', lambda e: self._cancel_capture())
    
    def _load_config(self) -> Dict[str, int]:
        """Load configuration from JSON file or create default"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"✅ Loaded configuration from {CONFIG_FILE}")
                    return config
            except Exception as e:
                print(f"⚠️ Error loading config: {e}")
                print("Using default configuration")
                return DEFAULT_CONFIG.copy()
        else:
            print(f"ℹ️ Config file not found, using defaults")
            return DEFAULT_CONFIG.copy()
    
    def _save_config(self) -> bool:
        """Save configuration to JSON file"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to {CONFIG_FILE}")
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Title
        title_label = tk.Label(
            self.root,
            text="CareCam Button Position Configuration",
            font=("Arial", 16, "bold"),
            pady=20
        )
        title_label.pack()
        
        # Instructions
        instructions = tk.Label(
            self.root,
            text="Configure the positions of mic and speaker buttons\n"
                 "on the CareCam app window",
            font=("Arial", 10),
            pady=10
        )
        instructions.pack()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Mic Button Section
        mic_frame = ttk.LabelFrame(main_frame, text="Mic Button Position", padding="10")
        mic_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(mic_frame, text="X Position:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.mic_x_entry = ttk.Entry(mic_frame, width=10)
        self.mic_x_entry.insert(0, str(self.config['mic_button_x']))
        self.mic_x_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(mic_frame, text="Y Position:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.mic_y_entry = ttk.Entry(mic_frame, width=10)
        self.mic_y_entry.insert(0, str(self.config['mic_button_y']))
        self.mic_y_entry.grid(row=0, column=3, padx=5)
        
        self.select_mic_btn = ttk.Button(
            mic_frame,
            text="Select Mic Button Position",
            command=self._start_mic_capture
        )
        self.select_mic_btn.grid(row=1, column=0, columnspan=2, pady=10, padx=5, sticky=tk.EW)
        
        self.test_mic_btn = ttk.Button(
            mic_frame,
            text="Test Mic Position",
            command=self._test_mic_position
        )
        self.test_mic_btn.grid(row=1, column=2, columnspan=2, pady=10, padx=5, sticky=tk.EW)
        
        # Speaker Button Section
        speaker_frame = ttk.LabelFrame(main_frame, text="Speaker Button Position", padding="10")
        speaker_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(speaker_frame, text="X Position:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.speaker_x_entry = ttk.Entry(speaker_frame, width=10)
        self.speaker_x_entry.insert(0, str(self.config['speaker_button_x']))
        self.speaker_x_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(speaker_frame, text="Y Position:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.speaker_y_entry = ttk.Entry(speaker_frame, width=10)
        self.speaker_y_entry.insert(0, str(self.config['speaker_button_y']))
        self.speaker_y_entry.grid(row=0, column=3, padx=5)
        
        self.select_speaker_btn = ttk.Button(
            speaker_frame,
            text="Select Speaker Button Position",
            command=self._start_speaker_capture
        )
        self.select_speaker_btn.grid(row=1, column=0, columnspan=2, pady=10, padx=5, sticky=tk.EW)
        
        self.test_speaker_btn = ttk.Button(
            speaker_frame,
            text="Test Speaker Position",
            command=self._test_speaker_position
        )
        self.test_speaker_btn.grid(row=1, column=2, columnspan=2, pady=10, padx=5, sticky=tk.EW)
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready",
            font=("Arial", 10),
            fg="green",
            pady=15,
            wraplength=550
        )
        self.status_label.pack(fill=tk.X)
        
        # Action buttons (with extra padding to ensure visibility)
        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.pack(pady=20, fill=tk.X)
        
        self.save_btn = ttk.Button(
            button_frame,
            text="Save Configuration",
            command=self._save_configuration,
            width=20
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_to_defaults,
            width=20
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
    
    def _start_mic_capture(self):
        """Start capturing mic button position"""
        self.capturing_mic = True
        self.capturing_speaker = False
        self._update_status("Click on the Mic button in the CareCam app...", "blue")
        
        # Minimize window and wait for click
        self.root.iconify()
        self.root.after(500, self._wait_for_click, 'mic')
    
    def _start_speaker_capture(self):
        """Start capturing speaker button position"""
        self.capturing_speaker = True
        self.capturing_mic = False
        self._update_status("Click on the Speaker button in the CareCam app...", "blue")
        
        # Minimize window and wait for click
        self.root.iconify()
        self.root.after(500, self._wait_for_click, 'speaker')
    
    def _wait_for_click(self, button_type: str):
        """Wait for user to click and capture position"""
        # Get current mouse position when user clicks
        try:
            # Wait for click
            import time
            time.sleep(0.5)
            
            # Get position
            x, y = pyautogui.position()
            
            # Update configuration
            if button_type == 'mic':
                self.config['mic_button_x'] = x
                self.config['mic_button_y'] = y
                self.mic_x_entry.delete(0, tk.END)
                self.mic_x_entry.insert(0, str(x))
                self.mic_y_entry.delete(0, tk.END)
                self.mic_y_entry.insert(0, str(y))
                msg = f"Mic button position captured: ({x}, {y})"
            else:
                self.config['speaker_button_x'] = x
                self.config['speaker_button_y'] = y
                self.speaker_x_entry.delete(0, tk.END)
                self.speaker_x_entry.insert(0, str(x))
                self.speaker_y_entry.delete(0, tk.END)
                self.speaker_y_entry.insert(0, str(y))
                msg = f"Speaker button position captured: ({x}, {y})"
            
            print(f"✅ {msg}")
            
            # Restore window
            self.root.deiconify()
            self._update_status(msg, "green")
            
            self.capturing_mic = False
            self.capturing_speaker = False
            
        except Exception as e:
            print(f"❌ Error capturing position: {e}")
            self.root.deiconify()
            self._update_status(f"Error: {e}", "red")
            self.capturing_mic = False
            self.capturing_speaker = False
    
    def _cancel_capture(self):
        """Cancel position capture"""
        if self.capturing_mic or self.capturing_speaker:
            self.capturing_mic = False
            self.capturing_speaker = False
            self.root.deiconify()
            self._update_status("Capture cancelled", "orange")
    
    def _test_mic_position(self):
        """Test the mic button position by moving cursor to it"""
        try:
            x = int(self.mic_x_entry.get())
            y = int(self.mic_y_entry.get())
            
            self._update_status(f"Moving cursor to mic position ({x}, {y})...", "blue")
            pyautogui.moveTo(x, y, duration=1)
            self._update_status(f"Cursor at mic position ({x}, {y}). Check if correct!", "green")
            
        except ValueError:
            self._update_status("Invalid position values", "red")
            messagebox.showerror("Error", "Please enter valid numeric values for X and Y")
    
    def _test_speaker_position(self):
        """Test the speaker button position by moving cursor to it"""
        try:
            x = int(self.speaker_x_entry.get())
            y = int(self.speaker_y_entry.get())
            
            self._update_status(f"Moving cursor to speaker position ({x}, {y})...", "blue")
            pyautogui.moveTo(x, y, duration=1)
            self._update_status(f"Cursor at speaker position ({x}, {y}). Check if correct!", "green")
            
        except ValueError:
            self._update_status("Invalid position values", "red")
            messagebox.showerror("Error", "Please enter valid numeric values for X and Y")
    
    def _save_configuration(self):
        """Save the current configuration to file"""
        try:
            # Update config from entries
            self.config['mic_button_x'] = int(self.mic_x_entry.get())
            self.config['mic_button_y'] = int(self.mic_y_entry.get())
            self.config['speaker_button_x'] = int(self.speaker_x_entry.get())
            self.config['speaker_button_y'] = int(self.speaker_y_entry.get())
            
            if self._save_config():
                self._update_status("Configuration saved successfully!", "green")
                messagebox.showinfo("Success", f"Configuration saved to {CONFIG_FILE}")
            else:
                self._update_status("Failed to save configuration", "red")
                messagebox.showerror("Error", "Failed to save configuration file")
                
        except ValueError:
            self._update_status("Invalid position values", "red")
            messagebox.showerror("Error", "Please enter valid numeric values for all positions")
    
    def _reset_to_defaults(self):
        """Reset configuration to default values"""
        result = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to reset to default values?"
        )
        
        if result:
            self.config = DEFAULT_CONFIG.copy()
            
            # Update entries
            self.mic_x_entry.delete(0, tk.END)
            self.mic_x_entry.insert(0, str(self.config['mic_button_x']))
            self.mic_y_entry.delete(0, tk.END)
            self.mic_y_entry.insert(0, str(self.config['mic_button_y']))
            self.speaker_x_entry.delete(0, tk.END)
            self.speaker_x_entry.insert(0, str(self.config['speaker_button_x']))
            self.speaker_y_entry.delete(0, tk.END)
            self.speaker_y_entry.insert(0, str(self.config['speaker_button_y']))
            
            self._update_status("Reset to default values", "green")
    
    def _update_status(self, message: str, color: str):
        """Update status label"""
        self.status_label.config(text=message, fg=color)
        print(f"[{color.upper()}] {message}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("🎮 CareCam UI Configuration Tool")
    print("=" * 60)
    
    # Disable PyAutoGUI fail-safe
    pyautogui.FAILSAFE = False
    
    # Create and run application
    root = tk.Tk()
    app = UIConfigTool(root)
    
    print("\n✅ Configuration tool started")
    print(f"📁 Config file: {os.path.abspath(CONFIG_FILE)}")
    print("\nInstructions:")
    print("  1. Click 'Select Mic Button Position' and then click on the mic button")
    print("  2. Click 'Select Speaker Button Position' and then click on the speaker button")
    print("  3. Use 'Test' buttons to verify positions")
    print("  4. Click 'Save Configuration' to save")
    print("  5. Press ESC to cancel position capture\n")
    
    root.mainloop()


if __name__ == "__main__":
    main()
