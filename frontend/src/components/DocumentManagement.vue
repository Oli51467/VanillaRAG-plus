<template>
    <div class="document-management">

        <!-- 上传区域 -->
        <el-card class="upload-card">
            <div class="upload-content">
                <el-upload class="upload-area" drag action="http://localhost:8080/api/v1/documents/upload"
                    :on-success="handleUploadSuccess" :on-error="handleUploadError" :before-upload="beforeUpload"
                    :show-file-list="false">
                    <div class="upload-inner">
                        <el-icon class="upload-icon"><upload-filled /></el-icon>
                        <div class="upload-text">
                            <h3>拖拽文件到此处或点击上传</h3>
                            <p>支持 PDF、TXT、DOCX 格式文件</p>
                        </div>
                    </div>
                </el-upload>
            </div>
        </el-card>

        <!-- 文档列表 -->
        <el-card class="document-list-card">
            <div class="card-header">
                <div class="header-left">
                    <h3>我的文档</h3>
                    <el-tag v-if="documents.length > 0" type="info" round>{{ documents.length }} 个文件</el-tag>
                </div>
                <el-button type="primary" @click="fetchDocuments" :icon="Refresh">刷新</el-button>
            </div>

            <div class="document-list">
                <el-table v-loading="loading" :data="documents" style="width: 100%">
                    <el-table-column label="文档信息" min-width="300">
                        <template #default="scope">
                            <div class="document-info">
                                <el-icon class="document-icon">
                                    <document />
                                </el-icon>
                                <div class="document-details">
                                    <div class="document-name">{{ scope.row.file_name }}</div>
                                    <div class="document-meta">
                                        {{ formatFileSize(scope.row.file_size) }} · {{ formatDate(scope.row.upload_time)
                                        }}
                                    </div>
                                </div>
                            </div>
                        </template>
                    </el-table-column>

                    <el-table-column label="操作" width="120" align="right">
                        <template #default="scope">
                            <el-popconfirm title="确定要删除这个文档吗？" confirm-button-text="删除" cancel-button-text="取消"
                                icon-color="var(--danger-color)" @confirm="handleDelete(scope.row)">
                                <template #reference>
                                    <el-button type="danger" :icon="Delete" circle plain></el-button>
                                </template>
                            </el-popconfirm>
                        </template>
                    </el-table-column>
                </el-table>

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

            const isLt10M = file.size / 1024 / 1024 < 10
            if (!isLt10M) {
                ElMessage({
                    message: '文件大小不能超过10MB!',
                    type: 'error',
                    duration: 3000
                })
                return false
            }

            return true
        }

        // 上传成功处理
        const handleUploadSuccess = (response) => {
            ElMessage({
                message: '文档上传成功',
                type: 'success',
                duration: 3000
            })
            fetchDocuments()
        }

        // 上传失败处理
        const handleUploadError = (error) => {
            console.error('上传失败:', error)
            ElMessage({
                message: '文档上传失败',
                type: 'error',
                duration: 3000
            })
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
            fetchDocuments,
            beforeUpload,
            handleUploadSuccess,
            handleUploadError,
            handleDelete,
            formatFileSize,
            formatDate,
            Delete,
            Refresh
        }
    }
}
</script>

<style scoped>
.document-management {
    display: flex;
    flex-direction: column;
    gap: 24px;
    max-width: 1200px;
    margin: 0 auto;
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

.upload-card {
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.3s ease;
}

.upload-content {
    padding: 16px;
}

.upload-area {
    width: 100%;
}

.upload-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 30px 20px;
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
    font-size: 48px;
    color: var(--accent-color);
    margin-bottom: 16px;
    background-color: white;
    padding: 12px;
    border-radius: 50%;
    box-shadow: var(--shadow-sm);
}

.upload-text h3 {
    font-size: 18px;
    font-weight: 500;
    margin: 0 0 8px 0;
    color: var(--text-primary);
}

.upload-text p {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0;
}

.document-list-card {
    border-radius: 16px;
    overflow: hidden;
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
}

.document-info {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: 12px;
    transition: all 0.2s ease;
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
}

.document-info:hover {
    background-color: var(--hover-bg);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
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
}

.document-name {
    font-size: 15px;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 4px;
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
</style>