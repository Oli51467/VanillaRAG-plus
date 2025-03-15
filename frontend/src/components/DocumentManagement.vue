<template>
    <div class="document-management">
        <!-- 上传中遮罩层 -->
        <div v-if="uploading" class="upload-overlay">
            <div class="upload-progress-container">
                <el-progress :percentage="uploadProgress" :stroke-width="18" status="primary" show-text
                    :format="(percentage) => `上传中 ${percentage}%`" class="centered-progress"></el-progress>
                <p class="upload-status">文件 "{{ currentUploadFile.name || '文件' }}" 正在上传，请勿关闭窗口</p>
            </div>
        </div>

        <!-- 自定义删除确认对话框 -->
        <el-dialog v-model="deleteDialogVisible" custom-class="custom-delete-dialog" :show-close="false" width="450px"
            center align-center>
            <template #header>
                <div class="custom-dialog-header">
                    <h3>确定删除吗？</h3>
                </div>
            </template>
            <div class="custom-dialog-content">
                <p>您即将删除文档 "{{ currentDocument?.file_name || '' }}"。删除后将无法恢复，请确认您的操作。</p>
            </div>
            <template #footer>
                <div class="custom-dialog-footer">
                    <el-button class="cancel-btn" @click="deleteDialogVisible = false">取消</el-button>
                    <el-button class="confirm-btn" @click="confirmDelete">我确定</el-button>
                </div>
            </template>
        </el-dialog>

        <!-- 上传区域和配置区域 - 减小高度 -->
        <div class="upload-config-row">
            <!-- 左侧上传区域 -->
            <el-card class="upload-card">
                <div class="upload-content">
                    <el-upload class="upload-area" drag action="http://localhost:8080/api/v1/documents/upload"
                        :on-success="handleUploadSuccess" :on-error="handleUploadError" :before-upload="beforeUpload"
                        :on-progress="handleUploadProgress" :show-file-list="false" :disabled="uploading">
                        <div class="upload-inner compact">
                            <el-icon class="upload-icon"><upload-filled /></el-icon>
                            <div class="upload-text">
                                <h3>拖拽文件到此处或点击上传</h3>
                                <p>支持 PDF、TXT、DOCX 格式文件</p>
                            </div>
                        </div>
                    </el-upload>
                </div>
            </el-card>

            <!-- 右侧配置区域 -->
            <el-card class="config-card">
                <template #header>
                    <div class="config-header">
                        <h3>分段与检索设置</h3>
                    </div>
                </template>
                <div class="config-content">
                    <div class="config-row">
                        <div class="config-item half">
                            <span class="config-label bold-label">分段最大长度</span>
                            <el-input-number v-model="chunkSize" :min="100" :max="2000" :step="50" :disabled="uploading"
                                controls-position="right">
                                <template #suffix>
                                    <span class="unit-text">tokens</span>
                                </template>
                            </el-input-number>
                        </div>
                        <div class="config-item half">
                            <span class="config-label bold-label">分段重叠长度</span>
                            <el-input-number v-model="overlapSize" :min="0" :max="1000" :step="10" :disabled="uploading"
                                controls-position="right">
                                <template #suffix>
                                    <span class="unit-text">tokens</span>
                                </template>
                            </el-input-number>
                        </div>
                    </div>
                    <div class="config-row">
                        <div class="config-item half">
                            <span class="config-label bold-label">Embedding 模型</span>
                            <el-select v-model="embeddingModel" placeholder="请选择模型" :disabled="uploading"
                                style="width: 100%;">
                                <el-option v-for="item in embeddingModels" :key="item.value" :label="item.label"
                                    :value="item.value" />
                            </el-select>
                        </div>
                        <div class="config-item half">
                            <span class="config-label bold-label">检索相似度 TopK</span>
                            <el-slider v-model="topK" :min="1" :max="10" :step="1" :disabled="uploading"
                                :format-tooltip="(val) => `${val}`">
                            </el-slider>
                        </div>
                    </div>
                </div>
            </el-card>
        </div>

        <!-- 文档列表 -->
        <el-card class="document-list-card">
            <div class="card-header">
                <div class="header-left">
                    <h3>我的文档</h3>
                    <el-tag v-if="documents.length > 0" type="info" round>{{ documents.length }} 个文件</el-tag>
                </div>
                <el-button type="primary" @click="fetchDocuments" :icon="Refresh" :disabled="uploading">刷新</el-button>
            </div>

            <div class="document-list" v-loading="loading">
                <div class="document-grid">
                    <div v-for="doc in documents" :key="doc.id" class="document-card" @click="showDeleteConfirm(doc)">
                        <div class="document-card-content">
                            <el-icon class="document-icon" :class="getIconColorClass(doc.file_type)">
                                <document />
                            </el-icon>
                            <div class="document-details">
                                <div class="document-name">{{ doc.file_name }}</div>
                                <div class="document-meta">
                                    {{ formatFileSize(doc.file_size) }} · {{ formatDate(doc.upload_time) }}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div v-if="!loading && documents.length === 0" class="empty-data">
                    <el-empty description="暂无文档" :image-size="120">
                        <template #description>
                            <p>您还没有上传任何文档</p>
                        </template>
                    </el-empty>
                </div>
            </div>
        </el-card>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Document, Delete, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

