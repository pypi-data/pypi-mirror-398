import decimal
import json
import sqlite3
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
import boto3
import mysql.connector
import psycopg2
from psycopg2 import extras

class Database:
    DEFAULT_DB_TYPE = "sqlite"
    DEFAULT_TIMEOUT = 30
    
    CONFIGURED_CONNECTIONS = {}

    @classmethod
    def load_config(cls, config: dict):
        if "Database" in config.keys():
            tool_config = config["Database"]
            cls.DEFAULT_DB_TYPE = tool_config.get("DEFAULT_DB_TYPE", cls.DEFAULT_DB_TYPE)
            cls.DEFAULT_TIMEOUT = tool_config.get("DEFAULT_TIMEOUT", cls.DEFAULT_TIMEOUT)
            cls.CONFIGURED_CONNECTIONS = tool_config.get("CONNECTIONS", cls.CONFIGURED_CONNECTIONS)

    @classmethod
    def query(cls, sql: str, db_type: Optional[str] = None, connection_params: Optional[dict] = None) -> str:
        target_type = db_type or cls.DEFAULT_DB_TYPE
        params = connection_params or cls.CONFIGURED_CONNECTIONS.get(target_type, {})
        if target_type == "sqlite":
            return cls._query_sqlite(sql, params)
        elif target_type == "postgres":
            return cls._query_postgres(sql, params)
        elif target_type == "mysql":
            return cls._query_mysql(sql, params)
        elif target_type == "dynamodb":
            return cls._query_dynamodb(sql, params)
        else:
            return json.dumps({"error": f"Unsupported database type: {target_type}"})

    ### PRIVATE UTILITIES START
    @classmethod
    def _query_sqlite(cls, sql: str, params: dict) -> str:
        db_path = params.get("database", ":memory:")
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=cls.DEFAULT_TIMEOUT)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                rows = [dict(row) for row in cursor.fetchall()]
                return json.dumps(rows, default=cls._json_serializer)
            else:
                conn.commit()
                return json.dumps({"status": "success", "rows_affected": cursor.rowcount})
        except Exception as e:
            return json.dumps({"error": str(e)})
        finally:
            if conn:
                conn.close()

    @classmethod
    def _query_postgres(cls, sql: str, params: dict) -> str:
        if psycopg2 is None:
            return json.dumps({"error": "psycopg2 module not installed"})
        conn = None
        try:
            conn = psycopg2.connect(**params)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(sql)
                if sql.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    return json.dumps(rows, default=cls._json_serializer)
                else:
                    conn.commit()
                    return json.dumps({"status": "success", "rows_affected": cursor.rowcount})
        except Exception as e:
            return json.dumps({"error": str(e)})
        finally:
            if conn:
                conn.close()

    @classmethod
    def _query_mysql(cls, sql: str, params: dict) -> str:
        if mysql is None:
            return json.dumps({"error": "mysql-connector-python module not installed"})
        conn = None
        try:
            conn = mysql.connector.connect(**params)
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(sql)
                if sql.strip().upper().startswith("SELECT"):
                    rows = cursor.fetchall()
                    return json.dumps(rows, default=cls._json_serializer)
                else:
                    conn.commit()
                    return json.dumps({"status": "success", "rows_affected": cursor.rowcount})
        except Exception as e:
            return json.dumps({"error": str(e)})
        finally:
            if conn:
                conn.close()

    @classmethod
    def _query_dynamodb(cls, sql: str, params: dict) -> str:
        if boto3 is None:
            return json.dumps({"error": "boto3 module not installed"})
        try:
            session_kwargs = {}
            if "region_name" in params:
                session_kwargs["region_name"] = params["region_name"]
            if "aws_access_key_id" in params:
                session_kwargs["aws_access_key_id"] = params["aws_access_key_id"]
            if "aws_secret_access_key" in params:
                session_kwargs["aws_secret_access_key"] = params["aws_secret_access_key"]
            dynamodb = boto3.client('dynamodb', **session_kwargs)
            response = dynamodb.execute_statement(Statement=sql)
            items = response.get('Items', [])
            parsed_items = [cls._deserialize_dynamodb_item(item) for item in items]
            
            return json.dumps(parsed_items, default=cls._json_serializer)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @classmethod
    def _deserialize_dynamodb_item(cls, item: dict) -> dict:
        from boto3.dynamodb.types import TypeDeserializer
        deserializer = TypeDeserializer()
        return {k: deserializer.deserialize(v) for k, v in item.items()}

    @classmethod
    def _json_serializer(cls, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    ### PRIVATE UTILITIES END
