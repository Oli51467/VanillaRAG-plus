<template>
    <div class="chat-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <h3>对话历史</h3>
                <el-button type="primary" size="small" class="new-chat-btn"
                    @click="createNewConversation">新对话</el-button>
            </div>
            <div class="conversation-list" v-loading="loadingConversations">
                <div v-if="conversations.length === 0" class="empty-list">
                    <p>暂无对话历史</p>
                </div>
                <div v-for="conv in conversations" :key="conv.id" class="conversation-item"
                    :class="{ active: currentConversationId === conv.id }">
                    <div class="conversation-item-content" @click="switchConversation(conv.id)">
                        <div class="conversation-title">
                            <el-icon class="conversation-icon">
                                <ChatDotRound />
                            </el-icon>
                            <span>{{ conv.title }}</span>
                        </div>
                        <div class="conversation-right">
                            <div class="conversation-time">{{ formatDate(conv.created_at) }}</div>
                            <div class="conversation-actions">
                                <el-dropdown trigger="click" @command="handleConversationAction($event, conv)"
                                    placement="right-start" popper-class="conversation-dropdown">
                                    <el-icon class="more-icon">
                                        <more />
                                    </el-icon>
                                    <template #dropdown>
                                        <el-dropdown-menu>
                                            <el-dropdown-item command="edit">
                                                <el-icon>
                                                    <Edit />
                                                </el-icon>
                                                <span>重命名</span>
                                            </el-dropdown-item>
                                            <el-dropdown-item command="delete" divided>
                                                <el-icon style="color: var(--danger-color);">
                                                    <Delete />
                                                </el-icon>
                                                <span style="color: var(--danger-color);">删除</span>
                                            </el-dropdown-item>
                                        </el-dropdown-menu>
                                    </template>
                                </el-dropdown>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 编辑对话标题对话框 -->
        <el-dialog v-model="editDialogVisible" title="重命名对话" width="30%" center destroy-on-close
            custom-class="rename-dialog">
            <div class="custom-input-container">
                <input v-model="editingTitle" placeholder="请输入对话标题" class="custom-input" />
            </div>
            <template #footer>
                <span class="dialog-footer">
                    <el-button @click="editDialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="saveConversationTitle">确定</el-button>
                </span>
            </template>
        </el-dialog>

        <div class="chat-wrapper">

            <div class="chat-content">
                <div class="chat-messages" ref="messagesContainer">
                    <!-- 欢迎消息 -->
                    <div class="message-row system">
                        <div class="message-avatar">
                            <el-avatar :size="36" :icon="ChatSquare" />
                        </div>
                        <div class="message-content">
                            <p>👋 您好！我是您的文档助手，可以回答关于您上传文档的问题。</p>
                            <p>请先在"文档管理"页面上传文档，然后在这里提问。</p>
                        </div>
                    </div>

                    <!-- 消息列表 -->
                    <div v-for="(message, index) in messages" :key="index" class="message-row" :class="message.role">
                        <template v-if="message.role === 'assistant'">
                            <div class="message-avatar">
                                <el-avatar :size="36" :icon="ChatSquare" />
                            </div>
                            <div class="message-content markdown-body" v-html="formatMessage(message.content)">
                            </div>
                        </template>
                        <template v-else>
                            <div class="message-content">
                                <p v-html="formatMessage(message.content)"></p>
                            </div>
                            <div class="message-avatar">
                                <el-avatar :size="36" :icon="User" />
                            </div>
                        </template>
                    </div>

                    <!-- 加载中状态 -->
                    <div v-if="loading" class="message-row assistant">
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
                            <div class="model-option" :class="{ active: selectedModel === 'deepseek-chat' }"
                                @click="selectModel('deepseek-chat')">
                                <span>DeepSeek</span>
                            </div>
                            <div class="model-option" :class="{ active: selectedModel === 'Qwen/QwQ-32B' }"
                                @click="selectModel('Qwen/QwQ-32B')">
                                <span>Qwen</span>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, ChatSquare, Position, Loading, More, Edit, Delete, ChatDotRound } from '@element-plus/icons-vue'
