from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref

__all__ = [
    'BaseModel',
    'Database',
    'Page',
    'Mention',
]

BaseModel = declarative_base()


class Database(BaseModel):
    __tablename__ = 'database'

    id = Column(String(128), primary_key=True)
    title = Column(String(512))

    def __repr__(self):
        return f"Database(id={repr(self.id)}, title={repr(self.title)})"


class Page(BaseModel):
    __tablename__ = 'page'

    id = Column(String(128), primary_key=True)
    title = Column(String(512))
    url = Column(String(256))
    database_id = Column(String(128), ForeignKey('database.id'))
    database = relationship('Database', backref=backref('pages', cascade='all,delete'))
    parent_id = Column(String(128), ForeignKey('page.id'))
    parent = relationship('Page', backref=backref('child_pages', cascade='all,delete'), remote_side=[id])
    last_edited = Column(String(128), nullable=False)
    crawling_time = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"Page(id={repr(self.id)}, title={repr(self.title)}, last_edited={repr(self.last_edited)})"


class Mention(BaseModel):
    __tablename__ = 'mention'

    id = Column(Integer, primary_key=True)
    page_id = Column(String(128), ForeignKey('page.id'), nullable=False)
    page = relationship('Page', backref=backref('mentions', cascade='all,delete'), foreign_keys=[page_id])
    mentioned_id = Column(String(128), ForeignKey('page.id'), nullable=True)
    mentioned = relationship('Page', backref=backref('mentioned_by', cascade='all,delete'), foreign_keys=[mentioned_id])

    def __repr__(self):
        return f"Mention(id={repr(self.id)}, page_id={repr(self.page_id)}, mentioned_id={repr(self.mentioned_id)})"
