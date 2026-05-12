from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, or_, desc, func, extract
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Category, Item, Favorite, Announcement
from datetime import datetime, timedelta
import secrets
import shutil
import os

# ==================== 1. 数据库配置 ====================
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/campus_trade"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="校园二手交易平台 - 前后端分离API")

@app.on_event("startup")
def init_default_data():
    """在服务启动时自动初始化外键依赖数据（例如默认的分类），避免前端发布时报 500 外键约束错误引发跨域异常"""
    db = SessionLocal()
    if db.query(Category).count() == 0:
        db.add(Category(name="默认分类"))
        db.add(Category(name="电子产品"))
        db.add(Category(name="生活用品"))
        db.commit()
    db.close()

# 挂载静态文件目录用来响应上传的图片
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== 2. 数据交互 Schema ====================
class ItemCreate(BaseModel):
    title: str
    description: str
    price: float
    category_id: int
    user_id: int
    images: str = "[]" # 接收前端传来的多图JSON结构

class UserAuth(BaseModel):
    username: str
    password: str

# 模拟的 Token 会话存储（课设足够，企业级应存 Redis 或 JWT）
fake_token_store = {}

def get_current_user(token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not token or token not in fake_token_store:
        raise HTTPException(status_code=401, detail="请先登录")
    user_id = fake_token_store[token]
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="无效的用户凭证")
    return user

# ==================== 身份验证与权限接口 ====================
@app.post("/api/register")
def register(user: UserAuth, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="用户名已被注册")
    # 初始化第一个用户为管理员（方便测试）
    is_admin = db.query(User).count() == 0
    new_user = User(username=user.username, password=user.password, role="admin" if is_admin else "user")
    db.add(new_user)
    db.commit()
    return {"message": "注册成功，请登录"}

@app.post("/api/login")
def login(user: UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username, User.password == user.password).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = secrets.token_hex(16)
    fake_token_store[token] = db_user.id
    return {
        "message": "登录成功", 
        "token": token, 
        "user_id": db_user.id, 
        "username": db_user.username,
        "role": db_user.role
    }

@app.post("/api/upload")
def upload_image(file: UploadFile = File(...)):
    """加分项：多图上传"""
    file_location = f"uploads/{secrets.token_hex(8)}_{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    return {"url": f"http://localhost:8000/{file_location}"}

# ==================== 3. 核心考核接口 ====================