import axios from 'axios'
import MarkdownIt from 'markdown-it'

// 初始化 markdown-it 实例
const md = new MarkdownIt({
    html: true,        // 启用 HTML 标签
    breaks: true,      // 将换行符转换为 <br>
    linkify: true,     // 将 URL 转换为链接
    typographer: true  // 启用一些语言中性的替换和引号
})

// 后端API基础URL
const RAG_API_BASE_URL = 'http://localhost:8080/api/v1/rag/'
const CONVERSATION_API_BASE_URL = 'http://localhost:8080/api/v1/conversations/'

export default {
    name: 'Chat',
    components: {
        User,
        ChatSquare,
        Position,
        Loading,
        More,
        Edit,
        Delete,
        ChatDotRound
    },
    setup() {
        const userInput = ref('')
        const messages = ref([])
        const loading = ref(false)
        const messagesContainer = ref(null)
        const inputRef = ref(null)
        const selectedModel = ref('Qwen/QwQ-32B') // 默认使用Qwen模型
        const currentConversationId = ref(localStorage.getItem('currentConversationId') || null)
        const conversations = ref([])
        const loadingConversations = ref(false)
        const editDialogVisible = ref(false)
        const editingTitle = ref('')
        const editingConversationId = ref(null)

        // 选择模型
        const selectModel = (modelName) => {
            selectedModel.value = modelName
        }

        // 加载对话列表
        const loadConversations = async () => {
            loadingConversations.value = true
            try {
                const response = await axios.get(CONVERSATION_API_BASE_URL)
                conversations.value = response.data.conversations || []
            } catch (error) {
                console.error('获取对话列表失败:', error)
                ElMessage({
                    message: '获取对话列表失败',
                    type: 'error',
                    duration: 3000
                })
            } finally {
                loadingConversations.value = false
            }
        }

        // 加载对话消息
        const loadMessages = async (conversationId) => {
            if (!conversationId) return

            loading.value = true
            try {
                const response = await axios.get(`${CONVERSATION_API_BASE_URL}${conversationId}/messages`)

                // 清空现有消息
                messages.value = []

                // 添加消息
                const messageList = response.data.messages || []
                if (messageList.length === 0) {
                    // 如果没有消息，添加一个系统欢迎消息
                    messages.value.push({
                        role: 'system',
                        content: '👋 您好！我是您的文档助手，可以回答关于您上传文档的问题。\n请先在"文档管理"页面上传文档，然后在这里提问。'
                    })
                } else {
                    messageList.forEach(msg => {
                        messages.value.push({
                            role: msg.role,
                            content: msg.content
                        })
                    })
                }

                // 滚动到底部
                await nextTick()
                scrollToBottom()
            } catch (error) {
                console.error('获取消息失败:', error)
                ElMessage({
                    message: '获取消息失败',
                    type: 'error',
                    duration: 3000
                })
            } finally {
                loading.value = false
            }
        }

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

            try {
                // 调用后端RAG聊天接口
                const response = await axios.post(`${RAG_API_BASE_URL}chat`, {
                    query: message,
                    model: selectedModel.value,
                    top_k: 5,
                    conversation_id: currentConversationId.value
                })

                // 获取大模型的回复
                const modelResponse = response.data.response

                // 更新当前对话ID
                currentConversationId.value = response.data.conversation_id

                // 保存到本地存储
                localStorage.setItem('currentConversationId', currentConversationId.value)

                // 添加助手回复
                messages.value.push({
                    role: 'assistant',
                    content: modelResponse
                })

                // 刷新对话列表
                loadConversations()
            } catch (error) {
                console.error('调用RAG接口失败:', error)

                // 添加错误消息
                messages.value.push({
                    role: 'assistant',
                    content: '出错啦。'
                })

                ElMessage({
                    message: '获取回答失败，请稍后再试',
                    type: 'error',
                    duration: 3000
                })
            } finally {
                // 取消加载状态
                loading.value = false

                // 滚动到底部
                nextTick(() => {
                    scrollToBottom()
                })
            }
        }

        // 滚动到底部
        const scrollToBottom = () => {
            if (messagesContainer.value) {
                messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
            }
        }

        // 格式化消息内容（支持完整的Markdown）
        const formatMessage = (content) => {
            if (!content) return ''

            // 使用 markdown-it 处理 Markdown 格式
            return md.render(content)
        }

        // 创建新对话
        const createNewConversation = () => {
            // 清空当前对话ID
            currentConversationId.value = null
            localStorage.removeItem('currentConversationId')

            // 清空消息
            messages.value = []
        }

        // 切换对话
        const switchConversation = async (conversationId) => {
            if (currentConversationId.value === conversationId) return

            currentConversationId.value = conversationId
            localStorage.setItem('currentConversationId', conversationId)

            // 加载对话消息
            await loadMessages(conversationId)
        }

        // 处理对话操作
        const handleConversationAction = (command, conversation) => {
            if (command === 'edit') {
                // 打开编辑对话框
                editingTitle.value = conversation.title
                editingConversationId.value = conversation.id
                editDialogVisible.value = true
            } else if (command === 'delete') {
                // 确认删除
                ElMessageBox.confirm(
                    '确定要删除这个对话吗？此操作不可恢复。',
                    '删除对话',
                    {
                        confirmButtonText: '删除',
                        cancelButtonText: '取消',
                        type: 'warning',
                    }
                ).then(() => {
                    deleteConversation(conversation.id)
                }).catch(() => {
                    // 取消删除
                })
            }
        }

        // 保存对话标题
        const saveConversationTitle = async () => {
            if (!editingTitle.value.trim()) {
                ElMessage({
                    message: '标题不能为空',
                    type: 'warning',
                    duration: 3000
                })
                return
            }

            try {
                // 获取当前对话
                const conversation = conversations.value.find(c => c.id === editingConversationId.value)
                if (!conversation) {
                    throw new Error('对话不存在')
                }

                // 直接更新对话标题
                await axios.post(`${CONVERSATION_API_BASE_URL}${editingConversationId.value}`, {
                    title: editingTitle.value
                })

                ElMessage({
                    message: '标题已更新',
                    type: 'success',
                    duration: 3000
                })

                // 关闭对话框
                editDialogVisible.value = false

                // 刷新对话列表
                await loadConversations()
            } catch (error) {
                console.error('更新标题失败:', error)
                ElMessage({
                    message: '更新标题失败',
                    type: 'error',
                    duration: 3000
                })
            }
        }

        // 删除对话
        const deleteConversation = async (conversationId) => {
            try {
                await axios.delete(`${CONVERSATION_API_BASE_URL}${conversationId}`)

                ElMessage({
                    message: '对话已删除',
                    type: 'success',
                    duration: 3000
                })

                // 如果删除的是当前对话，清空当前对话ID
                if (currentConversationId.value === conversationId) {
                    currentConversationId.value = null
                    localStorage.removeItem('currentConversationId')
                    messages.value = []
                }

                // 刷新对话列表
                await loadConversations()
            } catch (error) {
                console.error('删除对话失败:', error)
                ElMessage({
                    message: '删除对话失败',
                    type: 'error',
                    duration: 3000
                })
            }
        }

        onMounted(async () => {
            // 聚焦输入框
            if (inputRef.value && inputRef.value.input) {
                inputRef.value.input.focus()
            }

            // 加载对话列表
            await loadConversations()

            // 如果有当前对话ID，加载对话消息
            if (currentConversationId.value) {
                await loadMessages(currentConversationId.value)
            }
        })

        return {
            userInput,
            messages,
            loading,
            messagesContainer,
            inputRef,
            selectedModel,
            selectModel,
            sendMessage,
            formatMessage,
            formatDate: (dateStr) => {
                if (!dateStr) return ''
                const date = new Date(dateStr)
                return date.toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                })
            },
            currentConversationId,
            conversations,
            loadingConversations,
            createNewConversation,
            switchConversation,
            handleConversationAction,
            deleteConversation,
            editDialogVisible,
            editingTitle,
            editingConversationId,
            saveConversationTitle,
            User,
            ChatSquare,
            Position,
            Loading,
            More,
            Edit,
            Delete,
            ChatDotRound
        }
    }
}
</script>

