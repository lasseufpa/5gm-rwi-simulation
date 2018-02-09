import numpy as np

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as db
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class FormatError(Exception):
    pass


class Episode(Base):
    __tablename__ = 'episodes'

    id = db.Column(db.Integer, primary_key=True)

    insite_pah = db.Column(db.String)
    sumo_path = db.Column(db.String)
    simulation_time_begin = db.Column(db.Integer)
    sampling_time = db.Column(db.Float)

    @property
    def number_of_scenes(self):
        return len(self.scenes)


class InsiteObject(Base):
    __tablename__ = 'objects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    _dimension = db.Column(db.LargeBinary)
    _vertice_array = db.Column(db.LargeBinary)
    _position = db.Column(db.LargeBinary)

    scene_id = db.Column(db.Integer, db.ForeignKey('scenes.id'))
    scene = relationship("Scene", backref="objects")

    @property
    def dimension(self):
        return np.frombuffer(self._dimension, np.float64).reshape((3,))

    @dimension.setter
    def dimension(self, v):
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._dimension = v.tobytes()

    @property
    def position(self):
        return np.frombuffer(self._position, np.float64).reshape((3,))

    @position.setter
    def position(self, v):
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._position = v.tobytes()

    @property
    def vertice_array(self):
        return np.frombuffer(self._vertice_array, np.float64).reshape((-1,3))

    @vertice_array.setter
    def vertice_array(self, v):
        v = np.array(v, np.float64)
        if v.ndim != 2 or v.shape[1] != 3:
            raise FormatError()
        self._vertice_array = v.tobytes()


class InsiteReceiver(Base):
    __tablename__ = 'receivers'

    id = db.Column(db.Integer, primary_key=True)
    total_received_power = db.Column(db.Float)
    mean_time_of_arrival = db.Column(db.Float)
    _position = db.Column(db.LargeBinary)

    object_id = db.Column(db.Integer, db.ForeignKey('objects.id'))
    episode = relationship("InsiteObject", backref="receivers")

    @property
    def position(self):
        return np.frombuffer(self._position, np.float64).reshape((3,))

    @position.setter
    def position(self, v):
        v = np.array(v, np.float64)
        if v.shape != (3,):
            raise FormatError()
        self._position = v.tobytes()

    @property
    def number_of_rays(self):
        return len(self.rays)


class Ray(Base):
    __tablename__ = 'rays'

    id = db.Column(db.Integer, primary_key=True)
    departure_elevation = db.Column(db.Float)
    departure_azimuth = db.Column(db.Float)
    arrival_elevation = db.Column(db.Float)
    arrival_azimuth = db.Column(db.Float)
    path_gain = db.Column(db.Float)
    time_of_arrival = db.Column(db.Float)
    interactions = db.Column(db.String)

    receiver_id = db.Column(db.Integer, db.ForeignKey('receivers.id'))
    episode = relationship("InsiteReceiver", backref="rays")

    @property
    def is_los(self):
        return len(self.interactions.split('-')) == 2

class Scene(Base):
    __tablename__ = 'scenes'

    """- map between transmitters and mobile objects
            - map between receivers and mobile objects"""

    id = db.Column(db.Integer, primary_key=True)
    _study_area = db.Column(db.LargeBinary)

    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id'))
    episode = relationship("Episode", backref="scenes")

    @property
    def study_area(self):
        return np.frombuffer(self._study_area, np.float64).reshape((2, 3))

    @study_area.setter
    def study_area(self, v):
        v = np.array(v, np.float64)
        if v.shape != (2, 3):
            raise FormatError()
        self._study_area = v.tobytes()

    @property
    def number_of_transmitters(self):
        raise NotImplementedError()

    @property
    def number_of_receivers(self):
        n_rec = 0
        for obj in self.objects:
            n_rec += len(obj.receivers)
        return n_rec

    @property
    def number_of_mobile_objects(self):
        return len(self.objects)

#engine = create_engine('sqlite:////tmp/episodedata.db')
engine = create_engine('sqlite:///episodedata.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)