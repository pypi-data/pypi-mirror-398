from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from dataflow.db import Base

class PodActivity(Base):
    """TABLE 'POD_ACTIVITY'
    
    Attributes:
        id (int): Primary key for the pod activity entry.
        username (str): Foreign key referencing the USER table.
        pod_name (str): Name of the pod.
        namespace (str): Namespace of the pod.
        start_time (datetime): Timestamp of when the pod started.
        stop_time (datetime): Timestamp of when the pod stopped.
        status (str): Current status of the pod.
        instance_type (str): Type of instance the pod is running on.
        node_name (str): Name of the node where the pod is running.
    """
    
    __tablename__ = 'POD_ACTIVITY'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, ForeignKey('USER.user_name', ondelete="SET NULL"), nullable=True, index=True)
    pod_name = Column(String, nullable=False, unique=True, index=True)
    namespace = Column(String, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True))
    stop_time = Column(DateTime(timezone=True))
    status = Column(String, nullable=False, index=True)
    instance_type = Column(String, index=True)
    node_name = Column(String)
    active_app_type_ids = Column(JSON, nullable=False)