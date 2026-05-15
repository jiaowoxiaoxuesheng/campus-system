<template>
  <div style="background:white; padding: 20px; border-radius: 8px; max-width: 900px; margin: 0 auto;">
    <h2>🛍️ 我的购买</h2>
    
    <div v-if="purchases.length === 0" style="text-align: center; color: #999; padding: 40px;">
      暂无购买记录
    </div>
    
    <table v-else style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr style="background: #f5f5f5; border-bottom: 2px solid #ddd;">
          <th style="padding: 12px; text-align: left;">商品名称</th>
          <th style="padding: 12px; text-align: left;">卖家</th>
          <th style="padding: 12px; text-align: center;">价格</th>
          <th style="padding: 12px; text-align: center;">购买时间</th>
          <th style="padding: 12px; text-align: center;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="purchase in purchases" :key="purchase.id" style="border-bottom: 1px solid #eee;">
          <td style="padding: 12px;">
            <router-link :to="`/item/${purchase.item_id}`" style="color: #2196F3; text-decoration: none; cursor: pointer;">
              {{ purchase.item_title }}
            </router-link>
          </td>
          <td style="padding: 12px;">{{ purchase.seller_name }}</td>
          <td style="padding: 12px; text-align: center; color: red; font-weight: bold;">¥{{ purchase.price }}</td>
          <td style="padding: 12px; text-align: center; font-size: 0.9em;">{{ formatDate(purchase.created_at) }}</td>
          <td style="padding: 12px; text-align: center;">
            <button @click="contactSeller(purchase.seller_name)" style="background: #4CAF50; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">
              💬 联系卖家
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const purchases = ref([])
const userId = localStorage.getItem('user_id')

const formatDate = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN')
}

onMounted(async () => {
  if (!userId) {
    alert('请先登录！')
    return
  }
  
  try {
    const res = await fetch(`http://localhost:8000/api/users/${userId}/purchases`)
    if (res.ok) {
      purchases.value = await res.json()
    } else {
      alert('加载购买记录失败')
    }
  } catch (e) {
    alert('网络错误: ' + e.message)
  }
})

const contactSeller = (sellerName) => {
  alert(`请通过平台站内信联系 "${sellerName}" 卖家`)
}
</script>

<style scoped>
table {
  width: 100%;
}

th, td {
  padding: 12px;
}

tbody tr:hover {
  background: #f9f9f9;
}
</style>
