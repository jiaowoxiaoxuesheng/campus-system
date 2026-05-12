<template>
  <div style="background:white; padding: 20px; border-radius: 8px;">
    <h2>我的发布与商品管理</h2>
    <div style="margin-bottom: 15px; display: flex; gap: 10px;">
      <button @click="batchUpdateStatus(1)" class="btn bg-green">批量上架</button>
      <button @click="batchUpdateStatus(2)" class="btn bg-blue">批量标记已售出</button>
      <button @click="batchUpdateStatus(3)" class="btn bg-orange">批量下架</button>
    </div>
    
    <table style="width: 100%; border-collapse: collapse; text-align: left;">
      <thead>
        <tr style="border-bottom: 2px solid #ddd;">
          <th style="padding: 10px;"><input type="checkbox" @change="toggleAll" :checked="selected.length === items.length && items.length > 0"/> 全选</th>
          <th>商品图片</th>
          <th>标题</th>
          <th>价格</th>
          <th>状态</th>
          <th>浏览量</th>
          <th>发布时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.id" style="border-bottom: 1px solid #eee;">
          <td style="padding: 10px;"><input type="checkbox" :value="item.id" v-model="selected" /></td>
          <td>
            <img :src="getCover(item.images)" alt="cover" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;" v-if="getCover(item.images)">
            <span v-else>无图</span>
          </td>
          <td>{{ item.title }}</td>
          <td style="color: red; font-weight: bold;">￥{{ item.price }}</td>
          <td>
            <span v-if="item.status === 1" style="color: #4CAF50;">售卖中</span>
            <span v-else-if="item.status === 2" style="color: #2196F3;">已售出</span>
            <span v-else style="color: #FF9800;">已下架</span>
          </td>
          <td>{{ item.views }}</td>
          <td>{{ item.created_at.split(' ')[0] }}</td>
          <td>
            <button @click="deleteItem(item.id)" class="btn bg-red">删除</button>
          </td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="8" style="text-align: center; padding: 20px; color: gray;">暂无发布的商品</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const items = ref([])
const selected = ref([])
const userId = localStorage.getItem('user_id')

const load = async () => {
    try {
        const res = await fetch(`http://localhost:8000/api/users/${userId}/items`)
        items.value = await res.json()
        selected.value = []
    } catch (e) {
        console.error(e)
    }
}

const getCover = (imagesJson) => {
    try {
        const arr = JSON.parse(imagesJson)
        return arr.length > 0 ? arr[0] : null
    } catch { return null }
}

const deleteItem = async (id) => {
    if(!confirm('确定永久删除该物品吗？')) return
    await fetch(`http://localhost:8000/api/items/${id}`, { method: 'DELETE' })
    load()
}

const batchUpdateStatus = async (status) => {
    if(!selected.value.length) return alert('请先勾选需要操作的物品')
    const res = await fetch('http://localhost:8000/api/items/batch-status', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_ids: selected.value, status })
    })
    const data = await res.json()
    alert(data.message || '批量修改成功')
    load()
}

const toggleAll = (e) => {
    selected.value = e.target.checked ? items.value.map(i => i.id) : []
}

onMounted(load)
</script>

<style scoped>
.btn { border: none; padding: 6px 12px; cursor: pointer; border-radius: 4px; color: white; }
.bg-green { background: #4CAF50; }
.bg-blue { background: #2196F3; }
.bg-orange { background: #FF9800; }
.bg-red { background: #f44336; }
.btn:hover { opacity: 0.9; }
</style>