"""
HID event emitter module.
Emits mouse and keyboard events using uinput (preferred) or pyautogui fallback.
"""

import logging
import subprocess
import os
from typing import Tuple, Optional
import time
import uinput 


logger = logging.getLogger(__name__)


class HIDEmitter:
    """
    Emits HID events for mouse and desktop control.
    Attempts uinput first, falls back to pyautogui + wmctrl/xdotool.
    """
    
    def __init__(self, screen_width: int, screen_height: int, use_uinput: bool = True):
        """
        Initialize HID emitter.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            use_uinput: Whether to attempt uinput (requires permissions)
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.use_uinput = use_uinput and self._check_uinput()
        
        self.device = None
        self.pyautogui = None
        self.desktop_tool = None
        
        # Track current mouse position for uinput relative movements
        self.current_x = screen_width // 2
        self.current_y = screen_height // 2
        
        if self.use_uinput:
            self._init_uinput()
        else:
            self._init_fallback()
    
    def _check_uinput(self) -> bool:
        """Check if uinput is available."""
        try:
            import uinput
            # Check if /dev/uinput exists and is accessible
            if os.path.exists('/dev/uinput'):
                return True
            logger.warning("/dev/uinput not found, falling back to pyautogui")
            return False
        except ImportError:
            logger.warning("python-uinput not installed, falling back to pyautogui")
            return False
        except Exception as e:
            logger.warning(f"uinput check failed: {e}, falling back to pyautogui")
            return False
    
    def _init_uinput(self):
        """Initialize uinput virtual HID device."""
        try:
            import uinput
            
            events = (
                uinput.BTN_LEFT,
                uinput.BTN_RIGHT,
                uinput.BTN_MIDDLE,
                uinput.REL_X,
                uinput.REL_Y,
                uinput.REL_WHEEL,
            )
            
            self.device = uinput.Device(events)
            time.sleep(0.1)  # Give kernel time to register device
            logger.info("uinput device created successfully")
            
        except PermissionError:
            logger.error("Permission denied for uinput. Run setup.sh to configure permissions.")
            logger.info("Falling back to pyautogui")
            self.use_uinput = False
            self._init_fallback()
        except Exception as e:
            logger.error(f"Failed to create uinput device: {e}")
            logger.info("Falling back to pyautogui")
            self.use_uinput = False
            self._init_fallback()
    
    def _init_fallback(self):
        """Initialize fallback mode using pyautogui."""
        try:
            import pyautogui
            self.pyautogui = pyautogui
            # Disable failsafe to prevent mouse to corner interruption
            self.pyautogui.FAILSAFE = False
            # Set very fast duration for instant movement
            self.pyautogui.PAUSE = 0
            logger.info("Using pyautogui for mouse control")
            
            # Detect desktop switching tool
            if self._command_exists('wmctrl'):
                self.desktop_tool = 'wmctrl'
                logger.info("Using wmctrl for desktop switching")
            elif self._command_exists('xdotool'):
                self.desktop_tool = 'xdotool'
                logger.info("Using xdotool for desktop switching")
            else:
                logger.warning("Neither wmctrl nor xdotool found - desktop switching disabled")
                logger.info("Install with: sudo apt-get install wmctrl xdotool")
                
        except ImportError:
            logger.error("pyautogui not installed - cannot control mouse!")
            logger.error("Install with: pip3 install pyautogui")
            raise RuntimeError("No mouse control method available")
    
    def _command_exists(self, cmd: str) -> bool:
        """Check if command exists in PATH."""
        try:
            subprocess.run(['which', cmd], capture_output=True, check=True)
            return True
        except:
            return False
    
    def move_mouse(self, x: int, y: int):
        """
        Move mouse cursor to absolute position.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        # Clamp to screen bounds
        x = max(0, min(x, self.screen_width - 1))
        y = max(0, min(y, self.screen_height - 1))
        
        if self.use_uinput and self.device:
            try:
                import uinput
                
                # Calculate relative movement from current position
                delta_x = x - self.current_x
                delta_y = y - self.current_y
                
                # Emit relative mouse movement
                if delta_x != 0:
                    self.device.emit(uinput.REL_X, int(delta_x))
                if delta_y != 0:
                    self.device.emit(uinput.REL_Y, int(delta_y))
                
                # Update tracked position
                self.current_x = x
                self.current_y = y
                
            except Exception as e:
                logger.error(f"uinput move failed: {e}")
        else:
            if self.pyautogui:
                try:
                    self.pyautogui.moveTo(x, y, duration=0)
                except Exception as e:
                    logger.error(f"pyautogui move failed: {e}")
    
    def click(self, button: str = 'left'):
        """
        Perform mouse click.
        
        Args:
            button: 'left', 'right', or 'middle'
        """
        if self.use_uinput and self.device:
            try:
                import uinput
                button_map = {
                    'left': uinput.BTN_LEFT,
                    'right': uinput.BTN_RIGHT,
                    'middle': uinput.BTN_MIDDLE
                }
                btn = button_map.get(button, uinput.BTN_LEFT)
                
                # Press
                self.device.emit(btn, 1)
                time.sleep(0.01)  # Small delay
                # Release
                self.device.emit(btn, 0)
                
                logger.debug(f"{button} click via uinput")
                
            except Exception as e:
                logger.error(f"uinput click failed: {e}")
        else:
            if self.pyautogui:
                try:
                    self.pyautogui.click(button=button)
                    logger.debug(f"{button} click via pyautogui")
                except Exception as e:
                    logger.error(f"pyautogui click failed: {e}")
    
    def drag_start(self):
        """Start mouse drag operation."""
        if self.use_uinput and self.device:
            try:
                import uinput
                self.device.emit(uinput.BTN_LEFT, 1)
                logger.debug("Drag started via uinput")
            except Exception as e:
                logger.error(f"uinput drag_start failed: {e}")
        else:
            if self.pyautogui:
                try:
                    self.pyautogui.mouseDown()
                    logger.debug("Drag started via pyautogui")
                except Exception as e:
                    logger.error(f"pyautogui drag_start failed: {e}")
    
    def drag_end(self):
        """End mouse drag operation."""
        if self.use_uinput and self.device:
            try:
                import uinput
                self.device.emit(uinput.BTN_LEFT, 0)
                logger.debug("Drag ended via uinput")
            except Exception as e:
                logger.error(f"uinput drag_end failed: {e}")
        else:
            if self.pyautogui:
                try:
                    self.pyautogui.mouseUp()
                    logger.debug("Drag ended via pyautogui")
                except Exception as e:
                    logger.error(f"pyautogui drag_end failed: {e}")
    
    def scroll(self, amount: int):
        """
        Scroll mouse wheel.
        
        Args:
            amount: Scroll amount (positive = up, negative = down)
        """
        if self.use_uinput and self.device:
            try:
                import uinput
                # uinput uses negative values for scrolling up
                scroll_value = -amount if amount > 0 else abs(amount)
                self.device.emit(uinput.REL_WHEEL, scroll_value)
                logger.debug(f"Scroll {amount} via uinput")
            except Exception as e:
                logger.error(f"uinput scroll failed: {e}")
        else:
            if self.pyautogui:
                try:
                    # pyautogui.scroll() takes clicks, multiply for more noticeable effect
                    self.pyautogui.scroll(amount * 10)
                    logger.debug(f"Scroll {amount} via pyautogui")
                except Exception as e:
                    logger.error(f"pyautogui scroll failed: {e}")
    
    def switch_desktop(self, direction: str):
        """
        Switch virtual desktop/workspace.
        
        Args:
            direction: 'next' or 'previous'
        """
        if not self.desktop_tool:
            logger.warning("No desktop switching tool available")
            logger.info("Install with: sudo apt-get install wmctrl xdotool")
            return
        
        try:
            if self.desktop_tool == 'wmctrl':
                # Get current desktop
                result = subprocess.run(['wmctrl', '-d'], capture_output=True, text=True, timeout=2)
                
                if result.returncode != 0:
                    logger.error(f"wmctrl failed: {result.stderr}")
                    return
                
                current = None
                total = 0
                
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            if '*' in parts[1]:
                                current = int(parts[0])
                            total += 1
                
                if current is not None and total > 0:
                    if direction == 'previous':
                        target = (current - 1) % total
                    else:  # 'next'
                        target = (current + 1) % total
                    
                    result = subprocess.run(['wmctrl', '-s', str(target)], 
                                          capture_output=True, timeout=2)
                    
                    if result.returncode == 0:
                        logger.info(f"Switched to desktop {target} (was {current})")
                    else:
                        logger.error(f"Desktop switch failed: {result.stderr}")
                else:
                    logger.error("Could not determine current desktop")
                    
            elif self.desktop_tool == 'xdotool':
                # Get current desktop
                result = subprocess.run(['xdotool', 'get_desktop'], 
                                      capture_output=True, text=True, timeout=2)
                
                if result.returncode != 0:
                    logger.error(f"xdotool get_desktop failed: {result.stderr}")
                    return
                
                current = int(result.stdout.strip())
                
                # Get total desktops
                result = subprocess.run(['xdotool', 'get_num_desktops'], 
                                      capture_output=True, text=True, timeout=2)
                
                if result.returncode != 0:
                    logger.error(f"xdotool get_num_desktops failed: {result.stderr}")
                    return
                
                total = int(result.stdout.strip())
                
                if direction == 'previous':
                    target = (current - 1) % total
                else:  # 'next'
                    target = (current + 1) % total
                
                result = subprocess.run(['xdotool', 'set_desktop', str(target)], 
                                      capture_output=True, timeout=2)
                
                if result.returncode == 0:
                    logger.info(f"Switched to desktop {target} (was {current})")
                else:
                    logger.error(f"Desktop switch failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Desktop switch command timed out")
        except ValueError as e:
            logger.error(f"Failed to parse desktop number: {e}")
        except Exception as e:
            logger.error(f"Desktop switch failed: {e}")
    
    def close(self):
        """Clean up resources."""
        if self.device:
            try:
                # uinput devices auto-close when the file descriptor is closed
                # The Python object will handle this automatically
                logger.info("uinput device closed")
            except:
                pass
        
        logger.info("HID emitter closed")