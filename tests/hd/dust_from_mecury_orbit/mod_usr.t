! 彗星轨道计算（简化椭圆轨道）
subroutine get_comet_position(time, x_comet)
  double precision, intent(in) :: time
  double precision, intent(out) :: x_comet(2)
  double precision :: a = 0.387*AU, period = 88d0*day, theta
  
  theta = 2*pi*mod(time,period)/period
  x_comet = a*[cos(theta), sin(theta)]
end subroutine

! 辐射压修正引力
subroutine special_gravity(ixI^L, ixO^L, wCT, x, gravity)
  integer :: ispecies = get_current_species()
  double precision :: beta(3) = [0.5d0, 0.05d0, 0.005d0]  ! 预设β值
  
  gravity(ixO^S,:) = -(1.0d0 - beta(ispecies)) * GM_sun * x(ixO^S,:)/norm2(x)**3
end subroutine

! 尘埃释放源项
subroutine dust_source(qdt, ixI^L, ixO^L, wCT, w, x, qs)
  double precision :: x_comet(2), sigma=1e8  ! 源半径100km
  call get_comet_position(global_time, x_comet)
  
  do i=ixO^LIM1
    do j=ixO^LIM2
      r = norm2(x(i,j,:)-x_comet)
      w(i,j,rho_1) = w(i,j,rho_1) + Q0*exp(-(r/sigma)**2)*dt/(sqrt(pi)*sigma) * 0.6  ! 小粒径
      w(i,j,rho_2) = w(i,j,rho_2) + Q0*exp(-(r/sigma)**2)*dt/(sqrt(pi)*sigma) * 0.3  
      w(i,j,rho_3) = w(i,j,rho_3) + Q0*exp(-(r/sigma)**2)*dt/(sqrt(pi)*sigma) * 0.1  ! 大粒径
    enddo
  enddo
end subroutine