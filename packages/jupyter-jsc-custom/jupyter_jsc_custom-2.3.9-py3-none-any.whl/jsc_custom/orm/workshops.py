from jupyterhub.orm import Base
from jupyterhub.orm import JSONDict
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Integer
from sqlalchemy import Unicode


class JSONDictCache(JSONDict):
    cache_ok = True


class WorkshopShares(Base):
    """Workshop Shares"""

    __tablename__ = "workshops"
    id = Column(Integer, primary_key=True, autoincrement=True)
    instructor_user_id = Column(Integer, default=0)
    workshop_id = Column(Unicode(255), unique=True, nullable=False)
    user_options = Column(JSONDictCache, default={})

    def to_dict(self):
        return {
            "workshop_id": self.workshop_id,
            "instructor_user_id": self.instructor_user_id,
            "user_options": self.user_options,
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.workshop_id} (by {self.instructor_user_id}): {self.user_options}>"

    @classmethod
    def find(cls, db, user_options):
        """Find a group by name.
        Returns None if not found.
        """
        return db.query(cls).filter(cls.user_options == user_options).first()

    @classmethod
    def find_by_workshop_id(cls, db, workshop_id):
        """Find a group by name.
        Returns None if not found.
        """
        return db.query(cls).filter(cls.workshop_id == workshop_id).first()

    @classmethod
    def find_by_user_id(cls, db, instructor_user_id):
        """Find a group by name.
        Returns None if not found.
        """
        return db.query(cls).filter(cls.instructor_user_id == instructor_user_id).all()
