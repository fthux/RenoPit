"""验证脚本：检查 SQLAlchemy 模型结构是否与 04-database-schema.md 一致"""
import sys
import os

# 在导入任何 app 模块之前设置环境变量，让 config 读取 SQLite URL
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["UPLOAD_DIR"] = "uploads"
os.environ["REPORT_DIR"] = "reports"

sys.path.insert(0, ".")

from sqlalchemy import create_engine, inspect

# 现在导入会使用 sqlite:///:memory: 连接
from app.core.database import Base, engine
from app.models import Project, ProjectImage, ProjectFile, Analysis, Report

# 重建所有表到 SQLite 内存数据库
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

inspector = inspect(engine)

def check(condition, msg):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {msg}")
    else:
        failed += 1
        print(f"  ❌ {msg}")

passed = 0
failed = 0

print("=" * 60)
print("阶段 1 验收：数据库模型 vs 04-database-schema.md")
print("=" * 60)

# --- projects 表 ---
print("\n📋 projects 表")
cols = {c["name"]: c for c in inspector.get_columns("projects")}
check("id" in cols, "id 列存在")
check("access_token" in cols, "access_token 列存在")
check("status" in cols, "status 列存在")
check("input_text" in cols, "input_text 列存在")
check("created_at" in cols, "created_at 列存在")
check("updated_at" in cols, "updated_at 列存在")

idxs = inspector.get_indexes("projects")
idx_names = {i["name"] for i in idxs}
check("idx_projects_access_token" in idx_names, "access_token 索引存在")
check("idx_projects_status" in idx_names, "status 索引存在")
check("idx_projects_created_at" in idx_names, "created_at 索引存在")

# --- project_images 表 ---
print("\n📋 project_images 表")
cols = {c["name"]: c for c in inspector.get_columns("project_images")}
check("id" in cols, "id 列存在")
check("project_id" in cols, "project_id 列存在")
check("original_filename" in cols, "original_filename 列存在")
check("storage_path" in cols, "storage_path 列存在")
check("file_size" in cols, "file_size 列存在")
check("width" in cols, "width 列存在")
check("height" in cols, "height 列存在")
check("created_at" in cols, "created_at 列存在")

fks = inspector.get_foreign_keys("project_images")
check(len(fks) > 0 and fks[0]["referred_table"] == "projects", "外键 → projects.id 存在")
idxs = inspector.get_indexes("project_images")
check(any("project_id" in i["column_names"] for i in idxs), "project_id 索引存在")

# --- project_files 表 ---
print("\n📋 project_files 表")
cols = {c["name"]: c for c in inspector.get_columns("project_files")}
check("id" in cols, "id 列存在")
check("project_id" in cols, "project_id 列存在")
check("original_filename" in cols, "original_filename 列存在")
check("storage_path" in cols, "storage_path 列存在")
check("file_type" in cols, "file_type 列存在")
check("extracted_text" in cols, "extracted_text 列存在")
check("file_size" in cols, "file_size 列存在")
check("created_at" in cols, "created_at 列存在")

fks = inspector.get_foreign_keys("project_files")
check(len(fks) > 0 and fks[0]["referred_table"] == "projects", "外键 → projects.id 存在")
idxs = inspector.get_indexes("project_files")
check(any("project_id" in i["column_names"] for i in idxs), "project_id 索引存在")

# --- analyses 表 ---
print("\n📋 analyses 表")
cols = {c["name"]: c for c in inspector.get_columns("analyses")}
check("id" in cols, "id 列存在")
check("project_id" in cols, "project_id 列存在")
check("raw_result_json" in cols, "raw_result_json 列存在")
check("error_message" in cols, "error_message 列存在")
check("created_at" in cols, "created_at 列存在")

fks = inspector.get_foreign_keys("analyses")
check(len(fks) > 0 and fks[0]["referred_table"] == "projects", "外键 → projects.id 存在")

uq_analyses = inspector.get_unique_constraints("analyses")
check(len(uq_analyses) == 0, "project_id 无 UNIQUE 约束（与 schema 一致）")

# --- reports 表 ---
print("\n📋 reports 表")
cols = {c["name"]: c for c in inspector.get_columns("reports")}
check("id" in cols, "id 列存在")
check("project_id" in cols, "project_id 列存在")
check("analysis_id" in cols, "analysis_id 列存在")
check("file_path" in cols, "file_path 列存在")
check("created_at" in cols, "created_at 列存在")

fks = inspector.get_foreign_keys("reports")
referred_tables = {fk["referred_table"] for fk in fks}
check("projects" in referred_tables, "外键 → projects.id 存在")
check("analyses" in referred_tables, "外键 → analyses.id 存在")

uq_reports = inspector.get_unique_constraints("reports")
check(len(uq_reports) > 0 and "analysis_id" in uq_reports[0]["column_names"], "analysis_id UNIQUE 约束存在")

# --- 总结 ---
print("\n" + "=" * 60)
total = passed + failed
print(f"验收结果：{passed}/{total} 通过")
if failed == 0:
    print("✅ 阶段 1 验收通过！所有模型与 04-database-schema.md 一致")
else:
    print(f"❌ 阶段 1 验收未通过：{failed} 项不匹配")
print("=" * 60)