<style scoped>
.chat-container {
    height: 100%;
    display: flex;
    justify-content: flex-start;
}

.sidebar {
    width: 350px;
    height: 100%;
    background-color: var(--secondary-bg);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
}

.sidebar-header {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.sidebar-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
}

.new-chat-btn {
    font-size: 13px;
    padding: 6px 12px;
    height: auto;
}

.conversation-list {
    flex: 1;
    overflow-y: auto;
    padding: 0;
}

.empty-list {
    padding: 20px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 15px;
}

.conversation-item {
    padding: 14px 16px;
    margin-bottom: 2px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    box-sizing: border-box;
    border-radius: 0;
}

.conversation-item:hover {
    background-color: var(--hover-bg);
}

.conversation-item.active {
    background-color: var(--accent-light);
    border-left: 3px solid var(--accent-color);
    padding-left: 13px;
}

.conversation-item-content {
    display: flex;
    flex: 1;
    align-items: center;
    justify-content: space-between;
    overflow: hidden;
    width: 100%;
    min-width: 0;
}

.conversation-title {
    font-size: 15px;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 180px;
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 12px;
}

.conversation-icon {
    font-size: 18px;
    color: var(--text-secondary);
    flex-shrink: 0;
    margin-left: 0;
}

.conversation-title span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
}

