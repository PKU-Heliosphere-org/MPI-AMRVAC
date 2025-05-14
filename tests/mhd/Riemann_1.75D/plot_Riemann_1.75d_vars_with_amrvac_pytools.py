import numpy as np
import matplotlib.pyplot as plt
from amrvac_pytools.vtkfiles import read, amrplot
import glob
import os

# 配置参数
file_prefix = "./Riemann_1.75D"  # 文件前缀
time_steps = range(0, 15)        # 时间步范围(根据实际文件调整)
output_dir = "./plots"           # 输出目录

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 获取变量列表(以第一个时间步为例)
sample_data = read.load_vtkfile(time_steps[0], file=file_prefix, type='vtu')
variables = sample_data.getVarnames()
print(f"Available variables: {variables}")

# 对每个时间步进行处理
for step in time_steps:
    try:
        # 读取数据
        data = read.load_vtkfile(step, file=file_prefix, type='vtu')
        
        # 计算需要的行数(向上取整)
        n_cols = 2  # 固定两列
        n_rows = (len(variables) + 1) // n_cols 

        # 创建多面板图，调整figsize以适应新布局
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4*n_rows))

        #a if len(variables) == 1:
        #a    axes = [axes]  # 确保单个变量时axes仍是列表

        # 展平axes数组便于迭代
        axes = axes.ravel() 
            
        # 绘制每个变量
        for i, var in enumerate(variables):
            ax = axes[i]    # 获取当前子图
            # 获取变量数据
            var_data = getattr(data, var)
            
            # 绘制曲线
            ax.plot(data.getCenterPoints(), var_data, 'b-')
            ax.set_title(f"Time Step {step}: {var}")
            ax.set_xlabel("Position")
            ax.set_ylabel(var)

            # 添加离散点显示网格
            ax.scatter(data.getCenterPoints(), var_data, 
                s=5, c='red', marker='o', 
                alpha=0.6, label='AMR Cell Centers')

            # 添加图例
            ax.legend()
        
        plt.tight_layout()
        
        # 保存图像
        output_path = os.path.join(output_dir, f"step_{step:04d}.png")
        plt.savefig(output_path)
        plt.close()
        print(f"Saved plot for step {step} to {output_path}")
        
    except Exception as e:
        print(f"Error processing step {step}: {str(e)}")

print("All time steps processed!")

# 视频生成功能 (追加在脚本末尾)
def create_video(image_folder, video_name, fps=5):
    """
    将图像序列转换为MP4视频
    
    参数:
        image_folder: 包含PNG图像的目录
        video_name: 输出视频文件名
        fps: 帧率(每秒帧数)
    """
    import cv2
    import os
    
    images = sorted([img for img in os.listdir(image_folder) if img.endswith(".png")])
    if not images:
        print("未找到PNG图像文件")
        return
    
    # 读取第一张图像获取尺寸
    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))
    
    # 添加所有图像到视频
    for image in images:
        video.write(cv2.imread(os.path.join(image_folder, image)))
    
    cv2.destroyAllWindows()
    video.release()
    print(f"视频已生成: {video_name}")

# 使用示例 (可取消注释使用)
create_video(output_dir, "riemann_simulation.mp4", fps=3)