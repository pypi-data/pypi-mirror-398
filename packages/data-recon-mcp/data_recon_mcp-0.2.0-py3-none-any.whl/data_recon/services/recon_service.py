"""Reconciliation check execution service."""

import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..models.datasource import DataSource, DataSourceType
from ..connectors import MySQLConnector, SnowflakeConnector, BaseConnector


class ReconService:
    """Service for executing reconciliation checks."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _jsonify(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""
        from decimal import Decimal
        from datetime import datetime, date
        
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._jsonify(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._jsonify(v) for v in obj]
        return obj
    
    def _get_datasource(self, name: str) -> DataSource:
        """Get data source by name."""
        ds = self.db.query(DataSource).filter(DataSource.name == name).first()
        if not ds:
            raise ValueError(f"Data source '{name}' not found")
        return ds
    
    def _get_connector(self, datasource: DataSource) -> BaseConnector:
        """Get appropriate connector for data source type."""
        config = json.loads(datasource.connection_config)
        
        if datasource.type == DataSourceType.MYSQL:
            return MySQLConnector(config)
        elif datasource.type == DataSourceType.SNOWFLAKE:
            return SnowflakeConnector(config)
        else:
            raise ValueError(f"Unsupported data source type: {datasource.type}")
    
    def _build_where_clause(self, partition_config: Optional[Dict[str, Any]]) -> Optional[str]:
        """Build WHERE clause from partition config."""
        if not partition_config:
            return None
        
        column = partition_config.get("column")
        start_value = partition_config.get("start_value")
        end_value = partition_config.get("end_value")
        
        conditions = []
        if start_value is not None:
            conditions.append(f"{column} >= '{start_value}'")
        if end_value is not None:
            conditions.append(f"{column} < '{end_value}'")
        
        return " AND ".join(conditions) if conditions else None
    
    def run_row_count_check(
        self,
        source_ds: str, source_db: str, source_table: str, source_schema: Optional[str],
        target_ds: str, target_db: str, target_table: str, target_schema: Optional[str],
        partition_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute row count comparison."""
        source = self._get_datasource(source_ds)
        target = self._get_datasource(target_ds)
        
        where_clause = self._build_where_clause(partition_config)
        
        source_connector = self._get_connector(source)
        target_connector = self._get_connector(target)
        
        with source_connector:
            source_count = source_connector.get_row_count(
                source_db, source_table, source_schema, where_clause
            )
        
        with target_connector:
            target_count = target_connector.get_row_count(
                target_db, target_table, target_schema, where_clause
            )
        
        difference = abs(source_count - target_count)
        max_count = max(source_count, target_count, 1)
        match_percentage = ((max_count - difference) / max_count) * 100
        
        return {
            "source_count": source_count,
            "target_count": target_count,
            "difference": difference,
            "match_percentage": round(match_percentage, 4),
            "match": source_count == target_count
        }
    
    def run_aggregate_check(
        self,
        source_ds: str, source_db: str, source_table: str, source_schema: Optional[str],
        target_ds: str, target_db: str, target_table: str, target_schema: Optional[str],
        columns: List[str],
        aggregates: List[str],
        partition_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute aggregate comparison."""
        source = self._get_datasource(source_ds)
        target = self._get_datasource(target_ds)
        
        where_clause = self._build_where_clause(partition_config)
        
        source_connector = self._get_connector(source)
        target_connector = self._get_connector(target)
        
        with source_connector:
            source_aggs = source_connector.get_aggregates(
                source_db, source_table, columns, aggregates, source_schema, where_clause
            )
        
        with target_connector:
            target_aggs = target_connector.get_aggregates(
                target_db, target_table, columns, aggregates, target_schema, where_clause
            )
        
        results = []
        all_match = True
        
        for col in columns:
            source_vals = source_aggs.get(col, {})
            target_vals = target_aggs.get(col, {})
            
            differences = {}
            col_match = True
            
            for agg in aggregates:
                s_val = source_vals.get(agg)
                t_val = target_vals.get(agg)
                
                # Handle numeric comparison with tolerance
                if s_val is not None and t_val is not None:
                    try:
                        s_float = float(s_val)
                        t_float = float(t_val)
                        diff = abs(s_float - t_float)
                        # Allow tiny floating point differences
                        if diff > 0.0001:
                            differences[agg] = diff
                            col_match = False
                    except (TypeError, ValueError):
                        if s_val != t_val:
                            differences[agg] = {"source": s_val, "target": t_val}
                            col_match = False
                elif s_val != t_val:
                    differences[agg] = {"source": s_val, "target": t_val}
                    col_match = False
            
            if not col_match:
                all_match = False
            
            results.append({
                "column": col,
                "source_values": source_vals,
                "target_values": target_vals,
                "differences": differences,
                "match": col_match
            })
        
        return self._jsonify({
            "columns": results,
            "all_match": all_match
        })
    
    def run_schema_check(
        self,
        source_ds: str, source_db: str, source_table: str, source_schema: Optional[str],
        target_ds: str, target_db: str, target_table: str, target_schema: Optional[str]
    ) -> Dict[str, Any]:
        """Execute schema comparison."""
        source = self._get_datasource(source_ds)
        target = self._get_datasource(target_ds)
        
        source_connector = self._get_connector(source)
        target_connector = self._get_connector(target)
        
        with source_connector:
            source_cols = source_connector.get_table_schema(source_db, source_table, source_schema)
        
        with target_connector:
            target_cols = target_connector.get_table_schema(target_db, target_table, target_schema)
        
        source_col_names = {col["name"].lower() for col in source_cols}
        target_col_names = {col["name"].lower() for col in target_cols}
        
        only_in_source = list(source_col_names - target_col_names)
        only_in_target = list(target_col_names - source_col_names)
        
        source_types = {col["name"].lower(): col["data_type"] for col in source_cols}
        target_types = {col["name"].lower(): col["data_type"] for col in target_cols}
        
        type_diffs = []
        for col_name in source_col_names & target_col_names:
            if source_types[col_name] != target_types[col_name]:
                type_diffs.append({
                    "column": col_name,
                    "source_type": source_types[col_name],
                    "target_type": target_types[col_name]
                })
        
        match = len(only_in_source) == 0 and len(only_in_target) == 0 and len(type_diffs) == 0
        
        return {
            "source_columns": source_cols,
            "target_columns": target_cols,
            "columns_only_in_source": only_in_source,
            "columns_only_in_target": only_in_target,
            "type_differences": type_diffs,
            "match": match
        }
    
    def run_sample_check(
        self,
        source_ds: str, source_db: str, source_table: str, source_schema: Optional[str],
        target_ds: str, target_db: str, target_table: str, target_schema: Optional[str],
        primary_key: List[str],
        sample_size: int = 100,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute sample row comparison."""
        source = self._get_datasource(source_ds)
        target = self._get_datasource(target_ds)
        
        source_connector = self._get_connector(source)
        target_connector = self._get_connector(target)
        
        # Get columns to compare
        compare_cols = columns if columns else None
        
        with source_connector:
            source_data = source_connector.get_sample_rows(
                source_db, source_table, sample_size, source_schema,
                compare_cols, primary_key
            )
        
        with target_connector:
            # Get target data for the same primary keys
            target_data = target_connector.get_sample_rows(
                target_db, target_table, sample_size * 2, target_schema,
                compare_cols, primary_key
            )
        
        # Index target rows by primary key
        pk_indices = [source_data["columns"].index(pk) for pk in primary_key]
        
        target_by_pk = {}
        for row in target_data["rows"]:
            pk_values = tuple(row[i] for i in pk_indices)
            target_by_pk[pk_values] = row
        
        matched = 0
        mismatched = 0
        missing_in_target = 0
        mismatches = []
        
        for source_row in source_data["rows"]:
            pk_values = tuple(source_row[i] for i in pk_indices)
            
            if pk_values not in target_by_pk:
                missing_in_target += 1
                continue
            
            target_row = target_by_pk[pk_values]
            
            # Compare values
            differences = []
            for i, col in enumerate(source_data["columns"]):
                if source_row[i] != target_row[i]:
                    differences.append({
                        "column": col,
                        "source_value": source_row[i],
                        "target_value": target_row[i]
                    })
            
            if differences:
                mismatched += 1
                mismatches.append({
                    "primary_key_values": dict(zip(primary_key, pk_values)),
                    "differences": differences
                })
            else:
                matched += 1
        
        total_compared = matched + mismatched + missing_in_target
        match_percentage = (matched / total_compared * 100) if total_compared > 0 else 100
        
        return {
            "sample_size": sample_size,
            "rows_compared": total_compared,
            "matched": matched,
            "mismatched": mismatched,
            "missing_in_target": missing_in_target,
            "missing_in_source": 0,  # Would need reverse check
            "mismatches": mismatches[:10],  # Limit to first 10
            "match_percentage": round(match_percentage, 2)
        }
