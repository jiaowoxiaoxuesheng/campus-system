<template>
  <div>
    <header class="nav">
      <div class="logo">校园二手交易</div>
      <nav class="nav-links">
        <router-link to="/">首页广场</router-link>
        <router-link to="/announcements">系统公告</router-link>

        <!-- 根据登录状态显示不同导航 -->
        <template v-if="auth.token">
          <router-link v-if="auth.role === 'user'" to="/publish">发布闲置</router-link>
          <router-link v-if="auth.role === 'user'" to="/my-publishes">我的发布</router-link>
          <router-link v-if="auth.role === 'user'" to="/my-favorites">我的收藏</router-link>
          
          <!-- 管理员可见菜单 -->
          <router-link v-if="auth.role === 'admin'" to="/admin-panel" style="color: red;">管理中心</router-link>
          
          <span style="margin-left: 20px;">
            欢迎你，{{ auth.username }}
            <span v-if="auth.role === 'user'" style="color: #FF9800; font-weight:bold;"> (余额: ￥{{ auth.balance }})</span>
            <a href="#" @click.prevent="logout" style="color: gray; margin-left: 10px; font-size: 0.9em;">[登出]</a>
          </span>
        </template>

        <template v-else>
          <router-link to="/login">登录/注册</router-link>
        </template>
      </nav>
    </header>
    <main style="padding: 20px;">
      <router-view></router-view>
    </main>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const auth = reactive({
  token: '',
  username: '',
  role: '',
  balance: 0
})

onMounted(async () => {
  auth.token = localStorage.getItem('token') || ''
  const userId = localStorage.getItem('user_id')
  
  // 每次刷新请求最新余额与身份
  if(auth.token && userId) {
      try {
          const res = await fetch(`http://localhost:8000/api/me/${userId}`)
          if(res.ok) {
              const data = await res.json()
              auth.username = data.username
              auth.role = data.role
              auth.balance = data.balance
          }
      } catch(e) {}
  }
})

const logout = () => {
  localStorage.clear()
  auth.token = ''
  auth.username = ''
  auth.role = ''
  router.push('/login')
  // 为了确保响应式立刻更新，这里加个强制刷新最稳妥且适合新手逻辑
  setTimeout(() => location.reload(), 100)
}
</script>

<style>
body { font-family: Arial, sans-serif; margin: 0; background: #f5f7fa; }
.nav { display: flex; justify-content: space-between; align-items: center; padding: 15px 5%; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.nav-links a { margin-left: 15px; text-decoration: none; color: #333; font-weight: bold; }
.nav-links a.router-link-active { color: #4CAF50; }
.logo { font-weight: 900; color: #4CAF50; font-size: 1.2rem; }
</style>