# AMRVAC Riemann_1.75D 并行化设计说明

## 1. 并行初始化
```fortran
! 主程序启动MPI
call comm_start()  ! 初始化MPI环境
```
- 功能：建立MPI通信域，分配进程ID
- 关键变量：`mype`(当前进程), `npe`(总进程数)

## 2. 数据分区
```mermaid
graph LR
    A[全局网格] --> B[空间分解]
    B --> C[Morton排序]
    C --> D[动态负载均衡]
```
- 负载均衡阈值：`load_threshold = 1.2`

## 3. 通信模式
| 通信类型       | 调用函数                  | 应用场景               |
|----------------|--------------------------|-----------------------|
| 点对点通信     | MPI_SENDRECV            | 边界Ghost Cell交换    |
| 集体通信       | MPI_ALLREDUCE           | 时间步长同步          |
| 非阻塞通信     | MPI_ISEND/MPI_IRECV      | 通信-计算重叠         |

## 4. 典型工作流
```fortran
do while (t < t_max)
    call getbc()       ! 边界同步
    call advance()     ! 推进计算
    call resettree()   ! 动态AMR
end do
```

## 5. 性能优化
- 通信压缩：使用`MPI_PACK`减少数据量
- 拓扑感知：根据NUMA节点分配网格
- 异步I/O：`MPI_FILE_*`系列函数

## 6. 扩展建议
1. 增加OpenMP线程级并行
2. 采用MPI-4.0的持久通信
3. 集成GPU加速
