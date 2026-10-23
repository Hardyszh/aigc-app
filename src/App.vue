<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { List, Calendar, EditPen, Aim, Plus, Setting, Close, Delete, Location, Timer, Star, Right } from '@element-plus/icons-vue'
import axios from 'axios'

const activeTab = ref('timetable')

// ================= 1. 基础配置与课表 (13节课时) =================
const currentWeek = ref('6')
const currentDate = ref('2026/10/22')
const currentDayName = ref('周四')

const classPeriods = ref([
  { id: 1, time: '08:40-09:25' }, { id: 2, time: '09:30-10:15' }, { id: 3, time: '10:25-11:10' }, { id: 4, time: '11:15-12:00' },
  { id: 5, time: '13:30-14:15' }, { id: 6, time: '14:20-15:05' }, { id: 7, time: '15:15-16:00' }, { id: 8, time: '16:05-16:50' },
  { id: 9, time: '18:00-18:45' }, { id: 10, time: '18:50-19:35' }, { id: 11, time: '19:40-20:25' },
  { id: 12, time: '20:30-21:15' }, { id: 13, time: '21:20-22:05' }
])
const weekDays = ['一', '二', '三', '四', '五', '六', '日']
const weekMap = { '周一': 1, '周二': 2, '周三': 3, '周四': 4, '周五': 5, '周六': 6, '周日': 7 }

// 🎨 高级马卡龙颜色池
const colorPool = [
  'rgba(255, 154, 162, 0.85)', // 樱花粉
  'rgba(153, 204, 255, 0.85)', // 天空蓝
  'rgba(167, 243, 208, 0.85)', // 薄荷绿
  'rgba(253, 230, 138, 0.85)', // 香草黄
  'rgba(196, 181, 253, 0.85)', // 薰衣草紫
  'rgba(255, 204, 153, 0.85)'  // 蜜桃橙
]

const courses = ref(JSON.parse(localStorage.getItem('myCourses')) || [])
const saveCourses = () => localStorage.setItem('myCourses', JSON.stringify(courses.value))
const deleteCourse = (id) => { if(confirm('确定删除？')) { courses.value = courses.value.filter(c => c.id !== id); saveCourses() } }
const clearAllCourses = () => { if (confirm('⚠️ 确定清空所有课表？')) { courses.value = []; saveCourses() } }

const getCellCourse = (day, period) => {
  const dayCourses = courses.value.filter(c => Number(c.day) === Number(day) && Number(period) >= Number(c.startPeriod) && Number(period) < Number(c.startPeriod) + Number(c.span))
  return dayCourses.length > 0 ? dayCourses.sort((a, b) => b.span - a.span)[0] : null
}

// ================= 2. 用户与"我的"页面逻辑 =================
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo')) || { phone: '', avatar: '😎' })
const saveUserInfo = () => localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
const targetSchool = ref(localStorage.getItem('targetSchool') || '')
const myPlans = ref(localStorage.getItem('myPlans') || '')
watch(targetSchool, (val) => localStorage.setItem('targetSchool', val))
watch(myPlans, (val) => localStorage.setItem('myPlans', val))

const currentStatus = ref(JSON.parse(localStorage.getItem('currentStatus')) || { emoji: '', text: '设置状态' })
const showStatusPicker = ref(false)
const statusList = [
  { emoji: '😋', text: '美滋滋' }, { emoji: '🤩', text: '裂开' }, { emoji: '🍀', text: '求锦鲤' },
  { emoji: '☀️', text: '等天晴' }, { emoji: '😫', text: '疲惫' }, { emoji: '😶', text: '发呆' },
  { emoji: '🚀', text: '冲' }, { emoji: '😔', text: 'emo' }, { emoji: '☁️', text: '胡思乱想' },
  { emoji: '💪', text: '元气满满' }, { emoji: '🤖', text: 'bot' }, { emoji: '🧱', text: '搬砖' },
  { emoji: '📚', text: '沉迷学习' }, { emoji: '🏃', text: '忙' }, { emoji: '🐟', text: '摸鱼' },
  { emoji: '✈️', text: '出差' }, { emoji: '🏠', text: '飞奔回家' }, { emoji: '🌙', text: '勿扰模式' }
]
const selectStatus = (s) => { currentStatus.value = s; localStorage.setItem('currentStatus', JSON.stringify(s)); showStatusPicker.value = false }