@app.get("/api/items")
def get_items(
    keyword: Optional[str] = None,
    category_id: Optional[int] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    """分页查询物品、多条件组合筛选、模糊搜索"""
    query = db.query(Item).filter(Item.status == 1)
    
    if keyword:
        query = query.filter(or_(Item.title.contains(keyword), Item.description.contains(keyword)))
    if category_id:
        query = query.filter(Item.category_id == category_id)
    if min_price is not None:
        query = query.filter(Item.price >= min_price)
    if max_price is not None:
        query = query.filter(Item.price <= max_price)
    if start_date:
        query = query.filter(Item.created_at >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Item.created_at <= datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        
    total = query.count()
    items = query.order_by(desc(Item.created_at)).offset((page - 1) * size).limit(size).all()
    
    return {
        "total": total,
        "items": [{
            "id": i.id, "title": i.title, "price": i.price, "views": i.views,
            "created_at": i.created_at.strftime("%Y-%m-%d"),
            "category_name": i.category.name if i.category else "默认",
            "owner_name": i.owner.username if i.owner else "未知"
        } for i in items]
    }

@app.get("/api/items/{item_id}")
def get_item_detail(item_id: int, token: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """物品详情，含浏览量自增机制"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item: raise HTTPException(status_code=404)
    
    # 增加浏览量逻辑：如果不是作者本人且不是管理员，则增加浏览量
    should_increment = True
    if token and token in fake_token_store:
        user_id = fake_token_store[token]
        user = db.query(User).filter(User.id == user_id).first()
        if user and (user.role == 'admin' or user.id == item.user_id):
            should_increment = False
            
    if should_increment:
        item.views += 1
        db.commit()
    
    # 构造返回体加入 owner_name 等前端可能需要的字段（防止直接返回ORM引发部分关联属性缺失）
    # 但由于旧逻辑直接返回 item，前端可能期望原样。为了不破坏前端，我们直接转换成dict并加字段
    # 由于 item 是 ORM 对象，我们可以手动构建 dict：
    return {
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "price": item.price,
        "status": item.status,
        "views": item.views,
        "images": item.images,
        "created_at": item.created_at.isoformat(),
        "user_id": item.user_id,
        "category_name": item.category.name if item.category else "默认",
        "owner_name": item.owner.username if item.owner else "未知"
    }

@app.post("/api/items")
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """物品发布"""
    new_item = Item(**item.dict())
    db.add(new_item)
    db.commit()
    return {"message": "发布成功"}

@app.put("/api/items/{item_id}")
def edit_item(item_id: int, item_data: ItemCreate, db: Session = Depends(get_db)):
    """物品编辑"""
    item = db.query(Item).filter(Item.id == item_id).first()
    for key, value in item_data.dict().items():
        setattr(item, key, value)
    db.commit()
    return {"message": "修改成功"}

@app.delete("/api/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    """物品删除（级联删除由数据库模型保证）"""
    db.query(Item).filter(Item.id == item_id).delete()
    db.commit()
    return {"message": "删除成功"}

@app.post("/api/favorites")
def toggle_favorite(user_id: int, item_id: int, db: Session = Depends(get_db)):
    """收藏与取消收藏"""
    fav = db.query(Favorite).filter_by(user_id=user_id, item_id=item_id).first()
    if fav:
        db.delete(fav)
        msg = "取消收藏"
    else:
        db.add(Favorite(user_id=user_id, item_id=item_id))
        msg = "收藏成功"
    db.commit()
    return {"message": msg}

@app.get("/api/users/{user_id}/favorites")
def get_my_favorites(user_id: int, db: Session = Depends(get_db)):
    """我的收藏列表"""
    favs = db.query(Favorite).filter(Favorite.user_id == user_id).all()
    return [f.item for f in favs]

@app.get("/api/users/{user_id}/items")
def get_my_publishes(user_id: int, db: Session = Depends(get_db)):
    """我的发布列表"""
    return db.query(Item).filter(Item.user_id == user_id).all()

@app.put("/api/items/batch-status")
def batch_update_status(item_ids: List[int], status: int, db: Session = Depends(get_db)):
    """加分项：批量修改商品状态"""
    db.query(Item).filter(Item.id.in_(item_ids)).update({"status": status}, synchronize_session=False)
    db.commit()
    return {"message": "批量更新状态成功"}

@app.get("/api/hot-items")
def get_hot_items(db: Session = Depends(get_db)):
    """加分项：热门商品排行"""
    return db.query(Item).order_by(desc(Item.views)).limit(5).all()

@app.get("/api/price-trends")
def get_price_trends(db: Session = Depends(get_db)):
    """加分项：价格趋势展示 (全局按分类统计平均价格)"""
    trends = db.query(
        Category.name, 
        func.avg(Item.price).label("avg_price")
    ).join(Item, Category.id == Item.category_id).group_by(Category.name).all()
    
    return [{"category_name": t[0], "avg_price": round(t[1] or 0, 2)} for t in trends]

@app.get("/api/price-trends/{category_name}")
def get_category_price_trend(category_name: str, db: Session = Depends(get_db)):
    """类别下随时间变化的折线图价格趋势"""
    # 按日期(年-月-日)分组统计平均价格
    items = db.query(
        func.date(Item.created_at).label('date'),
        func.avg(Item.price).label('avg_price')
    ).join(Category, Category.id == Item.category_id)\
     .filter(Category.name == category_name)\
     .group_by('date').order_by('date').all()
    
    # 将日期转为字符串，价格保留两位小数
    return [{"date": str(i[0]), "avg_price": round(i[1] or 0, 2)} for i in items]

from fastapi.responses import StreamingResponse
import io
import csv

@app.get("/api/export-items")
def export_items(db: Session = Depends(get_db)):
    """加分项：数据导出 (CSV)"""
    items = db.query(Item).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "标题", "描述", "价格", "状态", "浏览量", "发布时间"])
    for item in items:
        writer.writerow([item.id, item.title, item.description, item.price, item.status, item.views, item.created_at.strftime("%Y-%m-%d %H:%M:%S")])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=items_export.csv"}
    )

class CategoryCreate(BaseModel):
    name: str

@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    return db.query(Category).all()

@app.post("/api/categories")
def create_category(data: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：添加分类"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    db.add(Category(name=data.name))
    db.commit()
    return {"message": "分类添加成功"}

@app.delete("/api/categories/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：删除分类"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404)
    db.delete(cat)
    db.commit()
    return {"message": "分类删除成功"}

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    images: str = "[]"

@app.get("/api/announcements")
def get_announcements(db: Session = Depends(get_db)):
    """获取所有公告(公开)"""
    return db.query(Announcement).order_by(desc(Announcement.created_at)).all()

@app.post("/api/announcements")
def create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：发布公告"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    ann = Announcement(title=data.title, content=data.content, images=data.images)
    db.add(ann)
    db.commit()
    return {"message": "公告发布成功"}

@app.delete("/api/announcements/{ann_id}")
def delete_announcement(ann_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """管理员：删除公告"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="无权操作")
    ann = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not ann:
        raise HTTPException(status_code=404)
    db.delete(ann)
    db.commit()
    return {"message": "公告删除成功"}

@app.post("/api/items/{item_id}/buy")
def buy_item(item_id: int, db: Session = Depends(get_db)):
    """模拟购买机制"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item or item.status != 1:
        raise HTTPException(status_code=400, detail="商品已被抢走或已下架")
    
    # 将商品状态设为已售出
    item.status = 2
    
    # 为卖家增加余额（如果是管理员在后台强制改status为3的话，是不走这个接口且不加钱的，符合逻辑要求）
    seller = db.query(User).filter(User.id == item.user_id).first()
    if seller:
        seller.balance += item.price
        
    db.commit()
    return {"message": "购买成功！"}

@app.get("/api/me/{user_id}")
def get_my_info(user_id: int, db: Session = Depends(get_db)):
    """同步刷新用户余额"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user: raise HTTPException(status_code=404)
    return {"username": user.username, "balance": round(user.balance,2), "role": user.role}

@app.get("/api/admin/all-items")
def admin_get_all_items(db: Session = Depends(get_db)):
    """管理员：强制查看与管理所有商品"""
    items = db.query(Item).order_by(desc(Item.created_at)).all()
    return [{"id": i.id, "title": i.title, "price": i.price, "status": i.status, "owner_name": i.owner.username if i.owner else "未知"} for i in items]

