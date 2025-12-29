from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastpluggy_plugin.ui_tools.extra_widget.display.card import CardWidget
from sqlalchemy import text, Table, Column, Integer, String, Float, Boolean, MetaData, create_engine
from sqlalchemy.orm import Session
import json
import httpx
import asyncio
from typing import List, Dict, Any, Optional

from fastpluggy.core.database import get_db
from fastpluggy.core.dependency import get_view_builder
from fastpluggy.core.widgets import TableWidget, FormWidget
from fastpluggy.core.menu.decorator import menu_entry

alerts_router = APIRouter(prefix="/alerts", tags=["postgres_alerts"])


def ensure_alerts_table(db: Session):
    """
    Ensure the alerts configuration table exists
    """
    query = text("""
        CREATE TABLE IF NOT EXISTS pg_alerts (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            metric VARCHAR(255) NOT NULL,
            condition VARCHAR(50) NOT NULL,
            threshold FLOAT NOT NULL,
            webhook_url VARCHAR(1024),
            webhook_service VARCHAR(50),
            enabled BOOLEAN DEFAULT TRUE,
            last_triggered TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.execute(query)
    db.commit()


def get_alerts(db: Session):
    """
    Get all configured alerts
    """
    ensure_alerts_table(db)
    
    query = text("""
        SELECT 
            id, 
            name, 
            metric, 
            condition, 
            threshold, 
            webhook_url, 
            webhook_service, 
            enabled, 
            last_triggered, 
            created_at
        FROM pg_alerts
        ORDER BY id
    """)
    
    result = db.execute(query).mappings()
    return [dict(row) for row in result]


def create_alert(db: Session, alert_data: Dict[str, Any]):
    """
    Create a new alert
    """
    ensure_alerts_table(db)
    
    query = text("""
        INSERT INTO pg_alerts (
            name, 
            metric, 
            condition, 
            threshold, 
            webhook_url, 
            webhook_service, 
            enabled
        ) VALUES (
            :name, 
            :metric, 
            :condition, 
            :threshold, 
            :webhook_url, 
            :webhook_service, 
            :enabled
        ) RETURNING id
    """)
    
    result = db.execute(query, alert_data).mappings().first()
    db.commit()
    return result["id"]


def delete_alert(db: Session, alert_id: int):
    """
    Delete an alert
    """
    query = text("""
        DELETE FROM pg_alerts
        WHERE id = :alert_id
    """)
    

    db.execute(query, {"alert_id": alert_id})
    db.commit()


def update_alert(db: Session, alert_id: int, alert_data: Dict[str, Any]):
    """
    Update an alert
    """
    query = text("""
        UPDATE pg_alerts
        SET 
            name = :name, 
            metric = :metric, 
            condition = :condition, 
            threshold = :threshold, 
            webhook_url = :webhook_url, 
            webhook_service = :webhook_service, 
            enabled = :enabled
        WHERE id = :alert_id
    """)
    

    db.execute(query, {**alert_data, "alert_id": alert_id})
    db.commit()


def get_available_metrics():
    """
    Get available metrics for alerts
    """
    return [
        {"value": "table_bloat", "label": "Table Bloat Percentage"},
        {"value": "index_scans", "label": "Index Scan Count"},
        {"value": "query_duration", "label": "Query Duration (ms)"},
        {"value": "connection_count", "label": "Active Connection Count"},
        {"value": "vacuum_days", "label": "Days Since Last Vacuum"},
        {"value": "replication_lag", "label": "Replication Lag (bytes)"},
    ]


def get_available_conditions():
    """
    Get available conditions for alerts
    """
    return [
        {"value": ">", "label": "Greater Than"},
        {"value": "<", "label": "Less Than"},
        {"value": "=", "label": "Equal To"},
        {"value": ">=", "label": "Greater Than or Equal To"},
        {"value": "<=", "label": "Less Than or Equal To"},
    ]


def get_available_webhook_services():
    """
    Get available webhook services
    """
    return [
        {"value": "slack", "label": "Slack"},
        {"value": "discord", "label": "Discord"},
        {"value": "teams", "label": "Microsoft Teams"},
        {"value": "pagerduty", "label": "PagerDuty"},
        {"value": "custom", "label": "Custom Webhook"},
    ]


async def test_webhook(webhook_url: str, webhook_service: str, message: str):
    """
    Test a webhook by sending a test message
    """
    payload = {}
    
    if webhook_service == "slack":
        payload = {
            "text": message
        }
    elif webhook_service == "discord":
        payload = {
            "content": message
        }
    elif webhook_service == "teams":
        payload = {
            "text": message
        }
    elif webhook_service == "pagerduty":
        payload = {
            "incident": {
                "title": "Test Alert",
                "description": message,
                "service": {
                    "id": "PostgreSQL",
                    "type": "service"
                }
            }
        }
    else:  # custom
        payload = {
            "message": message,
            "source": "postgres_tools",
            "type": "test"
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                timeout=10.0
            )
            return response.status_code < 400
    except Exception as e:
        return False


@alerts_router.get("")
async def get_alerts_view(
    request: Request, 
    db=Depends(get_db), 
    view_builder=Depends(get_view_builder)
):
    """
    Get the PostgreSQL alerts and webhooks view
    """
    # Get alerts data
    alerts_data = get_alerts(db)
    
    # Create widgets
    alerts_table = TableWidget(
        title="Configured Alerts",
        endpoint="/postgres/alerts",
        data=alerts_data,
        description="Configure alerts based on database metrics and send notifications via webhooks."
    )
    
    # Create a form for adding new alerts
    new_alert_form = FormWidget(
        title="Add New Alert",
        endpoint="/postgres/alerts/create",
        fields=[
            {"name": "name", "label": "Alert Name", "type": "text", "required": True},
            {"name": "metric", "label": "Metric", "type": "select", "options": get_available_metrics(), "required": True},
            {"name": "condition", "label": "Condition", "type": "select", "options": get_available_conditions(), "required": True},
            {"name": "threshold", "label": "Threshold", "type": "number", "required": True},
            {"name": "webhook_url", "label": "Webhook URL", "type": "text", "required": False},
            {"name": "webhook_service", "label": "Webhook Service", "type": "select", "options": get_available_webhook_services(), "required": False},
            {"name": "enabled", "label": "Enabled", "type": "checkbox", "default": True}
        ]
    )
    
    # Create a card with webhook testing functionality
    webhook_test_card = CardWidget(
        title="Test Webhook",
        content="Use the form below to test your webhook configuration."
    )
    
    # Render the view
    return view_builder.generate(
        request,
        title="PostgreSQL Alerts & Webhooks",
        widgets=[
            alerts_table,
            new_alert_form,
            webhook_test_card
        ]
    )


@alerts_router.post("/create")
async def create_alert_endpoint(
    request: Request,
    name: str = Form(...),
    metric: str = Form(...),
    condition: str = Form(...),
    threshold: float = Form(...),
    webhook_url: Optional[str] = Form(None),
    webhook_service: Optional[str] = Form(None),
    enabled: bool = Form(True),
    db=Depends(get_db)
):
    """
    Create a new alert
    """
    alert_data = {
        "name": name,
        "metric": metric,
        "condition": condition,
        "threshold": threshold,
        "webhook_url": webhook_url,
        "webhook_service": webhook_service,
        "enabled": enabled
    }
    
    alert_id = create_alert(db, alert_data)
    
    # Redirect back to the alerts page
    return {"success": True, "alert_id": alert_id}


@alerts_router.post("/test-webhook")
async def test_webhook_endpoint(
    request: Request,
    webhook_url: str = Form(...),
    webhook_service: str = Form(...),
    message: str = Form("This is a test alert from PostgreSQL Tools")
):
    """
    Test a webhook
    """
    success = await test_webhook(webhook_url, webhook_service, message)
    
    if success:
        return {"success": True, "message": "Webhook test successful"}
    else:
        raise HTTPException(status_code=400, detail="Webhook test failed")


@alerts_router.delete("/{alert_id}")
async def delete_alert_endpoint(
    request: Request,
    alert_id: int,
    db=Depends(get_db)
):
    """
    Delete an alert
    """
    delete_alert(db, alert_id)
    
    return {"success": True}


@alerts_router.put("/{alert_id}")
async def update_alert_endpoint(
    request: Request,
    alert_id: int,
    name: str = Form(...),
    metric: str = Form(...),
    condition: str = Form(...),
    threshold: float = Form(...),
    webhook_url: Optional[str] = Form(None),
    webhook_service: Optional[str] = Form(None),
    enabled: bool = Form(True),
    db=Depends(get_db)
):
    """
    Update an alert
    """
    alert_data = {
        "name": name,
        "metric": metric,
        "condition": condition,
        "threshold": threshold,
        "webhook_url": webhook_url,
        "webhook_service": webhook_service,
        "enabled": enabled
    }
    
    update_alert(db, alert_id, alert_data)
    
    return {"success": True}