.conversation-right {
    display: flex;
    align-items: center;
    white-space: nowrap;
    flex-shrink: 0;
    margin-left: 12px;
}

.conversation-time {
    font-size: 13px;
    color: var(--text-secondary);
    white-space: nowrap;
}

.conversation-actions {
    display: flex;
    align-items: center;
    margin-left: 8px;
}

.more-icon {
    cursor: pointer;
    margin-left: 8px;
    font-size: 18px;
    opacity: 0.7;
    transition: opacity 0.2s ease;
}

.more-icon:hover {
    opacity: 1;
}

.chat-wrapper {
    display: flex;
    flex-direction: column;
    width: calc(80% - 20px);
    height: 100%;
    padding: 0 16px;
    align-items: center;
}

.chat-header {
    margin-bottom: 20px;
    text-align: center;
    width: 100%;
    max-width: 800px;
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
    height: calc(100% - 220px);
    /* 减少高度，为输入框留出空间 */
    position: relative;
    border-radius: 12px;
    background-color: var(--secondary-bg);
    margin-bottom: 20px;
    /* 添加底部间距 */
    width: 100%;
    max-width: 800px;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    width: 100%;
}

.message-row {
    display: flex;
    width: 100%;
    animation: fadeIn 0.3s ease;
    gap: 16px;
}

.message-row.assistant {
    justify-content: flex-start;
}

.message-row.user {
    justify-content: flex-end;
}

.message-row.system {
    justify-content: flex-start;
}

.message-avatar {
    flex-shrink: 0;
    align-self: flex-start;
}

.message-content {
    background-color: var(--secondary-bg);
    padding: 10px 12px;
    /* 统一上下内边距 */
    border-radius: 12px;
    color: var(--text-primary);
    line-height: 1.5;
    /* 稍微增加基础行高 */
    font-size: 15px;
    max-width: calc(100% - 80px);
    word-break: break-word;
    overflow-wrap: break-word;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    margin-bottom: 0;
    /* 移除底部外边距 */
}

.message-content p {
    margin: 0 0 4px 0;
    /* 减小段落间距 */
}

.message-content p:last-child {
    margin-bottom: 0;
}

.message-row.user .message-content {
    background-color: var(--accent-light);
    color: var(--text-primary);
    border: 1px solid var(--accent-color);
}

.message-row.system .message-content {
    background-color: var(--hover-bg);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
}

.chat-input-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 12px 16px;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    width: 98%;
    max-width: 800px;
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
    padding: 10px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 4px 0;
    /* 统一上下外边距 */
    border: 1px solid var(--border-color);
}

:deep(pre code) {
    background-color: transparent;
    padding: 0;
    white-space: pre;
}

/* Markdown 样式增强 */
:deep(.message-content) {
    overflow-x: auto;
    padding: 10px 12px;
    /* 增加顶部内边距 */
}

