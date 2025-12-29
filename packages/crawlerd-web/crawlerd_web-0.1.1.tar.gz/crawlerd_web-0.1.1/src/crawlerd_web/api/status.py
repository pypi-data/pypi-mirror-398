from fastapi import APIRouter, HTTPException
from crawler.services.status import StatusService
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter()

class TiDBStats(BaseModel):
    total: int
    by_status: Dict[str, int]
    by_node: Dict[str, int]
    matrix: Dict[str, Dict[str, int]]
    total_size: int
    start_time: Optional[Any]
    last_active: Optional[Any]
    rates: Dict[str, int]
    error: Optional[str] = None

class KafkaPartitionLag(BaseModel):
    partition: int
    current: int
    end: int
    lag: int

class KafkaStats(BaseModel):
    total_lag: int
    partitions: List[KafkaPartitionLag]
    error: Optional[str] = None

class RabbitMQStats(BaseModel):
    connected: bool
    host: str
    vhost: str
    queue_name: Optional[str]
    message_count: Optional[int]
    consumer_count: Optional[int]
    error: Optional[str] = None


@router.get("/status/tidb/{dataset_name}", response_model=TiDBStats, summary="获取 TiDB 数据集统计")
async def get_tidb_status(dataset_name: str):
    """
    Get TiDB statistics for a specific dataset (table).
    """
    return StatusService.get_tidb_stats(dataset_name)

@router.get("/status/kafka/{dataset_name}", response_model=Optional[KafkaStats], summary="获取 Kafka 消费积压情况")
async def get_kafka_status(dataset_name: str):
    """
    Get Kafka lag statistics for a specific dataset's topic/group.
    Returns null if Kafka is unavailable.
    """
    return StatusService.get_kafka_lag(dataset_name)

@router.get("/status/rabbitmq/{dataset_name}", response_model=Optional[RabbitMQStats], summary="获取 RabbitMQ 队列状态")
async def get_rabbitmq_status(dataset_name: str):
    """
    Get RabbitMQ queue statistics for a specific dataset.
    Returns null if RabbitMQ is unavailable.
    """
    return StatusService.get_rabbitmq_status(dataset_name)
