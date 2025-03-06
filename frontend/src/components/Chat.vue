<template>
  <div class="chat-container">
    <el-card class="chat-card">
      <template #header>
        <div class="card-header">
          <span>聊天</span>
        </div>
      </template>
      <div class="chat-content">
        <el-empty description="聊天功能将在下一轮对话中实现"></el-empty>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'Chat',
  setup() {
    return {}
  }
}
</script>

<style scoped>
.chat-container {
  height: 100%;
}

.chat-card {
  height: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  font-weight: bold;
}

.chat-content {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}
</style> 