from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# ==========================================
# 数据库模型定义文件 (models.py)
# 作用：将Python里的"类"映射成MySQL数据库里的"表"。
# 比如 User 类对应 users 表，类里面的属性就是表里的字段(列)。
# 这用到了ORM（对象关系映射）技术，不用手写SQL语句就能操作数据库。
# ==========================================

# 声明基类，所有的数据表类都要继承这个基类
Base = declarative_base()

class User(Base):
    """
    用户表 (存储平台所有用户的账号、密码、角色等信息)
    """
    __tablename__ = 'users' # 数据库中真实的表名
    
    # primary_key=True 代表这是主键(唯一标识符)，index=True代表为它建立索引提升查询速度
    id = Column(Integer, primary_key=True, index=True) 
    username = Column(String(50), unique=True, nullable=False) # 用户名，unique=True表示不能重复，nullable=False表示必填
    password = Column(String(100), nullable=False) # 密码（实际开发中这里应该存加密后的哈希值）
    role = Column(String(20), default="user") # 角色：'user' 为普通买家/卖家, 'admin' 为管理员
    balance = Column(Float, default=0.0) # 用户钱包余额（别人购买物品后，钱会加到这里）
    is_active = Column(Boolean, default=True) # 封号/启用状态标签
    
    # 关系映射：让Python知道用户和物品、收藏、购买记录之间的对应关系
    # cascade='all, delete-orphan' 表示级联删除：如果注销了用户，他发布的物品、收藏记录也会一并自动删除，保持数据库干净
    items = relationship('Item', back_populates='owner', cascade='all, delete-orphan')
    favorites = relationship('Favorite', back_populates='user', cascade='all, delete-orphan')
    purchases = relationship('Purchase', back_populates='buyer', cascade='all, delete-orphan', foreign_keys='Purchase.buyer_id')

class Category(Base):
    """
    商品分类表 (如：数码产品、书籍、生活用品)
    """
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False) # 分类的名称
    
    # 一个分类下有多个物品（一对多关系）
    items = relationship('Item', back_populates='category')

class Item(Base):
    """
    闲置物品表 (核心表，存储用户发布的所有二手商品信息)
    """
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False) # 物品名称
    description = Column(String(500)) # 物品详细描述
    price = Column(Float, nullable=False) # 价格
    status = Column(Integer, default=1) # 物品状态 -> 1:上架中, 2:已售出, 3:已下架
    views = Column(Integer, default=0)  # 浏览量统计 (每次别人点开详情就+1)
    images = Column(String(1000), default="[]") # 图片路径，使用JSON数组格式存入字符串中，支持多图
    price_history = Column(String(2000), default="[]") # 价格变化历史，记录历次改价（用于生成折线图）
    created_at = Column(DateTime, default=datetime.now) # 自动打上发布时的系统时间戳
    
    # 外键关联 (Foreign Key)：关联到其他表的ID
    # ondelete='CASCADE'表示主表(如User)被删时，当前记录跟着删；'SET NULL'表示主表记录被删时，当前字段设为空(不删商品本身)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE')) # 关联发布者的ID
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL')) # 关联商品分类的ID
    
    owner = relationship('User', back_populates='items') # 反向与User关联
    category = relationship('Category', back_populates='items') # 反向与Category关联
    favorited_by = relationship('Favorite', back_populates='item', cascade='all, delete-orphan')

class Favorite(Base):
    """
    收藏夹表 (多对多中间表，记录谁收藏了哪个物品)
    """
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE')) # 谁收藏的
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE')) # 收藏的啥
    created_at = Column(DateTime, default=datetime.now) # 什么时候收藏的
    
    user = relationship('User', back_populates='favorites')
    item = relationship('Item', back_populates='favorited_by')

class Announcement(Base):
    """
    公告表 (管理员发布的系统公告)
    """
    __tablename__ = 'announcements'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False) # 公告标题
    content = Column(String(1000)) # 公告正文
    images = Column(String(1000), default="[]") # 公告可能附带的图片 
    created_at = Column(DateTime, default=datetime.now)

class Purchase(Base):
    """
    订单/购买记录表 (记录一笔交易，谁买了谁的什么东西)
    """
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE')) # 买家ID
    seller_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL')) # 卖家ID
    item_id = Column(Integer, ForeignKey('items.id', ondelete='SET NULL')) # 商品ID
    
    # 这里特别设计了"快照"字段：
    # 为什么需要快照？因为商品如果后来被卖家删除了，不应该影响买家查看历史订单的商品名叫什么、当时花多少钱。
    item_title = Column(String(100))  # 存储购买时的商品名称快照
    price = Column(Float)  # 存储购买时的成交价格快照
    created_at = Column(DateTime, default=datetime.now) # 交易时间
    
    buyer = relationship('User', back_populates='purchases', foreign_keys=[buyer_id])
    seller = relationship('User', foreign_keys=[seller_id])
    item = relationship('Item', foreign_keys=[item_id])