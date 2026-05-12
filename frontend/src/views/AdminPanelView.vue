<template>
  <div style="background:white; padding: 20px; border-radius: 8px;">
    <h2 style="color: red;">⚙️ 后台管理中心 (Admin Only)</h2>
    
    <div style="display: flex; gap: 40px; margin-top: 20px;">
      <!-- 分类管理 -->
      <div style="flex: 1; border: 1px solid #eee; padding: 15px; border-radius: 8px;">
        <h3>📁 商品分类管理</h3>
        <ul style="margin-bottom: 15px;">
          <li v-for="cat in categories" :key="cat.id" style="margin-bottom: 5px;">
            {{ cat.id }} - {{ cat.name }}
            <button @click="deleteCategory(cat.id)" style="color:red; background:none; border:none; cursor:pointer;" title="删除">[删除]</button>
          </li>
        </ul>
        <input v-model="newCategory" placeholder="新增类别名..." style="padding: 6px; border:1px solid #ccc; width: 60%">
        <button @click="addCategory" class="btn bg-blue" style="margin-left:5px;">添加类别</button>
      </div>

      <!-- 全局物品管理 (下架权) -->
      <div style="flex: 2; border: 1px solid #eee; padding: 15px; border-radius: 8px;">
        <h3>🔨 全局物品状态强制管理</h3>
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="border-bottom: 2px solid #ddd;"><th>ID</th><th>标题</th><th>卖家</th><th>状态</th><th>强制操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id" style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px;">{{ item.id }}</td>
              <td>{{ item.title }}</td>
            <td>{{ item.owner_name }}</td>
            <td>
              <span v-if="item.status === 1" style="color: green;">售卖中</span>
              <span v-else-if="item.status === 2" style="color: blue;">已售出</span>
              <span v-else style="color: orange;">强制下架</span>
            </td>
            <td>
              <button v-if="item.status !== 3" @click="forceTakeDown(item.id)" class="btn bg-orange">违规强制下架</button>
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 增加：发布系统公告 -->
    <div style="margin-top: 30px; border: 1px solid #eee; padding: 15px; border-radius: 8px;">
      <h3>📢 发布系统公告 (全站可见)</h3>
      <div style="display: flex; flex-direction: column; gap: 10px; max-width: 600px;">
        <input v-model="announcement.title" placeholder="公告标题..." required style="padding:8px; border:1px solid #ccc; border-radius: 4px;" />
        <textarea v-model="announcement.content" placeholder="公告内容..." rows="4" required style="padding:8px; border:1px solid #ccc; border-radius: 4px;"></textarea>
        
        <div>
          <label>上传配图: </label>
          <input type="file" @change="uploadAnnounceImage" accept="image/*" />
        </div>
        <div v-if="announcement.images.length > 0" style="display: flex; gap:10px;">
          <img v-for="img in announcement.images" :src="img" :key="img" style="width: 80px; height: 80px; object-fit: cover;">
        </div>

        <button @click="publishAnnouncement" class="btn bg-blue" style="width: 120px;">确认发布公告</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const categories = ref([])
const items = ref([])
const newCategory = ref('')
const announcement = ref({ title: '', content: '', images: [] })
const token = localStorage.getItem('token')

const loadData = async () => {
    // 载入分类
    const resCat = await fetch('http://localhost:8000/api/categories')
    categories.value = await resCat.json()

    // 载入所有商品进行强制管理
    const resItem = await fetch('http://localhost:8000/api/admin/all-items')
    items.value = await resItem.json()
}

const addCategory = async () => {
    if(!newCategory.value) return 
    await fetch('http://localhost:8000/api/categories', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'token': token
        },
        body: JSON.stringify({ name: newCategory.value })
    })
    newCategory.value = ''
    loadData()
}

const deleteCategory = async (cat_id) => {
    if(!confirm("确定要删除这个分类吗？")) return;
    const res = await fetch(`http://localhost:8000/api/categories/${cat_id}`, {
        method: 'DELETE',
        headers: { 'token': token }
    })
    if(res.ok) {
        loadData()
    } else {
        alert("删除失败，可能该分类正在被使用或无权限")
    }
}

const uploadAnnounceImage = async (e) => {
    const file = e.target.files[0]
    if(!file) return
    const formData = new FormData()
    formData.append('file', file)
    
    // 复用已有的图片上传接口
    const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData
    })
    const data = await res.json()
    if(data.url) announcement.value.images.push(data.url)
}

const publishAnnouncement = async () => {
    if(!announcement.value.title || !announcement.value.content) return alert("标题和内容必填")
    
    const res = await fetch('http://localhost:8000/api/announcements', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'token': token 
        },
        body: JSON.stringify({
            title: announcement.value.title,
            content: announcement.value.content,
            images: JSON.stringify(announcement.value.images)
        })
    })
    
    if(res.ok) {
        alert("公告发布成功！")
        announcement.value = { title: '', content: '', images: [] }
    } else {
        alert("发布失败！")
    }
}

const forceTakeDown = async (item_id) => {
    if(!confirm("强制下架不会赔偿卖家，是否确认？")) return;
    // 使用原先就写好的批量状态修改接口，但仅勾选1个
    await fetch('http://localhost:8000/api/items/batch-status', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_ids: [item_id], status: 3 })
    })
    loadData()
}

onMounted(loadData)
</script>

<style scoped>
.btn { border: none; padding: 6px 12px; cursor: pointer; border-radius: 4px; color: white; }
.bg-blue { background: #2196F3; }
.bg-orange { background: #FF9800; }
</style>