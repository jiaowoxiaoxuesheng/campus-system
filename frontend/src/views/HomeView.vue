<template>
  <div>
    <!-- 引入的组件 -->
    <div class="filters">
      <input v-model="query.keyword" placeholder="搜索闲置物品关键字..." />
      <select v-model="query.categoryId" style="padding: 5px; border-radius: 4px; border: 1px solid #ccc;">
        <option value="">全部分类</option>
        <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
      </select>
      <PriceSlider v-model:min="query.minPrice" v-model:max="query.maxPrice" />
      <DatePicker v-model:start="query.startDate" v-model:end="query.endDate" />
      <button @click="fetchData">组合搜索</button>
      <button @click="exportData" style="background: #2196F3;">导出数据(CSV)</button>
    </div>

    <!-- 热门推荐 / 价格趋势 (加分项) -->
    <div style="display: flex; gap: 20px; margin-bottom: 20px;">
      <div class="panel">
        <h3>🔥 热门商品推荐</h3>
        <ul>
          <li v-for="hot in hotItems" :key="hot.id">{{ hot.title }} - 👁 {{ hot.views }}次浏览</li>
        </ul>
      </div>
      <div class="panel" style="flex: 1; position: relative;">
        <h3 v-if="!currentCategoryChart">📈 价格趋势 (分类均价) - 点击柱子查看详情</h3>
        <h3 v-else>📈 {{ currentCategoryChart }} 价格连线趋势图 (按日统计)</h3>
        <button v-if="currentCategoryChart" @click="resetChartToCategories" style="position: absolute; right: 20px; top: 15px; padding: 3px 10px; cursor: pointer;">返回总览</button>
        <div id="chart" style="width: 100%; height: 200px;"></div>
      </div>
    </div>

    <div class="item-grid" v-if="items.length">
      <div class="card" v-for="item in items" :key="item.id" @click="$router.push('/item/' + item.id)" style="cursor: pointer; transition: box-shadow 0.3s;" onmouseover="this.style.boxShadow='0 4px 8px rgba(0,0,0,0.2)'" onmouseout="this.style.boxShadow='none'">
        <h3 v-html="highlight(item.title)"></h3>
        <p style="color:red; font-weight:bold;">￥{{ item.price }}</p>
        <p style="font-size:12px; color: #888;">
          <span style="background:#eee; padding: 2px 6px; border-radius: 4px; margin-right: 5px;">{{ item.category_name }}</span>
          浏览数: {{ item.views }} | {{ item.created_at }}
        </p>
      </div>
    </div>
    <div v-else style="margin-top: 20px;">无相关物品</div>

    <Pagination :current-page="query.page" :total="total" :size="query.size" @page-change="onPageChange" />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import Pagination from '../components/Pagination.vue'
import PriceSlider from '../components/PriceSlider.vue'
import DatePicker from '../components/DatePicker.vue'

const items = ref([])
const total = ref(0)
const hotItems = ref([])
const categories = ref([])
const query = ref({ keyword: '', categoryId: '', minPrice: '', maxPrice: '', startDate: '', endDate: '', page: 1, size: 8 })

// 严格使用原生 fetch 进行交互
const fetchData = async () => {
    let url = `http://localhost:8000/api/items?page=${query.value.page}&size=${query.value.size}`
    if (query.value.keyword) url += `&keyword=${query.value.keyword}`
    if (query.value.categoryId) url += `&category_id=${query.value.categoryId}`
    if (query.value.minPrice) url += `&min_price=${query.value.minPrice}`
    if (query.value.maxPrice) url += `&max_price=${query.value.maxPrice}`
    
    try {
        const res = await fetch(url)
        const data = await res.json()
        items.value = data.items
        total.value = data.total
    } catch(e) { console.error('需要先启动后端服务器!') }
}

const currentCategoryChart = ref('') // 控制返回按钮和图表标题

const fetchAdvancedData = async () => {
    // 获取分类
    fetch('http://localhost:8000/api/categories')
        .then(res => res.json())
        .then(data => categories.value = data)

    // 获取热门
    const resHot = await fetch('http://localhost:8000/api/hot-items')
    hotItems.value = await resHot.json()

    // 获取价格趋势并绘制 Echarts（默认无点击）
    await initCategoryChart()
}

const initCategoryChart = async () => {
    const resTrend = await fetch('http://localhost:8000/api/price-trends')
    const trendData = await resTrend.json()
    
    currentCategoryChart.value = ''
    nextTick(() => {
        const myChart = echarts.init(document.getElementById('chart'))
        myChart.clear() // 清除老画布
        myChart.setOption({
            tooltip: { trigger: 'axis' },
            xAxis: { type: 'category', data: trendData.map(t => t.category_name) },
            yAxis: { type: 'value' },
            series: [{ name: '平均价格', type: 'bar', data: trendData.map(t => t.avg_price), itemStyle: { color: '#4169E1' } }]
        })
        
        // 绑定点击事件，解除旧事件，防止重复绑定
        myChart.off('click')
        myChart.on('click', async (params) => {
            const catName = params.name
            currentCategoryChart.value = catName
            const res = await fetch(`http://localhost:8000/api/price-trends/${catName}`)
            const lineData = await res.json()
            
            myChart.clear()
            myChart.setOption({
                tooltip: { trigger: 'axis' },
                xAxis: { type: 'category', data: lineData.map(d => d.date) },
                yAxis: { type: 'value' },
                series: [{ name: '每日均价', type: 'line', smooth: true, data: lineData.map(d => d.avg_price), areaStyle: {} }]
            })
            // 此时不用重绑，因为点击折线图上的点不需要再钻取了
            myChart.off('click')
        })
    })
}

const resetChartToCategories = () => {
    initCategoryChart()
}

// 导出数据
const exportData = () => {
    window.open('http://localhost:8000/api/export-items')
}

const onPageChange = (p) => { query.value.page = p; fetchData() }

// 交互：关键字高亮
const highlight = (title) => {
    if (!query.value.keyword) return title;
    const reg = new RegExp(`(${query.value.keyword})`, 'gi');
    return title.replace(reg, '<span style="background: yellow; color: red;">$1</span>');
}

onMounted(() => {
    fetchData()
    fetchAdvancedData()
})
</script>

<style scoped>
.filters { display: flex; gap: 15px; background: white; padding: 15px; border-radius: 8px; flex-wrap: wrap; margin-bottom: 20px;}
.panel { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.item-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }
.card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
button { background: #4CAF50; color: white; border: none; padding: 8px 15px; cursor: pointer; border-radius: 4px; }
</style>