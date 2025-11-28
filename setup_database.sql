-- Contoso 报销系统数据库初始化脚本
-- 在 PostgreSQL 中运行此脚本来创建数据库和用户

-- 创建数据库
CREATE DATABASE contoso_expense;

-- 创建用户
CREATE USER contoso_user WITH PASSWORD 'password';

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE contoso_expense TO contoso_user;

-- 连接到新数据库
\c contoso_expense

-- 授予schema权限
GRANT ALL ON SCHEMA public TO contoso_user;

