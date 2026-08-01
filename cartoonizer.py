import cv2
import numpy as np
import torch

class Cartoonizer:
    STYLES = ["cartoon", "anime", "3d_render", "sketch", "watercolor"]
    
    def __init__(self, style="cartoon", device="cuda"):
        self.style = style.lower().replace(" ", "_")
        self.device = device
        self.anime_model = None
        
    def set_model(self, model):
        self.anime_model = model
    
    def preprocess(self, frame):
        h, w = frame.shape[:2]
        new_h = ((h + 31) // 32) * 32
        new_w = ((w + 31) // 32) * 32
        if new_h == 0: new_h = 32
        if new_w == 0: new_w = 32
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        return resized, (h, w)
    
    def tensorize(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb).permute(2,0,1).unsqueeze(0).float().to(self.device)
        tensor = tensor / 127.5 - 1.0
        return tensor
    
    def detensorize(self, tensor, orig_h, orig_w):
        img = tensor.squeeze(0).permute(1,2,0).cpu().numpy()
        img = (img + 1.0) * 127.5
        img = np.clip(img, 0, 255).astype(np.uint8)
        rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return cv2.resize(rgb, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4)
    
    def apply_anime(self, frame):
        if self.anime_model is None:
            return self.apply_cartoon(frame)
        processed, (orig_h, orig_w) = self.preprocess(frame)
        tensor = self.tensorize(processed)
        with torch.no_grad():
            with torch.cuda.amp.autocast():
                output = self.anime_model(tensor)
        return self.detensorize(output, orig_h, orig_w)
    
    def apply_cartoon(self, frame):
        """Cute Cartoon — Beauty Filter Style (No Harsh Edges)"""
        # Step 1: Heavy bilateral smoothing (porcelain skin effect)
        img = cv2.bilateralFilter(frame, d=9, sigmaColor=100, sigmaSpace=100)
        img = cv2.bilateralFilter(img, d=9, sigmaColor=80, sigmaSpace=80)
        img = cv2.bilateralFilter(img, d=7, sigmaColor=60, sigmaSpace=60)
        
        # Step 2: Edge preserving filter (soft cartoon feel, NO harsh lines)
        img = cv2.edgePreservingFilter(img, flags=1, sigma_s=80, sigma_r=0.5)
        
        # Step 3: Very subtle color flattening (not posterization)
        # Just slight median blur on color channels in HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv[:,:,0] = cv2.medianBlur(hsv[:,:,0], 5)  # Smooth hue
        hsv[:,:,1] = cv2.medianBlur(hsv[:,:,1], 5)  # Smooth saturation
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Step 4: Vibrant cute colors
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.45, 0, 255)  # +45% saturation
        hsv[:,:,2] = np.clip(hsv[:,:,2] * 1.08, 0, 255)  # +8% brightness
        hsv = hsv.astype(np.uint8)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Step 5: Very soft unsharp for clarity (NO harsh light)
        gaussian = cv2.GaussianBlur(result, (0, 0), 2.0)
        result = cv2.addWeighted(result, 1.3, gaussian, -0.3, 0)
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return result
    
    def apply_3d_render(self, frame):
        cartoon = self.apply_cartoon(frame)
        kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
        sharp = cv2.filter2D(cartoon, -1, kernel)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        depth = cv2.magnitude(sobelx, sobely)
        depth = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        depth_color = cv2.applyColorMap(255 - depth, cv2.COLORMAP_JET)
        
        result = cv2.addWeighted(sharp, 0.85, depth_color, 0.15, 0)
        return result
    
    def apply_sketch(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        
        color_sketch = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        colored = cv2.addWeighted(frame, 0.2, color_sketch, 0.8, 0)
        return colored
    
    def apply_watercolor(self, frame):
        smooth = cv2.edgePreservingFilter(frame, flags=1, sigma_s=80, sigma_r=0.5)
        
        hsv = cv2.cvtColor(smooth, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:,:,1] = cv2.GaussianBlur(hsv[:,:,1], (7,7), 0)
        hsv[:,:,2] = cv2.GaussianBlur(hsv[:,:,2], (5,5), 0)
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        edges = cv2.dilate(edges, None, iterations=1)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        return cv2.addWeighted(result, 0.92, edges, 0.08, 0)
    
    def apply_cinematic(self, frame, intensity=0.2):
        if intensity <= 0:
            return frame
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
        l, a, b = cv2.split(lab)
        l = cv2.multiply(l, 1.05)
        b = cv2.add(b, 4)
        lab = cv2.merge([l, a, b])
        graded = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
        
        rows, cols = frame.shape[:2]
        X_kernel = cv2.getGaussianKernel(cols, cols/2)
        Y_kernel = cv2.getGaussianKernel(rows, rows/2)
        kernel = Y_kernel * X_kernel.T
        mask = (kernel / kernel.max()) ** 0.5
        for i in range(3):
            graded[:,:,i] = (graded[:,:,i] * mask).astype(np.uint8)
        
        return cv2.addWeighted(frame, 1-intensity, graded, intensity, 0)
    
    def apply_aesthetic(self, frame, filter_name="none"):
        if filter_name == "none":
            return frame
        elif filter_name == "vintage":
            kernel = np.array([[0.272, 0.534, 0.131],
                               [0.349, 0.686, 0.168],
                               [0.393, 0.769, 0.189]])
            return cv2.transform(frame, kernel)
        elif filter_name == "bright":
            return cv2.convertScaleAbs(frame, alpha=1.2, beta=30)
        elif filter_name == "dramatic":
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l = cv2.equalizeHist(l)
            return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
        elif filter_name == "soft":
            return cv2.GaussianBlur(frame, (5,5), 0)
        elif filter_name == "cinematic":
            return self.apply_cinematic(frame, intensity=0.35)
        return frame
    
    def process_frame(self, frame, aesthetic="none"):
        if frame is None or frame.size == 0:
            return frame
            
        original_shape = frame.shape[:2]
        
        if self.style == "anime":
            styled = self.apply_anime(frame)
        elif self.style == "cartoon":
            styled = self.apply_cartoon(frame)
        elif self.style == "3d_render":
            styled = self.apply_3d_render(frame)
        elif self.style == "sketch":
            styled = self.apply_sketch(frame)
        elif self.style == "watercolor":
            styled = self.apply_watercolor(frame)
        else:
            styled = self.apply_cartoon(frame)
        
        styled = self.apply_aesthetic(styled, aesthetic)
        styled = self.apply_cinematic(styled, intensity=0.15)
        
        if styled.shape[:2] != original_shape:
            styled = cv2.resize(styled, (original_shape[1], original_shape[0]), 
                              interpolation=cv2.INTER_LANCZOS4)
        
        return styled
    
    def process_video_frame(self, frame, style=None):
        if style and style != self.style:
            self.style = style.lower().replace(" ", "_")
        return self.process_frame(frame)
