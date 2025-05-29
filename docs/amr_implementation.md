# MPI-AMRVAC 自适应网格实现细节

## 核心数据结构

### 1. 网格面存储
```fortran
type facealloc
    double precision, dimension(:^D&), pointer :: face
end type facealloc

type(facealloc), dimension(:,:,:), allocatable :: pface  ! 存储相邻网格面数据
```

### 2. 细化通信控制
```fortran
type fake_neighbors
    integer :: igrid, ipe      ! 邻居网格和处理器信息
end type fake_neighbors

type(fake_neighbors), dimension(:^D&,:,:), allocatable :: fine_neighbors
```

## 关键子程序

### 1. 二阶延拓 (`prolong_2nd_stg`)
```fortran
subroutine prolong_2nd_stg(sCo,sFi,ixCo^L,ixFi^L,dxCo^D,xComin^D,dxFi^D,xFimin^D,ghost,fine_^L)
    ! 输入: 
    !   sCo - 粗网格状态
    !   sFi - 待填充的细网格状态
    ! 主要操作:
    !   1. 计算粗网格通量
    !   2. 通过斜率限制器进行二阶延拓
    !   3. 保持散度自由条件(DivB=0)
end subroutine
```

### 2. 面数据通信 (`comm_faces`)
```fortran
subroutine comm_faces
    ! MPI通信流程:
    !   1. 分配发送/接收缓冲区
    !   2. 发起非阻塞通信(MPI_IRECV/MPI_ISEND)
    !   3. 等待通信完成(MPI_WAITALL)
    ! 通信标签格式:
    !   itag = 4**ND*(igrid-1) + [方向编码]
end subroutine
```

## GEM重联专用优化

### 电流片识别
```python
# 伪代码展示电流片检测
def detect_current_sheet(B_field):
    grad_B = compute_gradient(B_field)
    J = curl(B_field)          # 电流密度
    return where(|J| > threshold)
```

### 动态调整示例
```fortran
! 在时间步进循环中
do while (time < tmax)
    call amr_refine_derefine()  ! 执行自适应调整
    call advance_solution()     ! 推进物理量
end do
```

## 性能调优建议

1. **平衡参数**：
   ```fortran
   w_refine_weight(1)=0.5d0   ! 增加密度权重
   refine_threshold=0.15d0     ! 更敏感的细化触发
   ```

2. **诊断命令**：
   ```bash
   # 监控网格变化
   grep "Refined" run.log | awk '{print $4}' | sort -n | uniq -c
   ```

3. **可视化验证**：
   ```python
   visit -o grid_*.vtu -p "Pseudocolor: RefinementLevel"
   ```
