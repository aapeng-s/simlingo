import pygame
import numpy as np
from PIL import Image
import threading
import queue
import time

class PygameVisualizer:
    """
    实时pygame可视化器，支持多种显示模式包括原始大小不缩放
    """
    
    def __init__(self, window_title="SimLingo Agent Visualization", width=1400, height=900):
        """
        初始化pygame可视化器
        
        Args:
            window_title: 窗口标题
            width: 窗口宽度
            height: 窗口高度
        """
        self.window_title = window_title
        self.width = width
        self.height = height
        self.running = False
        self.screen = None
        self.clock = None
        self.image_queue = queue.Queue(maxsize=5)  # 限制队列大小避免内存堆积
        self.display_thread = None
        
        # 图像显示控制 - 默认原始大小不缩放
        self.scale_factor = 1.0  # 用户可调整的缩放因子
        self.display_mode = "original"  # 默认原始大小: "fit", "fill", "original", "custom"
        self.zoom_step = 0.1  # 缩放步长
        
    def start(self):
        """启动可视化显示线程"""
        if not self.running:
            self.running = True
            self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
            self.display_thread.start()
            print("✅ Pygame可视化器已启动 - 默认原始大小显示")
    
    def stop(self):
        """停止可视化显示"""
        self.running = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2.0)
        if pygame.get_init():
            pygame.quit()
        print("✅ Pygame可视化器已停止")
    
    def display_image(self, pil_image):
        """
        显示PIL图像
        
        Args:
            pil_image: PIL Image对象
        """
        if not self.running:
            return
            
        try:
            # 将PIL图像转换为numpy数组
            if pil_image.mode == 'RGBA':
                img_array = np.array(pil_image)
                # 移除alpha通道
                img_array = img_array[:, :, :3]
            else:
                img_array = np.array(pil_image.convert('RGB'))
            
            # 非阻塞式添加到队列
            if not self.image_queue.full():
                self.image_queue.put(img_array, block=False)
        except queue.Full:
            # 如果队列满了，丢弃旧图像
            try:
                self.image_queue.get_nowait()
                self.image_queue.put(img_array, block=False)
            except queue.Empty:
                pass
        except Exception as e:
            print(f"⚠️ 显示图像时出错: {e}")
    
    def _display_loop(self):
        """主显示循环（在单独线程中运行）"""
        try:
            # 初始化pygame
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption(self.window_title)
            self.clock = pygame.time.Clock()
            
            # 字体
            font = pygame.font.Font(None, 36)
            small_font = pygame.font.Font(None, 24)
            
            last_image = None
            
            while self.running:
                # 处理pygame事件
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        return
                    elif event.type == pygame.KEYDOWN:
                        # 键盘控制图像显示
                        if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                            self.scale_factor += self.zoom_step
                        elif event.key == pygame.K_MINUS:
                            self.scale_factor = max(0.1, self.scale_factor - self.zoom_step)
                        elif event.key == pygame.K_0:
                            self.scale_factor = 1.0  # 重置缩放
                        elif event.key == pygame.K_1:
                            self.display_mode = "fit"  # 适应窗口
                        elif event.key == pygame.K_2:
                            self.display_mode = "fill"  # 填充窗口
                        elif event.key == pygame.K_3:
                            self.display_mode = "original"  # 原始大小 - 不缩放
                        elif event.key == pygame.K_4:
                            self.display_mode = "custom"  # 自定义缩放
                
                # 获取最新图像
                try:
                    img_array = self.image_queue.get_nowait()
                    last_image = img_array
                except queue.Empty:
                    pass
                
                # 清空屏幕
                self.screen.fill((30, 30, 30))  # 深灰色背景
                
                if last_image is not None:
                    # 调整图像大小根据显示模式
                    img_height, img_width = last_image.shape[:2]
                    
                    # 根据显示模式计算缩放比例
                    if self.display_mode == "fit":
                        # 适应窗口，保持长宽比
                        scale_x = (self.width - 60) / img_width
                        scale_y = (self.height - 100) / img_height
                        scale = min(scale_x, scale_y)
                    elif self.display_mode == "fill":
                        # 填充窗口，可能改变长宽比
                        scale_x = (self.width - 60) / img_width
                        scale_y = (self.height - 100) / img_height
                        scale = max(scale_x, scale_y)
                    elif self.display_mode == "original":
                        # 原始大小 - 不缩放
                        scale = 1.0
                    elif self.display_mode == "custom":
                        # 自定义缩放
                        scale = self.scale_factor
                    else:
                        scale = 1.0
                    
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    
                    # 创建pygame surface
                    img_surface = pygame.surfarray.make_surface(last_image.swapaxes(0, 1))
                    
                    # 只在非原始大小模式下进行缩放
                    if scale != 1.0:
                        img_surface = pygame.transform.scale(img_surface, (new_width, new_height))
                    
                    # 计算显示位置（居中或滚动）
                    if new_width <= self.width and new_height <= self.height - 100:
                        # 图像能完全显示，居中
                        x = (self.width - new_width) // 2
                        y = (self.height - new_height) // 2 + 50
                        self.screen.blit(img_surface, (x, y))
                    else:
                        # 图像太大，从左上角开始显示，允许查看完整图像
                        x = 10
                        y = 70
                        
                        # 如果图像超出窗口，进行裁剪显示
                        if new_width > self.width - 20 or new_height > self.height - 120:
                            # 计算可见区域
                            visible_width = min(new_width, self.width - 20)
                            visible_height = min(new_height, self.height - 120)
                            
                            # 创建裁剪区域
                            cropped_surface = pygame.Surface((visible_width, visible_height))
                            cropped_surface.blit(img_surface, (0, 0), (0, 0, visible_width, visible_height))
                            
                            self.screen.blit(cropped_surface, (x, y))
                        else:
                            self.screen.blit(img_surface, (x, y))
                    
                    # 显示信息
                    info_text = font.render("SimLingo Agent - Real-time Visualization (20 FPS)", True, (255, 255, 255))
                    self.screen.blit(info_text, (10, 10))
                    
                    # 控制提示
                    controls_text = small_font.render("Controls: +/- Zoom | 0 Reset | 1 Fit | 2 Fill | 3 Original | 4 Custom", True, (180, 180, 180))
                    self.screen.blit(controls_text, (10, 40))
                    
                    # 底部状态信息
                    scale_info = small_font.render(f"Image: {img_width}x{img_height} | Display: {new_width}x{new_height} | Scale: {scale:.2f}x", True, (200, 200, 200))
                    self.screen.blit(scale_info, (10, self.height - 65))
                    
                    mode_info = small_font.render(f"Mode: {self.display_mode.upper()} | Custom Scale: {self.scale_factor:.1f}x", True, (150, 255, 150))
                    self.screen.blit(mode_info, (10, self.height - 45))
                    
                    fps_info = small_font.render("Synchronized with agent inference rate (20 FPS)", True, (150, 255, 150))
                    self.screen.blit(fps_info, (10, self.height - 25))
                    
                else:
                    # 没有图像时显示等待信息
                    wait_text = font.render("Waiting for visualization data...", True, (255, 255, 255))
                    text_rect = wait_text.get_rect(center=(self.width//2, self.height//2))
                    self.screen.blit(wait_text, text_rect)
                    
                    # 显示控制提示
                    controls_text = small_font.render("Controls: +/- Zoom | 0 Reset | 1 Fit | 2 Fill | 3 Original | 4 Custom", True, (180, 180, 180))
                    self.screen.blit(controls_text, (10, 40))
                    
                    mode_info = small_font.render(f"Current Mode: {self.display_mode.upper()} | Custom Scale: {self.scale_factor:.1f}x", True, (150, 255, 150))
                    self.screen.blit(mode_info, (10, self.height - 45))
                
                # 更新显示
                pygame.display.flip()
                self.clock.tick(20)  # 20 FPS (与agent推理帧率一致)
                
        except Exception as e:
            print(f"❌ Pygame显示循环出错: {e}")
        finally:
            if pygame.get_init():
                pygame.quit()

# 全局单例实例
_global_visualizer = None

def get_visualizer():
    """获取全局可视化器实例"""
    global _global_visualizer
    if _global_visualizer is None:
        _global_visualizer = PygameVisualizer()
    return _global_visualizer

def start_visualization():
    """启动可视化"""
    visualizer = get_visualizer()
    visualizer.start()

def stop_visualization():
    """停止可视化"""
    global _global_visualizer
    if _global_visualizer is not None:
        _global_visualizer.stop()
        _global_visualizer = None

def display_image(pil_image):
    """显示图像（便捷函数）"""
    visualizer = get_visualizer()
    if not visualizer.running:
        visualizer.start()
    visualizer.display_image(pil_image) 