<template>
  <div class="app-container">
    <el-container>
      <el-header height="64px">
        <div class="header-content">
          <div class="nav-menu">
            <div class="nav-item" :class="{ active: activeIndex === '2' }" @click="handleSelect('2')">
              <el-icon><chat-dot-round /></el-icon>
              <span>开启对话</span>
            </div>
            <div class="nav-item" :class="{ active: activeIndex === '1' }" @click="handleSelect('1')">
              <el-icon>
                <document />
              </el-icon>
              <span>文档管理</span>
            </div>
          </div>
        </div>
      </el-header>
      <el-main>
        <transition name="fade" mode="out-in">
          <document-management v-if="activeIndex === '1'" />
          <chat v-else-if="activeIndex === '2'" />
        </transition>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref } from 'vue'
import { Document, ChatDotRound } from '@element-plus/icons-vue'
import DocumentManagement from './components/DocumentManagement.vue'
import Chat from './components/Chat.vue'

export default {
  name: 'App',
  components: {
    DocumentManagement,
    Chat,
    Document,
    ChatDotRound
  },
  setup() {
    const activeIndex = ref('2')

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
:root {
  --primary-bg: #ffffff;
  --secondary-bg: #f8fafc;
  --card-bg: #ffffff;
  --hover-bg: #f1f5f9;
  --border-color: #e2e8f0;

  --accent-color: #6366f1;
  --accent-light: rgba(99, 102, 241, 0.1);

  --text-primary: #334155;
  --text-secondary: #64748b;

  --success-color: #10b981;
  --danger-color: #ef4444;
  --warning-color: #f59e0b;

  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

body {
  margin: 0;
  padding: 0;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: var(--primary-bg);
  color: var(--text-primary);
}

.app-container {
  height: 100vh;
  width: 100%;
}

.el-container {
  height: 100%;
}

.el-header {
  background-color: var(--primary-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 0 24px;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
}

.nav-menu {
  display: flex;
  gap: 32px;
  justify-content: center;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-secondary);
}

.nav-item:hover {
  background-color: var(--hover-bg);
  color: var(--text-primary);
}

.nav-item.active {
  color: var(--accent-color);
  font-weight: 500;
  background-color: var(--accent-light);
}

.el-main {
  background-color: var(--secondary-bg);
  padding: 24px;
  overflow-y: auto;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 覆盖Element Plus默认样式 */
.el-button {
  border-radius: 8px;
}

.el-button--primary {
  background-color: var(--accent-color);
  border-color: var(--accent-color);
}

.el-button--primary:hover,
.el-button--primary:focus {
  background-color: #6366f1;
  border-color: #6366f1;
}

.el-card {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.3s ease;
}

.el-card:hover {
  box-shadow: var(--shadow-md);
}

.el-card__header {
  border-bottom: 1px solid var(--border-color);
  padding: 16px 20px;
  background-color: var(--secondary-bg);
}

.el-table {
  background-color: var(--card-bg);
  color: var(--text-primary);
}

.el-table th {
  background-color: var(--secondary-bg);
  color: var(--text-secondary);
  font-weight: 600;
}

.el-table td,
.el-table th.is-leaf {
  border-bottom: 1px solid var(--border-color);
}

.el-table--enable-row-hover .el-table__body tr:hover>td.el-table__cell {
  background-color: var(--hover-bg);
}

.el-input__inner {
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.el-input__inner:focus {
  border-color: var(--accent-color);
}

.el-message-box {
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
}

.el-message-box__title {
  color: var(--text-primary);
}

.el-message-box__message {
  color: var(--text-secondary);
}

.el-message-box__btns .el-button {
  background-color: var(--secondary-bg);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.el-message-box__btns .el-button--primary {
  background-color: var(--accent-color);
  border-color: var(--accent-color);
}
</style>