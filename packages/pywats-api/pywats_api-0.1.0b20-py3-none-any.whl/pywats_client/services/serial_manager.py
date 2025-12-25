"""
Serial Number Manager for pyWATS Client

Handles reservation and management of serial numbers for offline use.
Maintains a persistent pool of reserved serial numbers that can be used
even when the server is unavailable.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ReservedSerial:
    """A reserved serial number"""
    serial_number: str
    reserved_at: str  # ISO format datetime
    used: bool = False
    used_at: Optional[str] = None
    test_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReservedSerial":
        """Create from dictionary"""
        return cls(**data)


class SerialNumberManager:
    """
    Manages offline serial number reservation.
    
    Features:
    - Reserve serial numbers from server for offline use
    - Persist reserved serials locally
    - Track used serials
    - Auto-replenish pool when online
    - Sync used serials back to server
    
    Usage:
        mgr = SerialNumberManager(
            wats_client=wats_client,
            storage_path=Path("./serials.json")
        )
        
        # Get a serial for offline use
        serial = mgr.get_reserved_serial()
        
        # Mark as used when test completes
        mgr.mark_used(serial, test_id="test_123")
        
        # Sync used serials back when online
        await mgr.sync_used_serials()
    """
    
    def __init__(self, storage_path: Path = None):
        """
        Initialize serial number manager.
        
        Args:
            storage_path: Path to store reserved serials (default: ./serials.json)
        """
        self.storage_path = storage_path or Path.cwd() / "serials.json"
        self._reserved: Dict[str, ReservedSerial] = {}
        self._load()
    
    def _load(self) -> None:
        """Load reserved serials from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for serial_str, serial_data in data.items():
                    self._reserved[serial_str] = ReservedSerial.from_dict(serial_data)
                
                logger.info(f"Loaded {len(self._reserved)} reserved serials")
            
            else:
                logger.info("No existing serials file, starting fresh")
        
        except Exception as e:
            logger.error(f"Failed to load reserved serials: {e}")
            self._reserved = {}
    
    def _save(self) -> bool:
        """Save reserved serials to storage"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                serial: reserved.to_dict()
                for serial, reserved in self._reserved.items()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved {len(self._reserved)} reserved serials")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save reserved serials: {e}")
            return False
    
    def add_reserved(self, serials: List[str]) -> int:
        """
        Add serials to the reserved pool.
        
        Args:
            serials: List of serial numbers to reserve
            
        Returns:
            Number of serials added
        """
        added = 0
        now = datetime.now().isoformat()
        
        for serial in serials:
            if serial not in self._reserved:
                self._reserved[serial] = ReservedSerial(
                    serial_number=serial,
                    reserved_at=now
                )
                added += 1
                logger.debug(f"Reserved serial: {serial}")
        
        if added > 0:
            self._save()
            logger.info(f"Added {added} new serial(s) to pool")
        
        return added
    
    def get_reserved_serial(self) -> Optional[str]:
        """
        Get an unused reserved serial.
        
        Returns:
            Serial number or None if none available
        """
        for serial, reserved in self._reserved.items():
            if not reserved.used:
                logger.debug(f"Returning reserved serial: {serial}")
                return serial
        
        logger.warning("No unused reserved serials available")
        return None
    
    def mark_used(self, serial: str, test_id: Optional[str] = None) -> bool:
        """
        Mark a serial as used.
        
        Args:
            serial: Serial number
            test_id: Optional test ID this serial was used for
            
        Returns:
            True if successful
        """
        if serial not in self._reserved:
            logger.warning(f"Serial not in reserved pool: {serial}")
            return False
        
        reserved = self._reserved[serial]
        if reserved.used:
            logger.warning(f"Serial already marked as used: {serial}")
            return False
        
        reserved.used = True
        reserved.used_at = datetime.now().isoformat()
        reserved.test_id = test_id
        
        logger.info(f"Marked serial as used: {serial}")
        return self._save()
    
    def get_pool_status(self) -> Dict[str, int]:
        """
        Get status of the serial pool.
        
        Returns:
            Dictionary with pool statistics
        """
        total = len(self._reserved)
        used = sum(1 for s in self._reserved.values() if s.used)
        unused = total - used
        
        return {
            "total": total,
            "used": used,
            "unused": unused,
        }
    
    def get_used_serials(self) -> List[Dict[str, Any]]:
        """
        Get list of used serials (for syncing back to server).
        
        Returns:
            List of used serial records with metadata
        """
        used_serials = []
        for serial, reserved in self._reserved.items():
            if reserved.used:
                used_serials.append({
                    "serial_number": serial,
                    "reserved_at": reserved.reserved_at,
                    "used_at": reserved.used_at,
                    "test_id": reserved.test_id,
                })
        
        return used_serials
    
    def clear_used_serials(self) -> int:
        """
        Clear used serials from the pool (after syncing to server).
        
        Returns:
            Number of serials cleared
        """
        cleared = 0
        serials_to_remove = [
            serial for serial, reserved in self._reserved.items()
            if reserved.used
        ]
        
        for serial in serials_to_remove:
            del self._reserved[serial]
            cleared += 1
        
        if cleared > 0:
            self._save()
            logger.info(f"Cleared {cleared} used serial(s) from pool")
        
        return cleared
    
    def remove_serial(self, serial: str) -> bool:
        """
        Remove a serial from the pool.
        
        Args:
            serial: Serial number to remove
            
        Returns:
            True if successful
        """
        if serial not in self._reserved:
            logger.warning(f"Serial not found: {serial}")
            return False
        
        del self._reserved[serial]
        self._save()
        logger.info(f"Removed serial from pool: {serial}")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detailed statistics about the serial pool.
        
        Returns:
            Dictionary with statistics
        """
        status = self.get_pool_status()
        
        used_serials = self.get_used_serials()
        oldest_reserved = None
        newest_reserved = None
        
        if self._reserved:
            dates = [
                datetime.fromisoformat(s.reserved_at)
                for s in self._reserved.values()
            ]
            oldest_reserved = min(dates).isoformat()
            newest_reserved = max(dates).isoformat()
        
        return {
            **status,
            "oldest_reserved": oldest_reserved,
            "newest_reserved": newest_reserved,
            "pending_sync": len(used_serials),
        }
    
    def is_depleted(self, threshold: int = 1) -> bool:
        """
        Check if unused serial pool is below threshold.
        
        Args:
            threshold: Minimum unused serials to maintain
            
        Returns:
            True if unused count is below threshold
        """
        status = self.get_pool_status()
        return status["unused"] < threshold
    
    def get_recommendations(self) -> List[str]:
        """
        Get recommendations for serial pool management.
        
        Returns:
            List of recommendation messages
        """
        recommendations = []
        status = self.get_pool_status()
        
        if status["unused"] == 0:
            recommendations.append("Serial pool is depleted, reserve more serials")
        elif status["unused"] < 5:
            recommendations.append(
                f"Serial pool is low ({status['unused']} remaining), "
                "consider reserving more when online"
            )
        
        if status["used"] > 100:
            recommendations.append(
                f"High number of used serials ({status['used']}), "
                "sync with server when online"
            )
        
        return recommendations
