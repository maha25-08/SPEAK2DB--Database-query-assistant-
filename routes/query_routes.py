"""Query route registration for SPEAK2DB."""
import logging

def register_query_routes(app):
    """Register query routes on the Flask app."""
    try:
        from routes.query import query_bp
        app.register_blueprint(query_bp)
        logging.info("Query blueprint registered successfully")
    except ImportError as e:
        logging.error(f"Failed to import query blueprint: {e}")
    except Exception as e:
        logging.error(f"Failed to register query blueprint: {e}")
