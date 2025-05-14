
import pyvista as pv
import numpy as np

# 1. 读取VTU文件
mesh = pv.read("gem_2d0010.vtu")

# 2. 创建绘图窗口
plotter = pv.Plotter(shape=(2, 2))

# 子图1：数密度分布
plotter.subplot(0, 0)
plotter.add_mesh(mesh, scalars='rho', cmap='plasma', label='Density')
plotter.add_title("Number Density")

# 子图2：压强分布
plotter.subplot(0, 1)
plotter.add_mesh(mesh, scalars='p', cmap='viridis', label='Pressure')
plotter.add_title("Pressure")

# 子图3：速度场+磁力线
plotter.subplot(1, 0)
# 速度矢量
arrows = mesh.glyph(orient='v', scale='v_mag', factor=0.1)
plotter.add_mesh(arrows, color='red', label='Velocity')
# 磁力线
stream = mesh.streamlines('b', n_points=100, max_time=100)
plotter.add_mesh(stream, color='white', line_width=3)
plotter.add_title("Velocity & Field Lines")

# 子图4：磁场分布
plotter.subplot(1, 1)
plotter.add_mesh(mesh, scalars='b_mag', cmap='coolwarm', label='|B|')
plotter.add_title("Magnetic Field")

# 全局设置
plotter.link_views()  # 同步相机视角
plotter.add_scalar_bar(title_font_size=20)  # 色标
plotter.show()
