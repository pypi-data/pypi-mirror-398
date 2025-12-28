"""
Cursor Pagination - Keyset-based pagination for efficient traversal
No offset penalty - works seamlessly across shards.
"""

from typing import Any, Dict, List, Optional, Generic, TypeVar, Tuple
from dataclasses import dataclass
from base64 import b64encode, b64decode
import json


T = TypeVar("T")


@dataclass
class PageInfo:
    """Information about a page"""
    has_next: bool
    has_previous: bool
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    total_count: Optional[int] = None
    page_size: int = 0


@dataclass
class Page(Generic[T]):
    """A page of results"""
    items: List[T]
    page_info: PageInfo
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "pageInfo": {
                "hasNext": self.page_info.has_next,
                "hasPrevious": self.page_info.has_previous,
                "nextCursor": self.page_info.next_cursor,
                "prevCursor": self.page_info.prev_cursor,
                "totalCount": self.page_info.total_count,
                "pageSize": self.page_info.page_size
            }
        }


class CursorCodec:
    """Encodes and decodes cursors"""
    
    @staticmethod
    def encode_cursor(data: Dict[str, Any]) -> str:
        """Encode cursor to string"""
        # Convert datetime to ISO string for JSON serialization
        serializable_data = {}
        for key, value in data.items():
            if hasattr(value, 'isoformat'):
                serializable_data[key] = value.isoformat()
            else:
                serializable_data[key] = value
        
        json_str = json.dumps(serializable_data, sort_keys=True)
        bytes_data = json_str.encode("utf-8")
        b64 = b64encode(bytes_data).decode("utf-8")
        return b64
    
    @staticmethod
    def decode_cursor(cursor: str) -> Dict[str, Any]:
        """Decode cursor from string"""
        try:
            bytes_data = b64decode(cursor.encode("utf-8"))
            json_str = bytes_data.decode("utf-8")
            return json.loads(json_str)
        except:
            return {}


class KeysetPaginator:
    """Implements keyset pagination"""
    
    def __init__(self, order_by: str = "id", direction: str = "ASC"):
        self.order_by = order_by
        self.direction = direction
        self.codec = CursorCodec()
    
    def paginate(self, items: List[Dict[str, Any]], page_size: int = 10,
                cursor: Optional[str] = None, 
                backward: bool = False) -> Page[Dict[str, Any]]:
        """Paginate items using keyset"""
        
        # Decode cursor if provided
        cursor_data = self.codec.decode_cursor(cursor) if cursor else None
        
        # Filter items based on cursor
        filtered_items = self._filter_by_cursor(items, cursor_data, backward)
        
        # Sort items
        sorted_items = sorted(
            filtered_items,
            key=lambda x: x.get(self.order_by, ""),
            reverse=(self.direction == "DESC")
        )
        
        # Get page + 1 extra to determine if there's a next page
        page_items = sorted_items[:page_size + 1]
        has_next = len(page_items) > page_size
        
        if has_next:
            page_items = page_items[:page_size]
        
        # Generate cursors
        next_cursor = None
        prev_cursor = None
        
        if page_items:
            if has_next:
                last_item = page_items[-1]
                next_cursor = self.codec.encode_cursor({
                    self.order_by: last_item[self.order_by]
                })
            
            if cursor_data:
                first_item = page_items[0]
                prev_cursor = self.codec.encode_cursor({
                    self.order_by: first_item[self.order_by]
                })
        
        page_info = PageInfo(
            has_next=has_next,
            has_previous=cursor_data is not None,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            page_size=page_size
        )
        
        return Page(items=page_items, page_info=page_info)
    
    def _filter_by_cursor(self, items: List[Dict[str, Any]], 
                         cursor_data: Optional[Dict], 
                         backward: bool) -> List[Dict[str, Any]]:
        """Filter items after cursor position"""
        if not cursor_data:
            return items
        
        cursor_value = cursor_data.get(self.order_by)
        if cursor_value is None:
            return items
        
        filtered = []
        for item in items:
            item_value = item.get(self.order_by)
            
            if backward:
                if item_value < cursor_value:
                    filtered.append(item)
            else:
                if item_value > cursor_value:
                    filtered.append(item)
        
        return filtered