// 后端API基础URL
const API_BASE_URL = 'http://localhost:8080/api/v1/documents';

export default {
    name: 'DocumentManagement',
    components: {
        UploadFilled,
        Document
    },
    setup() {
        const documents = ref([])
        const loading = ref(false)
        const uploading = ref(false)
        const uploadProgress = ref(0)
        const currentUploadFile = ref({})
        const deleteDialogVisible = ref(false)
        const currentDocument = ref(null)

        // 新增的配置项
        const chunkSize = ref(500)
        const overlapSize = ref(50)
        const embeddingModel = ref('text-embedding-ada-002')
        const topK = ref(3)
        const embeddingModels = [
            { value: 'text-embedding-ada-002', label: 'OpenAI Ada 002' },
            { value: 'text-embedding-3-small', label: 'OpenAI Embedding 3 Small' },
            { value: 'text-embedding-3-large', label: 'OpenAI Embedding 3 Large' },
            { value: 'bge-base-zh', label: 'BGE Base (中文)' },
            { value: 'bge-large-zh', label: 'BGE Large (中文)' }
        ]

        // 获取文档列表
        const fetchDocuments = async () => {
            loading.value = true
            try {
                const response = await axios.get(`${API_BASE_URL}/list`)
                documents.value = response.data.documents || []
            } catch (error) {
                console.error('获取文档列表失败:', error)
                ElMessage({
                    message: '获取文档列表失败',
                    type: 'error',
                    duration: 3000
                })
            } finally {
                loading.value = false
            }
        }

        // 根据文件类型获取图标颜色类名
        const getIconColorClass = (fileType) => {
            if (!fileType) return '';

            const type = fileType.toLowerCase();
            if (type === 'pdf') {
                return 'pdf-icon';
            } else if (type === 'doc' || type === 'docx') {
                return 'doc-icon';
            } else if (type === 'txt') {
                return 'txt-icon';
            } else {
                return '';
            }
        }

        // 上传前验证
        const beforeUpload = (file) => {
            const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            const isAllowed = allowedTypes.includes(file.type)

            if (!isAllowed) {
                ElMessage({
                    message: '只能上传PDF、TXT或DOCX文件!',
                    type: 'error',
                    duration: 3000
                })
                return false
            }

            const isLt10M = file.size / 1024 / 1024 < 100
            if (!isLt10M) {
                ElMessage({
                    message: '文件大小不能超过100MB!',
                    type: 'error',
                    duration: 3000
                })
                return false
            }

            // 设置上传中状态和当前上传文件
            uploading.value = true
            uploadProgress.value = 0
            currentUploadFile.value = file

            return true
        }

        // 处理上传进度
        const handleUploadProgress = (event, file) => {
            uploadProgress.value = Math.round(event.percent)
        }

        // 上传成功处理
        const handleUploadSuccess = (response) => {
            // 重置上传状态
            uploading.value = false
            uploadProgress.value = 0

            ElMessage({
                message: '文档上传成功',
                type: 'success',
                duration: 3000
            })
            fetchDocuments()
        }

        // 上传失败处理
        const handleUploadError = (error) => {
            // 重置上传状态
            uploading.value = false
            uploadProgress.value = 0

            console.error('上传失败:', error)
            ElMessage({
                message: '文档上传失败',
                type: 'error',
                duration: 3000
            })
        }

        // 显示删除确认弹窗
        const showDeleteConfirm = (doc) => {
            currentDocument.value = doc
            deleteDialogVisible.value = true
        }

        // 确认删除
        const confirmDelete = () => {
            if (currentDocument.value) {
                handleDelete(currentDocument.value)
                deleteDialogVisible.value = false
            }
        }

        // 删除文档
        const handleDelete = async (row) => {
            try {
                await axios.delete(`${API_BASE_URL}/${row.id}`)
                ElMessage({
                    message: '文档删除成功',
                    type: 'success',
                    duration: 3000
                })
                fetchDocuments()
            } catch (error) {
                console.error('删除文档失败:', error)
                ElMessage({
                    message: '删除文档失败',
                    type: 'error',
                    duration: 3000
                })
            }
        }

        // 格式化文件大小
        const formatFileSize = (size) => {
            if (size < 1024) {
                return size + ' B'
            } else if (size < 1024 * 1024) {
                return (size / 1024).toFixed(1) + ' KB'
            } else {
                return (size / 1024 / 1024).toFixed(1) + ' MB'
            }
        }

        // 格式化日期
        const formatDate = (dateStr) => {
            if (!dateStr) return ''
            const date = new Date(dateStr)
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            })
        }

        onMounted(() => {
            fetchDocuments()
        })

        return {
            documents,
            loading,
            uploading,
            uploadProgress,
            currentUploadFile,
            deleteDialogVisible,
            currentDocument,
            chunkSize,
            overlapSize,
            embeddingModel,
            embeddingModels,
            topK,
            fetchDocuments,
            handleUploadSuccess,
            handleUploadError,
            handleUploadProgress,
            beforeUpload,
            handleDelete,
            showDeleteConfirm,
            confirmDelete,
            formatFileSize,
            formatDate,
            getIconColorClass,
            Refresh,
            Delete
        }
    }
}
</script>

