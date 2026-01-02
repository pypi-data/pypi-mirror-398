"""
代码生成API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sys

router = APIRouter()

def _get_gen():
    if 'main' in sys.modules:
        return sys.modules['main'].code_generator
    import main
    return main.code_generator

class CodeGenerateRequest(BaseModel):
    element: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None

class BatchCodeRequest(BaseModel):
    elements: List[Dict[str, Any]]
    operation_type: str = "click"

def get_code_generator():
    """依赖注入：获取代码生成器"""
    return _get_gen()

@router.post("/code/generate")
async def generate_code(request: CodeGenerateRequest, generator=Depends(get_code_generator)):
    """生成元素定位代码"""
    try:
        if not request.element:
            raise HTTPException(status_code=400, detail="元素信息不能为空")
        
        result = generator.generate_element_code(request.element, request.options)
        
        return {
            "success": True,
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"代码生成失败: {str(e)}"
        )

@router.post("/code/batch-generate")
async def generate_batch_code(request: BatchCodeRequest, generator=Depends(get_code_generator)):
    """生成批量操作代码"""
    try:
        if not request.elements:
            raise HTTPException(status_code=400, detail="元素列表不能为空")
        
        batch_code = generator.generate_batch_code(request.elements)
        
        return {
            "success": True,
            "code": batch_code,
            "element_count": len(request.elements)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量代码生成失败: {str(e)}"
        )