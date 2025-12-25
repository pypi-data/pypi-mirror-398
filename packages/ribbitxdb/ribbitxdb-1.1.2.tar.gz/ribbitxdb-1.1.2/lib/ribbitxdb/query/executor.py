from typing import List, Dict, Any, Optional
import re
from functools import reduce
from .parser import SQLParser
from ..schema.metadata import SchemaManager, Table, Column
from ..schema.types import DataType, TypeConverter
from ..index.manager import IndexManager
from ..security.hasher import BLAKE2Hasher
from ..storage.engine import StorageEngine
from ..storage.page import Page
import pickle
import struct

class QueryExecutor:
    def __init__(self, storage: StorageEngine, schema: SchemaManager, 
                 index_manager: IndexManager, hasher: BLAKE2Hasher):
        self.storage = storage
        self.schema = schema
        self.index_manager = index_manager
        self.hasher = hasher
        self.parser = SQLParser()
        self.table_pages: Dict[str, List[int]] = {}
    
    def execute(self, sql: str) -> Any:
        parsed = self.parser.parse(sql)
        
        if parsed['type'] == 'CREATE':
            return self.execute_create(parsed)
        elif parsed['type'] == 'DROP':
            return self.execute_drop(parsed)
        elif parsed['type'] == 'INSERT':
            return self.execute_insert(parsed)
        elif parsed['type'] == 'SELECT':
            return self.execute_select(parsed)
        elif parsed['type'] == 'UPDATE':
            return self.execute_update(parsed)
        elif parsed['type'] == 'DELETE':
            return self.execute_delete(parsed)
        else:
            raise ValueError(f"Unsupported query type: {parsed['type']}")
    
    def execute_create(self, parsed: Dict[str, Any]) -> bool:
        table_name = parsed['table']
        
        columns = []
        for col_def in parsed['columns']:
            data_type = self._parse_data_type(col_def['type'])
            column = Column(
                name=col_def['name'],
                data_type=data_type,
                primary_key=col_def.get('primary_key', False),
                not_null=col_def.get('not_null', False),
                unique=col_def.get('unique', False)
            )
            columns.append(column)
        
        table = Table(table_name, columns)
        success = self.schema.create_table(table)
        
        if success:
            self.table_pages[table_name] = []
            if table.primary_key:
                self.index_manager.create_index(f"{table_name}_pk")
        
        return success
    
    def execute_drop(self, parsed: Dict[str, Any]) -> bool:
        table_name = parsed['table']
        
        if table_name in self.table_pages:
            del self.table_pages[table_name]
        
        self.index_manager.drop_index(f"{table_name}_pk")
        
        return self.schema.drop_table(table_name)
    
    def execute_insert(self, parsed: Dict[str, Any]) -> bool:
        table_name = parsed['table']
        table = self.schema.get_table(table_name)
        
        if not table:
            raise ValueError(f"Table {table_name} does not exist")
        
        columns = parsed.get('columns')
        values = parsed['values']
        
        if columns:
            row_dict = dict(zip(columns, values))
        else:
            row_dict = dict(zip([col.name for col in table.columns], values))
        
        for col in table.columns:
            if col.name not in row_dict:
                row_dict[col.name] = col.default
        
        if not table.validate_row(row_dict):
            raise ValueError("Row validation failed")
        
        row_data = [row_dict.get(col.name) for col in table.columns]
        row_hash = self.hasher.hash_row(row_data)
        
        serialized_row = pickle.dumps({
            'data': row_data,
            'hash': row_hash
        })
        
        row_size = len(serialized_row)
        row_with_size = struct.pack('<I', row_size) + serialized_row
        
        if table_name not in self.table_pages or not self.table_pages[table_name]:
            page = self.storage.allocate_page(Page.TYPE_TABLE)
            self.table_pages[table_name] = [page.header.page_id]
        else:
            page_id = self.table_pages[table_name][-1]
            page = self.storage.get_page(page_id)
        
        if page.get_free_space() < len(row_with_size):
            page = self.storage.allocate_page(Page.TYPE_TABLE)
            self.table_pages[table_name].append(page.header.page_id)
        
        offset = len(page.data) - page.get_free_space()
        page.write_record(offset, row_with_size)
        
        if table.primary_key:
            pk_value = row_dict[table.primary_key]
            self.index_manager.insert(f"{table_name}_pk", pk_value, page.header.page_id)
        
        return True
    
    def execute_select(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        table_name = parsed['table']
        table = self.schema.get_table(table_name)
        
        if not table:
            raise ValueError(f"Table {table_name} does not exist")
        
        # Start with base table scan
        all_rows = self._scan_table(table_name)
        
        # Handle JOINs
        if parsed.get('joins'):
            all_rows = self._execute_joins(all_rows, parsed['joins'], table_name)
        
        # Apply WHERE clause
        if parsed.get('where'):
            all_rows = self._filter_rows_advanced(all_rows, parsed['where'])
        
        # Handle aggregates and GROUP BY
        if parsed.get('aggregates') or parsed.get('group_by'):
            all_rows = self._execute_aggregates(all_rows, parsed)
        else:
            # Apply DISTINCT
            if parsed.get('distinct'):
                all_rows = self._apply_distinct(all_rows, parsed['columns'])
            
            # Apply column selection
            if parsed['columns'] != ['*']:
                all_rows = [{col: row.get(col) for col in parsed['columns']} for row in all_rows]
        
        # Apply ORDER BY
        if parsed.get('order_by'):
            all_rows = self._apply_order_by(all_rows, parsed['order_by'])
        
        # Apply LIMIT and OFFSET
        if parsed.get('offset'):
            all_rows = all_rows[parsed['offset']:]
        if parsed.get('limit'):
            all_rows = all_rows[:parsed['limit']]
        
        return all_rows
    
    def execute_update(self, parsed: Dict[str, Any]) -> int:
        table_name = parsed['table']
        table = self.schema.get_table(table_name)
        
        if not table:
            raise ValueError(f"Table {table_name} does not exist")
        
        updates = parsed['updates']
        where_clause = parsed.get('where')
        
        all_rows = self._scan_table(table_name)
        
        count = 0
        for row in all_rows:
            should_update = True
            if where_clause:
                should_update = self._matches_where_advanced(row, where_clause)
            
            if should_update:
                for col, value in updates.items():
                    if col in row:
                        row[col] = value
                        count += 1
        
        self._rewrite_table(table_name, all_rows, table)
        
        return count
    
    def execute_delete(self, parsed: Dict[str, Any]) -> int:
        table_name = parsed['table']
        table = self.schema.get_table(table_name)
        
        if not table:
            raise ValueError(f"Table {table_name} does not exist")
        
        where_clause = parsed.get('where')
        
        all_rows = self._scan_table(table_name)
        
        if where_clause:
            remaining_rows = [row for row in all_rows if not self._matches_where_advanced(row, where_clause)]
            deleted_count = len(all_rows) - len(remaining_rows)
        else:
            deleted_count = len(all_rows)
            remaining_rows = []
        
        self._rewrite_table(table_name, remaining_rows, table)
        
        return deleted_count
    
    def _execute_joins(self, left_rows: List[Dict[str, Any]], joins: List[Dict[str, Any]], 
                       left_table: str) -> List[Dict[str, Any]]:
        """Execute JOIN operations"""
        result = left_rows
        
        for join in joins:
            join_type = join['type']
            join_table = join['table']
            on_clause = join['on']
            
            right_rows = self._scan_table(join_table)
            
            if join_type == 'INNER':
                result = self._inner_join(result, right_rows, on_clause)
            elif join_type == 'LEFT':
                result = self._left_join(result, right_rows, on_clause)
            elif join_type == 'RIGHT':
                result = self._right_join(result, right_rows, on_clause)
        
        return result
    
    def _inner_join(self, left: List[Dict], right: List[Dict], on: Dict) -> List[Dict]:
        """Perform INNER JOIN"""
        result = []
        for left_row in left:
            for right_row in right:
                if left_row.get(on['left']) == right_row.get(on['right']):
                    merged = {**left_row, **right_row}
                    result.append(merged)
        return result
    
    def _left_join(self, left: List[Dict], right: List[Dict], on: Dict) -> List[Dict]:
        """Perform LEFT JOIN"""
        result = []
        for left_row in left:
            matched = False
            for right_row in right:
                if left_row.get(on['left']) == right_row.get(on['right']):
                    merged = {**left_row, **right_row}
                    result.append(merged)
                    matched = True
            if not matched:
                result.append(left_row)
        return result
    
    def _right_join(self, left: List[Dict], right: List[Dict], on: Dict) -> List[Dict]:
        """Perform RIGHT JOIN"""
        return self._left_join(right, left, {'left': on['right'], 'right': on['left']})
    
    def _execute_aggregates(self, rows: List[Dict[str, Any]], parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute aggregate functions with optional GROUP BY"""
        aggregates = parsed.get('aggregates', [])
        group_by = parsed.get('group_by')
        having = parsed.get('having')
        
        if group_by:
            # Group rows
            groups = {}
            for row in rows:
                key = tuple(row.get(col) for col in group_by)
                if key not in groups:
                    groups[key] = []
                groups[key].append(row)
            
            # Calculate aggregates for each group
            result = []
            for key, group_rows in groups.items():
                agg_row = {}
                for i, col in enumerate(group_by):
                    agg_row[col] = key[i]
                
                for agg in aggregates:
                    agg_row[agg['alias']] = self._calculate_aggregate(group_rows, agg)
                
                # Apply HAVING filter
                if having:
                    if self._matches_where_advanced(agg_row, having):
                        result.append(agg_row)
                else:
                    result.append(agg_row)
            
            return result
        else:
            # Single aggregate result
            result_row = {}
            for agg in aggregates:
                result_row[agg['alias']] = self._calculate_aggregate(rows, agg)
            return [result_row]
    
    def _calculate_aggregate(self, rows: List[Dict[str, Any]], agg: Dict[str, Any]) -> Any:
        """Calculate aggregate function value"""
        func = agg['function']
        col = agg['column']
        
        if func == 'COUNT':
            if col == '*':
                return len(rows)
            else:
                return sum(1 for row in rows if row.get(col) is not None)
        
        values = [row.get(col) for row in rows if row.get(col) is not None]
        
        if not values:
            return None
        
        if func == 'SUM':
            return sum(values)
        elif func == 'AVG':
            return sum(values) / len(values)
        elif func == 'MIN':
            return min(values)
        elif func == 'MAX':
            return max(values)
        
        return None
    
    def _apply_distinct(self, rows: List[Dict[str, Any]], columns: List[str]) -> List[Dict[str, Any]]:
        """Apply DISTINCT to remove duplicate rows"""
        seen = set()
        result = []
        
        for row in rows:
            if columns == ['*']:
                key = tuple(sorted(row.items()))
            else:
                key = tuple(row.get(col) for col in columns)
            
            if key not in seen:
                seen.add(key)
                result.append(row)
        
        return result
    
    def _apply_order_by(self, rows: List[Dict[str, Any]], order_by: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Apply ORDER BY clause"""
        def compare_key(row):
            keys = []
            for order in order_by:
                val = row.get(order['column'])
                # Handle None values
                if val is None:
                    val = '' if isinstance(val, str) else 0
                keys.append(val if order['direction'] == 'ASC' else self._negate_for_sort(val))
            return tuple(keys)
        
        return sorted(rows, key=compare_key)
    
    def _negate_for_sort(self, val):
        """Negate value for descending sort"""
        if isinstance(val, (int, float)):
            return -val
        elif isinstance(val, str):
            # Reverse string comparison
            return ''.join(chr(255 - ord(c)) for c in val)
        return val
    
    def _filter_rows_advanced(self, rows: List[Dict[str, Any]], where_clause: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter rows with advanced WHERE clause support"""
        return [row for row in rows if self._matches_where_advanced(row, where_clause)]
    
    def _matches_where_advanced(self, row: Dict[str, Any], where_clause: Dict[str, Any]) -> bool:
        """Check if row matches advanced WHERE clause"""
        if where_clause.get('type') == 'COMPOUND':
            # Handle compound conditions with AND/OR
            conditions = where_clause['conditions']
            operators = where_clause['operators']
            
            result = self._evaluate_condition(row, conditions[0])
            
            for i, op in enumerate(operators):
                next_result = self._evaluate_condition(row, conditions[i + 1])
                if op == 'AND':
                    result = result and next_result
                elif op == 'OR':
                    result = result or next_result
            
            return result
        else:
            return self._evaluate_condition(row, where_clause)
    
    def _evaluate_condition(self, row: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        column = condition['column']
        operator = condition['operator']
        value = condition['value']
        row_value = row.get(column)
        
        if operator == '=':
            return row_value == value
        elif operator == '!=':
            return row_value != value
        elif operator == '<':
            return row_value < value
        elif operator == '>':
            return row_value > value
        elif operator == '<=':
            return row_value <= value
        elif operator == '>=':
            return row_value >= value
        elif operator == 'LIKE':
            return self._match_like_pattern(str(row_value) if row_value is not None else '', value)
        elif operator == 'IN':
            return row_value in value
        elif operator == 'BETWEEN':
            return value[0] <= row_value <= value[1]
        
        return False
    
    def _match_like_pattern(self, text: str, pattern: str) -> bool:
        """Match LIKE pattern (% = any chars, _ = single char)"""
        regex_pattern = pattern.replace('%', '.*').replace('_', '.')
        return bool(re.match(f'^{regex_pattern}$', text, re.IGNORECASE))
    
    def _rewrite_table(self, table_name: str, rows: List[Dict[str, Any]], table: Table):
        if table_name in self.table_pages:
            for page_id in self.table_pages[table_name]:
                page = self.storage.get_page(page_id)
                if page:
                    page.clear()
        
        self.table_pages[table_name] = []
        
        for row in rows:
            row_data = [row.get(col.name) for col in table.columns]
            row_hash = self.hasher.hash_row(row_data)
            
            serialized_row = pickle.dumps({
                'data': row_data,
                'hash': row_hash
            })
            
            row_size = len(serialized_row)
            row_with_size = struct.pack('<I', row_size) + serialized_row
            
            if not self.table_pages[table_name]:
                page = self.storage.allocate_page(Page.TYPE_TABLE)
                self.table_pages[table_name] = [page.header.page_id]
            else:
                page_id = self.table_pages[table_name][-1]
                page = self.storage.get_page(page_id)
            
            if page.get_free_space() < len(row_with_size):
                page = self.storage.allocate_page(Page.TYPE_TABLE)
                self.table_pages[table_name].append(page.header.page_id)
            
            offset = len(page.data) - page.get_free_space()
            page.write_record(offset, row_with_size)
    
    def _scan_table(self, table_name: str) -> List[Dict[str, Any]]:
        if table_name not in self.table_pages:
            return []
        
        table = self.schema.get_table(table_name)
        rows = []
        
        for page_id in self.table_pages[table_name]:
            page = self.storage.get_page(page_id)
            if not page:
                continue
            
            offset = 0
            data_end = len(page.data) - page.get_free_space()
            
            while offset < data_end:
                try:
                    if offset + 4 > data_end:
                        break
                    
                    size_bytes = page.read_record(offset, 4)
                    if not size_bytes or size_bytes == b'\x00\x00\x00\x00':
                        break
                    
                    row_size = struct.unpack('<I', size_bytes)[0]
                    
                    if offset + 4 + row_size > data_end:
                        break
                    
                    serialized_row = page.read_record(offset + 4, row_size)
                    row_obj = pickle.loads(serialized_row)
                    
                    row_data = row_obj['data']
                    row_hash = row_obj['hash']
                    
                    if self.hasher.verify_row(row_data, row_hash):
                        row_dict = {col.name: row_data[i] for i, col in enumerate(table.columns)}
                        rows.append(row_dict)
                    
                    offset += 4 + row_size
                except Exception:
                    break
        
        return rows
    
    def _parse_data_type(self, type_str: str) -> DataType:
        type_upper = type_str.upper()
        if type_upper == 'INTEGER':
            return DataType.INTEGER
        elif type_upper == 'REAL':
            return DataType.REAL
        elif type_upper == 'TEXT':
            return DataType.TEXT
        elif type_upper == 'BLOB':
            return DataType.BLOB
        else:
            return DataType.TEXT