<style scoped>
.document-management {
    display: flex;
    flex-direction: column;
    gap: 12px;
    /* 进一步减小组件之间的间距 */
    max-width: 1200px;
    margin: 0 auto;
    position: relative;
}

/* 上传和配置区域的布局 */
.upload-config-row {
    display: flex;
    gap: 16px;
    width: 100%;
}

.upload-card,
.config-card {
    flex: 1;
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.3s ease;
}

.config-header {
    padding: 4px 0;
    margin-bottom: 0;
}

.config-header h3 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
}

.config-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 4px 0;
}

.config-row {
    display: flex;
    gap: 12px;
    width: 100%;
}

.config-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.config-item.half {
    flex: 1;
}

.config-label {
    font-size: 13px;
    color: var(--text-secondary);
}

/* 减小上传区域相关元素的尺寸 */
.upload-card {
    flex: 1;
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.3s ease;
    min-height: 200px;
}

/* 关键修复：定位el-card的内部内容容器 */
.upload-card :deep(.el-card__body) {
    height: 100%;
    padding: 0 !important;
    display: flex;
    align-items: center;
    justify-content: center;
}

.upload-content {
    width: 100%;
    height: 100%;
    padding: 25px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.upload-area {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

:deep(.el-upload) {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

:deep(.el-upload-dragger) {
    width: 100%;
    max-width: 95%;
    margin: 0 auto;
    border: none !important;
    background-color: transparent !important;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.upload-inner.compact {
    padding: 30px 40px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-width: 3px;
    border-style: dashed;
    border-color: var(--border-color);
    border-radius: 12px;
    background-color: var(--secondary-bg);
}

.upload-inner {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
    border: 2px dashed var(--border-color);
    border-radius: 12px;
    transition: all 0.3s ease;
    background-color: var(--secondary-bg);
}

.upload-inner:hover {
    border-color: var(--accent-color);
    background-color: var(--accent-light);
}

.upload-icon {
    font-size: 56px;
    padding: 15px;
    color: var(--accent-color);
    background-color: var(--accent-light);
    border-radius: 50%;
    box-shadow: var(--shadow-sm);
    margin-right: 30px;
}

.upload-text h3 {
    font-size: 20px;
    font-weight: 600;
    margin: 0 0 10px 0;
    color: var(--text-primary);
}

.upload-text p {
    font-size: 16px;
    color: var(--text-secondary);
}

/* 调整Element Plus组件的尺寸 */
:deep(.el-input-number) {
    width: 100%;
}

:deep(.el-card__header) {
    padding: 6px 15px;
}

:deep(.el-card__body) {
    padding: 15px;
}

/* 上传遮罩层样式 */
.upload-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.6);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
}

.upload-progress-container {
    width: 500px;
    max-width: 90%;
    background-color: white;
    border-radius: 16px;
    padding: 30px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
    text-align: center;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

/* 让进度条居中并隐藏所有可能的叉号图标 */
.centered-progress {
    margin: 0 auto;
    width: 100% !important;
}

:deep(.el-progress) {
    width: 100%;
    display: flex;
    justify-content: center;
}

:deep(.el-progress-bar) {
    width: 100%;
    max-width: 400px;
    margin: 0 auto;
}

:deep(.el-progress__icon),
:deep(.el-icon-close),
:deep(.el-message-box__close),
:deep(.el-dialog__close),
:deep(.el-icon--close),
:deep(.close-icon),
:deep(.el-notification__closeBtn) {
    display: none !important;
}

/* 确保上传容器内没有任何关闭按钮 */
.upload-progress-container :deep(i),
.upload-progress-container :deep(button),
.upload-progress-container :deep(.close),
.upload-progress-container :deep([class*="close"]),
.upload-progress-container :deep([class*="Close"]) {
    display: none !important;
}

/* 修改删除确认按钮的文字颜色为白色 */
:deep(.el-message-box__btns .el-button--primary) {
    color: white !important;
}

.upload-status {
    margin-top: 16px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 14px;
}

.section-header {
    margin-bottom: 8px;
    text-align: center;
}

.section-header h2 {
    font-size: 28px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: var(--text-primary);
}

.section-description {
    font-size: 16px;
    color: var(--text-secondary);
    margin: 0;
}

.document-list-card {
    border-radius: 16px;
    overflow: hidden;
    flex-grow: 1;
    /* 允许文档列表区域占据更多空间 */
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border-color);
}

.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.header-left h3 {
    font-size: 18px;
    font-weight: 500;
    margin: 0;
    color: var(--text-primary);
}

.document-list {
    min-height: 300px;
    padding: 16px;
    position: relative;
}

.document-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    width: 100%;
}

.document-card {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
    overflow: hidden;
    cursor: pointer;
    /* 添加鼠标指针样式，表明可点击 */
}

.document-card:hover {
    background-color: var(--hover-bg);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.document-card-content {
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    position: relative;
}

.document-icon {
    font-size: 24px;
    color: var(--accent-color);
    background-color: var(--accent-light);
    padding: 8px;
    border-radius: 8px;
}

.document-details {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
}

.document-name {
    font-size: 15px;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.document-meta {
    font-size: 13px;
    color: var(--text-secondary);
}

.empty-data {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 60px 0;
}

:deep(.el-table) {
    --el-table-border-color: var(--border-color);
    --el-table-header-bg-color: var(--secondary-bg);
    --el-table-row-hover-bg-color: transparent;
    --el-table-bg-color: var(--card-bg);
    background-color: transparent !important;
}

:deep(.el-table__inner-wrapper::before),
:deep(.el-table__border-left-patch) {
    display: none;
}

:deep(.el-table__header) {
    font-weight: 500;
}

:deep(.el-table__row) {
    cursor: pointer;
    transition: all 0.2s ease;
    background-color: transparent !important;
}

:deep(.el-table__cell) {
    background-color: transparent !important;
    border-bottom: none !important;
}

:deep(.el-empty__description p) {
    color: var(--text-secondary);
    margin-top: 8px;
}

:deep(.el-tag--info) {
    background-color: var(--hover-bg);
    border-color: var(--border-color);
    color: var(--text-secondary);
}

/* 覆盖Element Plus上传组件的默认样式 */
:deep(.el-upload-dragger) {
    width: 100%;
    height: auto;
    background-color: transparent;
    border: none;
    padding: 0;
}

/* 针对上传状态下的样式 */
:deep(.el-upload--disabled .el-upload-dragger) {
    background-color: var(--secondary-bg);
    opacity: 0.7;
    cursor: not-allowed;
}

/* 添加新的图标颜色样式 */
.pdf-icon {
    color: #ff4d4f;
    /* 红色 */
}

.doc-icon {
    color: #1890ff;
    /* 蓝色 */
}

.txt-icon {
    color: #909399;
    /* 灰色 */
}

/* 配置区域卡片也需要调整高度以匹配 */
.config-card {
    min-height: 180px;
    display: flex;
    flex-direction: column;
}

/* 添加的新样式 */
.bold-label {
    font-weight: bold;
    color: #000;
}

.normal-black {
    font-weight: normal;
    color: #000;
}

.unit-text {
    color: #909399;
    margin-right: 25px;
    /* 为控制按钮留出空间 */
}

:deep(.el-dialog) {
    border-radius: 20px;
}

/* 修改输入框样式，解决双层框问题 */
:deep(.el-input-number .el-input__wrapper) {
    box-shadow: none;
    background-color: transparent;
    padding-right: 30px;
    /* 给右侧控制按钮留出空间 */
}

:deep(.el-input-number) {
    background-color: var(--secondary-bg);
    border-radius: 4px;
    border: 1px solid var(--border-color);
}

/* 移除上下箭头的边框 */
:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
    right: 0;
    border: none !important;
    background-color: transparent;
}

/* 解决下箭头的边框问题 */
:deep(.el-input-number__decrease) {
    border-top: none !important;
    border-right: none !important;
    border-left: none !important;
    border-bottom: none !important;
}

/* 覆盖分隔线 */
:deep(.el-input-number .el-input-number__increase),
:deep(.el-input-number .el-input-number__decrease) {
    border-radius: 0 !important;
}

:deep(.el-input-number__decrease::after),
:deep(.el-input-number__increase::after) {
    content: none !important;
}

:deep(.el-input-number .el-input-number__decrease + .el-input-number__increase) {
    border-top: none !important;
}

/* 恢复悬停效果 */
:deep(.el-input-number__decrease:hover),
:deep(.el-input-number__increase:hover) {
    color: var(--accent-color);
    background-color: transparent;
}

/* 修复内部输入框 */
:deep(.el-input-number .el-input__inner) {
    border: none;
}

/* 添加滑块组件的样式 */
:deep(.el-slider__runway) {
    margin-right: 0;
    width: 100%;
}

:deep(.el-slider .el-slider__button) {
    border: 2px solid var(--accent-color);
    width: 16px;
    height: 16px;
}

:deep(.el-slider .el-slider__bar) {
    background-color: var(--accent-color);
    height: 6px;
}

:deep(.el-slider .el-slider__runway) {
    height: 6px;
}

:deep(.el-tooltip__trigger) {
    font-weight: bold;
}

/* 修改下拉框选中文本样式 */
:deep(.el-select .el-input__inner) {
    font-weight: normal !important;
    color: #000 !important;
}

:deep(.el-select-dropdown__item) {
    font-weight: normal !important;
    color: #333 !important;
}

:deep(.el-select-dropdown__item.selected) {
    font-weight: normal !important;
    color: #000 !important;
}

:deep(.el-popper) {
    font-weight: normal;
}

:deep(.el-select__popper .el-select-dropdown__item) {
    font-weight: normal !important;
}

:deep(.el-select-dropdown__list) {
    font-weight: normal;
}

/* 确保选择框内的文本也是正常黑色 */
:deep(.el-select .el-select__wrapper) {
    font-weight: normal !important;
}

:deep(.el-input__wrapper) {
    font-weight: normal !important;
}

:deep(.el-input__inner) {
    font-weight: normal !important;
    color: #000 !important;
}

/* 自定义删除对话框样式 */
:deep(.el-dialog.custom-delete-dialog) {
    border-radius: 20px !important;
    overflow: hidden;
}

:deep(.custom-delete-dialog) {
    border-radius: 20px !important;
    display: flex;
    align-items: center;
    justify-content: center;
}

:deep(.custom-delete-dialog .el-dialog) {
    border-radius: 20px !important;
    margin-top: 0 !important;
}

:deep(.custom-delete-dialog .el-dialog__header) {
    padding: 25px 25px 15px;
    margin: 0;
    border-top-left-radius: 20px !important;
    border-top-right-radius: 20px !important;
}

:deep(.custom-delete-dialog .el-dialog__body) {
    padding: 15px 25px;
    color: #606266;
}

:deep(.custom-delete-dialog .el-dialog__footer) {
    padding: 15px 25px 25px;
    border-top: none;
}

.custom-dialog-header h3 {
    margin: 0;
    font-size: 20px;
    font-weight: bold;
    color: #000;
}

.custom-dialog-content {
    margin-bottom: 15px;
}

.custom-dialog-content p {
    margin: 10px 0;
    font-size: 15px;
    color: #606266;
}

.custom-dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 2px;
}

.cancel-btn {
    border-radius: 10px;
    background-color: white;
    color: #000;
    border: 1px solid #dcdfe6;
    padding: 10px 20px;
}

.confirm-btn {
    border-radius: 10px;
    background-color: #d92d21;
    color: white;
    border: none;
    padding: 10px 20px;
}

.confirm-btn:hover {
    background-color: #b42419;
}
</style>