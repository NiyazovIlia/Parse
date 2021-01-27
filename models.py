from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, ForeignKey, Table

Base = declarative_base()


# Mixin - маленькие классы которые мы наследуем и они притягивают за собой необхожимые нам атрибуты общие
# позволяет не громоздить одним и тем же кодом в разных местах

class IdMixin:
    id = Column(Integer, autoincrement=True, primary_key=True)


class UrlMixin:
    url = Column(String, unique=True, nullable=False)  # nullable - нулевой


class NameMixin:
    name = Column(String, nullable=False)


# создаем общую вспомогательную таблицу для post и tag и обращаемся по имени в __tablename__
tag_post = Table(
    "tag_post",
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('tag_id', Integer, ForeignKey('tag.id'))
)

comment_post = Table(
    "comment_post",
    Base.metadata,
    Column('post_id', Integer, ForeignKey('post.id')),
    Column('comment_id', Integer, ForeignKey('comment.id'))
)


class Post(IdMixin, UrlMixin, Base):  # так как мы наследуемся от Mixin то можно не прописывать id и url
    __tablename__ = 'post'
    title = Column(String, unique=False, nullable=False)
    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship("Author")  # сюда вернется список авторов которые ссылаются на данный пост
    tags = relationship('Tag', secondary=tag_post)
    comments = relationship('Comment', secondary=comment_post)


class Author(IdMixin, UrlMixin, NameMixin, Base):
    __tablename__ = 'author'
    posts = relationship("Post")  # сюда вернется список постов которые ссылаются на данного автора


class Tag(IdMixin, UrlMixin, NameMixin, Base):
    __tablename__ = 'tag'
    posts = relationship('Post', secondary=tag_post)


class Comment(IdMixin, UrlMixin, NameMixin, Base):
    __tablename__ = 'comment'
    posts = relationship('Post', secondary=comment_post)
