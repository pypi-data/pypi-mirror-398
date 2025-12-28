# DynamoDB Utilities

from typing import Dict, Set

# DynamoDB Reserved Keywords (subset of common ones)
# Full list: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ReservedWords.html
DYNAMODB_RESERVED_KEYWORDS: Set[str] = {
    'ABORT', 'ABSOLUTE', 'ACTION', 'ADD', 'AFTER', 'AGENT', 'AGGREGATE', 'ALL', 'ALSO', 'ALTER',
    'ANALYZE', 'AND', 'ANY', 'ARCHIVE', 'ARE', 'ARRAY', 'AS', 'ASC', 'ASSERT', 'AST', 'AT',
    'AUTHORIZATION', 'BACKUP', 'BATCH', 'BEFORE', 'BEGIN', 'BETWEEN', 'BIGINT', 'BINARY', 'BIT',
    'BLOB', 'BLOCK', 'BOOLEAN', 'BOTH', 'BREAK', 'BUCKET', 'BULK', 'BY', 'BYTE', 'CALL', 'CALLED',
    'CALLING', 'CAPACITY', 'CASCADE', 'CASCADED', 'CASE', 'CAST', 'CATALOG', 'CHAIN', 'CHANGE',
    'CHANGED', 'CHARACTER', 'CHECK', 'CLASS', 'CLOB', 'CLOSE', 'CLUSTER', 'CLUSTERED', 'CLUSTERING',
    'CLUSTERS', 'COALESCE', 'COLLATE', 'COLLATION', 'COLUMN', 'COLUMNS', 'COMBINE', 'COMMENT',
    'COMMIT', 'COMMITTED', 'COMPACT', 'COMPILE', 'COMPILED', 'CONCURRENTLY', 'CONDITION',
    'CONDITIONAL', 'CONFLICT', 'CONNECT', 'CONNECTION', 'CONSTRAINT', 'CONTAINS', 'CONVERT',
    'COPY', 'COST', 'CREATE', 'CROSS', 'CSV', 'CUBE', 'CURRENT', 'CURSOR', 'CYCLE', 'DATA',
    'DATABASE', 'DATABASES', 'DATE', 'DATETIME', 'DAY', 'DEALLOCATE', 'DEC', 'DECIMAL', 'DECLARE',
    'DEFAULT', 'DEFAULTS', 'DEFERRABLE', 'DEFERRED', 'DEFINE', 'DEFINED', 'DEFINITION', 'DELETE',
    'DELIMITER', 'DELIMITERS', 'DENSE_RANK', 'DEREF', 'DESC', 'DETACH', 'DETERMINISTIC', 'DICTIONARY',
    'DISABLE', 'DISCARD', 'DISTINCT', 'DO', 'DOCUMENT', 'DOMAIN', 'DOUBLE', 'DROP', 'EACH', 'ELEMENT',
    'ELSE', 'EMPTY', 'ENABLE', 'ENCODING', 'ENCRYPTED', 'END', 'ENUM', 'EQUAL', 'EQUALS', 'ERROR',
    'ERRORS', 'ESCAPE', 'EVENT', 'EXCEPT', 'EXCEPTION', 'EXCEPTIONS', 'EXCLUDE', 'EXCLUDING',
    'EXCLUSIVE', 'EXECUTE', 'EXISTS', 'EXPLAIN', 'EXPRESSION', 'EXTENDED', 'EXTENDS', 'EXTERNAL',
    'EXTRACT', 'FALSE', 'FAMILY', 'FETCH', 'FILTER', 'FIRST', 'FLOAT', 'FOLLOWING', 'FOR', 'FORCE',
    'FOREIGN', 'FORMAT', 'FORWARD', 'FOUNDATION', 'FRAME', 'FREE', 'FROM', 'FULL', 'FUNCTION',
    'FUNCTIONS', 'GENERAL', 'GENERATED', 'GET', 'GLOBAL', 'GO', 'GOTO', 'GRANT', 'GRANTED', 'GREATEST',
    'GROUP', 'GROUPING', 'GROUPS', 'HANDLER', 'HAVING', 'HEADER', 'HOLD', 'HOUR', 'IDENTITY', 'IF',
    'ILIKE', 'IMMEDIATE', 'IMMUTABLE', 'IMPLICIT', 'IMPORT', 'IN', 'INCLUDING', 'INCREMENT',
    'INCREMENTAL', 'INDEX', 'INDEXED', 'INDEXES', 'INDICATE', 'INHERITS', 'INITIALLY', 'INLINE',
    'INNER', 'INOUT', 'INPUT', 'INSENSITIVE', 'INSERT', 'INSTEAD', 'INT', 'INTEGER', 'INTERSECT',
    'INTERVAL', 'INTO', 'INVOKER', 'IS', 'ISNULL', 'ISOLATION', 'ITEM', 'ITEMS', 'ITERATE', 'JOIN',
    'KEY', 'KEYS', 'LABEL', 'LANGUAGE', 'LARGE', 'LAST', 'LATERAL', 'LEAD', 'LEADING', 'LEAKPROOF',
    'LEAST', 'LEFT', 'LENGTH', 'LEVEL', 'LIKE', 'LIMIT', 'LISTEN', 'LOAD', 'LOCAL', 'LOCALTIME',
    'LOCALTIMESTAMP', 'LOCATION', 'LOCK', 'LOCKS', 'LOGGED', 'MAPPING', 'MATCH', 'MATERIALIZED',
    'MAXVALUE', 'MINUS', 'MINUTE', 'MINVALUE', 'MODE', 'MODIFIES', 'MODIFY', 'MONTH', 'MOVE',
    'NAME', 'NAMES', 'NATIONAL', 'NATURAL', 'NCHAR', 'NCLOB', 'NESTED', 'NEW', 'NEXT', 'NO',
    'NONE', 'NOT', 'NOTHING', 'NOTIFY', 'NOTNULL', 'NOWAIT', 'NULL', 'NULLIF', 'NULLS', 'NUMBER',
    'NUMERIC', 'OBJECT', 'OF', 'OFF', 'OFFSET', 'OIDS', 'OLD', 'ON', 'ONLY', 'OPERATOR', 'OPTION',
    'OPTIONS', 'OR', 'ORDER', 'ORDINALITY', 'OTHERS', 'OUT', 'OUTER', 'OVER', 'OVERLAPS', 'OVERLAY',
    'OVERRIDING', 'OWNED', 'OWNER', 'PARSER', 'PARTIAL', 'PARTITION', 'PARTITIONED', 'PARTITIONS',
    'PASSING', 'PASSWORD', 'PLACING', 'PLANS', 'POLICY', 'POSITION', 'PRECEDING', 'PRECISION',
    'PREPARE', 'PREPARED', 'PRESERVE', 'PRIMARY', 'PRIOR', 'PRIVILEGES', 'PROCEDURAL', 'PROCEDURE',
    'PROGRAM', 'QUOTE', 'RANGE', 'RANK', 'READ', 'READS', 'REAL', 'REASSIGN', 'RECHECK', 'RECURSIVE',
    'REF', 'REFERENCES', 'REFERENCING', 'REFRESH', 'REINDEX', 'RELATIVE', 'RELEASE', 'RENAME',
    'REPEATABLE', 'REPLACE', 'REPLICA', 'RESET', 'RESTART', 'RESTRICT', 'RETURNING', 'RETURNS',
    'REVOKE', 'RIGHT', 'ROLE', 'ROLES', 'ROLLBACK', 'ROLLUP', 'ROUTINE', 'ROUTINES', 'ROW',
    'ROWS', 'RULE', 'SAVEPOINT', 'SCALE', 'SCHEMA', 'SCHEMAS', 'SCROLL', 'SEARCH', 'SECOND',
    'SECURITY', 'SELECT', 'SEQUENCE', 'SEQUENCES', 'SERIALIZABLE', 'SERVER', 'SESSION', 'SET',
    'SETS', 'SHARE', 'SHOW', 'SIMILAR', 'SIMPLE', 'SMALLINT', 'SNAPSHOT', 'SOME', 'SQL', 'STABLE',
    'STANDALONE', 'START', 'STATEMENT', 'STATISTICS', 'STDIN', 'STDOUT', 'STORAGE', 'STORED',
    'STRICT', 'STRIP', 'SUBSTRING', 'SYMMETRIC', 'SYSID', 'SYSTEM', 'TABLE', 'TABLES', 'TABLESPACE',
    'TEMP', 'TEMPLATE', 'TEMPORARY', 'TEXT', 'THEN', 'TIME', 'TIMESTAMP', 'TO', 'TRAILING',
    'TRANSACTION', 'TRANSFORM', 'TREAT', 'TRIGGER', 'TRIM', 'TRUE', 'TRUNCATE', 'TRUSTED', 'TYPE',
    'TYPES', 'UESCAPE', 'UNBOUNDED', 'UNCOMMITTED', 'UNENCRYPTED', 'UNION', 'UNIQUE', 'UNKNOWN',
    'UNLISTEN', 'UNLOGGED', 'UNTIL', 'UPDATE', 'USER', 'USERS', 'USING', 'VACUUM', 'VALID',
    'VALIDATE', 'VALIDATOR', 'VALUE', 'VALUES', 'VARCHAR', 'VARIADIC', 'VARYING', 'VERBOSE',
    'VERSION', 'VIEW', 'VIEWS', 'VOLATILE', 'WHEN', 'WHERE', 'WHITESPACE', 'WINDOW', 'WITH',
    'WITHIN', 'WITHOUT', 'WORK', 'WRAPPER', 'WRITE', 'XML', 'XMLATTRIBUTES', 'XMLCONCAT', 'XMLELEMENT',
    'XMLEXISTS', 'XMLFOREST', 'XMLPARSE', 'XMLPI', 'XMLROOT', 'XMLSERIALIZE', 'YEAR', 'YES', 'ZONE'
}


