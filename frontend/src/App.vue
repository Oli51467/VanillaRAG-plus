<template>
  <div class="app-container">
    <el-container>
      <el-header height="60px">
        <div class="header-content">
          <h1>文档管理系统</h1>
          <el-menu
            :default-active="activeIndex"
            mode="horizontal"
            @select="handleSelect"
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b">
            <el-menu-item index="1">文档管理</el-menu-item>
            <el-menu-item index="2">聊天</el-menu-item>
          </el-menu>
        </div>
      </el-header>
      <el-main>
        <document-management v-if="activeIndex === '1'" />
        <chat v-else-if="activeIndex === '2'" />
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref } from 'vue'
import DocumentManagement from './components/DocumentManagement.vue'
import Chat from './components/Chat.vue'

export default {
  name: 'App',
  components: {
    DocumentManagement,
    Chat
  },
  setup() {
    const activeIndex = ref('1')

    const handleSelect = (key) => {
      activeIndex.value = key
    }

    return {
      activeIndex,
      handleSelect
    }
  }
}
</script>

<style>
.app-container {
  height: 100%;
}

.el-container {
  height: 100%;
}

.el-header {
  background-color: #545c64;
  color: #fff;
  line-height: 60px;
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style> 