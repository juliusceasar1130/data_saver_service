# MySQL vs PostgreSQL 主要差异说明

> ⚠️ **已弃用 (DEPRECATED) — 标记日期: 2026-08-27**
> 本文件为「记录型方案」迁移配套文档。
> 当前正式方案为「RB位置状态版」（PostgreSQL），定义见项目根目录 [create_tables_postgresql.sql](../../../create_tables_postgresql.sql)。
> 其中 MySQL/PG 语法差异内容仍可作通用参考，整体仅供历史查阅。

本文档说明了在从 MySQL 迁移到 PostgreSQL 时需要注意的主要语法和功能差异。

## 1. 核心语法差异

### 1.1 自增主键

| MySQL | PostgreSQL |
|-------|-----------|
| `id BIGINT AUTO_INCREMENT PRIMARY KEY` | `id BIGSERIAL PRIMARY KEY` |
| `id INT AUTO_INCREMENT PRIMARY KEY` | `id SERIAL PRIMARY KEY` |

**说明**：
- PostgreSQL 使用 `SERIAL` 和 `BIGSERIAL` 类型，它们会自动创建序列（SEQUENCE）
- `SERIAL` = `INTEGER` + 自动序列
- `BIGSERIAL` = `BIGINT` + 自动序列

### 1.2 布尔类型

| MySQL | PostgreSQL |
|-------|-----------|
| `BOOLEAN` (实际存储为 TINYINT) | `BOOLEAN` (真正的布尔类型) |
| 值：`TRUE`, `FALSE`, `1`, `0` | 值：`TRUE`, `FALSE`, `'t'`, `'f'`, `'yes'`, `'no'`, `1`, `0` |

### 1.3 时间戳和自动更新

**MySQL 方式：**
```sql
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
```

**PostgreSQL 方式：**
```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

-- 需要创建触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为每个表创建触发器
CREATE TRIGGER update_table_name_updated_at
    BEFORE UPDATE ON table_name
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**说明**：PostgreSQL 没有 `ON UPDATE CURRENT_TIMESTAMP`，需要使用触发器实现。

### 1.4 注释语法

**MySQL 方式：**
```sql
CREATE TABLE users (
    id INT PRIMARY KEY COMMENT '用户ID',
    name VARCHAR(50) COMMENT '用户名'
) COMMENT='用户表';
```

**PostgreSQL 方式：**
```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(50)
);

-- 表注释
COMMENT ON TABLE users IS '用户表';

-- 字段注释
COMMENT ON COLUMN users.id IS '用户ID';
COMMENT ON COLUMN users.name IS '用户名';
```

### 1.5 存储引擎

**MySQL：**
```sql
ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
```

**PostgreSQL：**
- 不需要指定存储引擎（PostgreSQL 只有一个存储引擎）
- 字符集在数据库级别设置，建表时不需要指定

## 2. 数据类型对照表

| 用途 | MySQL | PostgreSQL |
|------|-------|-----------|
| 自增整数 | `INT AUTO_INCREMENT` | `SERIAL` |
| 自增长整数 | `BIGINT AUTO_INCREMENT` | `BIGSERIAL` |
| 日期时间 | `DATETIME` | `TIMESTAMP` |
| 布尔值 | `BOOLEAN` / `TINYINT(1)` | `BOOLEAN` |
| 文本 | `VARCHAR(n)` | `VARCHAR(n)` 或 `TEXT` |
| 大文本 | `TEXT` | `TEXT` |

## 3. 查询语法差异

### 3.1 限制结果数量

| MySQL | PostgreSQL |
|-------|-----------|
| `LIMIT 10` | `LIMIT 10` ✅ (相同) |

### 3.2 字符串连接

| MySQL | PostgreSQL |
|-------|-----------|
| `CONCAT(a, b)` | `a \|\| b` 或 `CONCAT(a, b)` |

### 3.3 当前时间

| MySQL | PostgreSQL |
|-------|-----------|
| `NOW()` | `NOW()` 或 `CURRENT_TIMESTAMP` ✅ |
| `CURDATE()` | `CURRENT_DATE` |

### 3.4 大小写敏感性

**MySQL：**
- 表名和列名默认不区分大小写（Windows/Mac）
- 字符串比较默认不区分大小写

**PostgreSQL：**
- 标识符（表名、列名）区分大小写，但会自动转为小写（除非用双引号）
- 字符串比较区分大小写
- 使用 `ILIKE` 进行不区分大小写的模糊查询

```sql
-- MySQL
SELECT * FROM users WHERE name LIKE '%john%';  -- 不区分大小写

-- PostgreSQL
SELECT * FROM users WHERE name ILIKE '%john%';  -- 不区分大小写
SELECT * FROM users WHERE name LIKE '%john%';   -- 区分大小写
```

## 4. Python 连接库差异

### MySQL 连接
```python
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='password',
    database='vehicle_db'
)
```

### PostgreSQL 连接
```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    user='postgres',
    password='password',
    database='vehicle_db'
)
```

或使用 `psycopg2` 的连接字符串：
```python
conn = psycopg2.connect("postgresql://user:password@localhost/vehicle_db")
```

## 5. 部署建议

### 5.1 创建数据库
```sql
-- 创建数据库（使用 UTF8 编码）
CREATE DATABASE vehicle_db
    WITH ENCODING 'UTF8'
    LC_COLLATE = 'zh_CN.UTF-8'
    LC_CTYPE = 'zh_CN.UTF-8'
    TEMPLATE = template0;
```

### 5.2 执行建表脚本
```bash
# 方式1：使用 psql 命令行
psql -U postgres -d vehicle_db -f 3_PostgreSQL数据库建表脚本.sql

# 方式2：在 psql 交互式环境中
\i /path/to/3_PostgreSQL数据库建表脚本.sql
```

### 5.3 查看表结构
```sql
-- 查看所有表
\dt

-- 查看表结构
\d vehicle_data

-- 查看表注释
SELECT obj_description('vehicle_data'::regclass);

-- 查看字段注释
SELECT 
    column_name, 
    col_description('vehicle_data'::regclass, ordinal_position) as comment
FROM information_schema.columns
WHERE table_name = 'vehicle_data';
```

## 6. 性能优化建议

### 6.1 索引
PostgreSQL 和 MySQL 的索引创建语法基本相同，但 PostgreSQL 支持更多索引类型：
- B-tree（默认）
- Hash
- GiST
- GIN
- BRIN

### 6.2 VACUUM
PostgreSQL 需要定期执行 VACUUM 来回收空间和更新统计信息：
```sql
-- 手动 VACUUM
VACUUM ANALYZE vehicle_data;

-- 建议启用自动 VACUUM（默认已启用）
```

## 7. 总结

主要需要修改的地方：
1. ✅ `AUTO_INCREMENT` → `SERIAL` / `BIGSERIAL`
2. ✅ `DATETIME` → `TIMESTAMP`
3. ✅ 注释语法：从 `COMMENT '...'` 改为 `COMMENT ON`
4. ✅ 自动更新时间戳：需要创建触发器
5. ✅ 移除 `ENGINE` 和 `CHARSET` 声明
6. ✅ Python 连接库：`mysql.connector` → `psycopg2`

已经为您准备好了完整的 PostgreSQL 建表脚本：`3_PostgreSQL数据库建表脚本.sql`
