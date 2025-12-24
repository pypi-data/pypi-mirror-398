"""
Data models for the Arca SDK
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any, Literal


@dataclass
class TableColumn:
    """Represents a column in an Arca table"""
    name: str
    type: Literal['VARCHAR', 'INTEGER', 'BIGINT', 'DOUBLE', 'BOOLEAN', 'TIMESTAMP', 'DATE', 'JSON']
    nullable: Optional[bool] = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SkillMetadata:
    """Metadata for table skills - helps AI understand how to use the table"""
    description: Optional[str] = None
    examples: Optional[List[str]] = None
    relationships: Optional[List[str]] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class MetadataField:
    """Metadata field definition for vector tables"""
    name: str
    type: str
    description: str
    examples: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class VectorSkillMetadata:
    """Metadata for vector skills - helps AI understand how to search the vector table"""
    description: Optional[str] = None
    metadata_fields: Optional[List[MetadataField]] = None
    search_examples: Optional[List[str]] = None
    filter_examples: Optional[List[str]] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests"""
        result = {}
        if self.description:
            result['description'] = self.description
        if self.metadata_fields:
            result['metadata_fields'] = [f.to_dict() for f in self.metadata_fields]
        if self.search_examples:
            result['search_examples'] = self.search_examples
        if self.filter_examples:
            result['filter_examples'] = self.filter_examples
        if self.notes:
            result['notes'] = self.notes
        return result
