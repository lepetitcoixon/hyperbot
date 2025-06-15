from fastapi import FastAPI, HTTPException, Request # Add Request
from fastapi.responses import JSONResponse # Add JSONResponse
import uvicorn
import logging
from typing import Optional, List, Dict, Any
import os
import sys # Added sys import
import glob
import json # Added for config handling
import shutil # For backing up config file

# Adjust sys.path to allow running script directly from project root
# Get the absolute path of the current script (api_server.py)
current_script_path = os.path.abspath(__file__)
# Get the path of the 'src' directory
src_directory_path = os.path.dirname(current_script_path)
# Get the path of the project root directory (parent of 'src')
project_root_path = os.path.dirname(src_directory_path)
# Add the project root to sys.path if it's not already there
if project_root_path not in sys.path:
    sys.path.insert(0, project_root_path)

# Attempt to import the bot class
try:
    from src.ccxt_main import CCXTHyperliquidBot
except ImportError as e:
    logging.error(f"Failed to import CCXTHyperliquidBot: {e}")
    CCXTHyperliquidBot = None  # Ensure it's defined for later checks

# Global bot instance
bot_instance: Optional[CCXTHyperliquidBot] = None
bot_initialization_error: Optional[str] = None

# Configure basic logging for the API server
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI() # Moved app definition here

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the exception with traceback for server-side debugging
    logger.error(f"Unhandled exception for request {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected server error occurred: {type(exc).__name__} - {str(exc)}"},
    )

@app.on_event("startup")
async def startup_event():
    """
    Initialize the bot instance when the API server starts.
    """
    global bot_instance, bot_initialization_error
    if CCXTHyperliquidBot is not None:
        try:
            # Assuming config.json is in ../config/ relative to ccxt_main.py
            # Adjust the path if your CCXTHyperliquidBot expects it differently
            # or if you have a specific path for the API server.
            bot_instance = CCXTHyperliquidBot()
            logger.info("CCXTHyperliquidBot instance created successfully.")
        except Exception as e:
            logger.error(f"Error initializing CCXTHyperliquidBot: {e}", exc_info=True)
            bot_initialization_error = str(e)
            bot_instance = None # Ensure instance is None if init fails
    else:
        logger.error("CCXTHyperliquidBot class not available due to import error.")
        bot_initialization_error = "CCXTHyperliquidBot class could not be imported."

# app = FastAPI() # Removed from here

@app.get("/")
async def root():
    if bot_initialization_error:
        return {"message": "API server is running with errors", "error": bot_initialization_error}
    return {"message": "API server is running"}

