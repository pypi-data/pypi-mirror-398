"""
Buzzerboy Platform Connectors - Helper Utilities Module

This module provides utility functions for Django applications, including URL processing,
email template handling, file operations, and configuration management. These helpers
complement the core configuration functions and provide commonly needed functionality
for web applications.

Key Features:
    - URL processing with HTTP/HTTPS prefix handling
    - Email template rendering with variable substitution
    - Django CORS and CSRF configuration helpers
    - JSON file loading with error handling
    - Email sending with error handling

Example:
    Basic usage::

        from PlatformConnectors import PlatformHelpers as ph
        
        # URL processing
        urls = ph.addHttpPrefix('example.com')
        
        # Email operations
        ph.send_email('Subject', 'Message', ['user@example.com'], 'from@example.com')
        
        # Configuration helpers
        allowed_hosts = ph.getAllowedHosts()
        csrf_origins = ph.getCSRFTrustedOrigins()

Author:
    Buzzerboy Inc

Version:
    0.8.6
"""

import os
from django.core.mail import send_mail
from smtplib import SMTPRecipientsRefused
from pathlib import Path
import json
import socket

import logging
logger = logging.getLogger(__name__)


def addHttpPrefix(url):
    """
    Add HTTP and HTTPS prefixes to a URL if not already present.
    
    This function ensures URLs have proper protocol prefixes, returning both
    HTTP and HTTPS versions. Useful for generating complete URLs from domain names.
    
    Args:
        url (str): The URL or domain name to process.
    
    Returns:
        dict: Dictionary with 'http' and 'https' keys containing complete URLs.
    
    Example:
        ::
        
            result = addHttpPrefix('example.com')
            # Returns: {'http': 'http://example.com', 'https': 'https://example.com'}
            
            result = addHttpPrefix('https://secure.example.com')
            # Returns: {'http': 'https://secure.example.com', 'https': 'https://secure.example.com'}
    
    Note:
        If the URL already has a protocol, both returned URLs will use that protocol.
    """
    result = {'http': '', 'https': ''}
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
        result = {'http': url, 'https': url.replace('http://', 'https://')} 

    return result

def allowHostCSVtoArray (csvString):
    """
    Convert a CSV string of allowed hosts to an array.
    
    Processes a comma-separated string of hostnames into a clean array,
    removing trailing slashes and whitespace. Supports wildcard '*' for
    allowing all hosts.
    
    Args:
        csvString (str): Comma-separated string of hostnames.
    
    Returns:
        list: List of cleaned hostname strings.
    
    Example:
        ::
        
            hosts = allowHostCSVtoArray('localhost, example.com/, api.example.com ')
            # Returns: ['localhost', 'example.com', 'api.example.com']
            
            all_hosts = allowHostCSVtoArray('*')
            # Returns: ['*']
    
    Note:
        The function removes trailing slashes and whitespace from each hostname
        to ensure consistent formatting for Django ALLOWED_HOSTS configuration.
    """
    if csvString == '*':
        return ['*']
    else:
        arr= [origin.strip() for origin in csvString.split(',')]
        #remove any traling slashes that might be in the array
        arr = [origin.rstrip('/') for origin in arr]
        return arr
    

def removeHttpPrefix(url):
    """
    Remove HTTP and HTTPS prefixes from a URL.
    
    Strips protocol prefixes from URLs to get clean domain names.
    Useful for normalizing URLs before processing.
    
    Args:
        url (str): URL with or without protocol prefix.
    
    Returns:
        str: URL without HTTP/HTTPS prefix.
    
    Example:
        ::
        
            domain = removeHttpPrefix('https://example.com')
            # Returns: 'example.com'
            
            domain = removeHttpPrefix('http://api.example.com/path')
            # Returns: 'api.example.com/path'
    """
    return url.replace('http://', '').replace('https://', '')

