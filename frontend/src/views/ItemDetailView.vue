<template>
  <div v-if="item" style="background:white; padding: 20px; border-radius: 8px; max-width: 800px; margin: 0 auto; box-shadow: var(--shadow-sm);">
    <button @click="$router.back()" style="background: #e2e8f0; color: #333; border: none; padding: 8px 18px; cursor: pointer; border-radius: 6px; margin-bottom: 20px; font-weight: bold; transition: var(--transition);">← 返回</button>
    
    <h2>{{ item.title }}</h2>
    <p style="color:red; font-size: 1.5em; font-weight:bold;">￥{{ item.price }}</p>
    <div style="color: #666; font-size: 0.9em; margin-bottom: 20px; display: flex; gap: 15px;">
        <span>👤 发布者: {{ item.owner_name }}</span>
        <span>👀 浏览量: {{ item.views }}</span>
        <span>🕒 发布时间: {{ item.created_at.split('T')[0] }}</span>
        <span>🏷️ 分类: {{ item.category_name }}</span>
    </div>

    <!-- 图集展示 -->
    <div v-if="images.length > 0" style="display: flex; gap: 10px; overflow-x: auto; margin-bottom: 20px;">
        <img v-for="(img, idx) in images" :key="idx" :src="img" @click="previewImage = img" style="width: 200px; height: 200px; object-fit: cover; border-radius: 8px; border: 1px solid #eee; cursor: zoom-in;" />
    </div>

    <div v-if="cmpInfo" style="margin-bottom: 20px; background: #e0f2fe; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
        <h4 style="margin: 0 0 10px 0; color: #1e40af;">📊 校园行情大盘</h4>
        <div style="font-size: 0.9em; color: #1e3a8a; line-height: 1.6;">
            <div>当前商品分类：<strong>{{ item.category_name }}</strong></div>
            <div>该分类全站最低价：<strong style="color: #059669;">￥{{ cmpInfo.min_price }}</strong></div>
            <div>同类商品平均价：<strong style="color: #ea580c;">￥{{ cmpInfo.avg_price }}</strong></div>
            <div v-if="item.price < cmpInfo.avg_price" style="margin-top: 10px; font-weight: bold; color: #dc2626;">💡 该卖家定价（￥{{ item.price }}）低于校园均价，是一笔划算的交易！</div>
            <div v-else style="margin-top: 10px; font-weight: bold; color: #4b5563;">💡 该卖家定价（￥{{ item.price }}）高于或等于均价。</div>
        </div>
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

  <!-- 图片预览模态框 -->
  <div v-if="previewImage" class="preview-modal" @click="previewImage = null">
      <img :src="previewImage" @click.stop />
      <button class="close-preview" @click="previewImage = null">×</button>
  </div>
  
  <!-- AI 助手组件 -->
  <div class="ai-assistant" :class="{ 'ai-open': isAIOpen }">
      <div v-if="!isAIOpen" class="ai-bubble" @click="isAIOpen = true">
          🤖 智能助手
      </div>
      <div v-else class="ai-panel">
          <div class="ai-header">
              <span>🤖 智能导购助手</span>
              <button @click="isAIOpen = false" style="background:none;border:none;color:white;cursor:pointer;font-size:1.2em;">×</button>
          </div>
          <div class="ai-chats" ref="aiChatBox">
              <div v-for="(msg, i) in aiMessages" :key="i" :class="msg.role">
                  <span>{{ msg.content }}</span>
              </div>
          </div>
          <div class="ai-input">
              <input v-model="aiKeyword" @keyup.enter="sendAIMsg" placeholder="问点什么..." style="flex:1; padding: 6px; border: 1px solid #ddd; border-radius:4px;" />
              <button @click="sendAIMsg" class="btn bg-blue" style="padding:6px 12px; margin-left: 8px;">发送</button>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const item = ref(null)
const images = ref([])
const cmpInfo = ref(null)
const previewImage = ref(null)
const isFavorite = ref(false)
const userId = localStorage.getItem('user_id')
const userRole = localStorage.getItem('role')

// AI Assistant
const isAIOpen = ref(false)
const aiKeyword = ref('')
const aiChatBox = ref(null)
const aiMessages = ref([
    { role: 'bot', content: '您好！我是校园二手平台智能助手。请问想了解怎么发布商品？还是关于议价、退货相关的问题？' }
])

