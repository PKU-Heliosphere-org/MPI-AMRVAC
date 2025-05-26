# MPI-AMRVAC并行化设计全面分析

## 1. 并行初始化模块
### 1.1 主要功能
- 初始化MPI并行环境
- 设置进程通信拓扑
- 创建自定义MPI数据类型
- 提供并行错误处理机制

### 1.2 关键实现
在`comm_lib.f`中实现核心功能：

1. **MPI环境初始化** (`comm_start`子程序):
```fortran
call MPI_INIT(ierrmpi)  ! 初始化MPI
call MPI_COMM_RANK(MPI_COMM_WORLD,mype,ierrmpi)  ! 获取进程rank
call MPI_COMM_SIZE(MPI_COMM_WORLD,npe,ierrmpi)    ! 获取总进程数
icomm = MPI_COMM_WORLD  ! 设置默认通信子
```

2. **数据类型验证**:
```fortran
call MPI_TYPE_GET_EXTENT(MPI_DOUBLE_PRECISION,lb,sizes,ierrmpi)
if (sizes /= size_double) call mpistop("Incompatible double size")
```

3. **自定义数据类型创建** (`init_comm_types`子程序):
```fortran
! 创建块数据类型
call MPI_TYPE_CREATE_SUBARRAY(ndim+1,sizes,subsizes,start,&
   MPI_ORDER_FORTRAN,MPI_DOUBLE_PRECISION,type_block,ierrmpi)
call MPI_TYPE_COMMIT(type_block,ierrmpi)
```

4. **错误处理** (`mpistop`子程序):
```fortran
call MPI_ABORT(icomm, ierrcode, ierrmpi)  ! 异常终止所有进程
```

### 1.3 调用关系
1. 程序启动时首先调用`comm_start`
2. 初始化阶段调用`init_comm_types`创建数据类型
3. 运行过程中通过`mpistop`处理错误
4. 程序结束调用`comm_finalize`清理MPI环境

关键数据结构：
- `mype`: 当前进程rank (0~npe-1)
- `npe`: 总进程数
- `icomm`: 通信子(默认MPI_COMM_WORLD)
- `type_block`: 基本网格数据通信类型

## 2. 自适应网格管理
### 2.1 网格数据结构
- 多级网格结构(levmin到levmax)
- 每个网格块包含：
  - 物理量数据(ps%w)
  - 网格坐标信息(rnode)
  - 邻居关系(neighbor)
- 交错网格支持(stagger_grid)

### 2.2 并行通信实现
在`amrgrid.f`中实现核心功能：

1. **网格树建立** (`settree`子程序):
```fortran
do levnew=2,refine_max_level
   if(refine_criterion==1) then
     call setdt
     call advance(0)  ! 需要先推进时间步
   end if
   call errest       ! 误差估计
   call amr_coarsen_refine  ! 执行细化/粗化
end do
```

2. **动态网格重置** (`resettree`子程序):
```fortran
call deallocateBflux  ! 释放边界通量存储
call amr_coarsen_refine  ! 重新建立网格
call allocateBflux   ! 重新分配边界通量
```

3. **特殊转换处理** (`resettree_convert`子程序):
```fortran
do while(levmin<my_levmin.or.levmax>my_levmax)
   call getbc(global_time,0.d0,ps,iwstart,nwgc)  ! 更新边界
   call forcedrefine_grid_io  ! 强制细化到指定级别
   call amr_coarsen_refine
end do
```

### 2.3 调用流程
1. 初始化时调用`settree`建立初始网格
2. 每个时间步后检查是否需要`resettree`
3. 输出前可能需要`resettree_convert`
4. 特殊物理模块可调用`initialize_after_settree`

关键控制参数：
- `refine_max_level`: 最大细化级别
- `refine_criterion`: 细化标准类型
- `level_io`: 输出时指定的网格级别


## 3. 边界条件处理
### 3.1 通信模式
在`mod_ghostcells_update.f`中实现三种通信模式：
1. **同级通信(Sibling)**：
   - 相同细化级别的相邻块通信
   - 使用`MPI_IRECV/MPI_ISEND`
   - 标签格式：`(3^ndim+4^ndim)*(igrid-1)+(dir+1)*3^(idim-1)`

2. **精细→粗粒度通信(Restrict)**：
   - 从精细块向粗粒度块发送数据
   - 使用`type_recv_r`自定义数据类型
   - 包含限制(restriction)操作

3. **粗粒度→精细通信(Prolong)**：
   - 从粗粒度块向精细块发送数据
   - 使用`type_recv_p`自定义数据类型
   - 包含插值(prolongation)操作

### 3.2 数据交换实现
核心子程序`getbc`实现流程：
```fortran
1. 物理边界预处理(fill_boundary_before_gc)
2. 准备粗粒度数据(coarsen_grid + fill_coarse_boundary) 
3. 接收同级/精细邻居数据(bc_recv_srl/bc_recv_restrict)
4. 发送数据到同级/粗粒度邻居(bc_send_srl/bc_send_restrict)
5. 等待通信完成(MPI_WAITALL)
6. 处理接收到的数据(bc_fill_srl/bc_fill_restrict)
7. 接收粗粒度邻居数据(bc_recv_prolong)
8. 发送数据到精细邻居(bc_send_prolong)
9. 插值处理(gc_prolong)
10. 物理边界后处理(fill_boundary_after_gc)
```