@app.post("/api/start")
async def start_bot():
    global bot_instance, bot_initialization_error
    if bot_initialization_error:
        raise HTTPException(status_code=500, detail=f"Bot initialization failed: {bot_initialization_error}")
    if bot_instance is None:
        raise HTTPException(status_code=500, detail="Bot instance not available. Check server logs for import errors.")

    if bot_instance.running:
        raise HTTPException(status_code=400, detail="Bot is already running.")

    try:
        bot_instance.start()
        logger.info("Bot start command issued via API.")
        return {"message": "Bot started successfully."}
    except Exception as e:
        logger.error(f"Error starting bot via API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

@app.post("/api/stop")
async def stop_bot():
    global bot_instance, bot_initialization_error
    if bot_initialization_error:
        # Allow stopping even if init failed, as some resources might be partially active
        logger.warning("Attempting to stop bot despite initialization error.")

    if bot_instance is None and not bot_initialization_error: # If no instance and no init error, then something is wrong
        raise HTTPException(status_code=500, detail="Bot instance not available and no initialization error reported.")

    if bot_instance is not None: # Proceed if bot_instance exists
        if not bot_instance.running:
            raise HTTPException(status_code=400, detail="Bot is not running.")

        try:
            bot_instance.stop()
            logger.info("Bot stop command issued via API.")
            return {"message": "Bot stopped successfully."}
        except Exception as e:
            logger.error(f"Error stopping bot via API: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")
    else: # Handle case where bot_instance is None due to initialization error
        return {"message": "Bot was not fully initialized, no active bot process to stop. Check logs."}

@app.get("/api/status")
async def get_bot_status():
    global bot_instance, bot_initialization_error
    if bot_initialization_error and bot_instance is None:
        raise HTTPException(status_code=500, detail=f"Bot initialization failed: {bot_initialization_error}")
    if bot_instance is None:
        raise HTTPException(status_code=500, detail="Bot instance not available. Check server logs.")

    status_info = {
        "bot_running": bot_instance.running,
        "account_summary": None,
        "active_positions": []
    }

    try:
        if hasattr(bot_instance, 'order_manager') and bot_instance.order_manager is not None:
            status_info["account_summary"] = bot_instance.order_manager.get_account_summary()
        else:
            logger.warning("Order manager not available on bot instance for account summary.")
            status_info["account_summary"] = {"error": "Order manager not available."}
    except Exception as e:
        logger.error(f"Error getting account summary: {e}", exc_info=True)
        status_info["account_summary"] = {"error": f"Could not retrieve account summary: {str(e)}"}

    try:
        status_info["active_positions"] = bot_instance.get_real_positions_from_account()
    except Exception as e:
        logger.error(f"Error getting active positions: {e}", exc_info=True)
        status_info["active_positions"] = [{"error": f"Could not retrieve active positions: {str(e)}"}]

    return status_info

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs") # Assuming logs are in ../logs/ relative to api_server.py
    try:
        if not os.path.isdir(log_dir):
            raise HTTPException(status_code=404, detail=f"Log directory not found: {log_dir}")

        list_of_files = glob.glob(os.path.join(log_dir, "ccxt_bot_complete_*.log"))
        if not list_of_files:
            raise HTTPException(status_code=404, detail="No 'ccxt_bot_complete_*.log' files found in log directory.")

        latest_file = max(list_of_files, key=os.path.getctime)

        if not os.path.isfile(latest_file):
             raise HTTPException(status_code=404, detail=f"Latest log file not found: {latest_file}")

        with open(latest_file, "r", encoding="utf-8") as f:
            log_lines = f.readlines()

        return {"log_file": os.path.basename(latest_file), "lines": log_lines[-lines:]}

    except HTTPException as http_exc: # Re-raise HTTPExceptions to be handled by FastAPI
        raise http_exc
    except FileNotFoundError: # Should be caught by isfile or isdir checks, but as a fallback
        logger.error(f"Log file processing error: File not found (should have been caught earlier).", exc_info=True)
        raise HTTPException(status_code=404, detail="Log file not found during processing.")
    except Exception as e:
        logger.error(f"Error reading log file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not read log file: {str(e)}")

# Define path for config.json relative to this file (api_server.py)
# api_server.py is in src/, config.json is in config/
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")

@app.get("/api/config")
async def get_config():
    try:
        if not os.path.exists(CONFIG_FILE_PATH):
            raise HTTPException(status_code=404, detail=f"Configuration file not found at {CONFIG_FILE_PATH}")

        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        return config_data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from config file {CONFIG_FILE_PATH}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading configuration file: Invalid JSON format. {str(e)}")
    except Exception as e:
        logger.error(f"Error reading config file {CONFIG_FILE_PATH}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not read configuration file: {str(e)}")

@app.post("/api/config")
async def update_config(new_config: Dict[str, Any]):
    global bot_instance, bot_initialization_error

    # Basic validation
    required_keys = ["general", "strategy", "technical_analysis", "auth"]
    if not all(key in new_config for key in required_keys):
        missing_keys = [key for key in required_keys if key not in new_config]
        raise HTTPException(status_code=400, detail=f"Missing required configuration keys: {', '.join(missing_keys)}")

    # Backup current config
    backup_file_path = CONFIG_FILE_PATH + ".bak"
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            shutil.copy2(CONFIG_FILE_PATH, backup_file_path)
            logger.info(f"Configuration file backed up to {backup_file_path}")
    except Exception as e:
        logger.error(f"Error backing up configuration file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not back up configuration file: {str(e)}")

    # Write new config
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=4)
        logger.info("New configuration written to file.")
    except Exception as e:
        logger.error(f"Error writing new configuration to file: {e}", exc_info=True)
        # Attempt to restore backup if write fails
        if os.path.exists(backup_file_path):
            try:
                shutil.copy2(backup_file_path, CONFIG_FILE_PATH)
                logger.info("Restored configuration from backup due to write error.")
            except Exception as restore_e:
                logger.error(f"FATAL: Could not restore backup config after write error: {restore_e}")
        raise HTTPException(status_code=500, detail=f"Could not write new configuration: {str(e)}")

    # Re-initialize bot
    was_running = False
    if bot_instance and bot_instance.running:
        was_running = True
        try:
            logger.info("Stopping bot before re-initialization...")
            bot_instance.stop()
        except Exception as e:
            logger.error(f"Error stopping bot during config update: {e}", exc_info=True)
            # Proceed with re-initialization anyway, but log the error
            # raise HTTPException(status_code=500, detail=f"Could not stop bot for re-configuration: {str(e)}")

    logger.info("Re-initializing bot with new configuration...")
    bot_initialization_error = None # Reset previous init error
    if CCXTHyperliquidBot is not None:
        try:
            bot_instance = CCXTHyperliquidBot() # Config class within bot reads from file
            logger.info("CCXTHyperliquidBot instance re-initialized successfully.")

            if was_running:
                logger.info("Restarting bot with new configuration as it was running before...")
                bot_instance.start()
                logger.info("Bot restarted successfully after config update.")

            return {"message": "Configuration updated and bot re-initialized successfully." + (" Bot restarted." if was_running else " Bot remains stopped.")}
        except Exception as e:
            logger.error(f"Error re-initializing CCXTHyperliquidBot after config update: {e}", exc_info=True)
            bot_initialization_error = str(e)
            # Attempt to restore backup if bot re-init fails
            if os.path.exists(backup_file_path):
                try:
                    shutil.copy2(backup_file_path, CONFIG_FILE_PATH)
                    logger.info("Restored configuration from backup due to bot re-initialization error.")
                except Exception as restore_e:
                     logger.error(f"FATAL: Could not restore backup config after bot re-init error: {restore_e}")
            raise HTTPException(status_code=500, detail=f"New configuration applied, but bot failed to re-initialize: {str(e)}. Config may have been restored from backup if possible.")
    else:
        # This case should ideally not be reached if server started correctly
        bot_initialization_error = "CCXTHyperliquidBot class not available for re-initialization."
        logger.error(bot_initialization_error)
        raise HTTPException(status_code=500, detail=bot_initialization_error)


# Placeholder for other routes

if __name__ == "__main__":
    # This is for local testing only.
    # In a production environment, Uvicorn should be run by a process manager.
    uvicorn.run(app, host="0.0.0.0", port=8000)
