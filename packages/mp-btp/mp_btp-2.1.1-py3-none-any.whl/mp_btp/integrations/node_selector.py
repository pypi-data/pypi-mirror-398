#!/usr/bin/env python3
"""
Node selector with account affinity.
Selects optimal node for account operations with session persistence.
"""
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from mp_btp.models import Account

logger = logging.getLogger(__name__)


def select_node_for_account(
    multi_node_client,
    account: Account,
    db: Session,
    region_hint: str = None
) -> Optional[str]:
    """
    Select node for account with affinity.
    
    Priority:
    1. preferred_node (if online)
    2. region_hint match
    3. least loaded node
    
    Args:
        multi_node_client: MultiNodeClient instance
        account: Account model
        db: Database session
        region_hint: Optional region tag (us, eu, asia)
    
    Returns:
        node_id or None
    """
    # 1. Check preferred node
    if account.preferred_node:
        node = multi_node_client.get_node(account.preferred_node)
        if node and node.get("status") == "online":
            logger.info(f"Using preferred node {account.preferred_node} for {account.subdomain}")
            return account.preferred_node
        else:
            logger.warning(f"Preferred node {account.preferred_node} offline, selecting new")
    
    # 2. Get available nodes
    tags = [region_hint] if region_hint else []
    nodes = multi_node_client.list_nodes(tags=tags)
    
    if not nodes:
        logger.error("No available nodes")
        return None
    
    # 3. Filter online nodes
    online = [n for n in nodes if n.get("status") == "online"]
    if not online:
        logger.error("No online nodes")
        return None
    
    # 4. Select least loaded (by active connections or custom metric)
    selected = min(online, key=lambda n: n.get("load", 0))
    node_id = selected.get("id")
    
    # 5. Update account affinity
    account.preferred_node = node_id
    db.commit()
    
    logger.info(f"Selected node {node_id} for {account.subdomain}")
    return node_id


def batch_select_nodes(
    multi_node_client,
    accounts: List[Account],
    db: Session,
    region_hint: str = None
) -> Dict[str, str]:
    """
    Batch select nodes for multiple accounts.
    Returns: {account_id: node_id}
    """
    result = {}
    for account in accounts:
        node_id = select_node_for_account(multi_node_client, account, db, region_hint)
        if node_id:
            result[str(account.id)] = node_id
    return result
