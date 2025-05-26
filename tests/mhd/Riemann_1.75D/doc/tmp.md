# MPI-AMRVAC时间推进中的并行通信设计

## 1. 整体架构
程序采用MPI进行分布式内存并行，主要通信发生在：
- 时间积分循环(`amrvac.f`中的`timeintegration`)
- 边界条件处理(`mod_ghostcells_update.f`) 
- 负载均衡(`mod_load_balance.f`)

### 1.1 MPI初始化实现
在`comm_lib.f`中完成MPI环境初始化：
```fortran
subroutine comm_start
  use mod_global_parameters
  call MPI_INIT(ierrmpi)  ! 初始化MPI环境
  call MPI_COMM_RANK(MPI_COMM_WORLD,mype,ierrmpi)  ! 获取进程rank
  call MPI_COMM_SIZE(MPI_COMM_WORLD,npe,ierrmpi)    ! 获取总进程数
  
  ! 验证数据类型大小匹配
  call MPI_TYPE_GET_EXTENT(MPI_DOUBLE_PRECISION,lb,sizes,ierrmpi)
  if (sizes /= size_double) call mpistop("Incompatible double size")
end subroutine comm_start
```

关键数据结构：
- `mype`: 当前进程rank(0~npe-1)
- `npe`: 总进程数
- `icomm`: 通信子(默认MPI_COMM_WORLD)

## 2. 时间推进中的关键通信步骤

### 2.0 通信数据类型创建
在`mod_ghostcells_update.f`中创建自定义MPI数据类型：
```fortran
subroutine get_bc_comm_type(comm_type,ixmin1,ixmax1,ixGmin1,ixGmax1,nwstart,nwbc)
  integer, intent(inout) :: comm_type
  integer, dimension(ndim+1) :: fullsize, subsize, start
  
  fullsize(1)=ixGmax1; fullsize(ndim+1)=nw  ! 全局网格大小
  subsize(1)=ixmax1-ixmin1+1;               ! 子区域大小
  subsize(ndim+1)=nwbc                       ! 变量数
  
  call MPI_TYPE_CREATE_SUBARRAY(ndim+1,fullsize,subsize,start,&
       MPI_ORDER_FORTRAN,MPI_DOUBLE_PRECISION,comm_type,ierrmpi)
  call MPI_TYPE_COMMIT(comm_type,ierrmpi)
end subroutine
```
关键点：
- 为每个通信方向创建特定数据类型
- 支持任意维度和变量数的子区域通信
- 使用`MPI_TYPE_COMMIT`提交数据类型

### 2.1 主循环通信实现
在`amrvac.f`的`timeintegration`中：

1. **全局状态检查**：
```fortran
call MPI_ALLREDUCE(crash,crashall,1,MPI_LOGICAL,MPI_LOR,icomm,ierrmpi)
if (crashall) then
  call saveamrfile(1)  ! 保存崩溃前状态
  call MPI_ABORT(icomm, iigrid, ierrmpi)
end if
```

2. **负载均衡触发**：
```fortran
if (refine_max_level>1 .and. .not.(fixgrid())) then
  call resettree  ! 重建网格树
  call load_balance  ! 重新分配网格
end if
```

3. **性能统计**：
```fortran
if (mype==0) then
  write(*,'(a,f12.3,a)')' Time spent on ghost cells:',time_bc,' sec'
  write(*,'(a,es12.3)')' Cells updated/proc/sec:',&
     dble(ncells_update)/dble(npe)/timeloop
end if
```
在`timeintegration`子程序中：
1. **全局同步**：使用`MPI_ALLREDUCE`检查崩溃状态
2. **负载均衡**：定期调用`load_balance`重新分配网格
3. **计时统计**：使用`MPI_WTIME`测量各阶段耗时

### 2.2 边界条件处理实现
在`mod_ghostcells_update.f`的`getbc`中：

1. **通信缓冲区管理**：
```fortran
! 分配发送/接收缓冲区
allocate(recvbuffer_srl(max_bufsize), sendbuffer_srl(max_bufsize))

! 非阻塞通信初始化
irecv_srl=0; isend_srl=0
do iigrid=1,igridstail
  if (neighbor_type==neighbor_sibling) then
    call MPI_IRECV(..., recvrequest_srl(irecv_srl),...)
    call MPI_ISEND(..., sendrequest_srl(isend_srl),...)
  end if
end do
```

2. **数据打包示例**：
```fortran
! 将面心变量打包到缓冲区
do idir=1,ndim
  shapes = [sizes_srl_send_stg(idir,i1)]
  sendbuffer_srl(ibuf:ibuf+shapes(1)-1) = &
     reshape(psb(igrid)%ws(ixSmin1:ixSmax1,idir), shapes)
  ibuf = ibuf + shapes(1)
end do
```

3. **通信等待与解包**：
```fortran
call MPI_WAITALL(nrecv_bc_srl, recvrequest_srl, recvstatus_srl, ierrmpi)

! 从缓冲区解包数据
ibuf = 1
do idir=1,ndim
  shapes = [sizes_srl_recv_stg(idir,i1)] 
  psb(igrid)%ws(ixRmin1:ixRmax1,idir) = &
     reshape(recvbuffer_srl(ibuf:ibuf+shapes(1)-1), [ixRmax1-ixRmin1+1])
  ibuf = ibuf + shapes(1)
end do
```
在`getbc`子程序中实现多级通信：
1. **同级网格通信**：
   - 使用`MPI_IRECV/MPI_ISEND`交换边界数据
   - 处理物理边界条件

2. **精细→粗粒度通信**：
   - 限制操作后发送粗粒度数据
   - 使用自定义MPI数据类型`type_recv_r`

3. **粗粒度→精细通信**：
   - 插值操作前接收粗粒度数据
   - 使用自定义MPI数据类型`type_recv_p`

### 3. 关键模块与功能

| 模块 | 主要功能 | 关键通信操作 |
|------|---------|-------------|
| `amrvac.f` | 主程序时间循环 | MPI_ALLREDUCE, MPI_BCAST |
| `mod_ghostcells_update.f` | 边界处理 | MPI_IRECV, MPI_ISEND |
| `mod_load_balance.f` | 负载均衡 | MPI非阻塞通信 |

## 4. 通信优化设计
1. **非阻塞通信**：重叠计算和通信
2. **自定义数据类型**：优化网格数据传输
3. **多级通信**：支持AMR多级网格
4. **交错网格支持**：特殊处理面心变量

## 5. 典型调用流程
1. 时间步开始时调用`getbc`更新边界
2. 计算物理量更新
3. 检查是否需要负载均衡
4. 重复直到完成时间积分
