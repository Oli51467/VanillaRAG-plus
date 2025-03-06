<template>
    <div class="chat-container">
        <div class="chat-wrapper">
            <div class="chat-header">
                <h2>智能文档助手</h2>
                <p class="chat-description">与您的文档进行对话，获取智能解答</p>
            </div>

            <div class="chat-content">
                <div class="chat-messages" ref="messagesContainer">
                    <!-- 欢迎消息 -->
                    <div class="message system">
                        <div class="message-content">
                            <p>👋 您好！我是您的文档助手，可以回答关于您上传文档的问题。</p>
                            <p>请先在"文档管理"页面上传文档，然后在这里提问。</p>
                        </div>
                    </div>

                    <!-- 消息列表 -->
                    <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
                        <div class="message-avatar">
                            <el-avatar :size="36" :icon="message.role === 'user' ? User : ChatSquare" />
                        </div>
                        <div class="message-content">
                            <p v-html="formatMessage(message.content)"></p>
                        </div>
                    </div>

                    <!-- 加载中状态 -->
                    <div v-if="loading" class="message assistant loading">
                        <div class="message-avatar">
                            <el-avatar :size="36" :icon="ChatSquare" />
                        </div>
                        <div class="message-content">
                            <div class="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="chat-input-container">
                    <div class="input-wrapper">
                        <el-input v-model="userInput" type="textarea" :rows="1" placeholder="输入您的问题..." resize="none"
                            :disabled="loading" @keydown.enter.prevent="sendMessage" ref="inputRef" autosize />
                    </div>
                    <div class="bottom-controls">
                        <div class="model-selector">
                            <div class="model-option active">
                                <span>deepseek</span>
                            </div>
                            <div class="model-option">
                                <span>Qwen2.5</span>
                            </div>
                        </div>
                        <el-button type="primary" :icon="loading ? Loading : Position"
                            :disabled="loading || !userInput.trim()" @click="sendMessage" circle />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { User, ChatSquare, Position, Loading } from '@element-plus/icons-vue'

export default {
    name: 'Chat',
    components: {
        User,
        ChatSquare,
        Position,
        Loading
    },
    setup() {
        const userInput = ref('')
        const messages = ref([])
        const loading = ref(false)
        const messagesContainer = ref(null)
        const inputRef = ref(null)

        // 发送消息
        const sendMessage = async () => {
            const message = userInput.value.trim()
            if (!message || loading.value) return

            // 添加用户消息
            messages.value.push({
                role: 'user',
                content: message
            })

            // 清空输入框
            userInput.value = ''

            // 滚动到底部
            await nextTick()
            scrollToBottom()

            // 设置加载状态
            loading.value = true

            // 模拟API调用延迟
            setTimeout(() => {
                // 添加助手回复
                messages.value.push({
                    role: 'assistant',
                    content: '这是聊天功能的演示界面，实际的聊天功能将在下一轮对话中实现。您可以在"文档管理"页面上传和管理文档。'
                })

                // 取消加载状态
                loading.value = false

                // 滚动到底部
                nextTick(() => {
                    scrollToBottom()
                })
            }, 1000)
        }

        // 滚动到底部
        const scrollToBottom = () => {
            if (messagesContainer.value) {
                messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
            }
        }

        // 格式化消息内容（支持简单的Markdown）
        const formatMessage = (content) => {
            if (!content) return ''

            // 替换换行符为<br>
            let formatted = content.replace(/\n/g, '<br>')

            // 替换代码块
            formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')

            // 替换行内代码
            formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>')

            return formatted
        }

        onMounted(() => {
            // 聚焦输入框
            if (inputRef.value && inputRef.value.input) {
                inputRef.value.input.focus()
            }
        })

        return {
            userInput,
            messages,
            loading,
            messagesContainer,
            inputRef,
            sendMessage,
            formatMessage,
            User,
            ChatSquare,
            Position,
            Loading
        }
    }
}
</script>

<style scoped>
.chat-container {
    height: 100%;
    display: flex;
    justify-content: center;
}

.chat-wrapper {
    display: flex;
    flex-direction: column;
    width: 100%;
    max-width: 900px;
    height: 100%;
}

.chat-header {
    margin-bottom: 20px;
    text-align: center;
}

.chat-header h2 {
    font-size: 28px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: var(--text-primary);
}

.chat-description {
    font-size: 16px;
    color: var(--text-secondary);
    margin: 0;
}

.chat-content {
    display: flex;
    flex-direction: column;
    flex: 1;
    height: calc(100% - 100px);
    position: relative;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px 0;
    display: flex;
    flex-direction: column;
    gap: 24px;
    max-height: calc(100vh - 350px);
    padding-bottom: 80px;
}

.message {
    display: flex;
    gap: 16px;
    max-width: 100%;
    animation: fadeIn 0.3s ease;
}

.message-avatar {
    flex-shrink: 0;
}

.message-content {
    background-color: var(--secondary-bg);
    padding: 12px 16px;
    border-radius: 12px;
    color: var(--text-primary);
    line-height: 1.6;
    font-size: 15px;
    max-width: calc(100% - 60px);
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
}

.message-content p {
    margin: 0 0 8px 0;
}

.message-content p:last-child {
    margin-bottom: 0;
}

.message.user .message-content {
    background-color: var(--accent-light);
    color: var(--text-primary);
    border: 1px solid var(--accent-color);
}

.message.system .message-content {
    background-color: var(--hover-bg);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
    margin-left: 52px;
    margin-bottom: 16px;
}

.chat-input-container {
    margin-top: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 0;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    position: absolute;
    bottom: 20px;
    left: 0;
    right: 0;
    z-index: 10;
}

.chat-input-container:focus-within {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.input-wrapper {
    display: flex;
    width: 100%;
}

.bottom-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 8px;
}

.model-selector {
    display: flex;
    gap: 10px;
}

.model-option {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 5px 12px;
    border-radius: 12px;
    font-size: 13px;
    background-color: var(--hover-bg);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid var(--border-color);
}

.model-option.active {
    background-color: var(--accent-light);
    color: var(--accent-color);
    border-color: var(--accent-color);
    font-weight: 500;
}

:deep(.el-textarea__inner) {
    background-color: transparent;
    border: none;
    color: var(--text-primary);
    font-size: 15px;
    padding: 8px 0;
    max-height: 150px;
    line-height: 1.6;
    box-shadow: none !important;
    text-align: left;
}

:deep(.el-textarea__inner:focus) {
    box-shadow: none !important;
    outline: none !important;
}

:deep(.el-textarea .el-input__wrapper) {
    background-color: transparent;
    box-shadow: none !important;
    padding: 0;
}

:deep(.el-button.is-circle) {
    flex-shrink: 0;
}

/* 代码样式 */
:deep(code) {
    background-color: rgba(0, 0, 0, 0.05);
    padding: 2px 4px;
    border-radius: 4px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 14px;
    color: var(--accent-color);
}

:deep(pre) {
    background-color: rgba(0, 0, 0, 0.05);
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 8px 0;
    border: 1px solid var(--border-color);
}

:deep(pre code) {
    background-color: transparent;
    padding: 0;
    white-space: pre;
}

/* 打字指示器 */
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
}

.typing-indicator span {
    width: 8px;
    height: 8px;
    background-color: var(--text-secondary);
    border-radius: 50%;
    display: inline-block;
    animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
    animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {

    0%,
    80%,
    100% {
        transform: scale(0.6);
        opacity: 0.4;
    }

    40% {
        transform: scale(1);
        opacity: 1;
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>