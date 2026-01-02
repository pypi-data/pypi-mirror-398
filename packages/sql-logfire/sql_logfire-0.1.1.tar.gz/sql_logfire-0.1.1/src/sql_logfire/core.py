import threading
import queue
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
from .models import Base, LogEntry

class LogFire:
    def __init__(self, db_engine):
        """
        Initializes LogFire with a SQLAlchemy engine.
        Automatically creates tables and starts a background worker.
        """
        self.engine = db_engine
        self.Session = sessionmaker(bind=self.engine)
        
        # 1. Auto-create tables (DDL)
        Base.metadata.create_all(self.engine)
        
        # 2. Setup Background Worker for Non-blocking logging
        self._log_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def log(self, message: str, level: str = "INFO"):
        """
        Public API: Puts log into queue and returns immediately.
        Does NOT block the main thread.
        """
        self._log_queue.put({"message": message, "level": level})

    def _process_queue(self):
        """
        Background thread that pulls from queue and writes to DB.
        """
        while not self._stop_event.is_set():
            try:
                # Block for 1 second waiting for an item
                record = self._log_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            # We got a record, let's write it
            session = self.Session()
            try:
                new_log = LogEntry(
                    message=record["message"], 
                    level=record["level"],
                    created_at=datetime.utcnow()
                )
                session.add(new_log)
                session.commit()
            except Exception as e:
                print(f"LogFire Error: Could not write to DB: {e}")
                session.rollback()
            finally:
                session.close()
                self._log_queue.task_done()

    def get_logs(self, minutes: int = 0, query_str: str = None):
        """
        Read API: Used by the UI to fetch data.
        """
        session = self.Session()
        try:
            query = session.query(LogEntry).order_by(desc(LogEntry.created_at))

            if minutes > 0:
                cutoff = datetime.utcnow() - timedelta(minutes=minutes)
                query = query.filter(LogEntry.created_at >= cutoff)
            
            if query_str:
                # Case-insensitive search
                query = query.filter(LogEntry.message.ilike(f"%{query_str}%"))

            return query.limit(500).all()
        finally:
            session.close()
            
    def shutdown(self):
        """Cleanly stop the worker thread"""
        self._stop_event.set()
        self._worker_thread.join()