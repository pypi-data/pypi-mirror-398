"""
告警服务层
处理告警相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import logging

from jettask.schemas import AlertRuleRequest

logger = logging.getLogger(__name__)


class AlertService:
    """告警服务类"""
    
    @staticmethod
    def get_alert_rules(
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        rules = AlertService._get_mock_rules()
        
        if is_active is not None:
            rules = [r for r in rules if r["is_active"] == is_active]
        
        total = len(rules)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_rules = rules[start:end]
        
        return {
            "success": True,
            "data": paginated_rules,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    @staticmethod
    def create_alert_rule(request: AlertRuleRequest) -> Dict[str, Any]:
        rule = {
            "id": f"rule_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": request.name,
            "rule_type": request.rule_type,
            "target_queues": request.target_queues,
            "condition": request.condition,
            "action_type": request.action_type,
            "action_config": request.action_config,
            "is_active": request.is_active,
            "description": request.description,
            "check_interval": request.check_interval,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_triggered": None,
            "updated_at": None
        }
        
        
        return {
            "success": True,
            "data": rule,
            "message": "告警规则创建成功"
        }
    
    @staticmethod
    def update_alert_rule(rule_id: str, request: AlertRuleRequest) -> Dict[str, Any]:
        rule = {
            "id": rule_id,
            "name": request.name,
            "rule_type": request.rule_type,
            "target_queues": request.target_queues,
            "condition": request.condition,
            "action_type": request.action_type,
            "action_config": request.action_config,
            "is_active": request.is_active,
            "description": request.description,
            "check_interval": request.check_interval,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        
        return {
            "success": True,
            "data": rule,
            "message": "告警规则更新成功"
        }
    
    @staticmethod
    def delete_alert_rule(rule_id: str) -> Dict[str, Any]:
        
        return {
            "success": True,
            "message": f"告警规则 {rule_id} 已删除"
        }
    
    @staticmethod
    def toggle_alert_rule(rule_id: str) -> Dict[str, Any]:
        current_state = True  
        new_state = not current_state
        
        return {
            "success": True,
            "data": {
                "id": rule_id,
                "is_active": new_state
            },
            "message": f"告警规则已{'启用' if new_state else '禁用'}"
        }
    
    @staticmethod
    def get_alert_history(
        rule_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        history = AlertService._generate_mock_history(rule_id)
        
        total = len(history)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_history = history[start:end]
        
        return {
            "success": True,
            "data": paginated_history,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    @staticmethod
    def test_alert_rule(rule_id: str) -> Dict[str, Any]:
        
        return {
            "success": True,
            "message": "测试通知已发送",
            "data": {
                "rule_id": rule_id,
                "test_time": datetime.now(timezone.utc).isoformat(),
                "notification_result": {
                    "status": "success",
                    "response": {"code": 200, "message": "OK"}
                }
            }
        }
    
    @staticmethod
    def get_alert_statistics(namespace: Optional[str] = None) -> Dict[str, Any]:
        return {
            "success": True,
            "data": {
                "total_rules": 15,
                "active_rules": 10,
                "inactive_rules": 5,
                "alerts_today": 25,
                "alerts_this_week": 156,
                "alerts_this_month": 892,
                "most_triggered_rule": {
                    "id": "rule_001",
                    "name": "队列积压告警",
                    "trigger_count": 42
                },
                "alert_trend": AlertService._generate_alert_trend(),
                "alert_by_type": {
                    "queue_size": 45,
                    "error_rate": 30,
                    "response_time": 15,
                    "custom": 10
                }
            }
        }
    
    @staticmethod
    def get_active_alerts(namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        return [
            {
                "id": "alert_active_001",
                "rule_id": "rule_001",
                "rule_name": "队列积压告警",
                "severity": "high",
                "triggered_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "trigger_value": 1500,
                "threshold": 1000,
                "queue": "order_queue",
                "status": "active",
                "acknowledged": False
            },
            {
                "id": "alert_active_002",
                "rule_id": "rule_002",
                "rule_name": "高错误率告警",
                "severity": "critical",
                "triggered_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
                "trigger_value": 0.15,
                "threshold": 0.1,
                "queue": "payment_queue",
                "status": "active",
                "acknowledged": True,
                "acknowledged_by": "admin",
                "acknowledged_at": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
            }
        ]
    
    @staticmethod
    def acknowledge_alert(alert_id: str, user: str = "system") -> Dict[str, Any]:
        
        return {
            "success": True,
            "data": {
                "alert_id": alert_id,
                "acknowledged": True,
                "acknowledged_by": user,
                "acknowledged_at": datetime.now(timezone.utc).isoformat()
            },
            "message": "告警已确认"
        }
    
    @staticmethod
    def resolve_alert(alert_id: str, resolution_note: Optional[str] = None) -> Dict[str, Any]:
        
        return {
            "success": True,
            "data": {
                "alert_id": alert_id,
                "status": "resolved",
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "resolution_note": resolution_note
            },
            "message": "告警已解决"
        }
    
    
    @staticmethod
    def _get_mock_rules() -> List[Dict[str, Any]]:
        return [
            {
                "id": "rule_001",
                "name": "队列积压告警",
                "rule_type": "queue_size",
                "target_queues": ["order_queue", "payment_queue"],
                "condition": {"threshold": 1000, "operator": ">"},
                "action_type": "webhook",
                "action_config": {"url": "https://example.com/webhook"},
                "is_active": True,
                "last_triggered": "2025-08-31T14:30:00Z",
                "created_at": "2025-08-01T10:00:00Z",
                "description": "当队列积压超过1000时触发告警"
            },
            {
                "id": "rule_002",
                "name": "高错误率告警",
                "rule_type": "error_rate",
                "target_queues": ["*"],
                "condition": {"threshold": 0.1, "operator": ">", "window": 300},
                "action_type": "email",
                "action_config": {"recipients": ["admin@example.com"]},
                "is_active": True,
                "last_triggered": None,
                "created_at": "2025-08-15T14:00:00Z",
                "description": "5分钟内错误率超过10%时告警"
            },
            {
                "id": "rule_003",
                "name": "响应时间告警",
                "rule_type": "response_time",
                "target_queues": ["api_queue"],
                "condition": {"threshold": 5000, "operator": ">", "percentile": 95},
                "action_type": "webhook",
                "action_config": {"url": "https://slack.com/webhook"},
                "is_active": False,
                "last_triggered": "2025-08-30T09:00:00Z",
                "created_at": "2025-07-01T08:00:00Z",
                "description": "95分位响应时间超过5秒时告警"
            },
            {
                "id": "rule_004",
                "name": "内存使用告警",
                "rule_type": "memory_usage",
                "target_queues": ["*"],
                "condition": {"threshold": 80, "operator": ">"},
                "action_type": "sms",
                "action_config": {"phone": "+1234567890"},
                "is_active": True,
                "last_triggered": "2025-08-29T16:00:00Z",
                "created_at": "2025-06-15T12:00:00Z",
                "description": "内存使用率超过80%时告警"
            }
        ]
    
    @staticmethod
    def _generate_mock_history(rule_id: str) -> List[Dict[str, Any]]:
        history = []
        for i in range(1, 21):
            triggered_at = datetime.now(timezone.utc) - timedelta(hours=i*3)
            is_resolved = i % 3 != 0  
            
            alert = {
                "id": f"alert_{rule_id}_{i}",
                "rule_id": rule_id,
                "triggered_at": triggered_at.isoformat(),
                "trigger_value": 1200 + i * 50,
                "threshold": 1000,
                "status": "resolved" if is_resolved else "active",
                "notification_sent": True,
                "notification_response": {"status": "success"}
            }
            
            if is_resolved:
                alert["resolved_at"] = (triggered_at + timedelta(hours=1)).isoformat()
                alert["resolution_note"] = f"自动恢复 - 值降至阈值以下"
            
            history.append(alert)
        
        return history
    
    @staticmethod
    def _generate_alert_trend() -> List[Dict[str, Any]]:
        trend = []
        now = datetime.now(timezone.utc)
        
        for i in range(7):
            date = (now - timedelta(days=6-i)).date()
            trend.append({
                "date": date.isoformat(),
                "count": 10 + i * 3 + (i % 2) * 5  
            })
        
        return trend