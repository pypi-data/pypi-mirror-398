import os
import httpx
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from loguru import logger
from typing import Optional

from service_forge.model.feedback import FeedbackCreate, FeedbackResponse, FeedbackListResponse
from service_forge.storage.feedback_storage import feedback_storage
from service_forge.db.database import create_database_manager
from service_forge.current_service import get_service

router = APIRouter(prefix="/sdk/feedback", tags=["feedback"])

def get_forward_api_url():
    if not get_service():
        return None
    if not get_service().config.feedback:
        return None
    return get_service().config.feedback.api_url

def get_forward_api_timeout():
    if not get_service():
        return None
    if not get_service().config.feedback:
        return None
    return get_service().config.feedback.api_timeout

async def forward_feedback_to_api(feedback_data: dict):
    """
    将反馈数据转发到外部 API

    Args:
        feedback_data: 反馈数据字典
    """
    forward_api_url = get_forward_api_url()
    forward_api_timeout = get_forward_api_timeout()
    print(forward_api_url)
    print(forward_api_timeout)
    if not forward_api_url:
        logger.debug("未配置转发 API URL，跳过转发")
        return
    try:
        # 处理 datetime 对象，转换为 ISO 格式字符串
        serializable_data = feedback_data.copy()
        if 'created_at' in serializable_data and serializable_data['created_at']:
            serializable_data['created_at'] = serializable_data['created_at'].isoformat()

        async with httpx.AsyncClient(timeout=forward_api_timeout) as client:
            response = await client.post(
                forward_api_url,
                json=serializable_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"反馈转发成功: feedback_id={feedback_data.get('feedback_id')}, status={response.status_code}")
    except httpx.TimeoutException:
        logger.warning(f"反馈转发超时: {forward_api_url}")
    except httpx.ConnectError as e:
        logger.warning(f"反馈转发连接失败: {forward_api_url} - {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"反馈转发失败: status={e.response.status_code}, detail={e.response.text}")
    except Exception as e:
        logger.error(f"反馈转发异常: {type(e).__name__}: {e}")



@router.post("/", response_model=FeedbackResponse, summary="创建工作流反馈")
async def create_feedback(feedback: FeedbackCreate, background_tasks: BackgroundTasks):
    """
    创建工作流执行完成后的用户反馈
    - **task_id**: 工作流任务ID - workflow的id
    - **workflow_name**: 工作流名称 - workflow的名称
    - **rating**: 可选的评分 (1-5) - 反馈中的一种，评分，可以为空
    - **comment**: 可选的用户评论 - 反馈中的一种，可以为空
    - **metadata**: 可选的额外元数据
    还少什么？ - trace_id?
    """
    try:
        # 保存到数据库
        feedback_data = await feedback_storage.create_feedback(
            task_id=feedback.task_id,
            workflow_name=feedback.workflow_name,
            rating=feedback.rating,
            comment=feedback.comment,
            metadata=feedback.metadata,
        )

        # 后台任务转发到外部 API (不阻塞响应)
        background_tasks.add_task(forward_feedback_to_api, feedback_data)

        return FeedbackResponse(**feedback_data)
    except Exception as e:
        logger.error(f"创建反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建反馈失败: {str(e)}")


@router.get("/{feedback_id}", response_model=FeedbackResponse, summary="获取单个反馈")
async def get_feedback(feedback_id: str):
    """
    根据反馈ID获取反馈详情

    - **feedback_id**: 反馈ID
    """
    feedback = await feedback_storage.get_feedback(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return FeedbackResponse(**feedback)


@router.get("/", response_model=FeedbackListResponse, summary="获取反馈列表")
async def list_feedbacks(
    task_id: Optional[str] = Query(None, description="按任务ID筛选"),
    workflow_name: Optional[str] = Query(None, description="按工作流名称筛选"),
):
    """
    获取反馈列表,支持按任务ID或工作流名称筛选

    - **task_id**: 可选,按任务ID筛选
    - **workflow_name**: 可选,按工作流名称筛选
    """
    try:
        if task_id:
            feedbacks = await feedback_storage.get_feedbacks_by_task(task_id)
        elif workflow_name:
            feedbacks = await feedback_storage.get_feedbacks_by_workflow(workflow_name)
        else:
            feedbacks = await feedback_storage.get_all_feedbacks()

        return FeedbackListResponse(
            total=len(feedbacks),
            feedbacks=[FeedbackResponse(**f) for f in feedbacks]
        )
    except Exception as e:
        logger.error(f"获取反馈列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取反馈列表失败: {str(e)}")


@router.delete("/{feedback_id}", summary="删除反馈")
async def delete_feedback(feedback_id: str):
    """
    删除指定的反馈

    - **feedback_id**: 反馈ID
    """
    success = await feedback_storage.delete_feedback(feedback_id)
    if not success:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return {"message": "反馈删除成功", "feedback_id": feedback_id}
