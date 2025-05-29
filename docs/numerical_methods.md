# MPI-AMRVAC 数值格式说明

## 1. 时间积分方法：三阶Runge-Kutta ('threestep')

MPI-AMRVAC使用三阶Runge-Kutta方法进行时间推进，具体实现为：

```fortran
do while (t < tmax)
    ! 第一阶段
    call compute_flux(U, F1)
    U1 = U + dt/3 * F1
    
    ! 第二阶段 
    call compute_flux(U1, F2)
    U2 = U + dt/2 * F2
    
    ! 第三阶段
    call compute_flux(U2, F3)
    U = U + dt * F3
    
    t = t + dt
end do
```

特点：
- 三阶精度时间离散
- 中等计算开销
- 较好的稳定性

## 2. 通量计算：HLL近似黎曼解

HLL (Harten-Lax-van Leer) 近似黎曼解：

```math
F^{HLL} = \begin{cases}
F_L & \text{if } S_L \geq 0 \\
\frac{S_R F_L - S_L F_R + S_L S_R (U_R - U_L)}{S_R - S_L} & \text{if } S_L < 0 < S_R \\
F_R & \text{if } S_R \leq 0
\end{cases}
```

其中：
- \( S_L \) 和 \( S_R \) 是波速估计
- \( F_L, F_R \) 是左右状态的通量
- \( U_L, U_R \) 是左右状态的守恒量

特点：
- 适用于MHD方程的近似解
- 计算效率高
- 能正确处理激波

## 3. 限制器：CADA3 TVD限制器

CADA3 (Conservative Adaptive Derivative Approximation) 限制器：

```fortran
phi(r) = max(0, min(1, 2r), min(2, r))
```

其中r是光滑度指示器：

```math
r_i = \frac{U_i - U_{i-1}}{U_{i+1} - U_i}
```

特点：
- 三阶精度
- 保持TVD (Total Variation Diminishing) 性质
- 有效抑制数值振荡

## 4. CFL条件控制

MPI-AMRVAC使用基于波速的CFL条件：

```math
dt = CFL \times \min\left(\frac{\Delta x}{|v| + c_s + c_A}\right)
```

其中：
- \( c_s \) 是声速
- \( c_A \) 是阿尔芬速度
- CFL数通常取0.8-0.9

特点：
- 自动适应局部波速
- 保证数值稳定性
- 参数可调(courantpar)