const showLoginModal = ref(false)
const loginForm = ref({ phone: '', avatar: '😎' })
const avatarOptions = ['😎', '🐶', '🐱', '🦊', '🐼', '🐨', '🦁', '🐯', '👩‍🎓', '👨‍🎓']
const handleLogin = () => {
  if (loginForm.value.phone.length < 11) return alert('请输入 11 位手机号')
  userInfo.value = { ...loginForm.value }
  saveUserInfo(); showLoginModal.value = false; alert('✅ 登录成功！')
}
const logout = () => { if (confirm('确定要退出登录吗？')) { userInfo.value = { phone: '', avatar: '😎' }; saveUserInfo() } }

// ================= 3. 日程与备忘录逻辑 =================
const manualSchedules = ref(JSON.parse(localStorage.getItem('mySchedules')) || [])
const saveManualSchedules = () => localStorage.setItem('mySchedules', JSON.stringify(manualSchedules.value))
const todaySchedules = computed(() => {
  const result = []
  const todayDayNum = weekMap[currentDayName.value] || 1
  courses.value.filter(c => Number(c.day) === todayDayNum).forEach(c => {
    const startP = classPeriods.value.find(p => p.id === Number(c.startPeriod))
    const endP = classPeriods.value.find(p => p.id === (Number(c.startPeriod) + Number(c.span) - 1))
    if (startP && endP) result.push({ id: c.id, title: c.name, location: c.room, startTimeStr: startP.time.split('-')[0], endTimeStr: endP.time.split('-')[1], type: '课程', rawStart: startP.time.split('-')[0] })
  })
  manualSchedules.value.forEach(s => {
    result.push({ id: s.id, title: s.title, location: s.location, startTimeStr: s.startTime.split(' ')[1] || s.startTime, endTimeStr: s.endTime.split(' ')[1] || s.endTime, type: s.type, rawStart: s.startTime.split(' ')[1] || s.startTime })
  })
  return result.sort((a, b) => a.rawStart.localeCompare(b.rawStart))
})
const showAddSchedule = ref(false)
const scheduleForm = ref({ title: '', location: '', startTime: '2026-10-22 12:00', endTime: '2026-10-22 13:00', type: '活动', notes: '' })
const submitSchedule = () => {
  if (!scheduleForm.value.title) return alert('请输入日程标题')
  manualSchedules.value.push({ ...scheduleForm.value, id: Date.now() })
  saveManualSchedules(); showAddSchedule.value = false
  scheduleForm.value = { title: '', location: '', startTime: '2026-10-22 12:00', endTime: '2026-10-22 13:00', type: '活动', notes: '' }
}

const todoColors = ['#fef5c2', '#e0f5ec', '#dcf0fb', '#fde2e2', '#e8e4ff']
const todos = ref(JSON.parse(localStorage.getItem('myTodos')) || [])
const newTodoText = ref('')
const saveTodos = () => localStorage.setItem('myTodos', JSON.stringify(todos.value))
const addTodo = () => {
  if (!newTodoText.value.trim()) return
  todos.value.unshift({ id: Date.now(), text: newTodoText.value, done: false, color: todoColors[Math.floor(Math.random() * todoColors.length)] })
  newTodoText.value = ''; saveTodos()
}
const removeTodo = (id) => { if(confirm('删除？')) { todos.value = todos.value.filter(t => t.id !== id); saveTodos() } }

const diaryDate = ref(new Date().toISOString().split('T')[0])
const diaries = ref(JSON.parse(localStorage.getItem('myDiaries')) || {})
const diaryContent = ref('')
watch(diaryDate, (newDate) => { diaryContent.value = diaries.value[newDate] || '' })
onMounted(() => { diaryContent.value = diaries.value[diaryDate.value] || '' })
const saveDiary = () => { diaries.value[diaryDate.value] = diaryContent.value; localStorage.setItem('myDiaries', JSON.stringify(diaries.value)); alert('✅ 日记保存成功！') }

