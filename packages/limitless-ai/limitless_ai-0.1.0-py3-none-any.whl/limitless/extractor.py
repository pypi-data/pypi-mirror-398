import cv2
import numpy as np
import pandas as pd
import json
import os
from importlib import resources

class UniversalInputExtractor:
    def __init__(self, templates_dir=None):
        self.templates = {}
        if templates_dir is None:
            try:
                # Try to get templates from package data
                self.templates_dir = str(resources.files('limitless').joinpath('templates'))
            except Exception:
                self.templates_dir = "templates"
        else:
            self.templates_dir = templates_dir
            
        self.load_templates()
        
        self.active_config = None
        self.active_template = None
        self.roi_in_frame = None # (x, y, w, h)
        self.scale = 1.0
        self.ref_frame_roi = None
        self.output_data = []

    def load_templates(self):
        # Scan templates directory for .png files and look for matching .json configs
        # Also scan subdirectories for config.json (new structure)
        for root, dirs, files in os.walk(self.templates_dir):
            if "config.json" in files:
                json_path = os.path.join(root, "config.json")
                try:
                    with open(json_path, "r") as f:
                        config = json.load(f)
                    
                    # Find all base images in this directory (black, blue, red, white, etc.)
                    base_images = [f for f in files if f.startswith("base") and (f.endswith(".svg") or f.endswith(".png"))]
                    
                    if not base_images:
                        # Fallback to config defined base_image if no "base*" files found
                        base_image = config.get("base_image")
                        if base_image:
                            base_images = [base_image]

                    for base_image in base_images:
                        image_path = os.path.join(root, base_image)
                        self.templates[image_path] = config
                        print(f"Loaded template: {config.get('name', root)} ({base_image})")
                except Exception as e:
                    print(f"Error loading template in {root}: {e}")

            # Legacy support for root .png files
            if root == self.templates_dir:
                for file in files:
                    if file.endswith(".png"):
                        name = os.path.splitext(file)[0]
                        json_path = os.path.join(self.templates_dir, name + ".json")
                        if os.path.exists(json_path):
                            with open(json_path, "r") as f:
                                config = json.load(f)
                            self.templates[os.path.join(self.templates_dir, file)] = config
                            print(f"Loaded legacy template: {file}")

    def _read_template(self, path, gray=True):
        """Read an image, supporting SVG via cairosvg if needed."""
        if path.endswith(".svg"):
            # Check if a PNG version exists first as a fallback
            png_path = path.replace(".svg", ".png")
            if os.path.exists(png_path):
                return cv2.imread(png_path, 0 if gray else 1)

            try:
                # Windows Cairo Path Hack
                if os.name == 'nt':
                    cairo_path = r'C:\Program Files\GTK3-Runtime Win64\bin'
                    if os.path.exists(cairo_path) and cairo_path not in os.environ['PATH']:
                        os.environ['PATH'] = cairo_path + os.pathsep + os.environ['PATH']

                import cairosvg
                import io
                from PIL import Image
                
                # Render SVG to PNG in memory
                png_data = cairosvg.svg2png(url=path)
                img = Image.open(io.BytesIO(png_data))
                img_np = np.array(img)
                
                # Convert RGBA to BGR or Gray
                if len(img_np.shape) == 3 and img_np.shape[2] == 4:
                    if gray:
                        return cv2.cvtColor(img_np, cv2.COLOR_RGBA2GRAY)
                    else:
                        return cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
                else:
                    if gray:
                        return cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                    else:
                        return cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            except (ImportError, OSError) as e:
                print(f"Warning: cairosvg failed or Cairo libraries not found. Cannot read SVG template: {path}")
                print("To fix this on Windows, install Cairo: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases")
                print(f"Alternatively, provide a PNG version at: {png_path}")
                return None
            except Exception as e:
                print(f"Error rendering SVG {path}: {e}")
                return None
        else:
            return cv2.imread(path, 0 if gray else 1)

    def register_controller_sift(self, frame):
        """Robustly find the controller using SIFT keypoint matching."""
        sift = cv2.SIFT_create()
        kp_frame, des_frame = sift.detectAndCompute(frame, None)
        
        if des_frame is None: return False
        
        best_matches_count = 0
        best_match = None
        
        index_params = dict(algorithm=1, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        
        for t_path, config in self.templates.items():
            template = self._read_template(t_path, gray=False)
            if template is None: continue
            
            kp_temp, des_temp = sift.detectAndCompute(template, None)
            if des_temp is None: continue
            
            matches = flann.knnMatch(des_temp, des_frame, k=2)
            
            # Ratio test
            good_matches = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)
            
            if len(good_matches) > 10:
                src_pts = np.float32([kp_temp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                
                M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                if M is not None:
                    h, w = template.shape[:2]
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)
                    
                    # Calculate bounding box
                    x_coords = dst[:, 0, 0]
                    y_coords = dst[:, 0, 1]
                    xmin, xmax = int(min(x_coords)), int(max(x_coords))
                    ymin, ymax = int(min(y_coords)), int(max(y_coords))
                    
                    # Basic sanity check on dimensions
                    if 50 < (xmax-xmin) < frame.shape[1] and 50 < (ymax-ymin) < frame.shape[0]:
                        if len(good_matches) > best_matches_count:
                            best_matches_count = len(good_matches)
                            self.roi_in_frame = (xmin, ymin, xmax-xmin, ymax-ymin)
                            self.active_config = config
                            self.scale = (xmax-xmin) / w
                            self.active_template = cv2.resize(template, (xmax-xmin, ymax-ymin))
                            best_match = t_path
                            
        if best_match:
            print(f"SIFT Detected {os.path.basename(best_match)} at {self.roi_in_frame}")
            return True
        return False

    def register_controller(self, frame):
        # Try SIFT first for robustness
        if self.register_controller_sift(frame):
            return True
        
        """Automatically find the controller overlay using Edge-Based Template Matching for transparency."""
        best_val = -1
        best_match = None
        
        search_scale = 0.25
        h, w = frame.shape[:2]
        small_frame = cv2.resize(frame, (int(w * search_scale), int(h * search_scale)))
        gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        
        # Use Canny edges to ignore background colors and focus on the controller's shape
        edges_frame = cv2.Canny(gray_frame, 50, 150)
        
        for t_path, config in self.templates.items():
            template = self._read_template(t_path, gray=True)
            if template is None: continue
            
            small_template = cv2.resize(template, (0,0), fx=search_scale, fy=search_scale)
            edges_template = cv2.Canny(small_template, 50, 150)
            
            for scale in np.linspace(0.5, 1.5, 5):
                resized = cv2.resize(edges_template, (0,0), fx=scale, fy=scale)
                if resized.shape[0] > edges_frame.shape[0] or resized.shape[1] > edges_frame.shape[1]:
                    continue
                    
                # TM_CCORR_NORMED works better with edge maps
                res = cv2.matchTemplate(edges_frame, resized, cv2.TM_CCORR_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                
                if max_val > best_val:
                    best_val = max_val
                    best_match = {
                        "config": config,
                        "template_path": t_path,
                        "loc": max_loc,
                        "scale": scale
                    }
        
        if best_val > 0.2: # Lower threshold for edge matching
            self.active_config = best_match["config"]
            self.scale = best_match["scale"]
            
            orig_template = self._read_template(best_match["template_path"], gray=False)
            self.active_template = cv2.resize(orig_template, (0,0), fx=self.scale, fy=self.scale)
            
            x, y = best_match["loc"]
            x = int(x / search_scale)
            y = int(y / search_scale)
            h, w = self.active_template.shape[:2]
            self.roi_in_frame = (x, y, w, h)
            
            print(f"Detected (Edge-Match) {os.path.basename(best_match['template_path'])} at {self.roi_in_frame} (quality: {best_val:.2f})")
            return True
        return False

    def auto_calibrate(self, video_path):
        """Find the most static version of the controller region to use as idle reference."""
        cap = cv2.VideoCapture(video_path)
        frames_to_check = 100
        roi_history = []
        frame_idx = 0
        
        print("Calibrating idle state (this may take a moment)...")
        while len(roi_history) < frames_to_check:
            ret, frame = cap.read()
            if not ret: break
            
            if self.roi_in_frame is None:
                # Only try registering every 10 frames to save time
                if frame_idx % 10 == 0:
                    if not self.register_controller(frame):
                        frame_idx += 1
                        continue
                else:
                    frame_idx += 1
                    continue
            
            x, y, w, h = self.roi_in_frame
            roi = frame[y:y+h, x:x+w]
            roi_history.append(roi)
            if len(roi_history) % 10 == 0:
                print(f"  Captured {len(roi_history)}/{frames_to_check} calibration frames...")
            frame_idx += 1
            
        cap.release()
        
        if not roi_history:
            return False
            
        # Simplest calibration: Use the frame that is most similar to the average
        # or just use the first frame for now (can be improved)
        self.ref_frame_roi = roi_history[0]
        return True

    def get_scaled_roi(self, base_roi):
        x, y, w, h = base_roi
        return (
            int(x * self.scale),
            int(y * self.scale),
            int(w * self.scale),
            int(h * self.scale)
        )

    def get_button_state(self, current_roi, base_roi):
        x, y, w, h = self.get_scaled_roi(base_roi)
        btn_roi = current_roi[y:y+h, x:x+w]
        ref_roi = self.ref_frame_roi[y:y+h, x:x+w]
        
        # For semi-transparent overlays, raw pixel difference is noisy due to background movement.
        # We use Edge-Based Difference which is more robust to background textures.
        gray_btn = cv2.cvtColor(btn_roi, cv2.COLOR_BGR2GRAY)
        gray_ref = cv2.cvtColor(ref_roi, cv2.COLOR_BGR2GRAY)
        
        # Detect edges - the controller's edges (letters, outlines) are static, 
        # but they get sharper/brighter when a button is pressed.
        edges_btn = cv2.Canny(gray_btn, 50, 150)
        edges_ref = cv2.Canny(gray_ref, 50, 150)
        
        # Calculate the difference in edge maps
        edge_diff = cv2.absdiff(edges_btn, edges_ref)
        
        # Also check for significant color/brightness shift (common in semi-transparent overlays)
        diff = cv2.absdiff(btn_roi, ref_roi)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray_diff, 70, 255, cv2.THRESH_BINARY)
        
        # Combine edge change and pixel change
        edge_change_ratio = np.sum(edge_diff > 0) / (w * h)
        pixel_change_ratio = np.sum(thresh > 0) / (w * h)
        
        # If either the edges change significantly or the pixels change a lot, the button is likely pressed
        return 1 if (edge_change_ratio > 0.03 or pixel_change_ratio > 0.1) else 0

    def get_stick_val(self, current_roi, base_roi):
        x, y, w, h = self.get_scaled_roi(base_roi)
        stick_roi = current_roi[y:y+h, x:x+w]
        ref_stick_roi = self.ref_frame_roi[y:y+h, x:x+w]
        
        # Use Edge-Based tracking for sticks to handle semi-transparency
        gray_stick = cv2.cvtColor(stick_roi, cv2.COLOR_BGR2GRAY)
        gray_ref = cv2.cvtColor(ref_stick_roi, cv2.COLOR_BGR2GRAY)
        
        edges_stick = cv2.Canny(gray_stick, 50, 150)
        edges_ref = cv2.Canny(gray_ref, 50, 150)
        
        # Take a smaller crop from the center of the idle stick edges to use as the "knob" template
        tw, th = int(w * 0.6), int(h * 0.6)
        tx, ty = (w - tw) // 2, (h - th) // 2
        template = edges_ref[ty:ty+th, tx:tx+tw]
        
        # Search for this knob in the current stick edges
        res = cv2.matchTemplate(edges_stick, template, cv2.TM_CCORR_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(res)
        
        dx = max_loc[0] - tx
        dy = max_loc[1] - ty
        
        max_dx = (w - tw) / 2
        max_dy = (h - th) / 2
        
        nx = dx / max_dx if max_dx > 0 else 0
        ny = dy / max_dy if max_dy > 0 else 0
        
        if abs(nx) < 0.1: nx = 0.0 # Slightly larger deadzone for transparency
        if abs(ny) < 0.1: ny = 0.0
        
        return round(float(np.clip(nx, -1.0, 1.0)), 2), round(float(np.clip(ny, -1.0, 1.0)), 2)

    def process_video(self, video_path, output_dir, sample_rate=1, show_debug=False, game_id=0):
        if self.ref_frame_roi is None:
            if not self.auto_calibrate(video_path):
                print(f"Error: Could not calibrate controller for {video_path}.")
                return

        cap = cv2.VideoCapture(video_path)
        frame_idx = 0
        os.makedirs(os.path.join(output_dir, 'frames'), exist_ok=True)
        
        # We need the full frame shape for gameplay ROI
        ret, first_frame = cap.read()
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            if frame_idx % sample_rate == 0:
                x, y, w, h = self.roi_in_frame
                current_controller_roi = frame[y:y+h, x:x+w]
                
                frame_filename = f"{video_name}_{frame_idx:06d}.jpg"
                frame_inputs = {
                    'frame': frame_filename,
                    'game_id': game_id
                }
                
                # Draw debug ROIs if requested
                debug_frame = None
                if show_debug:
                    debug_frame = frame.copy()
                    cv2.rectangle(debug_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                for btn, base_roi in self.active_config.get('buttons', {}).items():
                    frame_inputs[f'btn_{btn}'] = self.get_button_state(current_controller_roi, base_roi)
                    if show_debug:
                        bx, by, bw, bh = self.get_scaled_roi(base_roi)
                        color = (0, 0, 255) if frame_inputs[f'btn_{btn}'] == 1 else (0, 255, 255)
                        cv2.rectangle(debug_frame, (x+bx, y+by), (x+bx+bw, y+by+bh), color, 1)
                
                for stick, base_roi in self.active_config.get('sticks', {}).items():
                    sx, sy = self.get_stick_val(current_controller_roi, base_roi)
                    frame_inputs[f'stick_{stick}_x'] = sx
                    frame_inputs[f'stick_{stick}_y'] = sy
                    if show_debug:
                        bx, by, bw, bh = self.get_scaled_roi(base_roi)
                        cv2.rectangle(debug_frame, (x+bx, y+by), (x+bx+bw, y+by+bh), (255, 0, 0), 1)
                
                self.output_data.append(frame_inputs)
                
                if show_debug:
                    cv2.imshow("Input Extraction Debug (Press Q to stop)", debug_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Save gameplay frame
                cv2.imwrite(os.path.join(output_dir, 'frames', frame_filename), frame)
            
            frame_idx += 1
            if frame_idx % 500 == 0:
                print(f"  Processed {frame_idx} frames (Extracted {len(self.output_data)} training pairs)...")
        
        cap.release()
        if show_debug:
            cv2.destroyAllWindows()
        
        # Save labels incrementally or at the end
        df = pd.DataFrame(self.output_data)
        df.to_csv(os.path.join(output_dir, 'labels.csv'), index=False)
        print(f"Finished processing {video_path}. Data saved to {output_dir}")

    def process_directory(self, input_dir, output_dir, sample_rate=1):
        """Process all videos in a directory, assigning unique game IDs."""
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov')
        videos = [f for f in os.listdir(input_dir) if f.lower().endswith(video_extensions)]
        
        for i, video in enumerate(videos):
            print(f"Processing video {i+1}/{len(videos)}: {video}")
            video_path = os.path.join(input_dir, video)
            # Reset ROI and calibration for each video as they might have different overlays
            self.roi_in_frame = None
            self.ref_frame_roi = None
            self.process_video(video_path, output_dir, sample_rate=sample_rate, game_id=i)

if __name__ == "__main__":
    pass
