from airflow.settings import Session
from airflow.models import Connection


def conn_list(conn_type: str):
    sess = Session()
    try:
        ct = conn_type.lower()
        if ct in ("minio", "s3"):
            rows = sess.query(Connection).filter(Connection.conn_type.ilike("s3")).all()
        elif ct == "ssh":
            rows = sess.query(Connection).filter(Connection.conn_type == "ssh").all()
        else:
            rows = sess.query(Connection).all()
        return [c.conn_id for c in rows]
    finally:
        sess.close()