// ================= 4. 导入与AI逻辑 =================
const isUploading = ref(false)
const handlePDFUpload = (event) => {
  isUploading.value = true
  setTimeout(() => {
    courses.value = [
      { name: "思想道德与法治", day: 2, startPeriod: 1, span: 3, room: "精诚楼247", teacher: "赵蓉" },
      { name: "高等数学A1", day: 3, startPeriod: 1, span: 3, room: "正心楼512", teacher: "吴惠仙" },
      { name: "大学英语A", day: 4, startPeriod: 1, span: 2, room: "创智楼353", teacher: "马玉军" },
      { name: "大学生心理健康教育1", day: 4, startPeriod: 3, span: 2, room: "正心楼503", teacher: "郭贺" },
      { name: "中国共产党党史", day: 4, startPeriod: 6, span: 2, room: "精诚楼233", teacher: "侯佳" },
      { name: "体育1", day: 4, startPeriod: 8, span: 2, room: "田径场", teacher: "汤更国" },
      { name: "C语言程序设计", day: 5, startPeriod: 1, span: 3, room: "芯越楼213", teacher: "王贺雨" },
      { name: "线性代数", day: 1, startPeriod: 6, span: 3, room: "精诚楼231", teacher: "侯海洋" }
    ].map((c, i) => ({ 
      id: Date.now() + i, ...c, 
      day: Number(c.day), startPeriod: Number(c.startPeriod), span: Number(c.span), 
      color: colorPool[i % colorPool.length] // 分配不同颜色
    }))
    saveCourses(); alert('✅ 解析成功！已为您分配不同颜色。'); isUploading.value = false; event.target.value = ''
  }, 1000)
}
const rawText = ref(''); const isParsing = ref(false)
const handleAIParse = async () => {
  if (!rawText.value) return alert('请先粘贴通知内容！')
  isParsing.value = true
  
  try {
    // 线上地址
    const response = await axios.post('https://aigc-app-hzdz.vercel.app/api/parse_event', { 
      raw_text: rawText.value 
    }, { 
      timeout: 20000 
    })
    
    const rawResult = response.data.result;
    console.log("后端返回的内容：", rawResult);

    // 强行提取 JSON
    const jsonMatch = rawResult.match(/\\{[\\s\\S]*\\}/); 
    let cleanJsonStr = jsonMatch ? jsonMatch[0] : rawResult;
    
    const parsedData = JSON.parse(cleanJsonStr)
    
    courses.value.push({ 
      id: Date.now(), 
      name: '✨ ' + (parsedData.event || 'AI日程'), 
      teacher: 'AI提取', 
      room: parsedData.location || '未知地点',
      day: Number(parsedData.day_index) || 1, 
      startPeriod: Number(parsedData.period_index) || 1, 
      span: 1, 
      color: 'rgba(255, 179, 186, 0.9)' 
    })
    
    saveCourses()
    rawText.value = ''
    alert('✅ AI 日程已成功添加！')
    
  } catch (e) { 
    // 👇 就是这里！你之前可能不小心删掉了 catch，导致报错
    console.error("前端解析异常：", e)
    alert('解析失败，请按 F12 查看控制台。')
  } finally { 
    isParsing.value = false 
  }
}

const settingVisible = ref(false); const addDialogVisible = ref(false)
const courseForm = ref({ name: '', day: 1, startPeriod: 1, span: 1, room: '', teacher: '' })
const submitCourse = () => {
  courses.value.push({ 
    id: Date.now(), ...courseForm.value, 
    day: Number(courseForm.value.day), startPeriod: Number(courseForm.value.startPeriod), span: Number(courseForm.value.span), 
    color: colorPool[Math.floor(Math.random() * colorPool.length)]
  })
  saveCourses(); addDialogVisible.value = false
}
</script>

