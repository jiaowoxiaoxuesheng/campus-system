<template>
  <div style="background:white; padding: 20px; max-width: 500px; margin: 0 auto; border-radius: 8px;">
    <h2>发布闲置</h2>
    <form @submit.prevent="submit">
      <div style="margin-bottom:15px;"><label>物品名称: </label>
        <input v-model="form.title" required style="width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;">
      </div>
      <div style="margin-bottom:15px;"><label>描述 (支持多行): </label>
        <textarea v-model="form.description" style="width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;"></textarea>
      </div>
      <div style="margin-bottom:15px;"><label>价格 (￥): </label>
        <input type="number" step="0.01" min="0" v-model="form.price" required style="width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;">
      </div>
      
      <!-- 加分项：多图上传面板 -->
      <div style="margin-bottom:20px;">
        <label>商品分类: </label>
        <select v-model="form.category_id" required style="width: 100%; padding: 8px; margin-top: 5px; margin-bottom: 15px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px;">
           <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
        </select>
        
        <label>商品展示图片 (多图): </label>
        <input type="file" @change="uploadImage" accept="image/*" style="width: 100%; margin-top: 5px;">
        <div v-if="images.length > 0" style="margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap;">
          <div v-for="(img, index) in images" :key="index" style="position: relative; display: inline-block;">
            <img :src="img" style="width: 80px; height: 80px; object-fit: cover; border-radius: 4px; border: 1px solid #eee;">
            <button type="button" @click="removeImage(index)" style="position: absolute; top: -5px; right: -5px; background: red; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; font-size: 12px; line-height: 1; display:flex; align-items:center; justify-content:center; padding:0;">×</button>
          </div>
        </div>
      </div>
      
      <button type="submit" style="background:#4CAF50; color:white; padding:10px; width: 100%; border: none; border-radius: 4px; cursor: pointer; font-size: 1.1em;">确认发布</button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const form = ref({ title: '', description: '', price: '', category_id: 1 })
const images = ref([]) 
const categories = ref([])
const router = useRouter()

onMounted(async () => {
    // 动态获取管理员创建的所有最新分类
    const res = await fetch('http://localhost:8000/api/categories')
    categories.value = await res.json()
    if(categories.value.length > 0) form.value.category_id = categories.value[0].id
})

const uploadImage = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    
    // 修复：获取到文件后立刻重置 input 组件的 value
    // 原理：因为我们的系统支持多图且有自己渲染的缩略图模块，如果不清空，
    // 原生 input 就还会认为该文件处于选中状态，导致删图后文件名还能被看见，并且阻碍后续长传相同的图。
    e.target.value = ''
    
    try {
        const res = await fetch('http://localhost:8000/api/upload', {
            method: 'POST',
            body: formData
        })
        const data = await res.json()
        if(res.ok) {
            images.value.push(data.url)
        } else {
            alert('图片上传失败')
        }
    } catch (err) {
        alert('接口请求失败')
    }
}

const removeImage = (index) => {
    images.value.splice(index, 1)
}

const submit = async () => {
    const userId = localStorage.getItem('user_id')
    if(!userId) return alert("请先登录！")

    // 前端表单校验 (防止用户填入非法数据)
    if(form.value.title.trim() === '') return alert("物品名称不能为空或者全是空格！")
    if(parseFloat(form.value.price) < 0) return alert("价格不能为负数！")

    // 组合最终上传给后端的 JSON 报文
    const payload = {
        title: form.value.title.trim(),
        description: form.value.description || '暂无描述',
        price: parseFloat(form.value.price),
        category_id: form.value.category_id,
        user_id: parseInt(userId),
        images: JSON.stringify(images.value)
    }

    try {
        const res = await fetch('http://localhost:8000/api/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        
        if(res.ok) {
            alert('闲置物品发布成功！')
            router.push('/my-publishes')
        } else {
            const data = await res.json()
            alert('发布失败：' + (data.detail || '未知原因'))
        }
    } catch (e) {
        alert('发布异常：后端服务未启动或连接崩溃')
    }
}
</script>