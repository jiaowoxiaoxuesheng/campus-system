<template>
  <div style="background:white; padding: 20px; border-radius: 8px;">
    <h2>我的收藏</h2>
    <div class="item-grid" v-if="items.length">
      <div class="card" v-for="item in items" :key="item.id" @click="$router.push('/item/' + item.id)">
        <h3>{{ item.title }}</h3>
        <p style="color:red; font-weight:bold;">￥{{ item.price }}</p>
        <p style="font-size:12px; color: #888;">卖家发布时间: {{ item.created_at }}</p>
      </div>
    </div>
    <div v-else style="margin-top: 20px; color: gray;">暂无收藏任何物品</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const items = ref([])
const userId = localStorage.getItem('user_id')

onMounted(async () => {
    if(!userId) return
    const res = await fetch(`http://localhost:8000/api/users/${userId}/favorites`)
    items.value = await res.json()
})
</script>

<style scoped>
.item-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
.card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); cursor: pointer; transition: 0.3s; border: 1px solid #eee; }
.card:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
</style>