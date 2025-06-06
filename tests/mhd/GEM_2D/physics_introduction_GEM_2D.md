# GEM 2D Challenge 物理模型说明

## 1. 控制方程组

采用理想磁流体动力学(MHD)方程组：

**连续性方程**:
∂ρ/∂t + ∇·(ρv) = 0

**动量方程**:
∂(ρv)/∂t + ∇·[ρvv + (p+B²/2)I - BB] = 0

**能量方程**:
∂E/∂t + ∇·[(E+p+B²/2)v - (v·B)B] = 0

**磁场方程**:
∂B/∂t + ∇×(B×v) = 0

**状态方程**:
p = (γ-1)(E - ρv²/2 - B²/2)

其中：
- ρ: 质量密度
- v: 速度矢量
- p: 热力学压强
- B: 磁场强度
- E: 总能量密度
- γ=5/3: 绝热指数

## 2. 初始条件

### 2.1 背景等离子体
- 均匀密度: ρ₀ = 1
- 均匀压强: p₀ = 0.5
- 零速度场: v = 0

### 2.2 Harris电流片
B_x(y) = B₀ tanh(y/λ)
p(y) = p₀ + B₀²/2 sech²(y/λ)

参数：
- 电流片宽度: λ = 0.5
- 渐近磁场: B₀ = 1
- 中心压强: p₀ = 0.5

### 2.3 初始扰动
在电流片中心区域添加扰动：
B_y = δB sin(2πx/L_x) exp(-y²/2σ²)
其中：
- 扰动幅度: δB = 0.1
- 扰动宽度: σ = 0.5
- 系统长度: L_x = 25.6 (x∈[-12.8,12.8])

## 3. 边界条件

### 3.1 x方向 (周期性)
f(-L_x/2,y) = f(L_x/2,y)
B(-L_x/2,y) = B(L_x/2,y)

### 3.2 y方向 (对称/反对称)
**对称边界** (用于ρ,p,v_x,v_z,B_y):
f(x,-L_y/2) = f(x,L_y/2)
∂f/∂y|_sym = 0

**反对称边界** (用于v_y,B_x,B_z):
f(x,-L_y/2) = -f(x,L_y/2)
f|_antisym = 0

## 4. 数值方法配置

基于amrvac.par的数值参数：

### 4.1 网格系统
- 计算域: x∈[-12.8,12.8], y∈[-6.4,6.4]
- 基础分辨率: 64×64
- AMR等级: 最大4级

### 4.2 数值格式
- 时间积分: 三阶Runge-Kutta ('threestep')
- 通量计算: HLL近似黎曼解
- 限制器: CADA3 TVD限制器
- CFL数: 0.8

### 4.3 自适应网格
- 细化判据: 基于密度(0.4)、压强(0.3)、磁场(0.3)
- 细化阈值: 0.2
- 粗化比率: 0.1

## 5. 物理过程预期

该配置模拟磁重联过程：
1. 初始Harris平衡被扰动破坏
2. 电流片发展出X-line和磁岛结构
3. 磁场重联释放磁能
4. 等离子体被加速形成出流喷流
5. 系统最终达到新的平衡状态
