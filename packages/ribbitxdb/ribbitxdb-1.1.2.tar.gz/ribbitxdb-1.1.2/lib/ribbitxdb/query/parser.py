import re
from typing import List, Dict, Any, Optional
from ..schema.types import DataType

class Token:
    def __init__(self, type: str, value: str):
        self.type = type
        self.value = value
    
    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class SQLParser:
    KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 
        'SET', 'DELETE', 'CREATE', 'TABLE', 'DROP', 'ALTER', 'PRIMARY', 
        'KEY', 'NOT', 'NULL', 'UNIQUE', 'INTEGER', 'TEXT', 'REAL', 'BLOB',
        'AND', 'OR', 'ORDER', 'BY', 'LIMIT', 'OFFSET', 'ASC', 'DESC',
        'JOIN', 'LEFT', 'RIGHT', 'INNER', 'ON', 'AS', 'DISTINCT', 'COUNT',
        'SUM', 'AVG', 'MIN', 'MAX', 'GROUP', 'HAVING', 'IN', 'LIKE', 'BETWEEN'
    }
    
    def __init__(self):
        self.tokens: List[Token] = []
        self.position = 0
    
    def tokenize(self, sql: str) -> List[Token]:
        sql = sql.strip()
        tokens = []
        i = 0
        
        while i < len(sql):
            if sql[i].isspace():
                i += 1
                continue
            
            if sql[i] in '(),;=<>!':
                if i + 1 < len(sql) and sql[i:i+2] in ('<=', '>=', '!=', '<>'):
                    tokens.append(Token('OPERATOR', sql[i:i+2]))
                    i += 2
                else:
                    tokens.append(Token('SYMBOL', sql[i]))
                    i += 1
                continue
            
            if sql[i] in ('"', "'"):
                quote = sql[i]
                i += 1
                start = i
                while i < len(sql) and sql[i] != quote:
                    if sql[i] == '\\' and i + 1 < len(sql):
                        i += 2
                    else:
                        i += 1
                tokens.append(Token('STRING', sql[start:i]))
                i += 1
                continue
            
            if sql[i].isdigit() or (sql[i] == '-' and i + 1 < len(sql) and sql[i + 1].isdigit()):
                start = i
                if sql[i] == '-':
                    i += 1
                while i < len(sql) and (sql[i].isdigit() or sql[i] == '.'):
                    i += 1
                tokens.append(Token('NUMBER', sql[start:i]))
                continue
            
            if sql[i].isalpha() or sql[i] == '_':
                start = i
                while i < len(sql) and (sql[i].isalnum() or sql[i] == '_'):
                    i += 1
                word = sql[start:i]
                if word.upper() in self.KEYWORDS:
                    tokens.append(Token('KEYWORD', word.upper()))
                else:
                    tokens.append(Token('IDENTIFIER', word))
                continue
            
            if sql[i] == '*':
                tokens.append(Token('STAR', '*'))
                i += 1
                continue
            
            i += 1
        
        self.tokens = tokens
        return tokens
    
    def parse(self, sql: str) -> Dict[str, Any]:
        self.tokenize(sql)
        self.position = 0
        
        if not self.tokens:
            raise ValueError("Empty SQL statement")
        
        first_token = self.tokens[0]
        
        if first_token.value == 'SELECT':
            return self.parse_select()
        elif first_token.value == 'INSERT':
            return self.parse_insert()
        elif first_token.value == 'UPDATE':
            return self.parse_update()
        elif first_token.value == 'DELETE':
            return self.parse_delete()
        elif first_token.value == 'CREATE':
            return self.parse_create()
        elif first_token.value == 'DROP':
            return self.parse_drop()
        else:
            raise ValueError(f"Unsupported SQL statement: {first_token.value}")
    
    def current_token(self) -> Optional[Token]:
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None
    
    def consume(self, expected: Optional[str] = None) -> Token:
        token = self.current_token()
        if token is None:
            raise ValueError("Unexpected end of SQL statement")
        if expected and token.value != expected:
            raise ValueError(f"Expected {expected}, got {token.value}")
        self.position += 1
        return token
    
    def parse_select(self) -> Dict[str, Any]:
        self.consume('SELECT')
        
        # Parse DISTINCT
        distinct = False
        if self.current_token() and self.current_token().value == 'DISTINCT':
            distinct = True
            self.consume('DISTINCT')
        
        # Parse columns with aggregate functions
        columns = []
        aggregates = []
        if self.current_token() and self.current_token().type == 'STAR':
            columns.append('*')
            self.consume()
        else:
            while True:
                # Check for aggregate functions
                if self.current_token() and self.current_token().value in ('COUNT', 'SUM', 'AVG', 'MIN', 'MAX'):
                    agg_func = self.consume().value
                    self.consume('(')
                    if self.current_token() and self.current_token().type == 'STAR':
                        agg_col = '*'
                        self.consume()
                    else:
                        agg_col = self.consume().value
                    self.consume(')')
                    
                    # Check for AS alias
                    alias = None
                    if self.current_token() and self.current_token().value == 'AS':
                        self.consume('AS')
                        alias = self.consume().value
                    
                    aggregates.append({
                        'function': agg_func,
                        'column': agg_col,
                        'alias': alias or f"{agg_func.lower()}_{agg_col}"
                    })
                    columns.append(alias or f"{agg_func.lower()}_{agg_col}")
                else:
                    col = self.consume().value
                    columns.append(col)
                
                if self.current_token() and self.current_token().value == ',':
                    self.consume(',')
                else:
                    break
        
        self.consume('FROM')
        table = self.consume().value
        
        # Parse JOINs
        joins = []
        while self.current_token() and self.current_token().value in ('JOIN', 'INNER', 'LEFT', 'RIGHT'):
            join_type = 'INNER'
            if self.current_token().value in ('LEFT', 'RIGHT', 'INNER'):
                join_type = self.consume().value
            self.consume('JOIN')
            
            join_table = self.consume().value
            self.consume('ON')
            
            left_col = self.consume().value
            self.consume('=')
            right_col = self.consume().value
            
            joins.append({
                'type': join_type,
                'table': join_table,
                'on': {'left': left_col, 'right': right_col}
            })
        
        # Parse WHERE
        where_clause = None
        if self.current_token() and self.current_token().value == 'WHERE':
            self.consume('WHERE')
            where_clause = self.parse_where_advanced()
        
        # Parse GROUP BY
        group_by = None
        if self.current_token() and self.current_token().value == 'GROUP':
            self.consume('GROUP')
            self.consume('BY')
            group_by = []
            while True:
                group_by.append(self.consume().value)
                if self.current_token() and self.current_token().value == ',':
                    self.consume(',')
                else:
                    break
        
        # Parse HAVING
        having = None
        if self.current_token() and self.current_token().value == 'HAVING':
            self.consume('HAVING')
            having = self.parse_where_advanced()
        
        # Parse ORDER BY
        order_by = None
        if self.current_token() and self.current_token().value == 'ORDER':
            self.consume('ORDER')
            self.consume('BY')
            order_by = []
            while True:
                col = self.consume().value
                direction = 'ASC'
                if self.current_token() and self.current_token().value in ('ASC', 'DESC'):
                    direction = self.consume().value
                order_by.append({'column': col, 'direction': direction})
                
                if self.current_token() and self.current_token().value == ',':
                    self.consume(',')
                else:
                    break
        
        # Parse LIMIT and OFFSET
        limit = None
        offset = None
        if self.current_token() and self.current_token().value == 'LIMIT':
            self.consume('LIMIT')
            limit = int(self.consume().value)
            
            if self.current_token() and self.current_token().value == 'OFFSET':
                self.consume('OFFSET')
                offset = int(self.consume().value)
        
        return {
            'type': 'SELECT',
            'distinct': distinct,
            'columns': columns,
            'aggregates': aggregates,
            'table': table,
            'joins': joins,
            'where': where_clause,
            'group_by': group_by,
            'having': having,
            'order_by': order_by,
            'limit': limit,
            'offset': offset
        }
    
    def parse_insert(self) -> Dict[str, Any]:
        self.consume('INSERT')
        self.consume('INTO')
        table = self.consume().value
        
        columns = None
        if self.current_token() and self.current_token().value == '(':
            self.consume('(')
            columns = []
            while True:
                col = self.consume()
                columns.append(col.value)
                if self.current_token() and self.current_token().value == ',':
                    self.consume(',')
                else:
                    break
            self.consume(')')
        
        self.consume('VALUES')
        self.consume('(')
        
        values = []
        while True:
            token = self.consume()
            if token.type == 'STRING':
                values.append(token.value)
            elif token.type == 'NUMBER':
                if '.' in token.value:
                    values.append(float(token.value))
                else:
                    values.append(int(token.value))
            elif token.value == 'NULL':
                values.append(None)
            else:
                values.append(token.value)
            
            if self.current_token() and self.current_token().value == ',':
                self.consume(',')
            else:
                break
        
        self.consume(')')
        
        return {
            'type': 'INSERT',
            'table': table,
            'columns': columns,
            'values': values
        }
    
    def parse_update(self) -> Dict[str, Any]:
        self.consume('UPDATE')
        table = self.consume().value
        self.consume('SET')
        
        updates = {}
        while True:
            col = self.consume().value
            self.consume('=')
            value_token = self.consume()
            
            if value_token.type == 'STRING':
                value = value_token.value
            elif value_token.type == 'NUMBER':
                value = float(value_token.value) if '.' in value_token.value else int(value_token.value)
            elif value_token.value == 'NULL':
                value = None
            else:
                value = value_token.value
            
            updates[col] = value
            
            if self.current_token() and self.current_token().value == ',':
                self.consume(',')
            else:
                break
        
        where_clause = None
        if self.current_token() and self.current_token().value == 'WHERE':
            self.consume('WHERE')
            where_clause = self.parse_where()
        
        return {
            'type': 'UPDATE',
            'table': table,
            'updates': updates,
            'where': where_clause
        }
    
    def parse_delete(self) -> Dict[str, Any]:
        self.consume('DELETE')
        self.consume('FROM')
        table = self.consume().value
        
        where_clause = None
        if self.current_token() and self.current_token().value == 'WHERE':
            self.consume('WHERE')
            where_clause = self.parse_where()
        
        return {
            'type': 'DELETE',
            'table': table,
            'where': where_clause
        }
    
    def parse_create(self) -> Dict[str, Any]:
        self.consume('CREATE')
        self.consume('TABLE')
        table = self.consume().value
        self.consume('(')
        
        columns = []
        while True:
            col_name = self.consume().value
            col_type = self.consume().value
            
            constraints = {
                'primary_key': False,
                'not_null': False,
                'unique': False
            }
            
            while self.current_token() and self.current_token().type == 'KEYWORD':
                keyword = self.current_token().value
                if keyword == 'PRIMARY':
                    self.consume('PRIMARY')
                    self.consume('KEY')
                    constraints['primary_key'] = True
                elif keyword == 'NOT':
                    self.consume('NOT')
                    self.consume('NULL')
                    constraints['not_null'] = True
                elif keyword == 'UNIQUE':
                    self.consume('UNIQUE')
                    constraints['unique'] = True
                else:
                    break
            
            columns.append({
                'name': col_name,
                'type': col_type,
                **constraints
            })
            
            if self.current_token() and self.current_token().value == ',':
                self.consume(',')
            else:
                break
        
        self.consume(')')
        
        return {
            'type': 'CREATE',
            'table': table,
            'columns': columns
        }
    
    def parse_drop(self) -> Dict[str, Any]:
        self.consume('DROP')
        self.consume('TABLE')
        table = self.consume().value
        
        return {
            'type': 'DROP',
            'table': table
        }
    
    def parse_where(self) -> Dict[str, Any]:
        left = self.consume().value
        operator = self.consume().value
        right_token = self.consume()
        
        if right_token.type == 'STRING':
            right = right_token.value
        elif right_token.type == 'NUMBER':
            right = float(right_token.value) if '.' in right_token.value else int(right_token.value)
        elif right_token.value == 'NULL':
            right = None
        else:
            right = right_token.value
        
        return {
            'column': left,
            'operator': operator,
            'value': right
        }
    
    def parse_where_advanced(self) -> Dict[str, Any]:
        """Parse WHERE clause with support for LIKE, IN, BETWEEN, AND, OR"""
        conditions = []
        logical_ops = []
        
        while True:
            left = self.consume().value
            operator = self.consume().value
            
            # Handle LIKE
            if operator == 'LIKE':
                pattern = self.consume().value
                conditions.append({
                    'column': left,
                    'operator': 'LIKE',
                    'value': pattern
                })
            # Handle IN
            elif operator == 'IN':
                self.consume('(')
                values = []
                while True:
                    token = self.consume()
                    if token.type == 'STRING':
                        values.append(token.value)
                    elif token.type == 'NUMBER':
                        values.append(float(token.value) if '.' in token.value else int(token.value))
                    else:
                        values.append(token.value)
                    
                    if self.current_token() and self.current_token().value == ',':
                        self.consume(',')
                    else:
                        break
                self.consume(')')
                conditions.append({
                    'column': left,
                    'operator': 'IN',
                    'value': values
                })
            # Handle BETWEEN
            elif operator == 'BETWEEN':
                start_token = self.consume()
                start_val = float(start_token.value) if start_token.type == 'NUMBER' and '.' in start_token.value else int(start_token.value) if start_token.type == 'NUMBER' else start_token.value
                
                self.consume('AND')
                
                end_token = self.consume()
                end_val = float(end_token.value) if end_token.type == 'NUMBER' and '.' in end_token.value else int(end_token.value) if end_token.type == 'NUMBER' else end_token.value
                
                conditions.append({
                    'column': left,
                    'operator': 'BETWEEN',
                    'value': [start_val, end_val]
                })
            # Handle standard operators
            else:
                right_token = self.consume()
                if right_token.type == 'STRING':
                    right = right_token.value
                elif right_token.type == 'NUMBER':
                    right = float(right_token.value) if '.' in right_token.value else int(right_token.value)
                elif right_token.value == 'NULL':
                    right = None
                else:
                    right = right_token.value
                
                conditions.append({
                    'column': left,
                    'operator': operator,
                    'value': right
                })
            
            # Check for AND/OR
            if self.current_token() and self.current_token().value in ('AND', 'OR'):
                logical_ops.append(self.consume().value)
            else:
                break
        
        if len(conditions) == 1:
            return conditions[0]
        
        return {
            'type': 'COMPOUND',
            'conditions': conditions,
            'operators': logical_ops
        }