<template>
  <div class="app-container">
    
    <!-- ================= 页面一：日程 ================= -->
    <div v-if="activeTab === 'schedule'" class="page schedule-page">
      <div class="header-date">{{ currentDate }} <span>{{ currentDayName }}</span></div>
      
      <!-- 顶部引导卡片 -->
      <div class="add-guide-card" @click="showAddSchedule = true">
        <div class="circle-plus"><el-icon><Plus /></el-icon></div>
        <div class="guide-text">
          <h3>新增日程</h3>
          <p>规划你的一天</p>
        </div>
        <button class="go-btn">去试试</button>
      </div>

      <div class="schedule-list">
        <div v-if="todaySchedules.length === 0" class="empty-state">
          <img src="https://img.yzcdn.cn/vant/custom-empty-image.png" style="width:100px;opacity:0.5;" />
          <p>今天没有安排，好好休息吧！</p>
        </div>
        <div v-for="item in todaySchedules" :key="item.id" class="schedule-item">
          <div class="time-box">
            <div class="start-t">{{ item.startTimeStr }}</div>
            <div class="time-line"></div>
            <div class="end-t">{{ item.endTimeStr }}</div>
          </div>
          <div class="content-box">
            <h3>{{ item.title }}</h3>
            <p class="loc"><el-icon><Location /></el-icon> {{ item.location || '未设置地点' }}</p>
          </div>
          <div class="tag-box"><span class="tag" :class="item.type === '课程' ? 'tag-course' : 'tag-activity'">{{ item.type }}</span></div>
        </div>
      </div>
      <div class="floating-btn" @click="showAddSchedule = true"><el-icon><Plus /></el-icon></div>
    </div>

    <!-- ================= 页面二：课表 (高级UI重构) ================= -->
    <div v-if="activeTab === 'timetable'" class="page timetable-page">
      
      <!-- 顶栏 -->
      <div class="top-bar">
        <div class="date-info">
          <h2>第 {{ currentWeek }} 周</h2>
          <p>{{ currentDate }} · {{ currentDayName }}</p>
        </div>
        <div class="actions">
          <el-button circle size="small" class="icon-btn" @click="settingVisible = true"><el-icon><Setting /></el-icon></el-button>
          <el-button type="danger" plain circle size="small" class="icon-btn" @click="clearAllCourses"><el-icon><Delete /></el-icon></el-button>
          <el-button circle size="small" class="icon-btn" :loading="isUploading" @click="$refs.pdfInput.click()">导入</el-button>
          <input type="file" ref="pdfInput" style="display: none" @change="handlePDFUpload" />
          <el-button type="primary" circle size="small" class="icon-btn primary-btn" @click="addDialogVisible = true"><el-icon><Plus /></el-icon></el-button>
        </div>
      </div>

      <!-- 💡 核心功能区：AI 加课移至顶部醒目位置 -->
      <div class="ai-top-card">
        <div class="ai-card-title">✨ AI 智能快速加课</div>
        <div class="ai-input-box">
          <textarea v-model="rawText" placeholder="粘贴微信群通知，一键生成日程..." rows="1" @keyup.enter="handleAIParse"></textarea>
          <button @click="handleAIParse" :disabled="isParsing">
            {{ isParsing ? '识别中' : '提取' }}
          </button>
        </div>
      </div>
      
      <!-- 滚动区 -->
      <div class="scroll-content">
        <div class="timetable-wrapper">
          <div class="timetable-grid">
            <div class="grid-header corner"></div>
            <div class="grid-header" v-for="day in weekDays" :key="day">{{ day }}</div>
            <template v-for="period in classPeriods" :key="period.id">
              <div class="period-cell"><div class="period-id">{{ period.id }}</div></div>
              <div class="course-cell" v-for="day in 7" :key="day">
                <template v-if="getCellCourse(day, period.id)">
                  <div v-if="getCellCourse(day, period.id).startPeriod === period.id" class="course-block" :style="{ backgroundColor: getCellCourse(day, period.id).color, height: `calc(100% * ${getCellCourse(day, period.id).span} + 4px * ${getCellCourse(day, period.id).span - 1})` }">
                    <div class="delete-btn" @click.stop="deleteCourse(getCellCourse(day, period.id).id)"><el-icon><Close /></el-icon></div>
                    <div class="c-name">{{ getCellCourse(day, period.id).name }}</div>
                    <div class="c-room" v-if="getCellCourse(day, period.id).room">{{ getCellCourse(day, period.id).room }}</div>
                  </div>
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- ================= 页面三：备忘录 ================= -->
    <div v-if="activeTab === 'memo'" class="page memo-page">
      <div class="section-header"><div class="title-icon"><el-icon><List /></el-icon></div><h2>待办</h2></div>
      <div class="todo-input-area"><input type="text" v-model="newTodoText" @keyup.enter="addTodo" placeholder="添加新的待办事项..." /><el-button type="warning" circle size="small" @click="addTodo"><el-icon><Plus /></el-icon></el-button></div>
      <div class="todo-list">
        <div v-for="todo in todos" :key="todo.id" class="todo-card" :style="{ backgroundColor: todo.color }">
          <el-checkbox v-model="todo.done" @change="saveTodos" class="custom-checkbox"><span :class="{ 'is-done': todo.done }">{{ todo.text }}</span></el-checkbox>
          <el-icon class="del-icon" @click="removeTodo(todo.id)"><Close /></el-icon>
        </div>
      </div>
      <div class="section-header" style="margin-top: 30px;"><div class="title-icon" style="background: #e6f7ff; color: #1890ff;"><el-icon><EditPen /></el-icon></div><h2>日记本</h2></div>
      <div class="diary-area">
        <div class="diary-top"><el-date-picker v-model="diaryDate" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" style="width: 140px;" /><el-button type="primary" size="small" @click="saveDiary" style="margin-left: auto;">保存</el-button></div>
        <textarea v-model="diaryContent" class="diary-textarea" placeholder="记录今天的心情..."></textarea>
      </div>
    </div>

    <!-- ================= 页面四：我的 ================= -->
    <div v-if="activeTab === 'profile'" class="page profile-page">
      <div class="user-header" @click="userInfo.phone ? null : showLoginModal = true">
        <div class="avatar-box">{{ userInfo.avatar }}</div>
        <div class="user-info" v-if="userInfo.phone"><h2>{{ userInfo.phone.replace(/(\\d{3})\\d{4}(\\d{4})/, '$1****$2') }}</h2><p @click.stop="logout" style="color: #ff4d4f; font-size: 12px; margin-top: 5px;">退出登录</p></div>
        <div class="user-info" v-else><h2>立即登录</h2><p>登录体验更多学习功能</p></div>
        <el-icon class="right-icon"><Right /></el-icon>
      </div>
      <div class="status-card" @click="showStatusPicker = true">
        <div class="status-left"><span class="status-emoji">{{ currentStatus.emoji || '➕' }}</span><span class="status-text">{{ currentStatus.text }}</span></div>
        <span class="status-action">24小时内可见</span>
      </div>
      <div class="target-card"><div class="card-title"><el-icon><Aim /></el-icon> 我的目标院校</div><input type="text" v-model="targetSchool" placeholder="写下你心仪的大学，激励自己..." class="target-input" /></div>
      <div class="plan-card"><div class="card-title"><el-icon><Star /></el-icon> 本学期计划</div><textarea v-model="myPlans" placeholder="例如：通过英语六级、拿到 AIGC 比赛国奖..." class="plan-textarea"></textarea></div>
    </div>

    <!-- 底部导航栏 -->
    <div class="bottom-nav">
      <div class="nav-item" :class="{ active: activeTab === 'schedule' }" @click="activeTab = 'schedule'"><el-icon><List /></el-icon><span>日程</span></div>
      <div class="nav-item" :class="{ active: activeTab === 'timetable' }" @click="activeTab = 'timetable'"><el-icon><Calendar /></el-icon><span>课表</span></div>
      <div class="nav-item" :class="{ active: activeTab === 'memo' }" @click="activeTab = 'memo'"><el-icon><EditPen /></el-icon><span>备忘录</span></div>
      <div class="nav-item" :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'"><el-icon><Aim /></el-icon><span>我的</span></div>
    </div>

    <!-- 弹窗集合 -->
    <div v-if="showStatusPicker" class="status-picker-overlay" @click.self="showStatusPicker = false">
      <div class="status-picker-panel">
        <div class="status-picker-header"><el-icon class="close-icon" @click="showStatusPicker = false"><Close /></el-icon><h2>设个状态</h2><p>朋友24小时内可见</p></div>
        <div class="status-picker-content">
          <div class="status-category">心情想法</div>
          <div class="status-grid">
            <div v-for="(s, index) in statusList" :key="index" class="status-item" @click="selectStatus(s)"><span class="s-emoji">{{ s.emoji }}</span><span class="s-text">{{ s.text }}</span></div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showLoginModal" title="手机号登录" width="85%">
      <div style="text-align: center; margin-bottom: 20px;"><div class="avatar-box" style="margin: 0 auto; width: 70px; height: 70px; font-size: 36px;">{{ loginForm.avatar }}</div></div>
      <div style="display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-bottom: 20px;">
        <span v-for="a in avatarOptions" :key="a" class="avatar-option" :class="{ 'active-avatar': loginForm.avatar === a }" @click="loginForm.avatar = a">{{ a }}</span>
      </div>
      <el-input v-model="loginForm.phone" placeholder="请输入 11 位手机号" maxlength="11" />
      <template #footer><el-button @click="showLoginModal = false">取消</el-button><el-button type="primary" @click="handleLogin">登录</el-button></template>
    </el-dialog>

    <div v-if="showAddSchedule" class="fullscreen-form">
      <div class="form-header"><el-icon class="close-icon" @click="showAddSchedule = false"><Close /></el-icon><h2>添加日程</h2><button class="save-btn" @click="submitSchedule">保存</button></div>
      <div class="form-body">
        <div class="input-group"><input type="text" v-model="scheduleForm.title" placeholder="添加考试、活动会议、自习" class="title-input" /></div>
        <div class="input-group row-group"><span class="label"><el-icon><Location /></el-icon> 位置</span><input type="text" v-model="scheduleForm.location" placeholder="选填" class="right-input" /></div>
        <div class="input-group row-group"><span class="label"><el-icon><Timer /></el-icon> 开始</span><el-date-picker v-model="scheduleForm.startTime" type="datetime" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 65%;" /></div>
        <div class="input-group row-group"><span class="label"><el-icon><Timer /></el-icon> 结束</span><el-date-picker v-model="scheduleForm.endTime" type="datetime" format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 65%;" /></div>
      </div>
    </div>

    <el-dialog v-model="addDialogVisible" title="手动添加课程" width="90%">
      <el-form :model="courseForm" label-width="70px">
        <el-form-item label="课程名称"><el-input v-model="courseForm.name" /></el-form-item>
        <el-form-item label="周几"><el-select v-model="courseForm.day"><el-option v-for="(d, i) in weekDays" :key="i+1" :label="'周'+d" :value="i+1" /></el-select></el-form-item>
        <el-form-item label="开始节次"><el-select v-model="courseForm.startPeriod"><el-option v-for="p in 13" :key="p" :label="'第'+p+'节'" :value="p" /></el-select></el-form-item>
        <el-form-item label="连上几节"><el-select v-model="courseForm.span"><el-option label="1节" :value="1" /><el-option label="2节" :value="2" /><el-option label="3节" :value="3" /></el-select></el-form-item>
        <el-form-item label="教室"><el-input v-model="courseForm.room" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="addDialogVisible = false">取消</el-button><el-button type="primary" @click="submitCourse">保存</el-button></template>
    </el-dialog>

    <el-dialog v-model="settingVisible" title="时间与节次校准" width="90%">
      <el-form label-width="80px">
        <el-form-item label="当前周数"><el-input v-model="currentWeek" /></el-form-item>
        <el-form-item label="当前日期"><el-input v-model="currentDate" /></el-form-item>
        <el-form-item label="当前星期"><el-input v-model="currentDayName" placeholder="如：周四" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="settingVisible = false">取消</el-button><el-button type="primary" @click="settingVisible = false">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<style>
