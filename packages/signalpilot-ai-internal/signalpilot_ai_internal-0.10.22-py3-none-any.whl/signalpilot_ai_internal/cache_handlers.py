"""
Cache endpoint handlers for SignalPilot AI.
Provides REST API handlers for chat histories and app values caching.
"""

import json
from typing import Any, Dict, Optional

from jupyter_server.base.handlers import APIHandler
import tornado

from .cache_service import get_cache_service


class ChatHistoriesHandler(APIHandler):
    """Handler for chat histories cache operations"""
    
    @tornado.web.authenticated
    def get(self, chat_id=None):
        """Get chat histories or specific chat history"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            if chat_id:
                # Get specific chat history
                history = cache_service.get_chat_history(chat_id)
                if history is None:
                    self.set_status(404)
                    self.finish(json.dumps({
                        "error": "Chat history not found",
                        "chat_id": chat_id
                    }))
                else:
                    self.finish(json.dumps({
                        "chat_id": chat_id,
                        "history": history
                    }))
            else:
                # Get all chat histories
                histories = cache_service.get_chat_histories()
                self.finish(json.dumps({
                    "chat_histories": histories,
                    "count": len(histories)
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
    
    @tornado.web.authenticated
    def post(self, chat_id=None):
        """Create or update chat history"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return
            
            if chat_id:
                # Update specific chat history
                history_data = body.get('history')
                if history_data is None:
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "Missing 'history' field in request body"
                    }))
                    return
                
                success = cache_service.set_chat_history(chat_id, history_data)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "chat_id": chat_id,
                        "message": "Chat history updated successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to save chat history"
                    }))
            else:
                # Bulk update operation
                chat_histories = body.get('chat_histories', {})
                if not isinstance(chat_histories, dict):
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "'chat_histories' must be an object"
                    }))
                    return
                
                # Update each chat history
                failures = []
                successes = []
                
                for cid, history in chat_histories.items():
                    if cache_service.set_chat_history(cid, history):
                        successes.append(cid)
                    else:
                        failures.append(cid)
                
                self.finish(json.dumps({
                    "success": len(failures) == 0,
                    "updated": successes,
                    "failed": failures,
                    "message": f"Updated {len(successes)} chat histories, {len(failures)} failed"
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
    
    @tornado.web.authenticated
    def delete(self, chat_id=None):
        """Delete chat history or all chat histories"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            if chat_id:
                # Delete specific chat history
                success = cache_service.delete_chat_history(chat_id)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "chat_id": chat_id,
                        "message": "Chat history deleted successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to delete chat history"
                    }))
            else:
                # Clear all chat histories
                success = cache_service.clear_chat_histories()
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "message": "All chat histories cleared successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to clear chat histories"
                    }))
                    
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class AppValuesHandler(APIHandler):
    """Handler for app values cache operations"""
    
    @tornado.web.authenticated
    def get(self, key=None):
        """Get app values or specific app value"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            if key:
                # Get specific app value
                default = self.get_argument('default', None)
                try:
                    if default:
                        default = json.loads(default)
                except json.JSONDecodeError:
                    pass  # Use string default
                
                value = cache_service.get_app_value(key, default)
                self.finish(json.dumps({
                    "key": key,
                    "value": value
                }))
            else:
                # Get all app values
                values = cache_service.get_app_values()
                self.finish(json.dumps({
                    "app_values": values,
                    "count": len(values)
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
    
    @tornado.web.authenticated
    def post(self, key=None):
        """Create or update app value"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return
            
            if key:
                # Update specific app value
                value_data = body.get('value')
                if value_data is None:
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "Missing 'value' field in request body"
                    }))
                    return
                
                success = cache_service.set_app_value(key, value_data)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "key": key,
                        "message": "App value updated successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to save app value"
                    }))
            else:
                # Bulk update operation
                app_values = body.get('app_values', {})
                if not isinstance(app_values, dict):
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "'app_values' must be an object"
                    }))
                    return
                
                # Update each app value
                failures = []
                successes = []
                
                for k, value in app_values.items():
                    if cache_service.set_app_value(k, value):
                        successes.append(k)
                    else:
                        failures.append(k)
                
                self.finish(json.dumps({
                    "success": len(failures) == 0,
                    "updated": successes,
                    "failed": failures,
                    "message": f"Updated {len(successes)} app values, {len(failures)} failed"
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
    
    @tornado.web.authenticated
    def delete(self, key=None):
        """Delete app value or all app values"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            if key:
                # Delete specific app value
                success = cache_service.delete_app_value(key)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "key": key,
                        "message": "App value deleted successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to delete app value"
                    }))
            else:
                # Clear all app values
                success = cache_service.clear_app_values()
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "message": "All app values cleared successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to clear app values"
                    }))
                    
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CacheInfoHandler(APIHandler):
    """Handler for cache service information"""
    
    @tornado.web.authenticated
    def get(self):
        """Get cache service information and statistics"""
        try:
            cache_service = get_cache_service()
            info = cache_service.get_cache_info()
            self.finish(json.dumps(info))
            
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