关键数据结构：
- `recvbuffer_srl/sendbuffer_srl`: 同级通信缓冲区
- `recvbuffer_r/sendbuffer_r`: 限制通信缓冲区  
- `recvbuffer_p/sendbuffer_p`: 插值通信缓冲区
- `type_send_srl/type_recv_srl`: 同级通信数据类型
- `type_send_r/type_recv_r`: 限制通信数据类型
- `type_send_p/type_recv_p`: 插值通信数据类型

### 3.3 性能优化
1. **非阻塞通信**：
```fortran
call MPI_IRECV(..., recvrequest_srl(irecv_srl),...)
call MPI_ISEND(..., sendrequest_srl(isend_srl),...)
call MPI_WAITALL(...)  # 延迟等待
```

2. **缓冲区重用**：
```fortran
allocate(pwbuf(npwbuf)%w)  # 预分配多个发送缓冲区
```

3. **OpenMP并行**：
```fortran
!$OMP PARALLEL DO SCHEDULE(dynamic)
do iigrid=1,igridstail
  ! 边界处理代码
end do
!$OMP END PARALLEL DO
```

4. **交错网格优化**：
```fortran
if(stagger_grid) then
  call MPI_IRECV(recvbuffer_srl, sizes_srl_recv_total,...)
  ! 特殊处理面心变量
end if
```

## 4. 负载均衡系统
### 4.1 负载评估
基于空间填充曲线(Space Filling Curve)的负载分配：
1. **Morton排序**：
   - 通过`get_Morton_range`计算每个进程的Morton编号范围
   - 确保每个进程获得近似相等数量的网格块

2. **负载指标**：
   - 主要考虑网格块数量均衡
   - 支持交错网格的额外负载计算

### 4.2 网格迁移实现
在`load_balance`子程序中：

1. **数据迁移准备**：
```fortran
call get_Morton_range()  ! 获取新的Morton范围
allocate(recvrequest(max_blocks), sendrequest(max_blocks))  ! 分配通信请求
```

2. **非阻塞通信**：
```fortran
do ipe=0,npe-1
   if (recv_ipe/=send_ipe) then
      call MPI_IRECV(..., recvrequest(irecv),...)  ! 接收数据
      call MPI_ISEND(..., sendrequest(isend),...)  ! 发送数据
   end if
end do
```

3. **交错网格处理**：
```fortran
if(stagger_grid) then
   call MPI_IRECV(..., recvrequest_stg(irecv),...)  ! 接收面心变量
   call MPI_ISEND(..., sendrequest_stg(isend),...)  ! 发送面心变量
end if
```

4. **同步等待**：
```fortran
call MPI_WAITALL(irecv,recvrequest,recvstatus,ierrmpi)  ! 等待所有接收完成
call MPI_WAITALL(isend,sendrequest,sendstatus,ierrmpi)  ! 等待所有发送完成
```

### 4.3 动态平衡策略
1. **触发条件**：
   - 定期触发(如每N个时间步)
   - 当负载不均衡超过阈值时触发

2. **网格重分配**：
```fortran
call change_ipe_tree_leaf(recv_igrid,recv_ipe,send_igrid,send_ipe)  ! 更新网格归属
call amr_Morton_order()  ! 重新计算Morton排序
```

3. **性能优化**：
   - 最小化数据迁移量
   - 重叠通信和计算
   - 支持增量式负载均衡

关键数据结构：
- `sfc`: 空间填充曲线排序结果
- `Morton_start/Morton_stop`: 每个进程的Morton范围
- `type_block_io`: 网格数据通信类型
- `type_block_io_stg`: 交错网格通信类型

## 5. 主程序并行流程
### 5.1 时间步进循环
在`timeintegration`子程序中实现：

1. **主循环结构**：
```fortran
do while (global_time < time_max)
   call getbc(...)       ! 更新边界条件
   call advance(...)     ! 推进物理量
   call resettree(...)   ! 动态网格调整
   call load_balance(...) ! 负载均衡
   global_time = global_time + dt
end do
```

2. **关键控制参数**：
- `time_max`: 最大模拟时间
- `ditregrid`: 网格调整间隔
- `fixgrid()`: 是否固定网格标志

### 5.2 同步机制
1. **全局同步**：
```fortran
call MPI_ALLREDUCE(crash,crashall,1,MPI_LOGICAL,MPI_LOR,icomm,ierrmpi)
if (crashall) call MPI_ABORT(...)  ! 异常终止
```

2. **负载均衡同步**：
```fortran
call MPI_WAITALL(irecv,recvrequest,recvstatus,ierrmpi)  ! 等待网格迁移完成
```

3. **性能统计同步**：
```fortran
if (mype==0) then  ! 只在主进程输出统计信息
   write(*,'(a,f12.3,a)')' Time spent on ghost cells:',time_bc,' sec'
end if
```

### 5.3 性能分析
1. **计时机制**：
```fortran
time_bc=MPI_WTIME()-time_bcin  ! 边界条件耗时
timegr_tot=timegr_tot+(MPI_WTIME()-timegr0)  ! 网格调整耗时
```

2. **性能指标**：
- 每个进程每秒更新的网格单元数：
```fortran
dble(ncells_update)*dble(nstep)/dble(npe)/timeloop
```

3. **负载均衡评估**：
- 输出各阶段耗时占比
- 监控网格迁移频率
- 统计计算/通信时间比

关键数据结构：
- `time_bc`: 边界条件处理时间
- `timegr_tot`: 网格调整总时间
- `timeio_tot`: I/O总时间
- `ncells_update`: 更新的网格单元数
