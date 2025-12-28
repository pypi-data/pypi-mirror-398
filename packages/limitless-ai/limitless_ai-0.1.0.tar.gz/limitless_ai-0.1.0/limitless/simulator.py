import gymnasium as gym
from gymnasium import spaces
import numpy as np
import cv2
import mss
import pygetwindow as gw
import vgamepad as vg
import time
from typing import Optional, Tuple, Any

class UniversalGameEnv(gym.Env):
    """
    A universal Gymnasium wrapper for commercial games.
    Captures screen content and sends inputs via a Virtual Xbox Controller.
    """
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(self, window_title: str, frame_shape: Tuple[int, int] = (224, 224)):
        super(UniversalGameEnv, self).__init__()
        
        self.window_title = window_title
        self.frame_shape = frame_shape
        self.sct = mss.mss()
        
        # Initialize Virtual Gamepad
        self.gamepad = vg.VX360Gamepad()
        
        # Find the game window
        self.window = self._find_window(window_title)
        if not self.window:
            print(f"Warning: Window '{window_title}' not found. Using primary monitor.")
            self.window = None

        # Action space matches the Limitless model output
        # buttons: [A, B, X, Y, LB, RB, Back, Start, LStick, RStick, DpadUp, DpadDown, DpadLeft, DpadRight]
        # sticks: [LX, LY, RX, RY]
        self.action_space = spaces.Dict({
            "buttons": spaces.MultiBinary(14),
            "sticks": spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
        })

        self.observation_space = spaces.Box(
            low=0, high=255, shape=(frame_shape[0], frame_shape[1], 3), dtype=np.uint8
        )

        # Mapping for vgamepad
        self.vg_buttons = [
            vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
        ]

    def _find_window(self, title):
        windows = gw.getWindowsWithTitle(title)
        if windows:
            return windows[0]
        return None

    def _get_obs(self):
        if self.window:
            monitor = {
                "top": self.window.top,
                "left": self.window.left,
                "width": self.window.width,
                "height": self.window.height,
            }
        else:
            monitor = self.sct.monitors[1] # Primary monitor

        img = np.array(self.sct.grab(monitor))
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
        img = cv2.resize(img, (self.frame_shape[1], self.frame_shape[0]))
        return img

    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None) -> Tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        # Removed window.activate() to avoid stealing focus
        return self._get_obs(), {}

    def step(self, action: Any) -> Tuple[np.ndarray, float, bool, bool, dict]:
        # 1. Apply Buttons
        for i, btn_val in enumerate(action["buttons"]):
            if btn_val > 0.5:
                self.gamepad.press_button(button=self.vg_buttons[i])
            else:
                self.gamepad.release_button(button=self.vg_buttons[i])
        
        # 2. Apply Sticks
        # vgamepad expects values from -32768 to 32767
        lx, ly, rx, ry = action["sticks"]
        self.gamepad.left_joystick_float(x_value_float=lx, y_value_float=-ly) # Invert Y for standard controller logic
        self.gamepad.right_joystick_float(x_value_float=rx, y_value_float=-ry)
        
        self.gamepad.update()
        
        obs = self._get_obs()
        return obs, 0.0, False, False, {}

    def close(self):
        del self.gamepad

        
        # In a universal simulator, reward and done are hard to define without game-specific logic.
        # NitroGen likely uses external reward signals or just behavior cloning (no reward needed).
        reward = 0.0
        terminated = False
        truncated = False
        
        return obs, reward, terminated, truncated, {}

    def render(self):
        if self.render_mode == "rgb_array":
            return self._get_obs()
        elif self.render_mode == "human":
            cv2.imshow("Universal Simulator", cv2.cvtColor(self._get_obs(), cv2.COLOR_RGB2BGR))
            cv2.waitKey(1)

    def close(self):
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Example usage
    # env = UniversalGameEnv(window_title="Minecraft")
    # obs, info = env.reset()
    # for _ in range(100):
    #     action = env.action_space.sample()
    #     obs, reward, term, trunc, info = env.step(action)
    #     env.render()
    pass
