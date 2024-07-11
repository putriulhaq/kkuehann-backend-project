import os
import psycopg2.pool
import atexit
import logging
from dotenv import load_dotenv
import time
from threading import Thread

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

pool = None 

class ConnectionPool:
    def __init__(self):
        self.min_conn = 1
        self.max_conn = 5
        self.idle_timeout = 30  # 5 menit dalam detik
        self.connections = {}
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                self.min_conn, 
                self.max_conn,
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            logger.debug("Connection pool created successfully")
            self.start_idle_connection_checker()
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to database: {e}")
            self.pool = None

    def get_connection(self):
        if self.pool:
            logger.debug("Getting connection from pool")
            return self.pool.getconn()
        else:
            logger.error("Connection pool is not initialized")
            raise Exception("Connection pool is not initialized")

    def return_connection(self, conn):
        if self.pool:
            logger.debug("Returning connection to pool")
            self.pool.putconn(conn)
        else:
            logger.error("Cannot return connection. Pool is not initialized")

    def close_all_connections(self):
        if self.pool:
            logger.debug("Closing all connections")
            self.pool.closeall()
        else:
            logger.error("Cannot close connections. Pool is not initialized")

    def check_idle_connections(self):
        current_time = time.time()
        for conn, last_used in list(self.connections.items()):
            if current_time - last_used > self.idle_timeout:
                logger.debug(f"Closing idle connection: {conn}")
                self.pool.putconn(conn)
                del self.connections[conn]

    def start_idle_connection_checker(self):
        def check_idle_periodically():
            while True:
                time.sleep(60)  # Periksa setiap menit
                self.check_idle_connections()

        Thread(target=check_idle_periodically, daemon=True).start()

def initializeConnectionPool():
    global pool
    pool = ConnectionPool()
    logger.debug(f"Initialized ConnectionPool: {pool}")

# Uncomment jika Anda ingin menutup koneksi saat keluar
# atexit.register(lambda: pool.close_all_connections() if pool else None)