class CursorPaginationBuilder:
    """Builds cursor pagination queries"""
    
    @staticmethod
    def build_query(table: str, page_size: int = 10, cursor: Optional[str] = None,
                   order_by: str = "id", direction: str = "ASC") -> str:
        """Build SQL query with cursor pagination"""
        
        query_parts = [f"SELECT * FROM {table}"]
        
        if cursor:
            # Decode cursor
            try:
                cursor_data = CursorCodec.decode_cursor(cursor)
                cursor_value = cursor_data.get(order_by)
                
                if cursor_value:
                    operator = ">" if direction == "ASC" else "<"
                    query_parts.append(f"WHERE {order_by} {operator} '{cursor_value}'")
            except:
                pass
        
        # Add ORDER BY
        query_parts.append(f"ORDER BY {order_by} {direction}")
        
        # Add LIMIT (fetch one extra to detect has_next)
        query_parts.append(f"LIMIT {page_size + 1}")
        
        return " ".join(query_parts)


class TimeWindowPaginator:
    """Paginate by time window"""
    
    def __init__(self, time_field: str = "created_at"):
        self.time_field = time_field
        self.codec = CursorCodec()
    
    def paginate_by_time(self, items: List[Dict[str, Any]], 
                        page_size: int = 10, 
                        cursor: Optional[str] = None,
                        window_days: int = 30) -> Page[Dict[str, Any]]:
        """Paginate by time window"""
        
        # Decode cursor if provided
        cursor_data = self.codec.decode_cursor(cursor) if cursor else None
        
        filtered_items = []
        for item in items:
            if cursor_data:
                # Filter items after cursor time
                item_time = item.get(self.time_field, "")
                cursor_time = cursor_data.get("timestamp", "")
                if item_time > cursor_time:
                    filtered_items.append(item)
            else:
                filtered_items.append(item)
        
        # Sort by time
        sorted_items = sorted(
            filtered_items,
            key=lambda x: x.get(self.time_field, ""),
            reverse=True
        )
        
        # Get page
        page_items = sorted_items[:page_size + 1]
        has_next = len(page_items) > page_size
        
        if has_next:
            page_items = page_items[:page_size]
        
        # Generate next cursor
        next_cursor = None
        if has_next and page_items:
            last_item = page_items[-1]
            next_cursor = self.codec.encode_cursor({
                "timestamp": last_item[self.time_field]
            })
        
        page_info = PageInfo(
            has_next=has_next,
            has_previous=cursor_data is not None,
            next_cursor=next_cursor,
            page_size=page_size
        )
        
        return Page(items=page_items, page_info=page_info)


class OffsetPaginationLegacy:
    """Legacy offset-based pagination (for comparison)"""
    
    @staticmethod
    def paginate(items: List[T], page_size: int = 10, 
                page_num: int = 1) -> Page[T]:
        """Paginate using offset"""
        offset = (page_num - 1) * page_size
        
        page_items = items[offset:offset + page_size]
        has_next = (offset + page_size) < len(items)
        has_previous = page_num > 1
        
        page_info = PageInfo(
            has_next=has_next,
            has_previous=has_previous,
            total_count=len(items),
            page_size=page_size
        )
        
        return Page(items=page_items, page_info=page_info)


class CursorPagination:
    """Main cursor pagination interface"""
    
    def __init__(self):
        self.keyset_paginator = KeysetPaginator()
        self.time_paginator = TimeWindowPaginator()
        self.codec = CursorCodec()
    
    def paginate_by_id(self, items: List[Dict[str, Any]], page_size: int = 10,
                      cursor: Optional[str] = None) -> Page[Dict[str, Any]]:
        """Paginate by ID (default)"""
        return self.keyset_paginator.paginate(items, page_size, cursor)
    
    def paginate_by_field(self, items: List[Dict[str, Any]], field: str,
                         page_size: int = 10, cursor: Optional[str] = None) -> Page[Dict[str, Any]]:
        """Paginate by specific field"""
        paginator = KeysetPaginator(order_by=field)
        return paginator.paginate(items, page_size, cursor)
    
    def paginate_by_time(self, items: List[Dict[str, Any]], page_size: int = 10,
                        cursor: Optional[str] = None) -> Page[Dict[str, Any]]:
        """Paginate by time"""
        return self.time_paginator.paginate_by_time(items, page_size, cursor)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pagination statistics"""
        return {
            "codec_type": "base64",
            "supported_pagination": ["keyset", "time", "offset"]
        }


if __name__ == "__main__":
    print("✓ Cursor pagination module loaded successfully")
