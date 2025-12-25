from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from dataflow.db import Base

class PodSessionHistory(Base):
    """TABLE 'POD_SESSION_HISTORY'
    
    Attributes:
        id (int): Primary key for the pod session history entry.
        username (str): Foreign key referencing the USER table.
        pod_name (str): Name of the pod.
        namespace (str): Namespace of the pod.
        start_time (datetime): Timestamp of when the pod session started.
        stop_time (datetime): Timestamp of when the pod session stopped.
        session_duration_minutes (Numeric): Duration of the pod session in minutes.
        instance_type (str): Type of instance the pod is running on.
        node_name (str): Name of the node where the pod is running.
    """
    
    __tablename__ = 'POD_SESSION_HISTORY'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, ForeignKey('USER.user_name', ondelete="SET NULL"), nullable=True, index=True)
    pod_name = Column(String, nullable=False, index=True)
    namespace = Column(String, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True))
    stop_time = Column(DateTime(timezone=True), nullable=False)
    session_duration_minutes = Column(Numeric(10, 2))
    instance_type = Column(String, index=True)
    node_name = Column(String)