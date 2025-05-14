"""
GEM磁重联可视化脚本（最终修正版）
与AMRVAC工具包兼容
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.interpolate import griddata

try:
    # 动态路径处理
    tool_path = Path('/Users/jshept/Documents/GitHubOrg/MPI-AMRVAC/tools/python')
    if str(tool_path) not in sys.path:
        sys.path.insert(0, str(tool_path))
    
    # 按实际模块结构导入
    from amrvac_pytools.vtkfiles.read import loadvti
    from amrvac_pytools.vtkfiles.amrplot import polyplot
    from amrvac_pytools.vtkfiles.streamplot import streamplot

    # 使用绝对路径加载数据文件
    data_file = "/Users/jshept/Documents/GitHubOrg/MPI-AMRVAC/tests/mhd/GEM_2D/gem_2d0008.vtu"
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"数据文件不存在于路径: {data_file}\n请确认文件位置或重新运行模拟")

    # 检查文件大小
    if os.path.getsize(data_file) == 0:
        raise ValueError(f"数据文件为空: {data_file}")

    try:
        # 使用通用VTK文件加载器
        from amrvac_pytools.vtkfiles.read import load_vtkfile
        ds = load_vtkfile(data_file, type='vtu')
        if ds is None:
            raise RuntimeError("VTK文件加载失败，可能文件已损坏")
            
        print("可用变量:", [var for var in ds.GetCellData().GetArrayNames() if not var.startswith('_')])
        
    except Exception as e:
        raise RuntimeError(
            f"加载VTK文件失败: {str(e)}\n"
            f"建议检查:\n"
            f"1. 文件完整性 (尝试重新生成)\n"
            f"2. VTK库版本兼容性\n"
            f"3. 文件权限"
        )

    # 创建图形和子图
    fig = plt.figure(figsize=(12, 8))
    
    # 子图1：密度分布
    ax1 = fig.add_subplot(2, 2, 1)
    plot_rho = polyplot(ds.rho, ds, cmap='viridis', axis=ax1, title='Density')
    
    # 子图2：压强分布
    ax2 = fig.add_subplot(2, 2, 2)
    plot_p = polyplot(ds.p, ds, cmap='plasma', axis=ax2, title='Pressure')
    
    # 子图3：磁场分布
    ax3 = fig.add_subplot(2, 2, 3)
    plot_b = polyplot(ds.b, ds, cmap='cool', axis=ax3, title='Magnetic Field')
    
    # 子图4：速度场
    ax4 = fig.add_subplot(2, 2, 4)
    plot_v = polyplot(ds.v, ds, cmap='hot', axis=ax4, title='Velocity')
    
    # 准备磁力线数据
    x = np.linspace(ds.bounds[0], ds.bounds[1], 100)
    y = np.linspace(ds.bounds[2], ds.bounds[3], 100)
    grid_x, grid_y = np.meshgrid(x, y)
    
    # 从AMR数据插值到规则网格
    points = ds.get_center_points()
    b_x = griddata(points, ds.b[:,0], (grid_x, grid_y), method='linear')
    b_y = griddata(points, ds.b[:,1], (grid_x, grid_y), method='linear')
    
    # 绘制磁力线
    streamplot(x, y, b_x, b_y, density=2, color='white', ax=ax3)
    
    plt.tight_layout()
    plt.show()

except ImportError as e:
    print("导入错误:", e)
    print("请确保：")
    print("1. 已正确安装AMRVAC Python工具包")
    print("2. 依赖库已安装(numpy, matplotlib, scipy等)")
except Exception as e:
    print("运行时错误:", e)
finally:
    plt.close('all')