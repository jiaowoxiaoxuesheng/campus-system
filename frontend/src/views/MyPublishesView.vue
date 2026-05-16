<template>
  <div class="publish-container">
    <h2 style="margin-bottom:20px; color:var(--text-main);">我的发布与商品管理</h2>
    <div style="margin-bottom: 20px; display: flex; gap: 15px;">
      <button @click="batchUpdateStatus(1)" class="btn bg-green">批量上架</button>
      <button @click="batchUpdateStatus(2)" class="btn bg-blue">批量标记已售出</button>
      <button @click="batchUpdateStatus(3)" class="btn bg-orange">批量下架</button>
    </div>
    
    <table class="publish-table">
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
        <tr v-for="item in items" :key="item.id">
          <td style="padding: 10px; width: 60px;"><input v-if="item.status === 1" type="checkbox" :value="item.id" v-model="selected" style="transform: scale(1.2);"/></td>
          <td>
            <img :src="getCover(item.images)" alt="cover" @click="previewImage = getCover(item.images)" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px; box-shadow: var(--shadow-sm); cursor: zoom-in;" v-if="getCover(item.images)">
            <span v-else style="color:var(--text-muted); font-size:0.85em; background:var(--bg-color); padding: 4px 8px; border-radius: 4px;">无图</span>
          </td>
          <td style="font-weight: 500;">{{ item.title }}</td>
          <td style="color: var(--danger-color); font-weight: bold; font-size: 1.1em;">￥{{ item.price }}</td>
          <td>
            <span class="status-tag" :class="item.status === 1 ? 'status-green' : (item.status === 2 ? 'status-blue' : 'status-orange')">
              {{ item.status === 1 ? '售卖中' : (item.status === 2 ? '已售出' : '已下架') }}
            </span>
          </td>
          <td style="color:var(--text-muted)">👁 {{ item.views }}</td>
          <td style="color:var(--text-muted)">{{ item.created_at.split(' ')[0] }}</td>
          <td>
            <button v-if="item.status === 1" @click="openEditModal(item)" class="btn bg-blue btn-action">修改</button>
            <button v-if="item.status === 1 || item.status === 2" @click="deleteItem(item.id)" class="btn bg-red btn-action">删除</button>
          </td>
        </tr>
        <tr v-if="items.length === 0">
          <td colspan="8" style="text-align: center; padding: 20px; color: gray;">暂无发布的商品</td>
        </tr>
      </tbody>
    </table>

    <!-- 编辑模态框 -->
    <div v-if="editingItem" class="modal-overlay">
      <div class="modal-content">
        <h3>修改商品信息</h3>
        <div style="margin-bottom: 10px;">
          <label>类别：</label>
          <select v-model="editForm.category_id" style="width: 100%; padding: 8px; margin-top: 5px;">
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
        </div>
        <div style="margin-bottom: 10px;">
          <label>价格：</label>
          <input type="number" v-model="editForm.price" style="width: 100%; padding: 8px; margin-top: 5px;">
        </div>
        <div style="margin-bottom: 20px;">
          <label>描述：</label>
          <textarea v-model="editForm.description" rows="4" style="width: 100%; padding: 8px; margin-top: 5px;"></textarea>
        </div>
        <div style="text-align: right;">
          <button @click="editingItem = null" class="btn bg-orange" style="margin-right: 10px;">取消</button>
          <button @click="saveEdit" class="btn bg-green">保存保存</button>
        </div>
      </div>
    </div>
  </div>

  <!-- 图片预览模态框 -->
  <div v-if="previewImage" class="preview-modal" @click="previewImage = null">
      <img :src="previewImage" @click.stop />
      <button class="close-preview" @click="previewImage = null">×</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const items = ref([])
const selected = ref([])
const categories = ref([])
const editingItem = ref(null)
const editForm = ref({
    title: '',
    description: '',
    price: 0,
    category_id: null,
    user_id: 0,
    images: '[]'
})
const userId = localStorage.getItem('user_id')
const previewImage = ref(null)

const load = async () => {
    try {
        const res = await fetch(`http://localhost:8000/api/users/${userId}/items`)
        items.value = await res.json()
        selected.value = []
        
        const resCat = await fetch('http://localhost:8000/api/categories')
        categories.value = await resCat.json()
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

const openEditModal = (item) => {
    editingItem.value = item.id
    editForm.value = {
        title: item.title,
        description: item.description,
        price: parseFloat(item.price),
        category_id: item.category_id,
        user_id: parseInt(userId),
        images: item.images || '[]'
    }
}

const saveEdit = async () => {
    try {
        const res = await fetch(`http://localhost:8000/api/items/${editingItem.value}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(editForm.value)
        })
        if (res.ok) {
            alert('修改成功')
            editingItem.value = null
            load()
        } else {
            const data = await res.json()
            alert('修改失败: ' + (data.detail || '未知原因'))
        }
    } catch (e) {
        console.error(e)
        alert('网络错误')
    }
}

onMounted(load)
</script>

<style scoped>
.publish-container {
  background: transparent;
  padding: 0;
}
.btn-action {
  padding: 6px 12px;
  font-size: 0.9em;
  margin-right: 8px;
}
.status-tag {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.85em;
  font-weight: bold;
}
.status-green { background: rgba(76, 175, 80, 0.1); color: var(--primary-color); }
.status-blue { background: rgba(33, 150, 243, 0.1); color: var(--secondary-color); }
.status-orange { background: rgba(255, 152, 0, 0.1); color: var(--warning-color); }

.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}
.modal-content {
  background: var(--card-bg);
  padding: 30px;
  border-radius: 12px;
  width: 450px;
  box-shadow: var(--shadow-md);
}
.modal-content h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: var(--text-main);
  border-bottom: 2px solid var(--bg-color);
  padding-bottom: 10px;
}
.preview-modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 9999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(5px); }
.preview-modal img { max-width: 90%; max-height: 90vh; object-fit: contain; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.close-preview { position: absolute; top: 20px; right: 30px; background: #fff; color: #333; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 24px; cursor: pointer; font-weight: bold; line-height: 40px; text-align: center; }
</style>
