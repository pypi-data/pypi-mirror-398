# Copyright 2025 Shi Jingqi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import tensorflow as tf
import numpy as np
from PIL import Image
import os
import cv2
import tempfile
import json
from tqdm import tqdm
import math
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

class ImgZip:
    """图像和视频压缩解压处理类，带详细进度条显示，支持自定义模型输入shape和图像质量分析"""
    
    def __init__(self, model_path, input_shape):
        """初始化ImgZip实例"""
        self.model_path = model_path
        self.input_shape = input_shape  # 格式为 (height, width, channels)，如 (80, 80, 3)
        self.autoencoder, self.encoder, self.decoder = self._load_and_split_model()
        # 确定编码器输出向量的维度
        test_input = np.random.rand(1, self.input_shape[0], self.input_shape[1], self.input_shape[2]).astype(np.float32)
        self.vector_dim = self.encoder.predict(test_input, verbose=0).shape[1]
    
    def _load_and_split_model(self):
        """加载自编码器模型并拆分编码器和解码器"""
        try:
            print("正在加载模型...")
            autoencoder = tf.keras.models.load_model(self.model_path)
            encoder = autoencoder.get_layer('encoder')
            decoder = autoencoder.get_layer('decoder')
            print("模型加载完成")
            return autoencoder, encoder, decoder
        except Exception as e:
            raise RuntimeError(f"模型加载失败: {str(e)}")
    
    # 图像数组转换与保存
    def image_to_array(self, img_path):
        """将图像转换为数组（使用模型输入shape）"""
        try:
            img = Image.open(img_path).resize((self.input_shape[1], self.input_shape[0])).convert('RGB')
            return np.array(img).astype(np.float32) / 255.0
        except Exception as e:
            raise IOError(f"图像转换为数组失败: {str(e)}")
    
    def array_to_image(self, img_array):
        """将数组转换为图像"""
        try:
            img_array = (img_array * 255).clip(0, 255).astype(np.uint8)
            return Image.fromarray(img_array)
        except Exception as e:
            raise ValueError(f"数组转换为图像失败: {str(e)}")
    
    def save_image_array(self, array, save_path):
        """将图像数组保存为文件"""
        try:
            np.save(save_path, array)
            return True
        except Exception as e:
            raise IOError(f"保存图像数组失败: {str(e)}")
    
    def load_image_array(self, array_path):
        """从文件加载图像数组"""
        try:
            return np.load(array_path)
        except Exception as e:
            raise IOError(f"加载图像数组失败: {str(e)}")
    
    # 图像压缩与解压
    def compress_image(self, img_path, patch=True, save_path=None, ability=0.):
        """压缩图像"""
        result = {}
        n_char = self.encoder.outputs[0].shape[-1]
        input_height, input_width = self.input_shape[0], self.input_shape[1]
        
        now_ab = n_char / (input_height * input_width * 3)
        
        if ability:
            change = now_ab / ability
        else:
            change = 1
        
        if patch:
            # 分块处理模式
            img = Image.open(img_path)
            w0, h0 = img.size
            w, h = int(w0 / math.sqrt(change)), int(h0 / math.sqrt(change))
            img = img.resize((w, h))
            
            # 计算分块数量
            cols = (w + input_width - 1) // input_width
            rows = (h + input_height - 1) // input_height
            
            # 保存形状信息
            result['shape'] = (w, h, cols, rows)
            result['vectors'] = []
            result['change'] = change
            
            # 创建足够大的画布
            canvas = Image.new('RGB', (cols * input_width, rows * input_height))
            canvas.paste(img, (0, 0))
            
            # 分块处理带进度条
            total_blocks = rows * cols
            with tqdm(total=total_blocks, desc="图像分块编码", unit="块") as pbar:
                for y in range(rows):
                    for x in range(cols):
                        # 裁剪出对应尺寸的块
                        block = canvas.crop((x * input_width, y * input_height, 
                                            (x + 1) * input_width, (y + 1) * input_height))
                        block_array = np.array(block).astype(np.float32) / 255.0
                        
                        # 编码
                        vector = self.encoder.predict(np.expand_dims(block_array, axis=0), verbose=0)[0]
                        result['vectors'].append(vector.astype(np.int16))
                        pbar.update(1)
                        
        else:
            # 单块处理模式
            img = Image.open(img_path).resize((input_width, input_height)).convert('RGB')
            img_array = np.array(img).astype(np.float32) / 255.0
            vector = self.encoder.predict(np.expand_dims(img_array, axis=0), verbose=0)[0]
            result['vector'] = vector.astype(np.int16)
            result['shape'] = (input_height, input_width)
            
        
        # 保存压缩结果
        if save_path:
            # 分离形状信息和向量数据
            shape_path = save_path + ".shape"
            with open(shape_path, 'w') as f:
                json.dump((result['shape'], result['change']), f)
            
            # 保存向量数据
            if patch:
                vectors = np.array(result['vectors'])
                np.save(save_path, vectors)
            else:
                np.save(save_path, result['vector'])
            return save_path
        else:
            return result
    
    def decompress_image(self, compressed_input, patch=True, save_path=None):
        """解压图像"""
        input_height, input_width = self.input_shape[0], self.input_shape[1]
        
        # 加载压缩数据
        if isinstance(compressed_input, str) and os.path.exists(compressed_input + ".npy"):
            # 从文件加载
            data = {}
            # 加载形状信息
            shape_path = compressed_input + ".shape"
            with open(shape_path, 'r') as f:
                data['shape'], data['change'] = json.load(f)
            
            # 加载向量数据
            vector_data = np.load(compressed_input + ".npy")
            if patch:
                data['vectors'] = vector_data
            else:
                data['vector'] = vector_data
        else:
            # 使用内存中的数据
            data = compressed_input
        
        if patch:
            # 提取原始尺寸信息
            w, h, cols, rows = data['shape']
            vectors = data['vectors']
            change = data['change']
            
            w2, h2 = int(w * math.sqrt(change)), int(h * math.sqrt(change))
            
            if len(vectors) != rows * cols:
                raise ValueError(f"压缩数据中的块数量与尺寸信息不匹配: {len(vectors)} != {rows * cols}")
            
            # 创建空白画布
            canvas = Image.new('RGB', (cols * input_width, rows * input_height))
            
            # 分块解码带进度条
            total_blocks = len(vectors)
            with tqdm(total=total_blocks, desc="图像分块解码", unit="块") as pbar:
                for idx, vector in enumerate(vectors):
                    # 计算当前块的位置
                    row = idx // cols
                    col = idx % cols
                    
                    # 解码单个块
                    decoded = self.decoder.predict(np.expand_dims(vector, axis=0), verbose=0)[0]
                    decoded = (decoded * 255).clip(0, 255).astype(np.uint8)
                    block_img = Image.fromarray(decoded)
                    
                    # 将块粘贴到画布上
                    canvas.paste(block_img, (col * input_width, row * input_height))
                    pbar.update(1)
            
            # 裁剪回原始尺寸
            img = canvas.crop((0, 0, w, h)).resize((w2, h2))
        else:
            # 单块处理模式
            vector = data['vector']
            decoded = self.decoder.predict(np.expand_dims(vector, axis=0), verbose=0)[0]
            decoded = (decoded * 255).clip(0, 255).astype(np.uint8)
            img = Image.fromarray(decoded)
        
        # 保存解压结果
        if save_path:
            img.save(save_path)
        
        return img
    
    # 图像质量分析
    def analyze_image_quality(self, img_path, reference_img_path=None):
        """
        分析图像质量，计算关键指标及综合得分
        :param img_path: 待分析图像路径
        :param reference_img_path: 参考图像路径（用于PSNR/SSIM计算，无则用自身平滑图作为参考）
        :return: 包含各指标和综合得分的字典
        """
        try:
            # 读取并预处理待分析图像
            img = Image.open(img_path).convert('RGB')
            img_array = np.array(img).astype(np.float32) / 255.0
            img_gray = np.array(img.convert('L')).astype(np.float32) / 255.0
            
            # 处理参考图像（无参考图时用高斯模糊后的图像作为噪声参考）
            if reference_img_path and os.path.exists(reference_img_path):
                ref_img = Image.open(reference_img_path).convert('RGB').resize(img.size)
                ref_array = np.array(ref_img).astype(np.float32) / 255.0
                ref_gray = np.array(ref_img.convert('L')).astype(np.float32) / 255.0
            else:
                # 高斯模糊生成参考图（模拟无参考质量评价）
                ref_gray = cv2.GaussianBlur(img_gray, (5, 5), 1.5)
                ref_array = cv2.GaussianBlur(img_array, (5, 5), 1.5)
            
            # 1. 计算信噪比（SNR）：信号方差/噪声方差
            signal_var = np.var(img_gray)
            noise_var = np.var(img_gray - ref_gray)
            snr_value = 10 * np.log10(signal_var / noise_var) if noise_var != 0 else 40.0  # 避免除零
            
            # 2. 计算峰值信噪比（PSNR）：衡量图像失真程度
            psnr_value = psnr(ref_array, img_array, data_range=1.0)
            
            # 3. 计算结构相似性（SSIM）：衡量结构一致性
            ssim_value = ssim(ref_gray, img_gray, data_range=1.0, win_size=11)
            
            # 4. 计算综合质量得分（加权求和，归一化到0-100分）
            # 权重分配：PSNR(40%)、SSIM(50%)、SNR(10%)
            psnr_score = min(max(psnr_value / 50 * 40, 0), 40)  # PSNR上限设为50，对应40分
            ssim_score = min(max(ssim_value * 50, 0), 50)       # SSIM上限1，对应50分
            snr_score = min(max(snr_value / 40 * 10, 0), 10)    # SNR上限40，对应10分
            total_score = round(psnr_score + ssim_score + snr_score, 2)
            
            # 得分等级说明
            if total_score >= 80:
                grade = "优秀"
            elif total_score >= 60:
                grade = "良好"
            elif total_score >= 40:
                grade = "一般"
            else:
                grade = "较差"
            
            result = {
                "图像路径": img_path,
                "参考图像路径": reference_img_path or "无（使用高斯模糊参考）",
                "信噪比（SNR）": round(snr_value, 2),
                "峰值信噪比（PSNR）": round(psnr_value, 2),
                "结构相似性（SSIM）": round(ssim_value, 4),
                "综合质量得分": total_score,
                "质量等级": grade
            }
            
            return result
        except Exception as e:
            raise RuntimeError(f"图像质量分析失败: {str(e)}")
    
    # 视频处理函数
    def _extract_frames(self, video_path, temp_dir=None):
        """从视频中提取帧，带进度条"""
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_paths = []
        frame_count = 0
        
        # 提取帧带进度条
        with tqdm(total=total_frames, desc="提取视频帧", unit="帧") as pbar:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 转换为RGB格式(OpenCV默认是BGR)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_img = Image.fromarray(frame_rgb)
                
                # 保存帧
                frame_path = os.path.join(temp_dir, f"frame_{frame_count:06d}.jpg")
                frame_img.save(frame_path)
                frame_paths.append(frame_path)
                
                frame_count += 1
                pbar.update(1)
        
        cap.release()
        return frame_paths, (fps, width, height), temp_dir
    
    def _frames_to_video(self, frame_paths, output_path, fps, width, height):
        """将帧组合成视频，带进度条"""
        # 定义编码器和创建VideoWriter对象
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # 组合帧带进度条
        with tqdm(total=len(frame_paths), desc="合成视频帧", unit="帧") as pbar:
            for frame_path in frame_paths:
                # 读取图像并转换为BGR格式
                frame = cv2.imread(frame_path)
                # 确保图像尺寸正确
                frame = cv2.resize(frame, (width, height))
                out.write(frame)
                pbar.update(1)
        
        out.release()
    
    def compress_video(self, video_path, output_dir, patch=True):
        """压缩视频，带详细进度条"""
        os.makedirs(output_dir, exist_ok=True)
        
        print("开始视频压缩流程...")
        
        # 提取帧
        print("步骤1/3: 提取视频帧")
        frame_paths, (fps, width, height), temp_dir = self._extract_frames(video_path)
        frame_count = len(frame_paths)
        print(f"成功提取 {frame_count} 帧")
        
        # 保存视频元数据
        metadata = {
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": frame_count,
            "patch": patch,
            "input_shape": self.input_shape  # 保存输入shape供解压使用
        }
        metadata_path = os.path.join(output_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # 压缩每一帧
        print("步骤2/3: 压缩视频帧")
        compressed_paths = []
        for i, frame_path in enumerate(tqdm(frame_paths, desc="压缩帧", unit="帧")):
            compressed_path = os.path.join(output_dir, f"frame_{i:06d}")
            self.compress_image(frame_path, patch=patch, save_path=compressed_path)
            compressed_paths.append(compressed_path)
        
        # 清理临时文件
        print("步骤3/3: 清理临时文件")
        with tqdm(total=len(frame_paths), desc="清理文件", unit="个") as pbar:
            for frame_path in frame_paths:
                if os.path.exists(frame_path):
                    os.remove(frame_path)
                pbar.update(1)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        
        print(f"视频压缩完成，共处理 {frame_count} 帧")
        return compressed_paths, metadata_path
    
    def decompress_video(self, compressed_dir, output_path):
        """解压视频，带详细进度条"""
        print("开始视频解压流程...")
        
        # 读取元数据
        metadata_path = os.path.join(compressed_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"找不到元数据文件: {metadata_path}")
            
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        fps = float(metadata['fps'])
        width = int(metadata['width'])
        height = int(metadata['height'])
        frame_count = int(metadata['frame_count'])
        patch = metadata['patch']
        # 从元数据加载输入shape（确保解压时与压缩时使用相同shape）
        self.input_shape = tuple(metadata['input_shape'])
        
        print(f"视频信息: 分辨率 {width}x{height}, 帧率 {fps:.2f}, 共 {frame_count} 帧, 模型输入shape {self.input_shape}")
        
        # 创建临时目录保存解压的帧
        temp_dir = tempfile.mkdtemp()
        frame_paths = []
        
        # 解压每一帧
        print("步骤1/2: 解压视频帧")
        for i in tqdm(range(frame_count), desc="解压帧", unit="帧"):
            compressed_path = os.path.join(compressed_dir, f"frame_{i:06d}")
            if not os.path.exists(compressed_path + ".npy"):
                raise FileNotFoundError(f"找不到压缩帧文件: {compressed_path}")
                
            frame_path = os.path.join(temp_dir, f"frame_{i:06d}.jpg")
            self.decompress_image(compressed_path, patch=patch, save_path=frame_path)
            frame_paths.append(frame_path)
        
        # 将帧组合成视频
        print("步骤2/2: 合成视频")
        self._frames_to_video(frame_paths, output_path, fps, width, height)
        
        # 清理临时文件
        print("清理临时文件...")
        with tqdm(total=len(frame_paths), desc="清理文件", unit="个") as pbar:
            for frame_path in frame_paths:
                if os.path.exists(frame_path):
                    os.remove(frame_path)
                pbar.update(1)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
        
        print(f"视频解压完成，已保存到 {output_path}")


def interactive_mode():
    """交互模式，允许用户通过命令行使用库功能"""
    print("===== img_zip 图像视频压缩工具 =====")
    # 模型输入shape说明
    print("\n【模型输入shape说明】")
    print("1. 芥象系列所有输入shape都只支持80*80")
    print("2. 芥象2系列模型支持的shape需要参考其模型文件命名")
    print("3. 输入格式为 高度,宽度,通道数（如 80,80,3），通道数默认3（RGB）")
    
    model_path = input("\n请输入.keras模型路径: ")
    shape_input = input("请输入模型的输入shape（格式：高度,宽度,通道数）: ")
    
    try:
        # 解析输入shape
        input_shape = tuple(map(int, shape_input.split(',')))
        if len(input_shape) != 3:
            raise ValueError("输入shape格式错误，必须包含高度、宽度、通道数三个数值")
        print(f"已设置模型输入shape为: {input_shape}")
        
        img_zip = ImgZip(model_path, input_shape)
        print("模型加载完成!")
    except ValueError as ve:
        print(f"初始化失败: {str(ve)}")
        return
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        return
    
    while True:
        print("\n请选择功能:")
        print("1. 压缩图像（支持自定义压缩率）")
        print("2. 解压图像（自动检测自定义的压缩率）")
        print("3. 压缩视频（不支持自定义压缩率）")
        print("4. 解压视频（不支持自定义压缩率）")
        print("5. 图像转数组")
        print("6. 数组转图像")
        print("7. 分析图像质量（计算SNR/PSNR/SSIM及综合得分）")
        print("0. 退出")
        
        choice = input("请选择 (0-7): ")
        
        if choice == '0':
            print("感谢使用，再见!")
            break
        
        elif choice == '1':
            img_path = input("请输入图像路径: ")
            if not os.path.exists(img_path):
                print("错误: 图像文件不存在")
                continue
                
            use_patch = input("使用分块处理? (y/n): ").lower() == 'y'
            save_path = input("请输入保存压缩结果的路径前缀: ")
            print('''
【关于自定义压缩率功能的提示】
1. 自定义压缩率通过缩放原始图实现，所以传入的压缩率大于该模型原生压缩率时会增加处理时间，小于该模型原生压缩率时会减少处理时间
2. 一般情况下，自定义的压缩率越高，图像解压后的效果越好
3. 自定义压缩率为0时，表示使用该模型的原生压缩率
4. 为了均衡压缩速度与解压效果，建议设为0.02
5. 当前该功能处于测试阶段，出现BUG请及时联系我们：xiaothink@foxmail.com
''')
            ability = float(input("输入您希望的预计压缩率: "))
            
            try:
                img_zip.compress_image(img_path, patch=use_patch, save_path=save_path, ability=ability)
                print(f"成功: 图像已压缩并保存到 {save_path}.npy 和 {save_path}.shape")
            except Exception as e:
                print(f"失败: {str(e)}")
        
        elif choice == '2':
            compressed_path = input("请输入压缩文件路径前缀: ")
            if not os.path.exists(compressed_path + ".npy"):
                print("错误: 压缩文件不存在")
                continue
                
            use_patch = input("使用分块处理? (y/n): ").lower() == 'y'
            save_path = input("请输入保存解压结果的路径: ")
            
            try:
                img_zip.decompress_image(compressed_path, patch=use_patch, save_path=save_path)
                print(f"成功: 图像已解压并保存到 {save_path}")
            except Exception as e:
                print(f"失败: {str(e)}")
        
        elif choice == '3':
            video_path = input("请输入视频路径: ")
            if not os.path.exists(video_path):
                print("错误: 视频文件不存在")
                continue
                
            output_dir = input("请输入保存压缩结果的目录: ")
            use_patch = input("使用分块处理? (y/n): ").lower() == 'y'
            
            try:
                _, _ = img_zip.compress_video(video_path, output_dir, patch=use_patch)
                print(f"成功: 视频已压缩并保存到 {output_dir}")
            except Exception as e:
                print(f"失败: {str(e)}")
        
        elif choice == '4':
            compressed_dir = input("请输入压缩帧所在目录: ")
            if not os.path.exists(compressed_dir):
                print("错误: 压缩目录不存在")
                continue
                
            output_path = input("请输入保存解压视频的路径: ")
            
            try:
                img_zip.decompress_video(compressed_dir, output_path)
                print(f"成功: 视频已解压并保存到 {output_path}")
            except Exception as e:
                print(f"失败: {str(e)}")
        
        elif choice == '5':
            img_path = input("请输入图像路径: ")
            if not os.path.exists(img_path):
                print("错误: 图像文件不存在")
                continue
                
            save_path = input("请输入保存数组的路径 (.npy): ")
            
            try:
                img_array = img_zip.image_to_array(img_path)
                img_zip.save_image_array(img_array, save_path)
                print(f"成功: 图像已转换为数组并保存到 {save_path}")
            except Exception as e:
                print(f"失败: {str(e)}")
        
        elif choice == '6':
            array_path = input("请输入数组文件路径 (.npy): ")
            if not os.path.exists(array_path):
                print("错误: 数组文件不存在")
                continue
                
            save_path = input("请输入保存图像的路径: ")
            
            try:
                img_array = img_zip.load_image_array(array_path)
                img = img_zip.array_to_image(img_array)
                img.save(save_path)
                print(f"成功: 数组已转换为图像并保存到 {save_path}")
            except Exception as e:
                print(f"失败: {str(e)}")
        
        elif choice == '7':
            img_path = input("请输入待分析图像路径: ")
            if not os.path.exists(img_path):
                print("错误: 待分析图像文件不存在")
                continue
                
            use_reference = input("是否使用参考图像进行对比分析? (y/n): ").lower() == 'y'
            reference_path = ""
            if use_reference:
                reference_path = input("请输入参考图像路径: ")
                if not os.path.exists(reference_path):
                    print("错误: 参考图像文件不存在，将使用默认高斯模糊参考")
                    reference_path = None
            
            try:
                quality_result = img_zip.analyze_image_quality(img_path, reference_path)
                print("\n===== 图像质量分析结果 =====")
                for key, value in quality_result.items():
                    print(f"{key}: {value}")
                print("===========================")
                print("得分说明：80分以上优秀，60-80分良好，40-60分一般，40分以下较差")
            except Exception as e:
                print(f"失败: {str(e)}")
        
        else:
            print("无效的选择，请重试")


if __name__ == "__main__":
    interactive_mode()
