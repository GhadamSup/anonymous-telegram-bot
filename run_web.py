"""
Standalone Web Admin Panel
Run: python run_web.py
"""
import logging
from web.app import app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Web Admin Panel Starting...")
    logger.info("URL: http://localhost:5000")
    logger.info("Login: admin / admin123")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)