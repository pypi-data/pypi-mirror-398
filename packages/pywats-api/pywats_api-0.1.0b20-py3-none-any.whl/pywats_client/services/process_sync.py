"""
Process Synchronization Service

Synchronizes process/operation data from WATS server for local caching.
This enables offline operation and faster lookups.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .connection import ConnectionService, ConnectionStatus

logger = logging.getLogger(__name__)


class ProcessSyncService:
    """
    Synchronizes process data from WATS server.
    
    Features:
    - Periodic sync of processes, levels, and product groups
    - Local caching for offline access
    - Automatic sync when coming online
    """
    
    def __init__(
        self,
        connection: ConnectionService,
        sync_interval: int = 300,
        cache_path: Optional[Path] = None
    ):
        self.connection = connection
        self.sync_interval = sync_interval
        self.cache_path = cache_path or self._get_default_cache_path()
        
        self._processes: List[Dict[str, Any]] = []
        self._levels: List[Dict[str, Any]] = []
        self._product_groups: List[Dict[str, Any]] = []
        
        self._sync_task: Optional[asyncio.Task] = None
        self._last_sync: Optional[datetime] = None
        self._running = False
        
        # Load cached data
        self._load_cache()
        
        # Register for connection status changes
        self.connection.on_status_change(self._on_connection_change)
    
    def _get_default_cache_path(self) -> Path:
        """Get default cache path"""
        import os
        if os.name == 'nt':
            base = Path(os.environ.get('APPDATA', '')) / 'pyWATS_Client' / 'cache'
        else:
            base = Path.home() / '.cache' / 'pywats_client'
        base.mkdir(parents=True, exist_ok=True)
        return base
    
    async def start(self) -> None:
        """Start the sync service"""
        if self._running:
            return
        
        self._running = True
        logger.info("Starting process sync service")
        
        # Initial sync if online
        if self.connection.status == ConnectionStatus.ONLINE:
            await self.sync()
        
        # Start periodic sync task
        self._sync_task = asyncio.create_task(self._sync_loop())
    
    async def stop(self) -> None:
        """Stop the sync service"""
        self._running = False
        
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
        
        logger.info("Process sync service stopped")
    
    async def sync(self) -> bool:
        """
        Synchronize data from WATS server.
        
        Returns True if sync successful.
        """
        client = self.connection.get_client()
        if not client:
            logger.warning("Cannot sync: not connected")
            return False
        
        try:
            logger.info("Syncing process data from WATS server...")
            
            # Sync processes
            processes = client.app.get_processes()
            if processes:
                self._processes = [
                    p.model_dump() if hasattr(p, 'model_dump') else dict(p) if hasattr(p, '__iter__') else {}
                    for p in processes
                ]
            
            # Sync levels
            levels = client.app.get_levels()
            if levels:
                self._levels = [
                    lv.model_dump() if hasattr(lv, 'model_dump') else dict(lv) if hasattr(lv, '__iter__') else {}
                    for lv in levels
                ]
            
            # Sync product groups
            product_groups = client.app.get_product_groups()
            if product_groups:
                self._product_groups = [
                    g.model_dump() if hasattr(g, 'model_dump') else dict(g) if hasattr(g, '__iter__') else {}
                    for g in product_groups
                ]
            
            self._last_sync = datetime.now()
            
            # Save to cache
            self._save_cache()
            
            logger.info(f"Sync complete: {len(self._processes)} processes, "
                       f"{len(self._levels)} levels, {len(self._product_groups)} product groups")
            return True
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False
    
    async def _sync_loop(self) -> None:
        """Background task for periodic sync"""
        while self._running:
            try:
                await asyncio.sleep(self.sync_interval)
                
                if self.connection.status == ConnectionStatus.ONLINE:
                    await self.sync()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
    
    def _on_connection_change(self, status: ConnectionStatus) -> None:
        """Handle connection status changes"""
        if status == ConnectionStatus.ONLINE and self._running:
            # Sync when coming online
            asyncio.create_task(self.sync())
    
    def _load_cache(self) -> None:
        """Load cached data from disk"""
        try:
            cache_file = self.cache_path / "processes_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._processes = data.get('processes', [])
                self._levels = data.get('levels', [])
                self._product_groups = data.get('product_groups', [])
                
                last_sync_str = data.get('last_sync')
                if last_sync_str:
                    self._last_sync = datetime.fromisoformat(last_sync_str)
                
                logger.info(f"Loaded cache: {len(self._processes)} processes")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    
    def _save_cache(self) -> None:
        """Save data to cache"""
        try:
            self.cache_path.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_path / "processes_cache.json"
            
            data = {
                'processes': self._processes,
                'levels': self._levels,
                'product_groups': self._product_groups,
                'last_sync': self._last_sync.isoformat() if self._last_sync else None
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    # Data access methods
    
    def get_processes(self) -> List[Dict[str, Any]]:
        """Get cached processes"""
        return self._processes.copy()
    
    def get_levels(self) -> List[Dict[str, Any]]:
        """Get cached levels"""
        return self._levels.copy()
    
    def get_product_groups(self) -> List[Dict[str, Any]]:
        """Get cached product groups"""
        return self._product_groups.copy()
    
    def get_process_by_code(self, process_code: str) -> Optional[Dict[str, Any]]:
        """Get process by process code"""
        for process in self._processes:
            if process.get('processCode') == process_code:
                return process
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get sync status"""
        return {
            'last_sync': self._last_sync.isoformat() if self._last_sync else None,
            'process_count': len(self._processes),
            'level_count': len(self._levels),
            'product_group_count': len(self._product_groups),
        }
