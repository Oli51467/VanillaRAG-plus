<template>
  <div class="document-management">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>上传文档</span>
        </div>
      </template>
      <div class="upload-content">
        <el-upload
          class="upload-area"
          drag
          action="http://localhost:8080/api/v1/documents/upload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          :show-file-list="false">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持上传 PDF、TXT、DOCX 文件
            </div>
          </template>
        </el-upload>
      </div>
    </el-card>

    <el-card class="document-list-card">
      <template #header>
        <div class="card-header">
          <span>文档列表</span>
          <el-button type="primary" @click="fetchDocuments">刷新</el-button>
        </div>
      </template>
      <div class="document-list">
        <el-table
          v-loading="loading"
          :data="documents"
          style="width: 100%">
          <el-table-column
            prop="file_name"
            label="文件名"
            min-width="180">
          </el-table-column>
          <el-table-column
            prop="file_size"
            label="文件大小"
            width="120">
            <template #default="scope">
              {{ formatFileSize(scope.row.file_size) }}
            </template>
          </el-table-column>
          <el-table-column
            prop="upload_time"
            label="上传时间"
            width="180">
            <template #default="scope">
              {{ formatDate(scope.row.upload_time) }}
            </template>
          </el-table-column>
          <el-table-column
            label="操作"
            width="120">
            <template #default="scope">
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!loading && documents.length === 0" class="empty-data">
          <el-empty description="暂无文档"></el-empty>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

// 后端API基础URL
const API_BASE_URL = 'http://localhost:8080/api/v1/documents';

export default {
  name: 'DocumentManagement',
  components: {
    UploadFilled
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
        ElMessage.error('获取文档列表失败')
      } finally {
        loading.value = false
      }
    }

    // 上传前验证
    const beforeUpload = (file) => {
      const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
      const isAllowed = allowedTypes.includes(file.type)
      
      if (!isAllowed) {
        ElMessage.error('只能上传PDF、TXT或DOCX文件!')
        return false
      }
      
      const isLt10M = file.size / 1024 / 1024 < 10
      if (!isLt10M) {
        ElMessage.error('文件大小不能超过10MB!')
        return false
      }
      
      return true
    }

    // 上传成功处理
    const handleUploadSuccess = (response) => {
      ElMessage.success('文档上传成功')
      fetchDocuments()
    }

    // 上传失败处理
    const handleUploadError = (error) => {
      console.error('上传失败:', error)
      ElMessage.error('文档上传失败')
    }

    // 删除文档
    const handleDelete = (row) => {
      ElMessageBox.confirm(
        `确定要删除文档 "${row.file_name}" 吗?`,
        '警告',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      )
        .then(async () => {
          try {
            await axios.delete(`${API_BASE_URL}/${row.id}`)
            ElMessage.success('文档删除成功')
            fetchDocuments()
          } catch (error) {
            console.error('删除文档失败:', error)
            ElMessage.error('删除文档失败')
          }
        })
        .catch(() => {
          // 取消删除
        })
    }

    // 格式化文件大小
    const formatFileSize = (size) => {
      if (size < 1024) {
        return size + ' B'
      } else if (size < 1024 * 1024) {
        return (size / 1024).toFixed(2) + ' KB'
      } else {
        return (size / 1024 / 1024).toFixed(2) + ' MB'
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
        minute: '2-digit',
        second: '2-digit'
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
      formatDate
    }
  }
}
</script>

<style scoped>
.document-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.upload-card, .document-list-card {
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.upload-content {
  padding: 20px 0;
}

.upload-area {
  width: 100%;
}

.document-list {
  min-height: 300px;
}

.empty-data {
  margin-top: 40px;
}
</style> 