def getCSRFHostsFromAllowedHosts (allowedHostsArray):
    """
    Generate CSRF trusted origins from allowed hosts.
    
    Converts an array of allowed hostnames into CSRF trusted origins by
    adding HTTP and HTTPS prefixes. Removes duplicates to ensure clean
    configuration for Django CSRF_TRUSTED_ORIGINS.
    
    Args:
        allowedHostsArray (list): List of allowed hostnames.
    
    Returns:
        list: List of CSRF trusted origins with HTTP/HTTPS prefixes.
    
    Example:
        ::
        
            allowed = ['localhost', 'example.com']
            origins = getCSRFHostsFromAllowedHosts(allowed)
            # Returns: [
            #     'http://localhost', 'https://localhost',
            #     'http://example.com', 'https://example.com'
            # ]
    
    Note:
        This function automatically deduplicates entries to prevent
        redundant CSRF origins in Django configuration.
    """
    result = []
    for host in allowedHostsArray:
        cleanHost = removeHttpPrefix(host)
        
        #only append to result if the result does not already include the value in cleanHost
        if not cleanHost in result:
            result.append(addHttpPrefix(cleanHost)['http'])
            result.append(addHttpPrefix(cleanHost)['https'])
    return result


def getAllowedHosts():
    """
    Get the complete list of allowed hosts for Django configuration.
    
    Builds Django ALLOWED_HOSTS list from environment variables, including
    localhost, local IP address, and custom hosts from ALLOWED_HOSTS_CSV.
    
    Returns:
        list: Complete list of allowed hosts for Django.
    
    Example:
        ::
        
            # With ALLOWED_HOSTS_CSV='example.com,api.example.com'
            hosts = getAllowedHosts()
            # Returns: ['127.0.0.1', '192.168.1.100', 'example.com', 'api.example.com']
    
    Environment Variables:
        ALLOWED_HOSTS_CSV (str): Comma-separated list of additional hosts.
                                Defaults to '*' (allow all).
    
    Note:
        The function automatically includes localhost (127.0.0.1) and attempts
        to detect the local machine's IP address for development convenience.
    """
    ALLOWED_HOSTS_CSV = os.getenv('ALLOWED_HOSTS_CSV', '*')
    ALLOWED_HOSTS = ['127.0.0.1']


    try:
        ALLOWED_HOSTS.append(socket.gethostbyname(socket.gethostname()))
    except Exception as e:
        ALLOWED_HOSTS.append('127.0.0.1')
    ALLOWED_HOSTS += allowHostCSVtoArray(ALLOWED_HOSTS_CSV)
    return ALLOWED_HOSTS


def getCSRFTrustedOrigins():
    """
    Get the complete list of CSRF trusted origins for Django.
    
    Generates Django CSRF_TRUSTED_ORIGINS from allowed hosts, including
    development defaults and custom origins from configuration.
    
    Returns:
        list: Complete list of CSRF trusted origins.
    
    Example:
        ::
        
            origins = getCSRFTrustedOrigins()
            # Returns: [
            #     'http://localhost:85', 'http://127.0.0.1', 'http://localhost:8000',
            #     'http://example.com', 'https://example.com', ...
            # ]
    
    Note:
        The function includes common development origins by default and
        generates additional origins from the allowed hosts configuration.
    """
    CSRF_TRUSTED_ORIGINS = ['http://localhost:85', 'http://127.0.0.1', 'http://localhost:8000']
    CSRF_TRUSTED_ORIGINS = getCSRFHostsFromAllowedHosts(getAllowedHosts())

    return CSRF_TRUSTED_ORIGINS


def GetEmailTemplate(template_name, variablesDict, BASE_DIR):
    """
    Load and render an email template with variable substitution.
    
    Reads an HTML email template file and replaces variables with provided values.
    Variables in templates should use the format {{variable_name}}.
    
    Args:
        template_name (str): Name of the template file in email_templates directory.
        variablesDict (dict): Dictionary of variables to substitute in the template.
        BASE_DIR (str): Base directory path for locating template files.
    
    Returns:
        str: Rendered email template with variables substituted.
    
    Example:
        ::
        
            # Template file: email_templates/welcome.html
            # Content: <h1>Welcome {{user_name}}!</h1>
            
            variables = {'user_name': 'John Doe'}
            template = GetEmailTemplate('welcome.html', variables, BASE_DIR)
            # Returns: '<h1>Welcome John Doe!</h1>'
    
    Raises:
        FileNotFoundError: If the template file doesn't exist.
        IOError: If there's an error reading the template file.
    
    Note:
        Variables are converted to strings using __str__() method, so any
        object with a string representation can be used as a variable value.
    """

    filename = os.path.join(BASE_DIR, 'email_templates', template_name)


    #read contents of file name into template
    with open(filename, 'r') as file:
        template = file.read()
        logger.debug(template)
        file.close()

    #replace variables in template with values from variablesDict
    for key, value in variablesDict.items():
        template = template.replace('{{'+key+'}}', value.__str__())

    return template