const scrollToBottom = () => {
    nextTick(() => {
        if (aiChatBox.value) aiChatBox.value.scrollTop = aiChatBox.value.scrollHeight;
    })
}

const sendAIMsg = () => {
    if (!aiKeyword.value.trim()) return;
    const txt = aiKeyword.value.trim();
    aiMessages.value.push({ role: 'user', content: txt });
    aiKeyword.value = '';
    scrollToBottom();
    
    setTimeout(() => {
        let reply = "抱歉，我不太明白您的意思。您可以问我：怎么买东西？怎么发布？保障如何？有没有砍价空间？";
        if (txt.includes('发布') || txt.includes('上架') || txt.includes('卖')) reply = "发布商品非常简单！在导航栏点击【发布闲置】，填写标题、价格和分类，如果有实拍图记得上传哦，这样更容易卖出！";
        else if (txt.includes('退款') || txt.includes('退货') || txt.includes('保障')) reply = "本平台主要提供撮合服务，建议同校尽量线下当面交易验货；如果是大额商品付款，请务必确认后再交易。";
        else if (txt.includes('比价') || txt.includes('便宜') || txt.includes('均价') || txt.includes('行情')) reply = "您可以在每个商品详情页中看到我们的【校园行情大盘】，会自动帮您全网比价，保证买得明白！";
        else if (txt.includes('怎么买') || txt.includes('买东西')) reply = "看到心仪的商品后，点击页面下方的【💳 立即购买】。扣除您的余额后，钱款就会打入对方账户！";
        else if (txt.includes('刀') || txt.includes('砍价') || txt.includes('便宜点')) reply = "商品目前是一口价哦~ 当然，您也可以在评论区或通过联系方式和卖家私下“小刀”一下。祝您校园淘宝愉快！";
        
        aiMessages.value.push({ role: 'bot', content: reply });
        scrollToBottom();
    }, 500);
}

onMounted(async () => {
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
    images.value = JSON.parse(data.images || "[]")
    
    try { 
        const cmp = await fetch(`http://localhost:8000/api/items/${route.params.id}/compare`); 
        if(cmp.ok) { cmpInfo.value = await cmp.json() }
    } catch(e){}
    
    if(userId) {
        try {
            const favRes = await fetch(`http://localhost:8000/api/users/${userId}/favorites`)
            if (favRes.ok) {
                const favs = await favRes.json()
                isFavorite.value = favs.some(f => f.id === data.id)
            }
        } catch(e) {}
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
            location.reload()
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

<style scoped>
.preview-modal {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.85); z-index: 9999;
    display: flex; justify-content: center; align-items: center;
    backdrop-filter: blur(5px);
}
.preview-modal img {
    max-width: 90%; max-height: 90vh; object-fit: contain;
    border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.close-preview {
    position: absolute; top: 20px; right: 30px;
    background: #fff; color: #333; border: none; border-radius: 50%;
    width: 40px; height: 40px; font-size: 24px; cursor: pointer;
    font-weight: bold; line-height: 40px; text-align: center;
}

/* AI助手样式 */
.ai-assistant { position: fixed; bottom: 30px; right: 30px; z-index: 1000; font-family: -apple-system, sans-serif; }
.ai-bubble { 
    background: #4CAF50; color: white; padding: 12px 20px; border-radius: 30px; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; font-weight: bold; 
    transition: transform 0.3s; 
}
.ai-bubble:hover { transform: scale(1.05); }
.ai-panel { 
    width: 320px; height: 430px; background: white; border-radius: 12px; 
    box-shadow: 0 10px 30px rgba(0,0,0,0.2); display: flex; flex-direction: column; overflow: hidden; 
}
.ai-header { background: #4CAF50; color: white; padding: 12px 15px; display: flex; justify-content: space-between; font-weight: bold; }
.ai-chats { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; background: #f9f9f9; }
.ai-chats .bot, .ai-chats .user { display: flex; max-width: 85%; }
.ai-chats .bot { align-self: flex-start; }
.ai-chats .user { align-self: flex-end; }
.ai-chats .bot span { background: white; padding: 10px 14px; border-radius: 2px 15px 15px 15px; color: #333; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.9em; line-height: 1.4; }
.ai-chats .user span { background: #E3F2FD; padding: 10px 14px; border-radius: 15px 2px 15px 15px; color: #1e3a8a; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.9em; line-height: 1.4; }
.ai-input { padding: 10px; background: white; border-top: 1px solid #eee; display: flex; }
</style>
