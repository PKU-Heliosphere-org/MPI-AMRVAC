# MPI-AMRVAC refine_criterion 参数说明

## refine_criterion=3 的含义

`refine_criterion=3` 是MPI-AMRVAC中网格自适应细化(AMR)的误差估计方法选择参数，具体为：

### 对应方法
- **3**: 基于Lohner型误差估计器（改进的梯度检测方法）
  
### 工作原理
1. 计算变量归一化梯度：
   ```math
   E_i = \frac{|\nabla U_i| \cdot \Delta x}{|U_i| + \epsilon}
   ```
2. 组合多个物理量的误差估计（密度、压强、磁场等）
3. 当组合误差超过阈值(refine_threshold)时触发网格细化

### 特点
- 对激波和间断有高灵敏度
- 自动适应不同物理量的量级
- 数值鲁棒性好（通过ε避免除零）

## 典型应用场景

### GEM重联模拟中的表现
1. 在电流片区域自动提高分辨率
2. 对磁场梯度变化敏感
3. 能有效捕捉X-point和磁岛结构

## 相关参数配置
```fortran
&meshlist
    refine_criterion = 3       ! Lohner型误差估计
    refine_threshold = 0.2d0  ! 细化触发阈值
    derefine_ratio = 0.1d0    ! 粗化触发比率
/
```

## 其他可选值（参考）
- 1: 简单梯度检测
- 2: Richardson外推误差估计
- 4: 小波变换检测