:deep(.message-content h1),
:deep(.message-content h2),
:deep(.message-content h3),
:deep(.message-content h4),
:deep(.message-content h5),
:deep(.message-content h6) {
    margin-top: 10px;
    /* 减小顶部外边距 */
    margin-bottom: 6px;
    /* 减小底部外边距 */
    font-weight: 600;
    line-height: 1.3;
    /* 稍微增加行高 */
    color: var(--text-primary);
}

:deep(.message-content h1) {
    font-size: 22px;
    margin-top: 0;
}

:deep(.message-content h2) {
    font-size: 18px;
}

:deep(.message-content h3) {
    font-size: 16px;
}

:deep(.message-content h4) {
    font-size: 15px;
}

:deep(.message-content h5) {
    font-size: 14px;
}

:deep(.message-content h6) {
    font-size: 13px;
}

:deep(.message-content p) {
    margin-bottom: 4px;
    /* 减小段落底部外边距 */
    margin-top: 4px;
    /* 增加段落顶部外边距，使上下一致 */
    line-height: 1.55;
    /* 增加行高 */
}

:deep(.message-content ul),
:deep(.message-content ol) {
    padding-left: 20px;
    margin-bottom: 4px;
    /* 减小列表底部外边距 */
    margin-top: 4px;
    /* 保持列表顶部外边距一致 */
}

:deep(.message-content li) {
    margin-bottom: 2px;
    /* 保持列表项底部外边距 */
    line-height: 1.55;
    /* 增加行高与段落一致 */
}

:deep(.message-content blockquote) {
    padding: 0 12px;
    /* 保持内边距 */
    margin: 4px 0;
    /* 上下外边距一致 */
    border-left: 4px solid var(--border-color);
    color: var(--text-secondary);
}

:deep(.message-content img) {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 4px 0;
    /* 统一上下外边距 */
}

:deep(.message-content a) {
    color: var(--accent-color);
    text-decoration: none;
}

:deep(.message-content a:hover) {
    text-decoration: underline;
}

:deep(.message-content table) {
    border-collapse: collapse;
    width: 100%;
    margin: 4px 0;
    /* 统一上下外边距 */
    overflow-x: auto;
    display: block;
}

:deep(.message-content th),
:deep(.message-content td) {
    border: 1px solid var(--border-color);
    padding: 6px 10px;
    /* 保持内边距 */
    text-align: left;
}

:deep(.message-content th) {
    background-color: var(--hover-bg);
    font-weight: 600;
}

:deep(.message-content tr:nth-child(even)) {
    background-color: var(--secondary-bg);
}

:deep(.message-content hr) {
    height: 1px;
    background-color: var(--border-color);
    border: none;
    margin: 8px 0;
    /* 统一上下外边距 */
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

:deep(.el-dropdown-menu__item) {
    display: flex;
    align-items: center;
    gap: 8px;
}

:deep(.el-dropdown-menu__item .el-icon) {
    margin-right: 0;
}

:deep(.conversation-dropdown) {
    margin-left: 4px !important;
    margin-top: 0 !important;
}

/* 自定义对话框样式 */
:deep(.rename-dialog) {
    border-radius: 12px;
    overflow: hidden;
}

:deep(.rename-dialog .el-dialog__header) {
    margin: 0;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
}

:deep(.rename-dialog .el-dialog__title) {
    font-weight: 600;
    font-size: 16px;
    color: var(--text-primary);
}

:deep(.rename-dialog .el-dialog__body) {
    padding: 20px;
}

:deep(.rename-dialog .el-dialog__footer) {
    padding: 12px 20px;
    border-top: 1px solid var(--border-color);
}

/* 自定义输入框 */
.custom-input-container {
    width: 100%;
    margin-bottom: 10px;
}

.custom-input {
    width: 100%;
    height: 40px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0 12px;
    background-color: var(--card-bg);
    color: var(--text-primary);
    font-size: 14px;
    transition: all 0.2s ease;
    box-sizing: border-box;
}

.custom-input:focus {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
    outline: none;
}
</style>