from threading import RLock
import json
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import BigInteger

from gateway.dto import CommandRequestDTO
from gateway.store import ICommandStore


Relation = declarative_base()
Session = scoped_session(sessionmaker())


class CommandStore(ICommandStore):

    def __init__(self):
        self.engine = create_engine("sqlite:///test.db?check_same_thread=False")
        self.session = Session(bind=self.engine)
        self.lock = RLock()
        Relation.metadata.create_all(self.engine)

    def dump_params(self, params):
        return json.dumps(params)

    def get_commands(self, offset=0, limit=100):
        """Return a list containing the issued commands using the
        specified criteria.
        """
        return self.session.query(CommandDAO)\
            .order_by(CommandDAO.command_id.desc())\
            .offset(offset)\
            .limit(limit)

    def set_status(self, command_id, status):
        with self.lock:
            self.session.query(CommandDAO)\
                .filter(CommandDAO.command_id==command_id)\
                .update({'status': status})
            self.session.flush()
            self.session.commit()

    def _persist(self, command):
        dao = CommandDAO(
            command_type=command.command,
            params=self.dump_params(command.params),
            issuer=command.issuer,
            authenticated_by=command.authenticated_by,
            host=command.host
        )
        with self.lock:
            self.session.add(dao)
            self.session.flush()
            self.session.commit()
        return dao.command_id


class CommandDAO(Relation):
    __tablename__ = 'commands'
    __table_args__ = {
        'sqlite_autoincrement': True    
    }

    command_id = Column(Integer,
        primary_key=True,
        name='command_id'
    )

    command_type = Column(String,
        nullable=False,
        name='command_type'
    )

    timestamp = Column(BigInteger,
        default=lambda: int(time.time() * 1000),
        nullable=False,
        name='timestamp'
    )

    issuer = Column(BigInteger,
        nullable=False,
        name='issuer'
    )

    authenticated_by = Column(BigInteger,
        nullable=False,
        name='authenticated_by'
    )

    host = Column(String,
        nullable=False,
        name='host'
    )

    params = Column(String,
        nullable=False,
        name='params'
    )

    status = Column(String,
        nullable=False,
        default='pending',
        name='status'
    )
