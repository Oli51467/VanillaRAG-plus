import os
import uuid
import traceback
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse

from app.services.document_service import DocumentService
from app.models.document import DocumentResponse, DocumentList

router = APIRouter()
document_service = DocumentService()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档并处理
    """
    # 检查文件类型是否允许
    if not document_service.allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    try:
        # 保存文件
        file_path = document_service.save_file(file)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 创建文档元数据
        doc_id = str(uuid.uuid4())
        metadata = {
            "id": doc_id,
            "file_name": file.filename,
            "file_path": file_path,
            "upload_time": datetime.now().isoformat(),
            "file_size": file_size,
            "source": file_path,
        }
        
        # 处理文档
        document_service.process_document(file_path, metadata)
        
        # 返回文档信息
        return {
            "id": doc_id,
            "file_name": file.filename,
            "file_path": file_path,
            "upload_time": datetime.now(),
            "file_size": file_size,
        }
    except Exception as e:
        # 记录详细错误信息
        error_detail = f"文档处理失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        
        # 如果文件已保存但处理失败，尝试删除文件
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")


@router.get("/list", response_model=DocumentList)
async def list_documents():
    """
    获取所有文档
    """
    try:
        documents = document_service.get_all_documents()
        
        # 转换日期时间格式
        for doc in documents:
            if "upload_time" in doc and doc["upload_time"]:
                try:
                    doc["upload_time"] = datetime.fromisoformat(doc["upload_time"])
                except:
                    doc["upload_time"] = datetime.now()
        
        return {"documents": documents}
    except Exception as e:
        error_detail = f"获取文档列表失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    删除文档
    """
    try:
        deleted = document_service.delete_document(doc_id)
        if deleted:
            return JSONResponse(content={"message": "文档删除成功"}, status_code=200)
        else:
            raise HTTPException(status_code=404, detail="文档不存在")
    except Exception as e:
        error_detail = f"删除文档失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}") 