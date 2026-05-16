from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), default="user") # 'user' 也就是买家/卖家, 'admin' 为管理员
    balance = Column(Float, default=0.0) # 小加分项：账户余额（别人购买物品后钱会进这里）
    is_active = Column(Boolean, default=True) # 是否启用
    
    # 关系：级联删除用户的物品和收藏
    items = relationship('Item', back_populates='owner', cascade='all, delete-orphan')
    favorites = relationship('Favorite', back_populates='user', cascade='all, delete-orphan')
    purchases = relationship('Purchase', back_populates='buyer', cascade='all, delete-orphan', foreign_keys='Purchase.buyer_id')

class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    
    items = relationship('Item', back_populates='category')

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    status = Column(Integer, default=1) # 1:上架, 2:已售出, 3:下架 (加分项: 商品状态)
    views = Column(Integer, default=0)  # 加分项: 浏览量
    images = Column(String(1000), default="[]") # 加分项: 多图上传，存JSON数组或逗号分隔列表
    created_at = Column(DateTime, default=datetime.now) # 自动记录发布时间
    
    # 外键关联
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))
    
    owner = relationship('User', back_populates='items')
    category = relationship('Category', back_populates='items')
    favorited_by = relationship('Favorite', back_populates='item', cascade='all, delete-orphan')

class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='favorites')
    item = relationship('Item', back_populates='favorited_by')

class Announcement(Base):
    __tablename__ = 'announcements'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(String(1000))
    images = Column(String(1000), default="[]") 
    created_at = Column(DateTime, default=datetime.now)

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    seller_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    item_id = Column(Integer, ForeignKey('items.id', ondelete='SET NULL'))
    item_title = Column(String(100))  # 存储快照，防止商品被删除后看不到标题
    price = Column(Float)  # 存储购买时的价格
    created_at = Column(DateTime, default=datetime.now)
    
    buyer = relationship('User', back_populates='purchases', foreign_keys=[buyer_id])
    seller = relationship('User', foreign_keys=[seller_id])
    item = relationship('Item', foreign_keys=[item_id])