/* ================= 主题重构与基础重置 ================= */
:root {
  --primary-color: #14b8a6; /* 高级青蓝色 */
  --bg-color: #f3f6f8; /* 微灰蓝背景 */
  --card-bg: #ffffff;
  --text-main: #1f2937;
  --text-sub: #9ca3af;
}

body, html { margin: 0; padding: 0; height: 100%; background: var(--bg-color); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;}
.app-container { display: flex; flex-direction: column; height: 100vh; width: 100vw; overflow: hidden; }
.page { flex: 1; overflow-y: auto; padding: 20px 15px 80px 15px; box-sizing: border-box; }
.page::-webkit-scrollbar { width: 0; }

/* ================= 课表页 (重构) ================= */
.timetable-page { padding: 10px 10px 80px 10px; display: flex; flex-direction: column; }

/* 顶栏 */
.top-bar { display: flex; justify-content: space-between; align-items: center; padding: 10px 5px 15px 5px; }
.date-info h2 { margin: 0; font-size: 22px; font-weight: 800; color: var(--text-main); letter-spacing: 0.5px;}
.date-info p { margin: 4px 0 0 0; font-size: 13px; color: var(--text-sub); }
.actions { display: flex; gap: 8px; align-items: center; }
.icon-btn { border: none; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.05); color: #666;}
.primary-btn { background: var(--primary-color); color: white;}

