"""
Email MCP Toolkit - Gmail operations using SimpleGmail.

Provides tools for sending, reading, searching, and managing Gmail emails.
Uses SimpleGmail library which wraps the Gmail API with OAuth2 authentication.
"""

import os
import json
import ssl
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from fastmcp import FastMCP

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.mcp.toolkits.serper_api import SerperApiMCPTools
from spellchecker import SpellChecker


class EmailMCPTools:
    """MCP toolkit for Gmail email operations using SimpleGmail."""
    
    def __init__(self, credentials_path: Optional[str] = None, **kwargs):
        """
        Initialize Email toolkit.
        
        Args:
            credentials_path: Path to OAuth2 credentials file (client_secret.json)
                             If None, will search in common locations
        """
        self._logger = Logger("MCP.Email")
        self._credentials_path = credentials_path
        self._gmail_client = None  # Lazy initialization
        self._token_path = None
    
    def _find_credentials(self) -> Optional[str]:
        """Find credentials file (client_secret.json or credentials.json) in common locations."""
        # Priority order:
        # 1. Environment variable
        # 2. Explicit credentials_path parameter
        # 3. Current directory (both filenames)
        # 4. Project root (both filenames)
        # 5. Home directory
        
        # Check environment variable first
        env_path = os.getenv("GMAIL_CREDENTIALS_PATH")
        if env_path and os.path.exists(env_path):
            self._logger.info("Found Gmail credentials at: {} (from env)", env_path)
            return env_path
        
        # Check explicit path
        if self._credentials_path and os.path.exists(self._credentials_path):
            self._logger.info("Found Gmail credentials at: {} (explicit)", self._credentials_path)
            return self._credentials_path
        
        # Check common filenames in current directory and project root
        filenames = ["client_secret.json", "credentials.json"]
        search_dirs = [".", os.path.expanduser("~")]
        
        # Also check project root if we can determine it
        try:
            # Try to find project root (where user saved client_secret.json)
            current_dir = os.getcwd()
            # Check if we're in a project directory
            if os.path.exists(os.path.join(current_dir, "client_secret.json")):
                search_dirs.insert(0, current_dir)
        except:
            pass
        
        for search_dir in search_dirs:
            for filename in filenames:
                full_path = os.path.join(search_dir, filename)
                if os.path.exists(full_path):
                    abs_path = os.path.abspath(full_path)
                    self._logger.info("Found Gmail credentials at: {}", abs_path)
                    return abs_path
        
        return None
    
    def _configure_ssl_for_oauth2client(self, ssl_cert_path: str):
        """Configure SSL for oauth2client/httplib2 which doesn't respect standard SSL settings."""
        try:
            import httplib2  # type: ignore
            
            # httplib2 uses ca_certs parameter instead of context
            # Patch the Http class to use our certificate file
            original_http_init = httplib2.Http.__init__
            
            def patched_http_init(self, *args, **kwargs):
                # Set ca_certs to our certificate file if not already set
                if 'ca_certs' not in kwargs:
                    kwargs['ca_certs'] = ssl_cert_path
                return original_http_init(self, *args, **kwargs)
            
            httplib2.Http.__init__ = patched_http_init
            self._logger.debug("Patched httplib2.Http to use certificate: {}", ssl_cert_path)
            
            # Also try to patch HTTPSConnectionWithTimeout if it exists
            # But check if it supports ca_certs first
            try:
                original_https_init = httplib2.HTTPSConnectionWithTimeout.__init__
                import inspect
                sig = inspect.signature(original_https_init)
                
                # Only patch if ca_certs is a valid parameter
                if 'ca_certs' in sig.parameters:
                    def patched_https_init(self, *args, **kwargs):
                        if 'ca_certs' not in kwargs:
                            kwargs['ca_certs'] = ssl_cert_path
                        return original_https_init(self, *args, **kwargs)
                    
                    httplib2.HTTPSConnectionWithTimeout.__init__ = patched_https_init
                    self._logger.debug("Patched httplib2.HTTPSConnectionWithTimeout")
            except (AttributeError, TypeError, ValueError) as e:
                # HTTPSConnectionWithTimeout might not exist or doesn't support ca_certs
                self._logger.debug("Could not patch HTTPSConnectionWithTimeout: {}", e)
            
        except ImportError:
            # httplib2 might not be available yet
            self._logger.debug("httplib2 not available for patching")
        except Exception as e:
            self._logger.warning("Could not patch httplib2: {}", e)
    
    def _get_gmail_client(self):
        """Lazy initialization of Gmail client."""
        if self._gmail_client is None:
            # Fix SSL certificates BEFORE importing SimpleGmail
            # Priority: 1. Corporate certs (Zscaler), 2. certifi, 3. System defaults
            ssl_cert_path = None
            
            # Check for corporate certificate bundles (common locations)
            corporate_cert_paths = [
                os.path.expanduser("~/.certs/cacert-with-zscaler.pem"),
                os.path.expanduser("~/.certs/cacert.pem"),
                "/etc/ssl/certs/ca-certificates.crt",
            ]
            
            for cert_path in corporate_cert_paths:
                if os.path.exists(cert_path):
                    ssl_cert_path = cert_path
                    self._logger.info("Found corporate SSL certificate: {}", cert_path)
                    break
            
            # Fallback to certifi if no corporate certs found
            if not ssl_cert_path:
                try:
                    import certifi
                    ssl_cert_path = certifi.where()
                    self._logger.debug("Using certifi SSL certificate: {}", ssl_cert_path)
                except ImportError:
                    pass  # certifi not available, will rely on system certificates
            
            # Set environment variables for libraries that respect them
            if ssl_cert_path:
                os.environ['SSL_CERT_FILE'] = ssl_cert_path
                os.environ['REQUESTS_CA_BUNDLE'] = ssl_cert_path
                os.environ['CURL_CA_BUNDLE'] = ssl_cert_path
                self._logger.info("Set SSL certificate environment variables to: {}", ssl_cert_path)
                
                # Configure Python's default SSL context
                try:
                    import ssl
                    ssl_context = ssl.create_default_context(cafile=ssl_cert_path)
                    ssl._create_default_https_context = lambda: ssl_context
                    self._logger.debug("Configured Python SSL context")
                    
                    # Also configure httplib2/oauth2client specifically
                    # This must happen BEFORE importing SimpleGmail
                    self._configure_ssl_for_oauth2client(ssl_cert_path)
                except Exception as e:
                    self._logger.warning("Could not configure SSL context: {}", e)
            
            try:
                from simplegmail import Gmail
            except ImportError:
                self._logger.error("simplegmail library not installed. Run: pip install simplegmail")
                raise RuntimeError("simplegmail library not installed. Run: pip install simplegmail")
            
            credentials_path = self._find_credentials()
            if not credentials_path:
                raise RuntimeError(
                    "Gmail credentials not found. Please set GMAIL_CREDENTIALS_PATH environment variable "
                    "or place client_secret.json in project root or current directory."
                )
            
            # Set token path to same directory as credentials
            # SimpleGmail automatically looks for gmail_token.json in the same directory as client_secret_file
            credentials_dir = os.path.dirname(os.path.abspath(credentials_path))
            self._token_path = os.path.join(credentials_dir, "gmail_token.json")
            
            # Initialize Gmail client with explicit credentials path
            # SimpleGmail will automatically:
            # 1. Look for gmail_token.json in the same directory as client_secret_file
            # 2. Use it if it exists (no re-authentication needed)
            # 3. Create it after first OAuth flow
            try:
                # SimpleGmail accepts client_secret_file parameter
                # It automatically handles token file in the same directory
                self._gmail_client = Gmail(client_secret_file=credentials_path)
                
                # Check if token file exists (means we've authenticated before)
                if os.path.exists(self._token_path):
                    self._logger.info("Using saved Gmail token from: {}", self._token_path)
                else:
                    self._logger.info("No saved token found - OAuth flow will trigger on first use")
                
                self._logger.success("Gmail client initialized successfully")
            except Exception as e:
                error_msg = str(e)
                # Check if it's an SSL certificate error
                if "CERTIFICATE_VERIFY_FAILED" in error_msg or "certificate verify failed" in error_msg.lower():
                    self._logger.error("SSL certificate verification failed: {}", e)
                    self._logger.info("This is a common issue on macOS. Try one of these solutions:")
                    self._logger.info("1. Install certificates: /Applications/Python\\ 3.12/Install\\ Certificates.command")
                    self._logger.info("2. Or run: pip install --upgrade certifi")
                    self._logger.info("3. Or set environment variable: export SSL_CERT_FILE=$(python3 -m certifi)")
                    raise RuntimeError(
                        f"SSL certificate verification failed. This is common on macOS.\n"
                        f"Solutions:\n"
                        f"1. Run: /Applications/Python\\ 3.12/Install\\ Certificates.command\n"
                        f"2. Or: pip install --upgrade certifi && export SSL_CERT_FILE=$(python3 -m certifi)\n"
                        f"3. Or: python3 -m pip install --upgrade certifi\n"
                        f"Original error: {error_msg}"
                    )
                else:
                    self._logger.error("Failed to initialize Gmail client: {}", e)
                    raise RuntimeError(f"Failed to initialize Gmail client: {str(e)}")
        
        return self._gmail_client
    
    def _get_message_by_id(self, gmail, message_id: str, search_labels: Optional[List[str]] = None):
        """
        Get a message by ID from SimpleGmail.
        
        SimpleGmail doesn't have a direct get_message() method, so we search for it.
        
        Args:
            gmail: Gmail client instance
            message_id: Message ID to find
            search_labels: Optional list of label names to search in (default: ["INBOX", "SENT", "ALL"])
        
        Returns:
            Message object or None if not found
        """
        if search_labels is None:
            search_labels = ["INBOX", "SENT", "ALL"]
        
        # First try: search in specific labels (more efficient)
        for label_name in search_labels:
            try:
                # Use attachments='download' to get attachment data (needed for size)
                label_messages = list(gmail.get_messages(
                    query=f"label:{label_name}",
                    attachments='download'
                ))[:100]
                message = next((m for m in label_messages if m.id == message_id), None)
                if message:
                    return message
            except Exception:
                continue
        
        # Second try: search all messages (less efficient, but broader search)
        try:
            # Use attachments='download' to get attachment data (needed for size)
            all_messages = list(gmail.get_messages(
                query="",
                attachments='download'
            ))[:200]
            message = next((m for m in all_messages if m.id == message_id), None)
            if message:
                return message
        except Exception:
            pass
        
        return None
    
    def register(self, mcp: FastMCP) -> None:
        """Register email tools with MCP server."""
        
        # Keep existing helper tools
        @mcp.tool(name="email_get_company_info")
        def get_company_info(company_name: str) -> dict:
            """
            Retrieve basic company information.

            Args:
                company_name (str): Name of the company.

            Returns:
                dict: Dictionary with company details.
            """
            self._logger.input("get_company_info INPUT: company_name={}", company_name)
            
            serper_api_tools = SerperApiMCPTools()
            results = serper_api_tools.search_internet(f"company information for {company_name}")
            
            self._logger.output("get_company_info OUTPUT: {}", results)
            return results

        @mcp.tool(name="email_get_email_signature")
        def get_email_signature() -> str:
            """
            Generate a professional email signature.

            Returns:
                str: Email signature.
            """
            signature = """
Nishant Khare
AVP, Head of Americas
Infosys Topaz"""
            self._logger.output("get_email_signature OUTPUT: {}", signature)
            return signature

        @mcp.tool(name="email_spell_check")
        def spell_check(text: str) -> dict:
            """
            Perform a simple spell check on the input text.

            Args:
                text (str): Text to check.

            Returns:
                dict: Original text and corrected version.
            """
            self._logger.input("spell_check INPUT: text_len={}", len(text or ""))

            spell = SpellChecker()
            words = text.split()
            misspelled = spell.unknown(words)

            corrections = {}
            corrected_words = []
            for word in words:
                if word in misspelled:
                    correction = spell.correction(word)
                    corrections[word] = correction
                    corrected_words.append(correction)
                else:
                    corrected_words.append(word)

            result = {
                "original": text,
                "corrected": " ".join(corrected_words),
                "corrections": corrections,
            }
            self._logger.output("spell_check OUTPUT: {}", result)
            return result
        
        # New Gmail tools
        @mcp.tool(name="email_send")
        def email_send(
            to: Union[str, List[str]],
            subject: str,
            body_plain: Optional[str] = None,
            body_html: Optional[str] = None,
            cc: Optional[Union[str, List[str]]] = None,
            bcc: Optional[Union[str, List[str]]] = None,
            attachments: Optional[List[str]] = None,
            signature: bool = False
        ) -> Dict[str, Any]:
            """
            Send an email via Gmail.
            
            Args:
                to: Recipient email address(es) - string or list of strings
                subject: Email subject
                body_plain: Plain text body (required if body_html not provided)
                body_html: HTML body (optional)
                cc: CC recipients (optional, string or list)
                bcc: BCC recipients (optional, string or list)
                attachments: List of file paths to attach (optional)
                signature: Use account signature (default: False)
            
            Returns:
                Dict with message_id, thread_id, status, error
            """
            self._logger.input("email_send INPUT: to={}, subject={}", to, subject)
            
            try:
                gmail = self._get_gmail_client()
                
                # Normalize recipients
                # SimpleGmail's send_message expects:
                # - to: string (single email or comma-separated)
                # - cc, bcc: list of strings (optional)
                to_list = [to] if isinstance(to, str) else to
                cc_list = [cc] if isinstance(cc, str) else (cc or [])
                bcc_list = [bcc] if isinstance(bcc, str) else (bcc or [])
                
                # Convert to to string (comma-separated if multiple)
                to_str = ", ".join(to_list) if isinstance(to_list, list) else str(to_list)
                
                # Validate body
                if not body_plain and not body_html:
                    raise ValueError("Either body_plain or body_html must be provided")
                
                # Get sender email from authenticated account
                sender_email = None
                try:
                    if hasattr(gmail, 'service'):
                        profile = gmail.service.users().getProfile(userId='me').execute()
                        sender_email = profile.get('emailAddress')
                except Exception:
                    # If we can't get profile, SimpleGmail will use authenticated account
                    pass
                
                # Prepare parameters
                # SimpleGmail's send_message signature:
                # - sender: str (required)
                # - to: str (required) - single email or comma-separated
                # - cc: Optional[List[str]]
                # - bcc: Optional[List[str]]
                # - attachments: Optional[List[str]]
                params = {
                    "to": to_str,  # Must be a string, not a list
                    "subject": subject,
                    "signature": signature,
                }
                
                # Add sender if available (SimpleGmail requires it)
                if sender_email:
                    params["sender"] = sender_email
                
                # Always include body - SimpleGmail needs at least one
                # Set both if provided, or at least one
                if body_html:
                    params["msg_html"] = body_html
                if body_plain:
                    params["msg_plain"] = body_plain
                if cc_list:
                    params["cc"] = cc_list
                if bcc_list:
                    params["bcc"] = bcc_list
                if attachments:
                    # Validate and normalize attachment file paths
                    # SimpleGmail expects absolute paths to existing files
                    validated_attachments = []
                    for att_path in attachments:
                        if not att_path:
                            continue
                        # Convert to Path object for easier handling
                        att_file = Path(att_path)
                        # Resolve to absolute path
                        if not att_file.is_absolute():
                            # If relative, try to resolve from current working directory
                            att_file = Path.cwd() / att_file
                        att_file = att_file.resolve()
                        
                        # Validate file exists
                        if not att_file.exists():
                            raise ValueError(f"Attachment file not found: {att_path}")
                        if not att_file.is_file():
                            raise ValueError(f"Attachment path is not a file: {att_path}")
                        
                        # Add as string (absolute path)
                        validated_attachments.append(str(att_file))
                    
                    if validated_attachments:
                        # SimpleGmail expects attachments as a list of file paths (strings)
                        # Each path should be absolute and point to an existing file
                        params["attachments"] = validated_attachments
                        self._logger.debug("Adding {} attachment(s) to email", len(validated_attachments))
                
                # Send message
                self._logger.debug("Calling gmail.send_message with params: {}", {k: v for k, v in params.items() if k != "attachments"})
                try:
                    message = gmail.send_message(**params)
                except (AttributeError, TypeError) as e:
                    error_str = str(e)
                    if "'list' object has no attribute 'encode'" in error_str or "encode" in error_str.lower():
                        # SimpleGmail might be trying to encode a list parameter
                        # This could be an issue with how SimpleGmail handles lists
                        # The error might be from recipients (to/cc/bcc) or attachments
                        self._logger.warning("SimpleGmail encode error detected: {}", error_str)
                        self._logger.debug("Trying alternative formats...")
                        
                        # Try converting recipients to comma-separated strings if they're lists
                        # SimpleGmail might expect strings for recipients
                        if isinstance(params.get("to"), list) and len(params["to"]) == 1:
                            params["to"] = params["to"][0]
                        if isinstance(params.get("cc"), list) and len(params.get("cc", [])) == 1:
                            params["cc"] = params["cc"][0]
                        if isinstance(params.get("bcc"), list) and len(params.get("bcc", [])) == 1:
                            params["bcc"] = params["bcc"][0]
                        
                        # Try passing attachments as single string if only one attachment
                        if "attachments" in params and isinstance(params["attachments"], list):
                            if len(params["attachments"]) == 1:
                                params["attachments"] = params["attachments"][0]
                        
                        self._logger.debug("Retrying with modified params...")
                        message = gmail.send_message(**params)
                    else:
                        raise
                
                result = {
                    "message_id": message.id,
                    "thread_id": message.thread_id,
                    "status": "sent",
                    "error": ""
                }
                
                self._logger.output("email_send OUTPUT: message_id={}, status=sent", message.id)
                return result
                
            except Exception as e:
                self._logger.error("email_send failed: {}", e)
                return {
                    "message_id": "",
                    "thread_id": "",
                    "status": "failed",
                    "error": str(e)
                }
        
        @mcp.tool(name="email_list_labels")
        def email_list_labels() -> Dict[str, Any]:
            """
            List all labels (folders) in Gmail account.
            
            Returns:
                Dict with labels list and count
            """
            self._logger.input("email_list_labels INPUT")
            
            try:
                gmail = self._get_gmail_client()
                labels = gmail.list_labels()
                
                labels_list = []
                for label in labels:
                    labels_list.append({
                        "id": label.id,
                        "name": label.name,
                        "type": label.type if hasattr(label, 'type') else "user"
                    })
                
                result = {
                    "labels": labels_list,
                    "count": len(labels_list)
                }
                
                self._logger.output("email_list_labels OUTPUT: {} labels found", len(labels_list))
                return result
                
            except Exception as e:
                self._logger.error("email_list_labels failed: {}", e)
                return {
                    "labels": [],
                    "count": 0,
                    "error": str(e)
                }
        
        @mcp.tool(name="email_list_messages")
        def email_list_messages(
            label_id: str = "INBOX",
            query: Optional[str] = None,
            max_results: int = 50,
            include_spam_trash: bool = False
        ) -> Dict[str, Any]:
            """
            List emails from a specific label/folder with optional filters.
            
            Args:
                label_id: Label ID to list from (default: "INBOX")
                query: Gmail search query (optional, e.g., "is:unread", "from:example@gmail.com")
                max_results: Maximum number of messages (default: 50, max: 500)
                include_spam_trash: Include spam and trash (default: False)
            
            Returns:
                Dict with messages list, count, and label_id
            """
            self._logger.input("email_list_messages INPUT: label_id={}, query={}, max_results={}", 
                            label_id, query, max_results)
            
            try:
                gmail = self._get_gmail_client()
                
                # Build query
                search_query = f"label:{label_id}"
                if query:
                    search_query = f"{search_query} {query}"
                if not include_spam_trash:
                    search_query = f"{search_query} -in:spam -in:trash"
                
                # Get messages
                # SimpleGmail get_messages() accepts:
                # - query: search query
                # - attachments: 'ignore', 'reference', or 'download' (default: 'reference')
                # We use 'reference' to get attachment metadata without downloading
                all_messages = gmail.get_messages(query=search_query, attachments='reference')
                messages = list(all_messages)[:min(max_results, 500)] if all_messages else []
                
                messages_list = []
                for msg in messages:
                    # Get recipients - SimpleGmail uses recipient (string), cc, bcc (lists)
                    recipients = {
                        "to": [msg.recipient] if hasattr(msg, 'recipient') and msg.recipient else [],
                        "cc": list(msg.cc) if hasattr(msg, 'cc') and msg.cc else [],
                        "bcc": list(msg.bcc) if hasattr(msg, 'bcc') and msg.bcc else []
                    }
                    
                    # Extract label names from label_ids (which are Label objects)
                    label_names = []
                    if hasattr(msg, 'label_ids') and msg.label_ids:
                        for label in msg.label_ids:
                            if hasattr(label, 'name'):
                                label_names.append(label.name)
                            elif isinstance(label, str):
                                label_names.append(label)
                    
                    # Derive is_unread and is_starred from label_ids
                    is_unread = 'UNREAD' in label_names
                    is_starred = 'STARRED' in label_names
                    
                    # Check for attachments
                    # SimpleGmail message objects have an 'attachments' attribute
                    # that is a list of Attachment objects (or None/empty if no attachments)
                    # Attachment objects have: filename, filetype, data (bytes or None)
                    # Note: Even with attachments='download', data may not be downloaded yet
                    # We need to explicitly download to get size, or access Gmail API metadata
                    attachments_list = []
                    has_attachments = False
                    if hasattr(msg, 'attachments') and msg.attachments:
                        has_attachments = True
                        for att in msg.attachments:
                            # Try to get size from data if available
                            size = 0
                            if att.data is not None:
                                size = len(att.data)
                            else:
                                # Try to download attachment to get size
                                # This is necessary because SimpleGmail doesn't expose size in metadata
                                try:
                                    if hasattr(att, 'download'):
                                        att.download()
                                        if att.data is not None:
                                            size = len(att.data)
                                except Exception as e:
                                    # If download fails, size remains 0
                                    # Log but don't fail - size is optional info
                                    self._logger.debug("Could not download attachment {} to get size: {}", att.filename if hasattr(att, 'filename') else 'unknown', e)
                            
                            attachments_list.append({
                                "filename": att.filename if hasattr(att, 'filename') and att.filename else "unknown",
                                "content_type": att.filetype if hasattr(att, 'filetype') and att.filetype else "unknown",
                                "size": size
                            })
                    
                    messages_list.append({
                        "id": msg.id,
                        "thread_id": msg.thread_id,
                        "sender": msg.sender if msg.sender else "",  # sender is a string
                        "subject": msg.subject or "",
                        "snippet": msg.snippet or "",
                        "date": msg.date if msg.date else "",  # date is a string in SimpleGmail
                        "is_unread": is_unread,
                        "is_starred": is_starred,
                        "labels": label_names,
                        "attachments": attachments_list,  # Include attachment info
                        "has_attachments": has_attachments  # Boolean flag for quick check
                    })
                
                result = {
                    "messages": messages_list,
                    "count": len(messages_list),
                    "label_id": label_id
                }
                
                self._logger.output("email_list_messages OUTPUT: {} messages found", len(messages_list))
                return result
                
            except Exception as e:
                self._logger.error("email_list_messages failed: {}", e)
                return {
                    "messages": [],
                    "count": 0,
                    "label_id": label_id,
                    "error": str(e)
                }
        
        @mcp.tool(name="email_read_message")
        def email_read_message(message_id: str) -> Dict[str, Any]:
            """
            Read full content of a specific email.
            
            Args:
                message_id: Gmail message ID
            
            Returns:
                Dict with full message details
            """
            self._logger.input("email_read_message INPUT: message_id={}", message_id)
            
            try:
                gmail = self._get_gmail_client()
                
                # Get message by ID using helper method
                message = self._get_message_by_id(gmail, message_id)
                
                if not message:
                    raise ValueError(f"Message {message_id} not found")
                
                # Get recipients - SimpleGmail uses recipient (string), cc, bcc (lists)
                recipients = {
                    "to": [message.recipient] if hasattr(message, 'recipient') and message.recipient else [],
                    "cc": list(message.cc) if hasattr(message, 'cc') and message.cc else [],
                    "bcc": list(message.bcc) if hasattr(message, 'bcc') and message.bcc else []
                }
                
                # Get attachments info
                # SimpleGmail Attachment objects have: filename, filetype, data (bytes or None)
                # Note: Even with attachments='download', data may not be downloaded yet
                # We need to explicitly download to get size
                attachments_list = []
                if message.attachments:
                    for att in message.attachments:
                        # Try to get size from data if available
                        size = 0
                        if att.data is not None:
                            size = len(att.data)
                        else:
                            # Try to download attachment to get size
                            try:
                                if hasattr(att, 'download'):
                                    att.download()
                                    if att.data is not None:
                                        size = len(att.data)
                            except Exception:
                                # If download fails, size remains 0
                                pass
                        
                        attachments_list.append({
                            "filename": att.filename if hasattr(att, 'filename') and att.filename else "unknown",
                            "content_type": att.filetype if hasattr(att, 'filetype') and att.filetype else "unknown",
                            "size": size
                        })
                
                # Extract label names from label_ids (which are Label objects)
                label_names = []
                if hasattr(message, 'label_ids') and message.label_ids:
                    for label in message.label_ids:
                        if hasattr(label, 'name'):
                            label_names.append(label.name)
                        elif isinstance(label, str):
                            label_names.append(label)
                
                result = {
                    "id": message.id,
                    "thread_id": message.thread_id,
                    "sender": message.sender if message.sender else "",  # sender is a string
                    "recipients": recipients,
                    "subject": message.subject or "",
                    "date": message.date if message.date else "",  # date is a string in SimpleGmail
                    "body_html": message.html or "",
                    "body_plain": message.plain or "",
                    "attachments": attachments_list,
                    "labels": label_names,
                    "is_unread": 'UNREAD' in label_names,
                    "is_starred": 'STARRED' in label_names
                }
                
                self._logger.output("email_read_message OUTPUT: message_id={}", message_id)
                return result
                
            except Exception as e:
                self._logger.error("email_read_message failed: {}", e)
                return {
                    "id": message_id,
                    "error": str(e)
                }
        
        @mcp.tool(name="email_search")
        def email_search(
            query: str,
            max_results: int = 50
        ) -> Dict[str, Any]:
            """
            Search emails using Gmail query syntax.
            
            Args:
                query: Gmail search query (e.g., "from:example@gmail.com subject:invoice after:2025/11/01")
                max_results: Maximum results (default: 50)
            
            Returns:
                Dict with messages list and count
            """
            self._logger.input("email_search INPUT: query={}, max_results={}", query, max_results)
            
            try:
                gmail = self._get_gmail_client()
                # SimpleGmail get_messages() only accepts 'query' parameter
                # We'll slice the results to limit the count
                all_messages = gmail.get_messages(query=query)
                messages = list(all_messages)[:min(max_results, 500)] if all_messages else []
                
                messages_list = []
                for msg in messages:
                    # Get recipients - SimpleGmail uses recipient (string), cc, bcc (lists)
                    recipients = {
                        "to": [msg.recipient] if hasattr(msg, 'recipient') and msg.recipient else [],
                        "cc": list(msg.cc) if hasattr(msg, 'cc') and msg.cc else [],
                        "bcc": list(msg.bcc) if hasattr(msg, 'bcc') and msg.bcc else []
                    }
                    
                    # Extract label names from label_ids (which are Label objects)
                    label_names = []
                    if hasattr(msg, 'label_ids') and msg.label_ids:
                        for label in msg.label_ids:
                            if hasattr(label, 'name'):
                                label_names.append(label.name)
                            elif isinstance(label, str):
                                label_names.append(label)
                    
                    # Derive is_unread and is_starred from label_ids
                    is_unread = 'UNREAD' in label_names
                    is_starred = 'STARRED' in label_names
                    
                    messages_list.append({
                        "id": msg.id,
                        "thread_id": msg.thread_id,
                        "sender": msg.sender if msg.sender else "",  # sender is a string
                        "subject": msg.subject or "",
                        "snippet": msg.snippet or "",
                        "date": msg.date if msg.date else "",  # date is a string in SimpleGmail
                        "is_unread": is_unread,
                        "is_starred": is_starred,
                        "labels": label_names
                    })
                
                result = {
                    "messages": messages_list,
                    "count": len(messages_list),
                    "query": query
                }
                
                self._logger.output("email_search OUTPUT: {} messages found", len(messages_list))
                return result
                
            except Exception as e:
                self._logger.error("email_search failed: {}", e)
                return {
                    "messages": [],
                    "count": 0,
                    "query": query,
                    "error": str(e)
                }
        
        @mcp.tool(name="email_move")
        def email_move(
            message_ids: List[str],
            to_label_id: str,
            from_label_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Move email(s) from one label to another.
            
            Args:
                message_ids: List of message IDs to move
                to_label_id: Target label ID (required)
                from_label_id: Source label ID (optional, if not provided removes from all labels)
            
            Returns:
                Dict with moved_count, message_ids, status, error
            """
            self._logger.input("email_move INPUT: message_ids={}, from={}, to={}", 
                            message_ids, from_label_id, to_label_id)
            
            try:
                gmail = self._get_gmail_client()
                
                # Get target label
                labels = gmail.list_labels()
                target_label = next((l for l in labels if l.id == to_label_id or l.name == to_label_id), None)
                if not target_label:
                    raise ValueError(f"Label '{to_label_id}' not found")
                
                # Get source label if provided
                from_label = None
                if from_label_id:
                    from_label = next((l for l in labels if l.id == from_label_id or l.name == from_label_id), None)
                    if not from_label:
                        raise ValueError(f"Label '{from_label_id}' not found")
                
                moved_count = 0
                failed_messages = []
                for msg_id in message_ids:
                    try:
                        # Get message by ID using helper method
                        # Search in the source label first for efficiency
                        search_labels = [from_label.name] if from_label else None
                        message = self._get_message_by_id(gmail, msg_id, search_labels=search_labels)
                        
                        if not message:
                            self._logger.warning("Message {} not found", msg_id)
                            failed_messages.append({"message_id": msg_id, "error": "Message not found"})
                            continue
                        
                        # Modify labels: add target, remove source
                        # SimpleGmail's modify_labels accepts Label objects or label IDs (strings)
                        # We'll use Label objects as they're more reliable
                        to_remove = [from_label] if from_label else []
                        to_add = [target_label]
                        
                        self._logger.debug("Modifying labels for message {}: add={}, remove={}", 
                                         msg_id, target_label.name if target_label else None, 
                                         from_label.name if from_label else None)
                        
                        message.modify_labels(to_add=to_add, to_remove=to_remove)
                        moved_count += 1
                        self._logger.debug("Successfully moved message {} from {} to {}", msg_id, from_label_id, to_label_id)
                    except Exception as e:
                        error_msg = str(e)
                        self._logger.error("Failed to move message {}: {}", msg_id, error_msg)
                        import traceback
                        self._logger.debug("Traceback: {}", traceback.format_exc())
                        failed_messages.append({"message_id": msg_id, "error": error_msg})
                
                result = {
                    "moved_count": moved_count,
                    "message_ids": message_ids,
                    "from_label_id": from_label_id,
                    "to_label_id": to_label_id,
                    "status": "success" if moved_count > 0 else "partial",
                    "error": "" if moved_count == len(message_ids) else f"{len(failed_messages)} message(s) failed",
                    "failed_messages": failed_messages if failed_messages else []
                }
                
                if moved_count == 0:
                    self._logger.warning("email_move OUTPUT: No messages moved. Failed: {}", failed_messages)
                else:
                    self._logger.output("email_move OUTPUT: {} messages moved, {} failed", moved_count, len(failed_messages))
                return result
                
            except Exception as e:
                self._logger.error("email_move failed: {}", e)
                return {
                    "moved_count": 0,
                    "message_ids": message_ids,
                    "from_label_id": from_label_id,
                    "to_label_id": to_label_id,
                    "status": "failed",
                    "error": str(e)
                }
        
        @mcp.tool(name="email_mark_read")
        def email_mark_read(message_ids: List[str]) -> Dict[str, Any]:
            """
            Mark email(s) as read.
            
            Args:
                message_ids: List of message IDs to mark as read
            
            Returns:
                Dict with marked_count, message_ids, status
            """
            self._logger.input("email_mark_read INPUT: message_ids={}", message_ids)
            
            try:
                gmail = self._get_gmail_client()
                
                # UNREAD is a Gmail system label - use the label ID directly as a string
                # Gmail system labels: UNREAD, INBOX, SENT, DRAFT, TRASH, SPAM, etc.
                # SimpleGmail's modify_labels accepts label IDs as strings for system labels
                unread_label_id = "UNREAD"
                
                marked_count = 0
                for msg_id in message_ids:
                    try:
                        message = self._get_message_by_id(gmail, msg_id)
                        if not message:
                            self._logger.warning("Message {} not found, skipping", msg_id)
                            continue
                        
                        # Remove UNREAD label to mark as read
                        # Use the label ID string directly - SimpleGmail handles system labels this way
                        message.modify_labels(to_remove=[unread_label_id])
                        marked_count += 1
                        self._logger.debug("Successfully marked message {} as read", msg_id)
                    except Exception as e:
                        self._logger.warning("Failed to mark message {} as read: {}", msg_id, e)
                
                result = {
                    "marked_count": marked_count,
                    "message_ids": message_ids,
                    "status": "success"
                }
                
                self._logger.output("email_mark_read OUTPUT: {} messages marked", marked_count)
                return result
                
            except Exception as e:
                self._logger.error("email_mark_read failed: {}", e)
                return {
                    "marked_count": 0,
                    "message_ids": message_ids,
                    "status": "failed",
                    "error": str(e)
                }
        
        @mcp.tool(name="email_mark_unread")
        def email_mark_unread(message_ids: List[str]) -> Dict[str, Any]:
            """
            Mark email(s) as unread.
            
            Args:
                message_ids: List of message IDs to mark as unread
            
            Returns:
                Dict with marked_count, message_ids, status
            """
            self._logger.input("email_mark_unread INPUT: message_ids={}", message_ids)
            
            try:
                gmail = self._get_gmail_client()
                
                # UNREAD is a Gmail system label - use the label ID directly as a string
                # Gmail system labels: UNREAD, INBOX, SENT, DRAFT, TRASH, SPAM, etc.
                # SimpleGmail's modify_labels accepts label IDs as strings for system labels
                unread_label_id = "UNREAD"
                
                marked_count = 0
                for msg_id in message_ids:
                    try:
                        message = self._get_message_by_id(gmail, msg_id)
                        if not message:
                            self._logger.warning("Message {} not found, skipping", msg_id)
                            continue
                        
                        # Add UNREAD label to mark as unread
                        # Use the label ID string directly - SimpleGmail handles system labels this way
                        message.modify_labels(to_add=[unread_label_id])
                        marked_count += 1
                        self._logger.debug("Successfully marked message {} as unread", msg_id)
                    except Exception as e:
                        self._logger.warning("Failed to mark message {} as unread: {}", msg_id, e)
                
                result = {
                    "marked_count": marked_count,
                    "message_ids": message_ids,
                    "status": "success"
                }
                
                self._logger.output("email_mark_unread OUTPUT: {} messages marked", marked_count)
                return result
                
            except Exception as e:
                self._logger.error("email_mark_unread failed: {}", e)
                return {
                    "marked_count": 0,
                    "message_ids": message_ids,
                    "status": "failed",
                    "error": str(e)
                }
        
        @mcp.tool(name="email_delete")
        def email_delete(message_ids: List[str]) -> Dict[str, Any]:
            """
            Delete email(s) (move to trash).
            
            Args:
                message_ids: List of message IDs to delete
            
            Returns:
                Dict with deleted_count, message_ids, status, error
            """
            self._logger.input("email_delete INPUT: message_ids={}", message_ids)
            
            try:
                gmail = self._get_gmail_client()
                
                deleted_count = 0
                for msg_id in message_ids:
                    try:
                        message = self._get_message_by_id(gmail, msg_id)
                        if not message:
                            continue
                        
                        message.trash()
                        deleted_count += 1
                    except Exception as e:
                        self._logger.warning("Failed to delete message {}: {}", msg_id, e)
                
                result = {
                    "deleted_count": deleted_count,
                    "message_ids": message_ids,
                    "status": "success",
                    "error": ""
                }
                
                self._logger.output("email_delete OUTPUT: {} messages deleted", deleted_count)
                return result
                
            except Exception as e:
                self._logger.error("email_delete failed: {}", e)
                return {
                    "deleted_count": 0,
                    "message_ids": message_ids,
                    "status": "failed",
                    "error": str(e)
                }
        
        @mcp.tool(name="email_download_attachment")
        def email_download_attachment(
            message_id: str,
            attachment_filename: str,
            save_path: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Download attachment from an email.
            
            Args:
                message_id: Gmail message ID
                attachment_filename: Name of attachment to download
                save_path: Local path to save attachment (optional, defaults to temp directory)
            
            Returns:
                Dict with message_id, filename, save_path, size, status, error
            """
            self._logger.input("email_download_attachment INPUT: message_id={}, filename={}", 
                            message_id, attachment_filename)
            
            try:
                gmail = self._get_gmail_client()
                
                message = self._get_message_by_id(gmail, message_id)
                if not message:
                    raise ValueError(f"Message {message_id} not found")
                
                # Find attachment
                attachment = None
                if message.attachments:
                    attachment = next((att for att in message.attachments if att.filename == attachment_filename), None)
                
                if not attachment:
                    raise ValueError(f"Attachment '{attachment_filename}' not found in message")
                
                # Determine save path
                if not save_path:
                    import tempfile
                    save_path = os.path.join(tempfile.gettempdir(), attachment_filename)
                else:
                    # Ensure directory exists
                    save_dir = os.path.dirname(save_path)
                    if save_dir and not os.path.exists(save_dir):
                        os.makedirs(save_dir, exist_ok=True)
                
                # Download attachment
                attachment.save(save_path)
                
                result = {
                    "message_id": message_id,
                    "filename": attachment_filename,
                    "save_path": save_path,
                    "size": attachment.size if hasattr(attachment, 'size') else 0,
                    "status": "success",
                    "error": ""
                }
                
                self._logger.output("email_download_attachment OUTPUT: saved to {}", save_path)
                return result
                
            except Exception as e:
                self._logger.error("email_download_attachment failed: {}", e)
                return {
                    "message_id": message_id,
                    "filename": attachment_filename,
                    "save_path": save_path or "",
                    "size": 0,
                    "status": "failed",
                    "error": str(e)
                }