def build_expression_attribute_names(attributes: list[str]) -> Dict[str, str]:
    """
    Build ExpressionAttributeNames mapping for DynamoDB reserved keywords.

    Args:
        attributes: List of attribute names that may contain reserved keywords

    Returns:
        Dictionary mapping attribute placeholders to actual attribute names

    Example:
        >>> build_expression_attribute_names(['email', 'roles', 'name'])
        {'#email': 'email', '#roles': 'roles', '#name': 'name'}
    """
    expression_attribute_names = {}

    for attr in attributes:
        if attr.upper() in DYNAMODB_RESERVED_KEYWORDS:
            # Use placeholder for reserved keywords
            placeholder = f"#{attr}"
            expression_attribute_names[placeholder] = attr
        else:
            # For non-reserved keywords, we could still use placeholders for consistency
            # but it's optional. For now, we'll only add placeholders for reserved keywords.
            pass

    return expression_attribute_names


def replace_reserved_keywords_in_expression(expression: str, attribute_names: Dict[str, str]) -> str:
    """
    Replace reserved keyword attribute names with placeholders in expressions.

    Args:
        expression: The expression string (e.g., ProjectionExpression)
        attribute_names: The ExpressionAttributeNames mapping

    Returns:
        Expression with reserved keywords replaced by placeholders

    Example:
        >>> replace_reserved_keywords_in_expression(
        ...     "pk, sk, email, roles, name",
        ...     {'#email': 'email', '#roles': 'roles'}
        ... )
        "pk, sk, #email, #roles, name"
    """
    result = expression

    # Replace each reserved keyword with its placeholder
    for placeholder, attr_name in attribute_names.items():
        result = result.replace(attr_name, placeholder)

    return result


def build_projection_with_reserved_keywords(attributes: list[str]) -> tuple[str, Dict[str, str]]:
    """
    Convenience function to build projection expression and attribute names mapping.

    Args:
        attributes: List of attribute names for projection

    Returns:
        Tuple of (projection_expression, expression_attribute_names)

    Example:
        >>> projection, attr_names = build_projection_with_reserved_keywords(
        ...     ['pk', 'sk', 'email', 'roles', 'name']
        ... )
        >>> projection
        "pk, sk, #email, #roles, name"
        >>> attr_names
        {'#email': 'email', '#roles': 'roles'}
    """
    # Build the attribute names mapping
    expression_attribute_names = build_expression_attribute_names(attributes)

    # Create projection expression
    projection_expression = ", ".join(attributes)

    # Replace reserved keywords with placeholders
    if expression_attribute_names:
        projection_expression = replace_reserved_keywords_in_expression(
            projection_expression, expression_attribute_names
        )

    return projection_expression, expression_attribute_names