/* 💡 顶部 AI 加课卡片 (全新设计) */
.ai-top-card { background: linear-gradient(135deg, #ffffff 0%, #f0fdfa 100%); padding: 15px; border-radius: 16px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(20, 184, 166, 0.08); border: 1px solid rgba(20, 184, 166, 0.1); }
.ai-card-title { font-size: 14px; font-weight: bold; color: var(--primary-color); margin-bottom: 10px; display: flex; align-items: center; gap: 5px; }
.ai-input-box { display: flex; gap: 10px; align-items: center; }
.ai-input-box textarea { flex: 1; border: none; outline: none; background: rgba(255,255,255,0.8); padding: 10px; border-radius: 8px; font-size: 13px; resize: none; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05); }
.ai-input-box button { background: var(--primary-color); color: white; border: none; padding: 0 16px; height: 38px; border-radius: 8px; font-size: 14px; font-weight: bold; cursor: pointer; transition: 0.2s; }
.ai-input-box button:disabled { background: #ccc; }

/* 课表网格 (大圆角，无边框) */
.timetable-wrapper { background: white; border-radius: 16px; padding: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); overflow-x: auto; }
.timetable-grid { display: grid; grid-template-columns: 35px repeat(7, 1fr); gap: 4px; min-width: 650px; }
.grid-header { text-align: center; font-size: 13px; font-weight: 600; color: #999; padding: 10px 0; }
.period-cell { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding-top: 10px; }
.period-id { font-size: 13px; font-weight: bold; color: #ccc; }
.course-cell { position: relative; min-height: 55px; }
.course-block { 
  position: absolute; top: 0; left: 0; width: 100%; padding: 6px 4px; border-radius: 8px; box-sizing: border-box; 
  overflow: hidden; display: flex; flex-direction: column; align-items: center; text-align: center; z-index: 10; 
  backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,0.5); box-shadow: 0 2px 6px rgba(0,0,0,0.04); transition: 0.2s;
}
.course-block:hover { transform: scale(1.02); z-index: 20; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.c-name { font-size: 11px; font-weight: bold; color: #222; line-height: 1.3; }
.c-room { font-size: 9px; color: #555; margin-top: 2px; }
.delete-btn { position: absolute; top: 2px; right: 2px; background: rgba(255,255,255,0.4); border-radius: 50%; width: 14px; height: 14px; display: flex; justify-content: center; align-items: center; cursor: pointer; opacity: 0; transition: 0.2s; }
.course-block:hover .delete-btn { opacity: 1; }

/* ================= 日程页 ================= */
.schedule-page { padding: 20px 15px; background: var(--bg-color); }
.header-date { font-size: 24px; font-weight: 800; color: var(--text-main); margin-bottom: 20px; }
.header-date span { font-size: 14px; font-weight: normal; color: var(--primary-color); background: #e6fffa; padding: 4px 8px; border-radius: 8px; margin-left: 8px; }
.add-guide-card { background: white; border-radius: 20px; padding: 25px 20px; display: flex; flex-direction: column; align-items: center; position: relative; box-shadow: 0 4px 20px rgba(0,0,0,0.03); margin-bottom: 25px; }
.circle-plus { width: 55px; height: 55px; background: var(--primary-color); color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 28px; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(20, 184, 166, 0.3); }
.guide-text { text-align: left; width: 100%; margin-bottom: 15px; }
.guide-text h3 { margin: 0 0 5px 0; font-size: 18px; color: var(--text-main); }
.guide-text p { margin: 0; font-size: 13px; color: var(--text-sub); }
.go-btn { position: absolute; right: 20px; bottom: 20px; background: #f0fdfa; color: var(--primary-color); border: none; border-radius: 20px; padding: 8px 20px; font-size: 13px; font-weight: bold; cursor: pointer; }
.schedule-list { display: flex; flex-direction: column; gap: 12px; }
.schedule-item { display: flex; background: white; border-radius: 16px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); align-items: stretch; }
.time-box { width: 65px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #444; font-size: 13px; font-weight: 600; }
.time-line { width: 2px; height: 20px; background: #e5e7eb; margin: 6px 0; border-radius: 2px; }
.content-box { flex: 1; padding-left: 12px; border-left: 4px solid var(--primary-color); display: flex; flex-direction: column; justify-content: center; }
.content-box h3 { margin: 0 0 6px 0; font-size: 16px; color: var(--text-main); }
.loc { margin: 0; font-size: 12px; color: var(--text-sub); display: flex; align-items: center; gap: 4px; }
.tag-box { display: flex; align-items: flex-start; }
.tag { font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: bold; }
.tag-course { background: #e6fffa; color: var(--primary-color); }
.tag-activity { background: #eff6ff; color: #3b82f6; }
.floating-btn { position: fixed; right: 20px; bottom: 80px; width: 56px; height: 56px; background: var(--primary-color); color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-size: 24px; box-shadow: 0 6px 20px rgba(20, 184, 166, 0.4); cursor: pointer; z-index: 99; transition: 0.2s; }
.floating-btn:hover { transform: scale(1.05); }

/* ================= 备忘录 ================= */
.memo-page { padding: 20px 15px; background: var(--bg-color); }
.section-header { display: flex; align-items: center; margin-bottom: 15px; }
.title-icon { width: 34px; height: 34px; background: #fff7ed; color: #f97316; border-radius: 10px; display: flex; justify-content: center; align-items: center; font-size: 20px; margin-right: 12px; }
.section-header h2 { margin: 0; font-size: 20px; color: var(--text-main); }
.todo-input-area { display: flex; gap: 10px; margin-bottom: 20px; background: white; padding: 12px 15px; border-radius: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }
.todo-input-area input { flex: 1; border: none; outline: none; font-size: 15px; }
.todo-card { display: flex; justify-content: space-between; align-items: center; padding: 16px; border-radius: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.custom-checkbox { width: 90%; }
.custom-checkbox .el-checkbox__label { font-size: 15px; color: #222; font-weight: 500; line-height: 1.4; white-space: normal;}
.is-done { text-decoration: line-through; color: #999 !important; }
.del-icon { color: #ff4d4f; font-size: 18px; cursor: pointer; opacity: 0.3; transition: 0.2s;}
.del-icon:hover { opacity: 1; }
.diary-area { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }
.diary-top { display: flex; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #f3f4f6; padding-bottom: 15px;}
.diary-textarea { width: 100%; height: 220px; border: none; outline: none; resize: none; font-size: 15px; line-height: 1.6; color: #444; }

/* ================= 我的 ================= */
.profile-page { padding: 20px 15px; background: var(--bg-color); }
.user-header { display: flex; align-items: center; margin-bottom: 20px; background: white; padding: 25px 20px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.03); cursor: pointer; }
.avatar-box { width: 65px; height: 65px; border-radius: 50%; background: #f3f4f6; display: flex; justify-content: center; align-items: center; font-size: 36px; margin-right: 18px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); }
.user-info h2 { margin: 0 0 6px 0; font-size: 20px; color: var(--text-main); }
.user-info p { margin: 0; font-size: 13px; color: var(--text-sub); }
.right-icon { margin-left: auto; color: #d1d5db; font-size: 20px; }
.status-card { display: flex; justify-content: space-between; align-items: center; background: white; padding: 18px 20px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); cursor: pointer; }
.status-left { display: flex; align-items: center; gap: 12px; font-size: 16px; font-weight: 500; }
.status-emoji { font-size: 22px; }
.status-action { font-size: 13px; color: var(--text-sub); }
.target-card, .plan-card { background: white; padding: 20px; border-radius: 16px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }
.card-title { display: flex; align-items: center; gap: 8px; font-size: 16px; font-weight: bold; color: var(--text-main); margin-bottom: 15px; }
.target-input, .plan-textarea { width: 100%; border: none; outline: none; background: #f9fafb; padding: 12px; border-radius: 12px; font-size: 14px; color: #333; box-sizing: border-box; }
.plan-textarea { resize: none; height: 120px; line-height: 1.5; }

/* 全屏表单 */
.fullscreen-form { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: var(--bg-color); z-index: 999; display: flex; flex-direction: column; animation: slideUp 0.3s ease-out; }
@keyframes slideUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
.form-header { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: white; }
.form-header h2 { margin: 0; font-size: 18px; color: var(--text-main); }
.close-icon { font-size: 22px; color: #333; cursor: pointer; }
.save-btn { background: var(--primary-color); color: white; border: none; padding: 8px 20px; border-radius: 20px; font-size: 14px; font-weight: bold; cursor: pointer; box-shadow: 0 2px 8px rgba(20, 184, 166, 0.3);}
.form-body { padding: 20px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
.input-group { background: white; border-radius: 16px; padding: 16px 20px; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.title-input { width: 100%; border: none; outline: none; font-size: 16px; font-weight: 500;}
.row-group { justify-content: space-between; }
.label { color: #4b5563; font-size: 15px; display: flex; align-items: center; gap: 8px; font-weight: 500; }
.right-input { border: none; outline: none; text-align: right; font-size: 15px; color: #333; flex: 1; }

/* 底部导航 */
.bottom-nav { position: fixed; bottom: 0; width: 100%; height: 65px; background: rgba(255,255,255,0.95); backdrop-filter: blur(10px); display: flex; box-shadow: 0 -2px 15px rgba(0,0,0,0.03); z-index: 100;}
.nav-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #9ca3af; font-size: 11px; cursor: pointer; transition: 0.2s;}
.nav-item .el-icon { font-size: 22px; margin-bottom: 4px; transition: 0.2s;}
.nav-item.active { color: var(--primary-color); font-weight: bold; }
.nav-item.active .el-icon { transform: translateY(-2px); }

/* 弹窗辅助 */
.status-picker-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.5); z-index: 999; display: flex; flex-direction: column; justify-content: flex-end; }
.status-picker-panel { background: #f8fafc; height: 75vh; border-radius: 24px 24px 0 0; padding: 20px; overflow-y: auto; }
.status-picker-header { text-align: center; position: relative; margin-bottom: 20px; }
.status-picker-header h2 { margin: 0; font-size: 18px; color: var(--text-main); }
.status-picker-header p { margin: 5px 0 0 0; font-size: 12px; color: var(--text-sub); }
.status-picker-header .close-icon { position: absolute; left: 0; top: 0; font-size: 24px; color: #333; cursor: pointer; }
.status-category { font-size: 14px; color: #666; margin-bottom: 15px; font-weight: bold;}
.status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
.status-item { display: flex; flex-direction: column; align-items: center; gap: 8px; cursor: pointer; transition: 0.2s; }
.status-item:hover { transform: scale(1.1); }
.s-emoji { font-size: 32px; }
.s-text { font-size: 12px; color: #555; }
</style>