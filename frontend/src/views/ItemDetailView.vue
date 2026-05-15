<template>
  <div v-if="item" style="background:white; padding: 20px; border-radius: 8px; max-width: 800px; margin: 0 auto;">
    <button @click="$router.back()" style="background: #eee; border: none; padding: 5px 15px; cursor: pointer; border-radius: 4px; margin-bottom: 20px;">← 返回</button>
    
    <h2>{{ item.title }}</h2>
    <p style="color:red; font-size: 1.5em; font-weight:bold;">￥{{ item.price }}</p>
    <div style="color: #666; font-size: 0.9em; margin-bottom: 20px; display: flex; gap: 15px;">
        <span>� 发布者: {{ item.owner_name }}</span>
        <span>👀 浏览量: {{ item.views }}</span>
        <span>🕒 发布时间: {{ item.created_at.split('T')[0] }}</span>
        <span>🏷️ 分类: {{ item.category_name }}</span>
    </div>

    <!-- 图集展示 -->
    <div v-if="images.length > 0" style="display: flex; gap: 10px; overflow-x: auto; margin-bottom: 20px;">
        <img v-for="(img, idx) in images" :key="idx" :src="img" style="width: 200px; height: 200px; object-fit: cover; border-radius: 8px; border: 1px solid #eee;" />
    </div>

    <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; min-height: 100px; margin-bottom: 20px;">
        <h4>物品描述：</h4>
        <p style="white-space: pre-wrap;">{{ item.description }}</p>
    </div>
    
    <div style="display: flex; gap: 15px;">
        <button v-if="item.status === 1 && item.user_id != userId && userRole !== 'admin'" @click="buyItem" style="background: #E91E63; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 1.1em; font-weight: bold;">
            💳 立即购买
        </button>

        <button @click="toggleFavorite" :style="{ background: isFavorite ? '#FF9800' : '#4CAF50', color: 'white', border: 'none', padding: '10px 20px', borderRadius: '4px', cursor: 'pointer', fontSize: '1.1em' }">
            {{ isFavorite ? '★ 取消收藏' : '☆ 加入收藏' }}
        </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const item = ref(null)
const images = ref([])
const isFavorite = ref(false)
const userId = localStorage.getItem('user_id')
const userRole = localStorage.getItem('role')

onMounted(async () => {
    // 加载详情与增加浏览量，传递 token 以防自己/管理员访问增加浏览量
    const token = localStorage.getItem('token') || ''
    const res = await fetch(`http://localhost:8000/api/items/${route.params.id}`, {
        headers: token ? { 'Authorization': token } : {}
    })
    if (!res.ok) {
        alert('加载商品详情失败: ' + res.status)
        return
    }
    const data = await res.json()
    item.value = data
    images.value = JSON.parse(data.images || '[]')
    
    // 检查是否已收藏
    if(userId) {
        try {
            const favRes = await fetch(`http://localhost:8000/api/users/${userId}/favorites`)
            if (favRes.ok) {
                const favs = await favRes.json()
                isFavorite.value = favs.some(f => f.id === data.id)
            }
        } catch(e) {
            console.error('获取收藏列表失败', e)
        }
    }
})

const buyItem = async () => {
    if(!userId) return alert('请先登录！')
    if(!confirm(`您确定要花费 ￥${item.value.price} 购买该商品吗？`)) return;

    try {
        const token = localStorage.getItem('token') || ''
        const res = await fetch(`http://localhost:8000/api/items/${item.value.id}/buy`, {
            method: 'POST',
            headers: token ? { 'Authorization': token } : {}
        })
        const data = await res.json()
        if(res.ok) {
            alert(data.message + "，这笔钱已经打入了卖家的余额！")
            location.reload() // 刷新以更新余额和商品状态
        } else {
            alert("购买失败：" + data.detail)
        }
    } catch(e) { alert("网络异常") }
}

const toggleFavorite = async () => {
    if(!userId) return alert('请先登录！')
    const res = await fetch(`http://localhost:8000/api/favorites?user_id=${userId}&item_id=${item.value.id}`, { method: 'POST' })
    const data = await res.json()
    alert(data.message)
    isFavorite.value = !isFavorite.value
}
</script>
