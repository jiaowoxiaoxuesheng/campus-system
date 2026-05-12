<template>
  <div style="max-width: 400px; margin: 50px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
    <h2 style="text-align: center; color: #4CAF50;">身份认证</h2>
    
    <form @submit.prevent="handleAuth">
      <div style="margin-bottom: 20px;">
        <label>用户名：</label>
        <input v-model="form.username" required placeholder="请输入用户名" style="width: 100%; padding: 8px; margin-top:5px; box-sizing: border-box; border:1px solid #ccc; border-radius:4px;">
      </div>
      
      <div style="margin-bottom: 20px;">
        <label>密码：</label>
        <input type="password" v-model="form.password" required placeholder="请输入密码" style="width: 100%; padding: 8px; margin-top:5px; box-sizing: border-box; border:1px solid #ccc; border-radius:4px;">
      </div>

      <div style="display: flex; gap: 15px;">
        <button type="submit" @click="isLogin = true" style="flex: 1; background: #4CAF50; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer;">登 录</button>
        <button type="button" @click="register" style="flex: 1; background: #2196F3; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer;">注 册</button>
      </div>
    </form>
    
    <p style="text-align: center; font-size: 12px; color: gray; margin-top: 20px;">注: 首个注册的用户将自动成为最高权限的 Admin</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({ username: '', password: '' })
const isLogin = ref(true)

const handleAuth = async () => {
    if(!isLogin.value) return; // 点击了注册按钮就不走登录逻辑
    
    // 登录请求
    try {
        const res = await fetch('http://localhost:8000/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form.value)
        })
        const data = await res.json()
        if(!res.ok) return alert(data.detail)
        
        // 保存权限与凭证，供 App.vue 使用
        localStorage.setItem('token', data.token)
        localStorage.setItem('user_id', data.user_id)
        localStorage.setItem('username', data.username)
        localStorage.setItem('role', data.role)
        
        alert(data.message)
        location.href = '/' // 快速刷新并跳到首页
    } catch(e) { alert("网络错误或者后端服务未启动") }
}

const register = async () => {
    isLogin.value = false;
    if(!form.value.username || !form.value.password) return alert("请先填写账密");
    
    try {
        const res = await fetch('http://localhost:8000/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(form.value)
        })
        const data = await res.json()
        if(!res.ok) return alert(data.detail)
        alert(data.message + "，现在可以点击登录按钮了！")
    } catch(e) { alert("网络错误或者后端服务未启动") }
}
</script>