def send_email (subject, message, recipient_list, from_email, **kwargs):
    """
    Send an email to specified recipients with error handling.
    
    Wrapper around Django's send_mail function with enhanced logging and
    error handling. Supports HTML email content and additional options.
    
    Args:
        subject (str): Email subject line.
        message (str): Email message content (can be HTML).
        recipient_list (list): List of recipient email addresses.
        from_email (str): Sender email address.
        **kwargs: Additional keyword arguments passed to Django's send_mail.
    
    Returns:
        None
    
    Example:
        ::
        
            send_email(
                'Welcome to Our Service',
                '<h1>Welcome!</h1><p>Thanks for joining.</p>',
                ['user@example.com'],
                'noreply@example.com'
            )
    
    Raises:
        SMTPRecipientsRefused: If the email server refuses the recipients.
                              This exception is caught and logged, not re-raised.
    
    Note:
        - The function automatically sets html_message for HTML content
        - Emails are sent with fail_silently=True to prevent application crashes
        - All parameters and errors are logged for debugging purposes
    """


    logger.debug(f'subject: {subject}')
    logger.debug(f'message: {message}')
    logger.debug(f'recipient_list: {recipient_list}')
    logger.debug(f'from_email: {from_email}')
    logger.debug(f'kwargs: {kwargs}')
    
    #set content type to html
    kwargs['html_message'] = message
    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=True, **kwargs)
    except SMTPRecipientsRefused:
        logger.error(f"Failed to send email to {recipient_list}. SMTPRecipientsRefused error.")





def LoadChoicesFromFile(file_name, prefixFolder='fixtures/'):
    """
    Load Django model choices from a JSON file.
    
    Reads a JSON file containing choice data and converts it to Django
    model field choices format. Useful for dynamic choice loading.
    
    Args:
        file_name (str): Name of the JSON file (without .json extension).
        prefixFolder (str, optional): Directory prefix for the file.
                                    Defaults to 'fixtures/'.
    
    Returns:
        list: List of tuples in Django choices format [(value, label), ...].
    
    Example:
        ::
        
            # File: fixtures/countries.json
            # Content: [
            #     {"value": "US", "label": "United States"},
            #     {"value": "CA", "label": "Canada"}
            # ]
            
            choices = LoadChoicesFromFile('countries')
            # Returns: [('US', 'United States'), ('CA', 'Canada')]
    
    Expected JSON Format:
        The JSON file should contain an array of objects with 'value' and 'label' keys::
        
            [
                {"value": "option1", "label": "Option 1"},
                {"value": "option2", "label": "Option 2"}
            ]
    
    Raises:
        FileNotFoundError: If the JSON file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        KeyError: If objects don't have required 'value' and 'label' keys.
    """

    CHOICE_FILE = f'{prefixFolder}{file_name}.json'
    with open(CHOICE_FILE) as file:
        choice_data = json.load(file)
    CHOICES = [(row['value'], row['label']) for row in choice_data]
    return CHOICES

def GetJsonFileContent(file_name, prefixFolder='fixtures/'):
    """
    Load and return JSON file content with error handling.
    
    Safely loads JSON file content with descriptive error messages.
    Useful for loading configuration files, fixtures, or data files.
    
    Args:
        file_name (str): Name of the JSON file (without .json extension).
        prefixFolder (str, optional): Directory prefix for the file.
                                    Defaults to 'fixtures/'.
    
    Returns:
        dict or list: Parsed JSON content.
    
    Example:
        ::
        
            # Load configuration data
            config = GetJsonFileContent('app_config')
            
            # Load test fixtures
            test_data = GetJsonFileContent('test_users', 'test_fixtures/')
    
    Raises:
        ValueError: If the file is not found or contains invalid JSON.
                   Error messages clearly indicate the specific issue.
    
    Note:
        This function provides better error messages than raw json.load(),
        making it easier to debug configuration and data loading issues.
    """
    try:
        JSON_FILE = f'{prefixFolder}{file_name}.json'
        with open(JSON_FILE) as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError(f"JSON file {file_name} not found in fixtures directory")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in {file_name}.json")