import json
import pandas as pd
import requests
import re
import io
import os
from robot.api.deco import keyword, library, not_keyword
from typing import Dict, List, Any, Optional
import logging

# Google API imports (optional)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

@library(scope='GLOBAL', auto_keywords=True)
class MoodleLibrary:
    """
    Thư viện Robot Framework để tương tác với Moodle Web Services API.
    Hỗ trợ tạo khóa học, quiz và quản lý nội dung từ file Excel.
    
    Tự động import các built-in libraries:
    - BuiltIn
    - OperatingSystem
    - Collections
    """
    
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    
    def get_library_instance(self, name):
        """Import built-in libraries automatically"""
        from robot.libraries.BuiltIn import BuiltIn
        return BuiltIn().get_library_instance(name)
    
    def __init__(self, base_url: str = None, token: str = None, google_credentials_path: str = None):
        """
        Khởi tạo kết nối với Moodle.
        
        Args:
            base_url: (Optional) URL của Moodle instance (ví dụ: https://moodle.example.com)
            token: (Optional) Web service token từ Moodle
            google_credentials_path: (Optional) Đường dẫn đến file credentials Google API
        
        Note:
            Nếu không truyền base_url và token, cần gọi "Set Up Moodle Connection" sau đó.
        """
        self.base_url = base_url.rstrip("/") if base_url else None
        self.token = token
        self.session = requests.Session()
        self.endpoint = f"{self.base_url}/webservice/rest/server.php" if base_url else None
        self.google_creds = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Gemini AI
        self.gemini_model = None
        
        # Import Robot Framework built-in libraries
        try:
            from robot.libraries.BuiltIn import BuiltIn
            self.builtin = BuiltIn()
            # Make built-in keywords available
            self.builtin.import_library('OperatingSystem')
            self.builtin.import_library('Collections')
        except:
            self.builtin = None
        if google_credentials_path and GOOGLE_API_AVAILABLE:
            self.setup_google_connection(google_credentials_path)

    # ===========================================================
    #  Connection Setup
    # ===========================================================

    @keyword("Set Up Moodle Connection")
    def setup_moodle_connection(self, token_file_path: str = None):
        """
        Thiết lập kết nối với Moodle từ file token.
        
        Args:
            token_file_path: Đường dẫn đến file token JSON
            
        Expected JSON format (Option 1 - Simple):
        {
            "base_url": "https://moodle.example.com",
            "token": "your_moodle_token"
        }
        
        Expected JSON format (Option 2 - Google-like):
        {
            "access_token": "your_moodle_token",
            "refresh_token": "https://moodle.example.com"
        }
        
        Returns:
            Dictionary với thông tin kết nối
        """
        if not token_file_path:
            raise Exception('Token file path is required')

        with open(token_file_path, 'r') as file:
            data = json.load(file)
        
        # Support both formats
        if 'access_token' in data and 'refresh_token' in data:
            # New format (Google-like)
            base_url = data.get('access_token')
            token = data.get('refresh_token')
        else:
            # Old format (backward compatible)
            base_url = data.get('base_url')
            token = data.get('token')
        
        if not base_url or not token:
            raise Exception('Token file must contain credentials (base_url+token or access_token+refresh_token)')
        
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.endpoint = f"{self.base_url}/webservice/rest/server.php"
        
        self.logger.info(f"Moodle connection setup: {self.base_url}")
        
        return {
            'base_url': self.base_url,
            'endpoint': self.endpoint,
            'token': self.token[:10] + '...',  # Show only first 10 chars for security
            'status': 'connected'
        }

    # ===========================================================
    #  Core API Methods
    # ===========================================================

    @not_keyword
    def call_moodle_api(self, function: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Gọi Moodle Web Service API.
        
        Args:
            function: Tên function của Moodle API
            params: Parameters cho function
            
        Returns:
            Response data từ Moodle API
        """
        if params is None:
            params = {}
        
        data = {
            'wstoken': self.token,
            'wsfunction': function,
            'moodlewsrestformat': 'json'
        }
        data.update(params)
        
        try:
            response = self.session.post(self.endpoint, data=data)
            response.raise_for_status()
            result = response.json()
            
            # Check for Moodle API errors
            if isinstance(result, dict) and 'exception' in result:
                raise Exception(f"Moodle API Error: {result.get('message', 'Unknown error')}")
            
            return result
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API call failed: {e}")
            raise Exception(f"Failed to call Moodle API: {str(e)}")

    # ===========================================================
    #  Course Category Management
    # ===========================================================

    @keyword("Get Course Categories")
    def get_course_categories(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả các course categories."""
        return self.call_moodle_api('core_course_get_categories')

    @keyword("Create Course Category")
    def create_course_category(self, name: str, parent: int = 0, description: str = "") -> Dict[str, Any]:
        """
        Tạo course category mới.
        
        Args:
            name: Tên category
            parent: ID của parent category (0 = top level)
            description: Mô tả category
        """
        params = {
            'categories[0][name]': name,
            'categories[0][parent]': parent,
            'categories[0][description]': description,
        }
        result = self.call_moodle_api('core_course_create_categories', params)
        return result[0] if isinstance(result, list) else result

    @keyword("Ensure Category Exists")
    def ensure_category_exists(self, name: str, parent: int = 0) -> Dict[str, Any]:
        """Đảm bảo category tồn tại, tạo mới nếu chưa có."""
        categories = self.get_course_categories()
        
        for cat in categories:
            if cat['name'] == name and cat['parent'] == parent:
                return cat
        
        return self.create_course_category(name, parent)

    # ===========================================================
    #  Course Management
    # ===========================================================

    @keyword("Create Course")
    def create_course(self, fullname: str, shortname: str, categoryid: int, 
                     summary: str = "", format: str = "topics") -> Dict[str, Any]:
        """
        Tạo khóa học mới.
        
        Args:
            fullname: Tên đầy đủ của khóa học
            shortname: Tên ngắn gọn (unique)
            categoryid: ID của category
            summary: Mô tả khóa học
            format: Định dạng khóa học (topics, weeks, social, etc.)
        """
        params = {
            'courses[0][fullname]': fullname,
            'courses[0][shortname]': shortname,
            'courses[0][categoryid]': categoryid,
            'courses[0][summary]': summary,
            'courses[0][format]': format,
        }
        result = self.call_moodle_api('core_course_create_courses', params)
        return result[0] if isinstance(result, list) else result

    @keyword("Get Course By Shortname")
    def get_course_by_shortname(self, shortname: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin khóa học theo shortname."""
        params = {'field': 'shortname', 'value': shortname}
        result = self.call_moodle_api('core_course_get_courses_by_field', params)
        
        if result and 'courses' in result and len(result['courses']) > 0:
            return result['courses'][0]
        return None

    @keyword("Ensure Course Exists")
    def ensure_course_exists(self, fullname: str, shortname: str, categoryid: int, 
                            summary: str = "") -> Dict[str, Any]:
        """Đảm bảo khóa học tồn tại, tạo mới nếu chưa có."""
        existing = self.get_course_by_shortname(shortname)
        if existing:
            return existing
        
        return self.create_course(fullname, shortname, categoryid, summary)

    @keyword("Get Course Contents")
    def get_course_contents(self, courseid: int) -> List[Dict[str, Any]]:
        """Lấy nội dung của khóa học."""
        params = {'courseid': courseid}
        return self.call_moodle_api('core_course_get_contents', params)


    # ===========================================================
    #  Quiz Management (Using GIFT Format)
    # ===========================================================

    @not_keyword
    def generate_gift_format(self, questions: List[Dict[str, Any]]) -> str:
        """
        Tạo nội dung GIFT format từ danh sách câu hỏi.
        
        GIFT là định dạng text đơn giản của Moodle để import câu hỏi.
        """
        gift_content = []
        
        for q in questions:
            question_text = q.get('question_text', '').strip()
            question_type = q.get('question_type', 'multichoice').lower()
            
            if question_type == 'multichoice':
                # Multiple choice question
                options = []
                correct_answer = str(q.get('correct_answer', 'A')).upper()
                
                for opt_key in ['option_a', 'option_b', 'option_c', 'option_d']:
                    if opt_key in q and pd.notna(q[opt_key]):
                        option_text = str(q[opt_key]).strip()
                        if option_text:
                            # Determine if this is the correct answer
                            opt_letter = opt_key.split('_')[1].upper()
                            if opt_letter == correct_answer:
                                options.append(f"    ={option_text}")
                            else:
                                options.append(f"    ~{option_text}")
                
                if options:
                    gift_question = f"::{question_text}::{question_text} {{\n"
                    gift_question += "\n".join(options)
                    gift_question += "\n}\n"
                    gift_content.append(gift_question)
            
            elif question_type == 'truefalse':
                # True/False question
                correct_answer = str(q.get('correct_answer', 'TRUE')).upper()
                is_true = correct_answer in ['TRUE', 'T', 'ĐÚNG', 'Đ']
                gift_question = f"::{question_text}::{question_text} {{{is_true}}}\n"
                gift_content.append(gift_question)
            
            elif question_type == 'shortanswer':
                # Short answer question
                correct_answer = str(q.get('correct_answer', '')).strip()
                gift_question = f"::{question_text}::{question_text} {{={correct_answer}}}\n"
                gift_content.append(gift_question)
        
        return "\n".join(gift_content)

    @keyword("Generate Quiz GIFT File")
    def generate_quiz_gift_file(self, questions: List[Dict[str, Any]], output_path: str) -> str:
        """
        Tạo file GIFT format để import vào Moodle.
        
        Args:
            questions: Danh sách câu hỏi
            output_path: Đường dẫn file output
            
        Returns:
            Đường dẫn file đã tạo
        """
        gift_content = self.generate_gift_format(questions)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(gift_content)
        
        self.logger.info(f"Generated GIFT file: {output_path}")
        return output_path

    @not_keyword
    def generate_moodle_xml(self, questions: List[Dict[str, Any]], quiz_name: str = "Quiz") -> str:
        """
        Tạo Moodle XML format từ danh sách câu hỏi.
        """
        xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_parts.append('<quiz>')
        
        for idx, q in enumerate(questions, 1):
            question_text = q.get('question_text', '').strip()
            question_type = q.get('question_type', 'multichoice').lower()
            points = q.get('points', 1)
            
            if question_type == 'multichoice':
                xml_parts.append('  <question type="multichoice">')
                xml_parts.append(f'    <name><text>Question {idx}</text></name>')
                xml_parts.append(f'    <questiontext format="html"><text><![CDATA[<p>{question_text}</p>]]></text></questiontext>')
                xml_parts.append(f'    <defaultgrade>{points}</defaultgrade>')
                xml_parts.append('    <single>true</single>')
                xml_parts.append('    <shuffleanswers>true</shuffleanswers>')
                
                correct_answer = str(q.get('correct_answer', 'A')).upper()
                
                for opt_key in ['option_a', 'option_b', 'option_c', 'option_d']:
                    if opt_key in q and pd.notna(q[opt_key]):
                        option_text = str(q[opt_key]).strip()
                        if option_text:
                            opt_letter = opt_key.split('_')[1].upper()
                            fraction = '100' if opt_letter == correct_answer else '0'
                            xml_parts.append(f'    <answer fraction="{fraction}" format="html">')
                            xml_parts.append(f'      <text><![CDATA[<p>{option_text}</p>]]></text>')
                            xml_parts.append('    </answer>')
                
                xml_parts.append('  </question>')
            
            elif question_type == 'truefalse':
                correct_answer = str(q.get('correct_answer', 'TRUE')).upper()
                is_true = correct_answer in ['TRUE', 'T', 'ĐÚNG', 'Đ']
                
                xml_parts.append('  <question type="truefalse">')
                xml_parts.append(f'    <name><text>Question {idx}</text></name>')
                xml_parts.append(f'    <questiontext format="html"><text><![CDATA[<p>{question_text}</p>]]></text></questiontext>')
                xml_parts.append(f'    <defaultgrade>{points}</defaultgrade>')
                xml_parts.append(f'    <answer fraction="{"100" if is_true else "0"}" format="moodle_auto_format">')
                xml_parts.append('      <text>true</text>')
                xml_parts.append('    </answer>')
                xml_parts.append(f'    <answer fraction="{"0" if is_true else "100"}" format="moodle_auto_format">')
                xml_parts.append('      <text>false</text>')
                xml_parts.append('    </answer>')
                xml_parts.append('  </question>')
        
        xml_parts.append('</quiz>')
        return '\n'.join(xml_parts)

    @keyword("Generate Quiz XML File")
    def generate_quiz_xml_file(self, questions: List[Dict[str, Any]], output_path: str, 
                               quiz_name: str = "Quiz") -> str:
        """
        Tạo file Moodle XML format để import vào Moodle.
        
        Args:
            questions: Danh sách câu hỏi
            output_path: Đường dẫn file output
            quiz_name: Tên quiz
            
        Returns:
            Đường dẫn file đã tạo
        """
        xml_content = self.generate_moodle_xml(questions, quiz_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        self.logger.info(f"Generated Moodle XML file: {output_path}")
        return output_path

    # ===========================================================
    #  Complete Workflow
    # ===========================================================

    @keyword("Create Course From Excel")
    def create_course_from_excel(self, excel_path: str) -> Dict[str, Any]:
        """
        Tạo khóa học từ file Excel.
        
        Args:
            excel_path: Đường dẫn đến file Excel
            
        Returns:
            Thông tin khóa học đã tạo
        """
        course_data = self.load_excel_course_data(excel_path)
        
        # Ensure category exists
        category_name = course_data.get('category', 'Miscellaneous')
        category = self.ensure_category_exists(category_name)
        
        # Create course
        course = self.ensure_course_exists(
            fullname=course_data.get('fullname', 'New Course'),
            shortname=course_data.get('shortname', 'newcourse'),
            categoryid=category['id'],
            summary=course_data.get('summary', '')
        )
        
        return course


    # ===========================================================
    #  User Management
    # ===========================================================

    @keyword("Create User")
    def create_user(self, username: str, password: str, firstname: str, lastname: str, 
                   email: str) -> Dict[str, Any]:
        """Tạo user mới trong Moodle."""
        params = {
            'users[0][username]': username,
            'users[0][password]': password,
            'users[0][firstname]': firstname,
            'users[0][lastname]': lastname,
            'users[0][email]': email,
            'users[0][auth]': 'manual',  # Required field
        }
        result = self.call_moodle_api('core_user_create_users', params)
        return result[0] if isinstance(result, list) else result

    @keyword("Enroll User In Course")
    def enroll_user_in_course(self, userid: int, courseid: int, roleid: int = 5) -> Dict[str, Any]:
        """
        Enroll user vào khóa học.
        
        Args:
            userid: ID của user
            courseid: ID của course
            roleid: ID của role (5 = Student, 3 = Teacher)
        """
        params = {
            'enrolments[0][roleid]': roleid,
            'enrolments[0][userid]': userid,
            'enrolments[0][courseid]': courseid,
        }
        return self.call_moodle_api('enrol_manual_enrol_users', params)
    
    @keyword("Get User By Username")
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo username.
        
        Args:
            username: Username của user
            
        Returns:
            User info dictionary or None if not found
        """
        users = self.call_moodle_api('core_user_get_users_by_field', {
            'field': 'username',
            'values[0]': username
        })
        
        if not users or not isinstance(users, list) or len(users) == 0:
            return None
        
        return users[0]
    
    @keyword("Get User By Email")
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo email.
        
        Args:
            email: Email của user
            
        Returns:
            User info dictionary or None if not found
        """
        users = self.call_moodle_api('core_user_get_users_by_field', {
            'field': 'email',
            'values[0]': email
        })
        
        if not users or not isinstance(users, list) or len(users) == 0:
            return None
        
        return users[0]
    
    @keyword("Get User By Username Or Email")
    def get_user_by_username_or_email(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin user theo username hoặc email.
        Thử username trước, nếu không tìm thấy thì thử email.
        
        Args:
            identifier: Username hoặc email của user
            
        Returns:
            User info dictionary or None if not found
        """
        # Try username first
        user = self.get_user_by_username(identifier)
        if user:
            return user
        
        # Try email if username fails
        if '@' in identifier:
            user = self.get_user_by_email(identifier)
            if user:
                return user
        
        return None
    
    @keyword("Enrol User")
    def enrol_user(self, username: str, course_shortname: str, roleid: int = 5) -> Dict[str, Any]:
        """
        Enrol user vào course bằng username và course shortname.
        
        Args:
            username: Username của user
            course_shortname: Shortname của course
            roleid: Role ID (5 = Student, 3 = Teacher)
        """
        # Get user ID
        user = self.get_user_by_username(username)
        
        if not user:
            raise Exception(f"User not found: {username}")
        
        userid = user['id']
        
        # Get course ID
        course = self.get_course_by_shortname(course_shortname)
        courseid = course['id']
        
        # Enrol
        return self.enroll_user_in_course(userid, courseid, roleid)


    # ===========================================================
    #  Google Docs Integration (Optional)
    # ===========================================================

    @keyword("Setup Google Connection")
    def setup_google_connection(self, token_file_path: str):
        """
        Thiết lập kết nối với Google API.
        
        Args:
            token_file_path: Đường dẫn đến file token Google API (JSON)
        """
        if not GOOGLE_API_AVAILABLE:
            raise Exception("Google API libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-api-python-client")
        
        if not token_file_path:
            raise Exception('Token file path is required')

        with open(token_file_path, 'r') as file:
            data = json.load(file)
            
        access_token = data['access_token']
        refresh_token = data['refresh_token']
        token_uri = data['token_uri']
        client_id = data['client_id']
        client_secret = data['client_secret']
        scopes = data['scopes']
        
        self.google_creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes
        )
        
        if not self.google_creds.valid:
            self.google_creds.refresh(Request())
            
        return self.google_creds

    @keyword("Get Google Doc ID From URL")
    def get_doc_id_from_url(self, url: str) -> Optional[str]:
        """Trích xuất Google Doc ID từ URL."""
        pattern = r"https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None
    
    @keyword("Get Assignment ID From URL")
    def get_assignment_id_from_url(self, url: str) -> Optional[int]:
        """
        Trích xuất Assignment Course Module ID từ Moodle URL.
        
        Args:
            url: Moodle assignment URL (e.g., http://moodle.com/mod/assign/view.php?id=23)
            
        Returns:
            Course Module ID (cmid) or None if not found
            
        Example:
            http://moodle.com/mod/assign/view.php?id=23 → 23
        """
        pattern = r"[?&]id=(\d+)"
        match = re.search(pattern, url)
        if match:
            return int(match.group(1))
        return None
    
    @keyword("Get Assignment Instance ID From Course Module ID")
    def get_assignment_instance_id_from_cmid(self, course_id: int, cmid: int) -> Optional[int]:
        """
        Convert Course Module ID to Assignment Instance ID.
        
        Args:
            course_id: Moodle course ID
            cmid: Course Module ID (from URL)
            
        Returns:
            Assignment Instance ID or None if not found
            
        Example:
            cmid=23 → instance_id=1
        """
        try:
            contents = self.call_moodle_api('core_course_get_contents', {
                'courseid': course_id
            })
            
            for section in contents:
                for module in section.get('modules', []):
                    if module.get('modname') == 'assign' and module.get('id') == cmid:
                        instance_id = module.get('instance')
                        self.logger.info(f"Converted cmid {cmid} → instance {instance_id}")
                        return instance_id
            
            self.logger.warning(f"Could not find assignment with cmid={cmid} in course {course_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error converting cmid to instance: {e}")
            return None
    

    @keyword("Get Google Drive File ID From URL")
    def get_drive_file_id_from_url(self, url: str) -> Optional[str]:
        """
        Trích xuất Google Drive/Sheets/Docs file ID từ URL.
        
        Supports:
        - Google Docs: https://docs.google.com/document/d/FILE_ID/...
        - Google Sheets: https://docs.google.com/spreadsheets/d/FILE_ID/...
        - Google Drive: https://drive.google.com/file/d/FILE_ID/...
        - Google Drive: https://drive.google.com/open?id=FILE_ID
        
        Args:
            url: Google Drive, Sheets, or Docs URL
            
        Returns:
            File ID or None if not found
        """
        # Pattern for Google Docs
        docs_pattern = r"https://docs\.google\.com/document/d/([a-zA-Z0-9-_]+)"
        match = re.search(docs_pattern, url)
        if match:
            return match.group(1)
        
        # Pattern for Sheets
        sheets_pattern = r"https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)"
        match = re.search(sheets_pattern, url)
        if match:
            return match.group(1)
        
        # Pattern for Drive file/d/
        drive_pattern = r"https://drive\.google\.com/file/d/([a-zA-Z0-9-_]+)"
        match = re.search(drive_pattern, url)
        if match:
            return match.group(1)
        
        # Pattern for Drive folder (supports /u/0/ or /u/N/ in path)
        folder_pattern = r"https://drive\.google\.com/drive/(?:u/\d+/)?folders/([a-zA-Z0-9-_]+)"
        match = re.search(folder_pattern, url)
        if match:
            return match.group(1)
        
        # Pattern for Drive open?id=
        open_pattern = r"https://drive\.google\.com/open\?id=([a-zA-Z0-9-_]+)"
        match = re.search(open_pattern, url)
        if match:
            return match.group(1)
        
        return None


    @keyword("Read Google Doc Content")
    def read_google_doc_content(self, doc_id: str) -> str:
        """
        Đọc nội dung từ Google Docs.
        
        Args:
            doc_id: ID của Google Doc
            
        Returns:
            Nội dung text của document
        """
        if not self.google_creds:
            raise Exception('Google authentication required. Call "Setup Google Connection" first.')

        try:
            service = build('drive', 'v3', credentials=self.google_creds)
            request = service.files().export_media(fileId=doc_id, mimeType='text/plain')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            return fh.getvalue().decode()
        except HttpError as error:
            raise Exception(f"Failed to read Google Doc: {str(error)}")

    @not_keyword
    def parse_questions_from_text(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse câu hỏi từ text content.
        
        Format mong đợi:
        Question 1: <câu hỏi>
        A. <đáp án A>
        B. <đáp án B>
        C. <đáp án C>
        D. <đáp án D>
        """
        pattern = r'(?:Question|Câu)\s+(\d+)[.:]\s*(.*?)\s*A\.\s*(.*?)\s*B\.\s*(.*?)\s*C\.\s*(.*?)\s*D\.\s*(.*?)(?=\s*(?:Question|Câu)|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if not matches:
            return []
        
        questions = []
        for match in matches:
            if len(match) < 6:
                continue
            
            question_num = match[0]
            question_text = ' '.join(match[1].split())
            
            question = {
                'question_number': int(question_num),
                'question_text': question_text,
                'question_type': 'multichoice',
                'option_a': ' '.join(match[2].split()),
                'option_b': ' '.join(match[3].split()),
                'option_c': ' '.join(match[4].split()),
                'option_d': ' '.join(match[5].split()),
                'points': 1
            }
            questions.append(question)
        
        return questions

    @not_keyword
    def parse_answer_keys(self, answers_content: str) -> Dict[str, str]:
        """
        Parse đáp án đúng từ text.
        
        Format mong đợi:
        1. A
        2. B
        3. C
        """
        pattern = r'(\d+)\.\s*([A-D])'  # Added \s* to handle whitespace
        answer_matches = re.findall(pattern, answers_content)
        answer_keys = {num: ans for num, ans in answer_matches}
        return answer_keys

    @keyword("Read Quiz From Google Doc")
    def read_quiz_from_google_doc(self, doc_id: str, delimiter: str = "---HẾT---") -> List[Dict[str, Any]]:
        """
        Đọc câu hỏi và đáp án từ Google Doc.
        
        Args:
            doc_id: ID của Google Doc
            delimiter: Chuỗi phân cách giữa câu hỏi và đáp án
            
        Returns:
            Danh sách câu hỏi với đáp án đúng
        """
        content = self.read_google_doc_content(doc_id)
        
        # Split content by delimiter
        parts = re.split(rf'-{{1,}}{re.escape(delimiter.strip("-"))}-{{1,}}', content, flags=re.IGNORECASE)
        doc_content = parts[0].strip() if len(parts) > 0 else ""
        answers_content = parts[1].strip() if len(parts) > 1 else ""
        
        # Parse questions
        questions = self.parse_questions_from_text(doc_content)
        
        # Parse answer keys
        answer_keys = self.parse_answer_keys(answers_content)
        
        # Map correct answers to questions
        for question in questions:
            question_num = str(question['question_number'])
            if question_num in answer_keys:
                question['correct_answer'] = answer_keys[question_num]
            else:
                question['correct_answer'] = 'A'  # Default
        
        return questions

    @keyword("Create Quiz From Google Doc")
    def create_quiz_from_google_doc(self, doc_id: str, output_path: str, output_format: str = 'gift') -> str:
        """
        Tạo file quiz từ Google Doc.
        
        Args:
            doc_id: ID của Google Doc hoặc URL
            output_path: Đường dẫn file output
            output_format: Định dạng output ('gift' hoặc 'xml')
            
        Returns:
            Đường dẫn file quiz đã tạo
        """
        # Extract doc ID from URL if needed
        if 'docs.google.com' in doc_id:
            doc_id = self.get_doc_id_from_url(doc_id)
            if not doc_id:
                raise Exception("Invalid Google Doc URL")
        
        # Read questions from Google Doc
        questions = self.read_quiz_from_google_doc(doc_id)
        
        if not questions:
            raise Exception("No questions found in Google Doc")
        
        # Generate quiz file
        if output_format.lower() == 'gift':
            return self.generate_quiz_gift_file(questions, output_path)
        else:
            return self.generate_quiz_xml_file(questions, output_path, "Quiz from Google Doc")

    # ===========================================================
    #  File Upload
    # ===========================================================

    @keyword("Upload File To Moodle")
    def upload_file_to_moodle(self, file_path: str, contextid: int = 1) -> Dict[str, Any]:
        """
        Upload file lên Moodle server.
        
        Args:
            file_path: Đường dẫn file cần upload
            contextid: Context ID (default: 1 for system context)
            
        Returns:
            Dictionary chứa thông tin file đã upload
            
        Example:
            file_info = moodle.upload_file_to_moodle("quiz_output.txt")
            print(f"File uploaded: {file_info['filename']}")
        """
        import os
        
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        
        # Upload file using Moodle upload endpoint
        upload_url = f"{self.base_url}/webservice/upload.php"
        
        with open(file_path, 'rb') as f:
            files = {
                'file_1': (filename, f, 'application/octet-stream')
            }
            
            data = {
                'token': self.token,
                'filepath': '/',
                'itemid': 0,
                'contextid': contextid,
                'component': 'user',
                'filearea': 'draft',
            }
            
            response = self.session.post(upload_url, files=files, data=data)
            response.raise_for_status()
            result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            file_info = result[0]
            self.logger.info(f"File uploaded successfully: {filename}")
            return file_info
        else:
            raise Exception(f"Upload failed: {result}")

    # ===========================================================
    #  Question Bank Management
    # ===========================================================

    @keyword("Create Question In Question Bank")
    def create_question_in_question_bank(self, courseid: int, category_name: str, 
                                         question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo câu hỏi trực tiếp vào Question bank.
        
        Args:
            courseid: ID của course
            category_name: Tên category trong Question bank
            question_data: Dictionary chứa thông tin câu hỏi
            
        Question data format:
            {
                'question_text': 'Câu hỏi?',
                'question_type': 'multichoice',  # multichoice, truefalse, shortanswer
                'option_a': 'Đáp án A',
                'option_b': 'Đáp án B',
                'option_c': 'Đáp án C',
                'option_d': 'Đáp án D',
                'correct_answer': 'A',  # A, B, C, D hoặc TRUE/FALSE
                'points': 1
            }
            
        Returns:
            Question info
        """
        # Get or create category
        category = self.ensure_category_exists(category_name, parent=0)
        
        # Prepare question based on type
        question_type = question_data.get('question_type', 'multichoice').lower()
        question_text = question_data.get('question_text', '')
        
        if question_type == 'multichoice':
            # Create multichoice question using GIFT format
            gift_text = self._create_gift_multichoice(question_data)
        elif question_type == 'truefalse':
            gift_text = self._create_gift_truefalse(question_data)
        elif question_type == 'shortanswer':
            gift_text = self._create_gift_shortanswer(question_data)
        else:
            raise Exception(f"Unsupported question type: {question_type}")
        
        # Note: Moodle core API doesn't have direct question creation
        # We need to use GIFT import or custom plugin
        self.logger.warning("Direct question creation requires GIFT import or custom plugin")
        
        return {
            'gift_format': gift_text,
            'category': category_name,
            'courseid': courseid,
            'note': 'Use import_questions_from_gift() to import this question'
        }

    @not_keyword
    def _create_gift_multichoice(self, question_data: Dict[str, Any]) -> str:
        """Create GIFT format for multichoice question"""
        question_text = question_data.get('question_text', '')
        correct = question_data.get('correct_answer', 'A').upper()
        
        options = []
        for key in ['A', 'B', 'C', 'D']:
            opt_key = f'option_{key.lower()}'
            if opt_key in question_data:
                prefix = '=' if key == correct else '~'
                options.append(f"    {prefix}{question_data[opt_key]}")
        
        gift = f"::{question_text}::{question_text} {{\n"
        gift += "\n".join(options)
        gift += "\n}\n"
        return gift

    @not_keyword
    def _create_gift_truefalse(self, question_data: Dict[str, Any]) -> str:
        """Create GIFT format for true/false question"""
        question_text = question_data.get('question_text', '')
        correct = question_data.get('correct_answer', 'TRUE').upper()
        is_true = correct in ['TRUE', 'T', 'ĐÚNG']
        return f"::{question_text}::{question_text} {{{is_true}}}\n"

    @not_keyword
    def _create_gift_shortanswer(self, question_data: Dict[str, Any]) -> str:
        """Create GIFT format for short answer question"""
        question_text = question_data.get('question_text', '')
        correct = question_data.get('correct_answer', '')
        return f"::{question_text}::{question_text} {{={correct}}}\n"

    @keyword("Import Questions From GIFT Text")
    def import_questions_from_gift(self, courseid: int, gift_text: str, 
                                   category_name: str = "Imported") -> str:
        """
        Import questions từ GIFT text vào Question bank.
        
        Args:
            courseid: ID của course
            gift_text: GIFT format text
            category_name: Tên category
            
        Returns:
            Path to temporary GIFT file
            
        Note:
            File được tạo tạm thời, bạn cần import manual qua UI
        """
        import tempfile
        import os
        
        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='gift_')
        
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(gift_text)
            
            self.logger.info(f"GIFT file created: {temp_path}")
            self.logger.warning("Import this file via: Course → Question bank → Import")
            
            return temp_path
        except Exception as e:
            os.close(fd)
            raise e

    @keyword("Create Questions From Google Doc")
    def create_questions_from_google_doc(self, doc_id: str, courseid: int,
                                         category_name: str = "From Google Docs") -> str:
        """
        Tạo questions từ Google Doc vào Question bank.
        
        Args:
            doc_id: Google Doc ID
            courseid: Course ID
            category_name: Category name
            
        Returns:
            Path to GIFT file for import
        """
        # Read questions from Google Doc
        questions = self.read_quiz_from_google_doc(doc_id)
        
        # Generate GIFT format
        gift_text = self.generate_gift_format(questions)
        
        # Create temp file
        gift_file = self.import_questions_from_gift(courseid, gift_text, category_name)
        
        return gift_file

    # ===========================================================
    #  Google Drive Integration
    # ===========================================================

    @keyword("Upload File To Google Drive")
    def upload_file_to_google_drive(self, file_path: str, folder_id: str = None) -> Dict[str, Any]:
        """
        Upload file lên Google Drive.
        
        Args:
            file_path: Đường dẫn file cần upload
            folder_id: ID của folder trên Drive (optional)
            
        Returns:
            File info including file ID and web link
        """
        if not GOOGLE_API_AVAILABLE:
            raise Exception("Google API libraries not installed")
        
        if not self.google_creds:
            raise Exception("Google credentials not setup. Call setup_google_connection() first")
        
        import os
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        # Build Drive service
        service = build('drive', 'v3', credentials=self.google_creds)
        
        # Prepare file metadata
        file_name = os.path.basename(file_path)
        file_metadata = {'name': file_name}
        
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Upload file
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, webContentLink'
        ).execute()
        
        self.logger.info(f"File uploaded to Google Drive: {file.get('name')}")
        
        return {
            'file_id': file.get('id'),
            'name': file.get('name'),
            'web_view_link': file.get('webViewLink'),
            'download_link': file.get('webContentLink')
        }

    @keyword("Create Quiz And Upload To Drive")
    def create_quiz_and_upload_to_drive(self, doc_id: str, folder_id: str = None) -> Dict[str, Any]:
        """
        Tạo quiz từ Google Doc và upload file GIFT lên Google Drive.
        
        Args:
            doc_id: Google Doc ID chứa câu hỏi
            folder_id: Google Drive folder ID (optional)
            
        Returns:
            Dictionary với thông tin file và links
        """
        # Read questions from Google Doc
        questions = self.read_quiz_from_google_doc(doc_id)
        
        # Generate GIFT format
        gift_content = self.generate_gift_format(questions)
        
        # Create temp file
        import tempfile
        import os
        
        fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='quiz_gift_')
        
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(gift_content)
            
            # Upload to Google Drive
            drive_info = self.upload_file_to_google_drive(temp_path, folder_id)
            
            self.logger.info(f"Quiz uploaded to Google Drive")
            
            return {
                'questions_count': len(questions),
                'file_id': drive_info['file_id'],
                'file_name': drive_info['name'],
                'view_link': drive_info['web_view_link'],
                'download_link': drive_info['download_link'],
                'message': 'Quiz file uploaded to Google Drive. Download and import to Moodle.'
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass

    # ===========================================================
    #  Google Drive File Download
    # ===========================================================

    @keyword("Download File From Google Drive")
    def download_file_from_google_drive(self, file_id: str, output_path: str) -> str:
        """
        Download file từ Google Drive.
        Supports Google Docs (export as text), Google Sheets (export as Excel), and regular files.
        
        Args:
            file_id: Google Drive file ID
            output_path: Đường dẫn lưu file
            
        Returns:
            Path to downloaded file
        """
        if not GOOGLE_API_AVAILABLE:
            raise Exception("Google API libraries not installed")
        
        if not self.google_creds:
            raise Exception("Google credentials not setup")
        
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        import io
        
        service = build('drive', 'v3', credentials=self.google_creds)
        
        # Get file metadata to check type
        file_metadata = service.files().get(fileId=file_id, fields='mimeType').execute()
        mime_type = file_metadata.get('mimeType', '')
        
        # Check file type and use appropriate download/export method
        if 'document' in mime_type:
            # Google Docs - Export as plain text
            self.logger.info(f"Exporting Google Doc as plain text...")
            request = service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
        elif 'spreadsheet' in mime_type:
            # Google Sheets - Export as Excel
            self.logger.info(f"Exporting Google Sheet as Excel...")
            request = service.files().export_media(
                fileId=file_id,
                mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            # Regular file download
            self.logger.info(f"Downloading regular file...")
            request = service.files().get_media(fileId=file_id)
        
        with io.FileIO(output_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        self.logger.info(f"File downloaded: {output_path}")
        return output_path

    def list_files_in_google_drive_folder(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        List all files in a Google Drive folder.
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            List of file dictionaries with 'id', 'name', 'mimeType'
        """
        if not self.google_creds:
            raise Exception("Google credentials not configured. Call Setup Google Connection first.")
        
        try:
            service = build('drive', 'v3', credentials=self.google_creds)
            
            # Query files in folder
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=100
            ).execute()
            
            files = results.get('files', [])
            self.logger.info(f"Found {len(files)} files in folder {folder_id}")
            
            return files
            
        except HttpError as error:
            self.logger.error(f"Failed to list files in folder: {error}")
            raise
    
    @keyword("Parse Students From Excel")
    def parse_students_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse danh sách học sinh từ file Excel.
        
        Excel format:
            | username | firstname | lastname | email |
            
        Args:
            file_path: Đường dẫn file Excel
            
        Returns:
            List of student dictionaries
        """
        df = pd.read_excel(file_path)
        
        required_cols = ['username', 'firstname', 'lastname', 'email']
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Missing required column: {col}")
        
        students = []
        for _, row in df.iterrows():
            student = {
                'username': str(row['username']).strip(),
                'firstname': str(row['firstname']).strip(),
                'lastname': str(row['lastname']).strip(),
                'email': str(row['email']).strip(),
                'password': row.get('password', 'Moodle@2024')  # Default password
            }
            students.append(student)
        
        self.logger.info(f"Parsed {len(students)} students from Excel")
        return students

    @keyword("Parse Courses From Excel")
    def parse_courses_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse danh sách khóa học từ file Excel.
        
        Excel format:
            | shortname | fullname | category | summary |
            
        Args:
            file_path: Đường dẫn file Excel
            
        Returns:
            List of course dictionaries
        """
        df = pd.read_excel(file_path)
        
        required_cols = ['shortname', 'fullname']
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Missing required column: {col}")
        
        courses = []
        for _, row in df.iterrows():
            course = {
                'shortname': str(row['shortname']).strip(),
                'fullname': str(row['fullname']).strip(),
                'category': str(row.get('category', 'Miscellaneous')).strip(),
                'summary': str(row.get('summary', '')).strip()
            }
            courses.append(course)
        
        self.logger.info(f"Parsed {len(courses)} courses from Excel")
        return courses

    @keyword("Bulk Create Students")
    def bulk_create_students(self, students: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Tạo hàng loạt học sinh trên Moodle.
        Nếu user đã tồn tại, vẫn add vào list để enrol.
        
        Args:
            students: List of student dictionaries
            
        Returns:
            Summary of created students and all usernames
        """
        created = []
        failed = []
        all_usernames = []
        
        for student in students:
            username = student['username']
            try:
                user = self.create_user(
                    username=username,
                    password=student['password'],
                    firstname=student['firstname'],
                    lastname=student['lastname'],
                    email=student['email']
                )
                created.append({
                    'username': username,
                    'userid': user['id']
                })
                all_usernames.append(username)
                self.logger.info(f"Created user: {username}")
            except Exception as e:
                error_msg = str(e).lower()
                # Check if user already exists (various error messages)
                if any(keyword in error_msg for keyword in ['already', 'exists', 'duplicate', 'invalid parameter']):
                    # User likely exists, add to enrollment list
                    all_usernames.append(username)
                    self.logger.info(f"User may already exist: {username}, will attempt enrollment")
                else:
                    # Real error, add to failed list
                    failed.append({
                        'username': username,
                        'error': str(e)
                    })
                    self.logger.warning(f"Failed to create {username}: {e}")
        
        return {
            'total': len(students),
            'created': len(created),
            'failed': len(failed),
            'created_users': created,
            'failed_users': failed,
            'all_usernames': all_usernames  # All usernames for enrollment
        }

    @keyword("Bulk Create Courses And Enrol Students")
    def bulk_create_courses_and_enrol_students(self, courses: List[Dict[str, Any]], 
                                                student_usernames: List[str]) -> Dict[str, Any]:
        """
        Tạo hàng loạt khóa học và enrol tất cả học sinh.
        Nếu course đã tồn tại, vẫn enrol students vào course đó.
        
        Args:
            courses: List of course dictionaries
            student_usernames: List of student usernames to enrol
            
        Returns:
            Summary of created courses and enrollments
        """
        created_courses = []
        failed_courses = []
        
        for course_data in courses:
            try:
                # Ensure category exists
                category = self.ensure_category_exists(course_data['category'])
                
                course_created = False
                course_id = None
                
                # Try to create course
                try:
                    course = self.create_course(
                        fullname=course_data['fullname'],
                        shortname=course_data['shortname'],
                        categoryid=category['id'],
                        summary=course_data.get('summary', '')
                    )
                    course_id = course['id']
                    course_created = True
                    self.logger.info(f"Created new course: {course_data['shortname']}")
                except Exception as create_error:
                    # Course might already exist
                    if "already used" in str(create_error).lower():
                        # Get existing course
                        try:
                            existing_course = self.get_course_by_shortname(course_data['shortname'])
                            course_id = existing_course['id']
                            self.logger.info(f"Course already exists: {course_data['shortname']}, will enrol students")
                        except:
                            raise create_error
                    else:
                        raise create_error
                
                # Enrol all students (whether course is new or existing)
                enrolled = 0
                for username in student_usernames:
                    try:
                        self.enrol_user(username, course_data['shortname'])
                        enrolled += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to enrol {username}: {e}")
                
                created_courses.append({
                    'shortname': course_data['shortname'],
                    'courseid': course_id,
                    'enrolled_count': enrolled,
                    'newly_created': course_created
                })
                
                status = "created" if course_created else "existing"
                self.logger.info(f"Course {course_data['shortname']} ({status}) with {enrolled} students enrolled")
                
            except Exception as e:
                failed_courses.append({
                    'shortname': course_data['shortname'],
                    'error': str(e)
                })
                self.logger.warning(f"Failed to process course {course_data['shortname']}: {e}")
        
        return {
            'total_courses': len(courses),
            'created': len(created_courses),
            'failed': len(failed_courses),
            'created_courses': created_courses,
            'failed_courses': failed_courses
        }

    @keyword("Complete Bulk Enrollment Workflow")
    def complete_bulk_enrollment_workflow(self, students_file_id: str, 
                                          courses_file_id: str) -> Dict[str, Any]:
        """
        Workflow hoàn chỉnh: Download Excel từ Drive, tạo students và courses.
        
        Args:
            students_file_id: Google Drive file ID của file danh sách học sinh
            courses_file_id: Google Drive file ID của file danh sách khóa học
            
        Returns:
            Complete summary of the workflow
        """
        import tempfile
        import os
        
        # Download files from Google Drive
        self.logger.info("Downloading files from Google Drive...")
        
        students_file = tempfile.mktemp(suffix='.xlsx')
        courses_file = tempfile.mktemp(suffix='.xlsx')
        
        try:
            self.download_file_from_google_drive(students_file_id, students_file)
            self.download_file_from_google_drive(courses_file_id, courses_file)
            
            # Parse Excel files
            self.logger.info("Parsing Excel files...")
            students = self.parse_students_from_excel(students_file)
            courses = self.parse_courses_from_excel(courses_file)
            
            # Create students
            self.logger.info("Creating students...")
            students_result = self.bulk_create_students(students)
            
            # Get list of ALL usernames (created + existing)
            all_usernames = students_result.get('all_usernames', [])
            if not all_usernames:
                # Fallback to created only
                all_usernames = [u['username'] for u in students_result['created_users']]
            
            # Create courses and enrol students
            self.logger.info("Creating courses and enrolling students...")
            courses_result = self.bulk_create_courses_and_enrol_students(
                courses, all_usernames
            )
            
            return {
                'students': students_result,
                'courses': courses_result,
                'summary': {
                    'total_students': students_result['total'],
                    'students_created': students_result['created'],
                    'total_courses': courses_result['total_courses'],
                    'courses_created': courses_result['created'],
                    'total_enrollments': sum(c['enrolled_count'] for c in courses_result['created_courses'])
                }
            }
            
        finally:
            # Cleanup temp files
            try:
                os.unlink(students_file)
                os.unlink(courses_file)
            except:
                pass

    # ==================== AUTOMATIC GRADING WITH GEMINI AI ====================
    
    @keyword("Setup Gemini AI")
    def setup_gemini_ai(self, api_key: str):
        """
        Setup Gemini AI for automatic grading.
        
        Args:
            api_key: Gemini API key from https://makersuite.google.com/app/apikey
        """
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            self.logger.info("Gemini AI configured with gemini-2.5-flash")
        except ImportError:
            raise Exception("google-generativeai not installed. Run: pip install google-generativeai")
    
    @keyword("Grade Submission With Gemini")
    def grade_submission_with_gemini(
        self,
        submission_text: str,
        question_text: str,
        answer_key: str,
        max_score: float = 10.0
    ) -> Dict[str, Any]:
        """
        Grade a submission using Gemini AI.
        
        Args:
            submission_text: Student's submission
            question_text: Test questions
            answer_key: Answer key
            max_score: Maximum score
            
        Returns:
            Dictionary with score, feedback, and details
        """
        if not hasattr(self, 'gemini_model'):
            raise Exception("Gemini AI not configured. Call 'Setup Gemini AI' first.")
        
        prompt = f"""You are a teacher grading a student's test submission.

TEST QUESTIONS:
{question_text}

ANSWER KEY:
{answer_key}

STUDENT SUBMISSION:
{submission_text}

Please grade this submission and provide:
1. A score out of {max_score}
2. Detailed feedback on what was correct and incorrect
3. Suggestions for improvement

Format your response as JSON:
{{
    "score": <number>,
    "feedback": "<detailed feedback>",
    "correct_answers": ["<list of correct answers>"],
    "incorrect_answers": ["<list of incorrect answers>"],
    "suggestions": "<suggestions for improvement>"
}}
"""
        
        response = self.gemini_model.generate_content(prompt)
        result_text = response.text
        
        # Extract JSON from response
        try:
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {
                    'score': max_score * 0.5,
                    'feedback': result_text,
                    'correct_answers': [],
                    'incorrect_answers': [],
                    'suggestions': 'Please review the material'
                }
        except:
            result = {
                'score': max_score * 0.5,
                'feedback': result_text,
                'correct_answers': [],
                'incorrect_answers': [],
                'suggestions': 'Please review the material'
            }
        
        self.logger.info(f"Graded submission: {result['score']}/{max_score}")
        return result
    
    @keyword("Complete Auto Grading Workflow")
    def complete_auto_grading_workflow(
        self,
        submissions_folder_id: str,
        question_file_id: str,
        answer_key_file_id: str,
        max_score: float = 10.0
    ) -> Dict[str, Any]:
        """
        Complete automatic grading workflow.
        
        Args:
            submissions_folder_id: Google Drive folder with student submissions
            question_file_id: File ID of test questions
            answer_key_file_id: File ID of answer key
            max_score: Maximum score
            
        Returns:
            Dictionary with grading results for all students
        """
        import tempfile
        
        if not self.google_creds:
            raise Exception("Google credentials not setup. Call 'Setup Google Connection' first.")
        
        if not hasattr(self, 'gemini_model'):
            raise Exception("Gemini AI not configured. Call 'Setup Gemini AI' first.")
        
        from googleapiclient.discovery import build
        
        # Download questions and answer key
        self.logger.info("Downloading questions and answer key...")
        question_file = tempfile.mktemp(suffix='.txt')
        answer_file = tempfile.mktemp(suffix='.txt')
        
        self.download_file_from_google_drive(question_file_id, question_file)
        self.download_file_from_google_drive(answer_key_file_id, answer_file)
        
        with open(question_file, 'r', encoding='utf-8') as f:
            questions = f.read()
        
        with open(answer_file, 'r', encoding='utf-8') as f:
            answer_key = f.read()
        
        # Get all submissions from folder
        self.logger.info("Getting student submissions...")
        service = build('drive', 'v3', credentials=self.google_creds)
        
        query = f"'{submissions_folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)"
        ).execute()
        
        submissions = results.get('files', [])
        self.logger.info(f"Found {len(submissions)} submissions")
        
        # Grade each submission
        grading_results = []
        for submission in submissions:
            try:
                # Download submission
                submission_file = tempfile.mktemp(suffix='.txt')
                self.download_file_from_google_drive(submission['id'], submission_file)
                
                with open(submission_file, 'r', encoding='utf-8') as f:
                    submission_text = f.read()
                
                # Grade with Gemini
                grade_result = self.grade_submission_with_gemini(
                    submission_text,
                    questions,
                    answer_key,
                    max_score
                )
                
                # Extract student name from filename
                student_name = submission['name'].replace('.txt', '').replace('.pdf', '').replace('.docx', '')
                
                grading_results.append({
                    'student_name': student_name,
                    'file_id': submission['id'],
                    'score': grade_result['score'],
                    'feedback': grade_result['feedback'],
                    'details': grade_result
                })
                
                self.logger.info(f"Graded {student_name}: {grade_result['score']}/{max_score}")
                
                # Cleanup
                os.unlink(submission_file)
                
            except Exception as e:
                self.logger.error(f"Failed to grade {submission['name']}: {e}")
                grading_results.append({
                    'student_name': submission['name'],
                    'file_id': submission['id'],
                    'score': 0,
                    'feedback': f'Error: {str(e)}',
                    'details': {}
                })
        
        # Cleanup
        os.unlink(question_file)
        os.unlink(answer_file)
        
        return {
            'total_submissions': len(submissions),
            'graded': len([r for r in grading_results if r['score'] > 0]),
            'failed': len([r for r in grading_results if r['score'] == 0]),
            'results': grading_results,
            'summary': {
                'average_score': sum(r['score'] for r in grading_results) / len(grading_results) if grading_results else 0,
                'max_score': max_score,
                'highest_score': max(r['score'] for r in grading_results) if grading_results else 0,
                'lowest_score': min(r['score'] for r in grading_results) if grading_results else 0
            }
        }

    @keyword("Grade Image Submission With Gemini Vision")
    def grade_image_submission_with_gemini_vision(
        self,
        image_path: str,
        questions: str,
        answer_key: str,
        max_score: float = 10.0
    ) -> Dict[str, Any]:
        """
        Grade a student submission from image using Gemini Vision API.
        
        Args:
            image_path: Path to image file (student's answer sheet)
            questions: Questions text
            answer_key: Answer key text
            max_score: Maximum score
            
        Returns:
            Grading result with score and feedback
        """
        try:
            import google.generativeai as genai
            from PIL import Image
            
            if not self.gemini_model:
                raise Exception("Gemini AI not configured. Call Setup Gemini AI first.")
            
            # Load image
            img = Image.open(image_path)
            
            # Create grading prompt
            prompt = f"""You are an expert teacher grading a student's exam.

QUESTIONS:
{questions}

ANSWER KEY:
{answer_key}

INSTRUCTIONS:
1. Extract the student's answers from the image
2. Compare with the answer key
3. Grade each answer (correct/incorrect)
4. Calculate total score out of {max_score}
5. Provide detailed feedback

Please respond in this format:
STUDENT ANSWERS:
[List extracted answers]

GRADING:
[Question-by-question evaluation]

SCORE: X/{max_score}

FEEDBACK:
[Overall feedback for the student]
"""
            
            # Use Gemini Vision to analyze image
            response = self.gemini_model.generate_content([prompt, img])
            
            # Parse response to extract score
            response_text = response.text
            
            # Extract score from response
            import re
            score_match = re.search(r'SCORE:\s*(\d+\.?\d*)', response_text)
            score = float(score_match.group(1)) if score_match else 0.0
            
            self.logger.info(f"Graded image submission: {score}/{max_score}")
            
            return {
                'score': score,
                'max_score': max_score,
                'feedback': response_text,
                'raw_response': response_text
            }
            
        except Exception as e:
            self.logger.error(f"Failed to grade image: {e}")
            raise
    
    @keyword("Complete Auto Grading From Images")
    def complete_auto_grading_from_images(
        self,
        submissions_folder_id: str,
        question_file_id: str,
        answer_key_file_id: str,
        max_score: float = 10.0
    ) -> Dict[str, Any]:
        """
        Complete auto-grading workflow for image submissions.
        
        Args:
            submissions_folder_id: Google Drive folder with image submissions
            question_file_id: File ID of questions
            answer_key_file_id: File ID of answer key
            max_score: Maximum score
            
        Returns:
            Grading results for all submissions
        """
        import tempfile
        
        # Download questions and answer key
        self.logger.info("Downloading questions and answer key...")
        question_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        answer_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        
        self.download_file_from_google_drive(question_file_id, question_file.name)
        self.download_file_from_google_drive(answer_key_file_id, answer_file.name)
        
        with open(question_file.name, 'r', encoding='utf-8') as f:
            questions = f.read()
        
        with open(answer_file.name, 'r', encoding='utf-8') as f:
            answer_key = f.read()
        
        # Get image submissions from folder
        self.logger.info("Getting student submissions...")
        submissions = self.list_files_in_google_drive_folder(submissions_folder_id)
        
        # Filter only images
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        image_submissions = [
            s for s in submissions 
            if any(s['name'].lower().endswith(ext) for ext in image_extensions)
        ]
        
        self.logger.info(f"Found {len(image_submissions)} image submissions")
        
        # Grade each submission
        grading_results = []
        
        for submission in image_submissions:
            try:
                # Download image
                image_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                self.download_file_from_google_drive(submission['id'], image_file.name)
                
                # Extract student name from filename
                student_name = submission['name'].rsplit('.', 1)[0]
                
                # Grade using Gemini Vision
                self.logger.info(f"Grading {student_name}...")
                result = self.grade_image_submission_with_gemini_vision(
                    image_file.name,
                    questions,
                    answer_key,
                    max_score
                )
                
                grading_results.append({
                    'student_name': student_name,
                    'file_id': submission['id'],
                    'score': result['score'],
                    'feedback': result['feedback']
                })
                
                self.logger.info(f"Graded {student_name}: {result['score']}/{max_score}")
                
                # Cleanup
                import os
                os.unlink(image_file.name)
                
            except Exception as e:
                self.logger.error(f"Failed to grade {submission['name']}: {e}")
                grading_results.append({
                    'student_name': submission['name'],
                    'file_id': submission['id'],
                    'score': 0,
                    'feedback': f'Error: {str(e)}'
                })
        
        # Cleanup
        import os
        os.unlink(question_file.name)
        os.unlink(answer_file.name)
        
        return {
            'total_submissions': len(image_submissions),
            'graded': len([r for r in grading_results if r['score'] > 0]),
            'failed': len([r for r in grading_results if r['score'] == 0]),
            'results': grading_results,
            'summary': {
                'average_score': sum(r['score'] for r in grading_results) / len(grading_results) if grading_results else 0,
                'max_score': max_score,
                'highest_score': max(r['score'] for r in grading_results) if grading_results else 0,
                'lowest_score': min(r['score'] for r in grading_results) if grading_results else 0
            }
        }
    

    
    @keyword("Create Submission For Student")
    def create_submission_for_student(
        self,
        assignment_id: int,
        user_id: int,
        submission_text: str = "Auto-submitted for grading"
    ) -> Dict[str, Any]:
        """
        Create/submit assignment for a student.
        
        Args:
            assignment_id: Assignment instance ID
            user_id: Student user ID
            submission_text: Text content for submission
            
        Returns:
            Submission result
        """
        try:
            params = {
                'assignmentid': assignment_id,
                'plugindata[onlinetext_editor][text]': submission_text,
                'plugindata[onlinetext_editor][format]': 1
            }
            
            result = self.call_moodle_api('mod_assign_save_submission', params)
            self.logger.info(f"Created submission for user {user_id} in assignment {assignment_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create submission for user {user_id}: {e}")
            raise
    
    @keyword("Submit Assignment For Students")
    def submit_assignment_for_students(
        self,
        assignment_id: int,
        student_usernames: List[str]
    ) -> Dict[str, Any]:
        """
        Create submissions for multiple students.
        
        Args:
            assignment_id: Assignment instance ID
            student_usernames: List of student usernames
            
        Returns:
            Summary of submissions created
        """
        created = []
        failed = []
        
        for username in student_usernames:
            try:
                user = self.get_user_by_username_or_email(username)
                if not user:
                    raise Exception(f"User '{username}' not found")
                
                self.create_submission_for_student(assignment_id, user['id'])
                created.append(username)
                
            except Exception as e:
                failed.append({'username': username, 'error': str(e)})
                self.logger.error(f"Failed to create submission for {username}: {e}")
        
        return {
            'total': len(student_usernames),
            'created': len(created),
            'failed': len(failed),
            'created_list': created,
            'failed_list': failed
        }
    

    @keyword("Upload Grades To Moodle")
    def upload_grades_to_moodle(
        self,
        course_id: int,
        assignment_id: int,
        grades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Upload grades to Moodle assignment using batch API.
        Automatically creates submissions if they don't exist.
        
        Args:
            course_id: Moodle course ID
            assignment_id: Moodle assignment instance ID
            grades: List of grade dictionaries with student_name, score, feedback
            
        Returns:
            Summary of uploaded grades
        """
        # Prepare grades data for batch upload
        grades_data = {}
        user_mapping = {}
        
        for idx, grade in enumerate(grades):
            try:
                # Get user by username or email
                user = self.get_user_by_username_or_email(grade['student_name'])
                
                if not user:
                    self.logger.warning(f"User '{grade['student_name']}' not found, skipping")
                    continue
                
                # Build parameters for this grade
                grades_data[f'grades[{idx}][userid]'] = user['id']
                grades_data[f'grades[{idx}][grade]'] = grade['score']
                grades_data[f'grades[{idx}][attemptnumber]'] = -1
                grades_data[f'grades[{idx}][addattempt]'] = 1  # Auto-create submission
                grades_data[f'grades[{idx}][workflowstate]'] = ''
                grades_data[f'grades[{idx}][plugindata][assignfeedbackcomments_editor][text]'] = grade.get('feedback', '')
                grades_data[f'grades[{idx}][plugindata][assignfeedbackcomments_editor][format]'] = 1
                
                user_mapping[idx] = grade['student_name']
                
            except Exception as e:
                self.logger.error(f"Error preparing grade for {grade['student_name']}: {e}")
        
        if not grades_data:
            self.logger.warning("No valid grades to upload")
            return {
                'total': len(grades),
                'uploaded': 0,
                'failed': len(grades),
                'uploaded_grades': [],
                'failed_grades': [{'student': g['student_name'], 'error': 'User not found'} for g in grades]
            }
        
        # Upload all grades at once
        try:
            params = {
                'assignmentid': assignment_id,
                'applytoall': 0,
                **grades_data
            }
            
            result = self.call_moodle_api('mod_assign_save_grades', params)
            
            self.logger.info(f"Successfully uploaded {len(user_mapping)} grades to assignment {assignment_id}")
            
            uploaded = [{'student': name, 'score': grades[idx]['score']} 
                       for idx, name in user_mapping.items()]
            
            return {
                'total': len(grades),
                'uploaded': len(uploaded),
                'failed': len(grades) - len(uploaded),
                'uploaded_grades': uploaded,
                'failed_grades': []
            }
            
        except Exception as e:
            self.logger.error(f"Failed to upload grades: {e}")
            return {
                'total': len(grades),
                'uploaded': 0,
                'failed': len(grades),
                'uploaded_grades': [],
                'failed_grades': [{'student': g['student_name'], 'error': str(e)} for g in grades]
            }
    
    
    @keyword("Export Grading Results To Excel")
    def export_grading_results_to_excel(
        self,
        grading_results: List[Dict[str, Any]],
        output_path: str,
        max_score: float = 10.0
    ) -> str:
        """
        Export grading results to Excel file.
        
        Args:
            grading_results: List of grading result dictionaries
            output_path: Path to save Excel file
            max_score: Maximum score for percentage calculation
            
        Returns:
            Path to created Excel file
        """
        import pandas as pd
        from datetime import datetime
        
        # Prepare data for Excel
        data = []
        for result in grading_results:
            data.append({
                'Student Name': result.get('student_name', 'Unknown'),
                'Score': result.get('score', 0),
                'Max Score': max_score,
                'Percentage': f"{(result.get('score', 0) / max_score * 100):.1f}%" if max_score > 0 else "0%",
                'Feedback': result.get('feedback', 'No feedback'),
                'File ID': result.get('file_id', '')
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Calculate summary statistics
        summary_data = {
            'Metric': [
                'Total Submissions',
                'Average Score',
                'Highest Score',
                'Lowest Score',
                'Pass Rate (>=50%)',
                'Generated At'
            ],
            'Value': [
                len(grading_results),
                f"{df['Score'].mean():.2f}/{max_score}" if len(df) > 0 else "N/A",
                f"{df['Score'].max():.2f}/{max_score}" if len(df) > 0 else "N/A",
                f"{df['Score'].min():.2f}/{max_score}" if len(df) > 0 else "N/A",
                f"{len(df[df['Score'] >= max_score/2])}/{len(df)}" if len(df) > 0 else "N/A",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Grading Results', index=False)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        self.logger.info(f"Grading results exported to: {output_path}")
        return output_path

    @keyword("Export Grading Results To CSV")
    def export_grading_results_to_csv(
        self,
        grading_results: List[Dict[str, Any]],
        output_path: str,
        max_score: float = 10.0,
        grade_item_name: str = "Auto Grading"
    ) -> str:
        """
        Export grading results to CSV file for Moodle gradebook import.
        
        Args:
            grading_results: List of grading result dictionaries
            output_path: Path to save CSV file
            max_score: Maximum score
            grade_item_name: Name of the grade item in Moodle
            
        Returns:
            Path to created CSV file
            
        CSV Format for Moodle:
            Username,Email,Full Name,Grade Item Name
            student001,student001@example.com,Nguyen Van A,10.0
        """
        import csv
        
        # Prepare data for CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Moodle gradebook import format
            fieldnames = ['Username', 'Email', 'Full Name', grade_item_name]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for result in grading_results:
                student_name = result.get('student_name', 'Unknown')
                score = result.get('score', 0)
                
                # Try to get user info
                user = self.get_user_by_username_or_email(student_name)
                
                if user:
                    writer.writerow({
                        'Username': user.get('username', student_name),
                        'Email': user.get('email', f'{student_name}@example.com'),
                        'Full Name': user.get('fullname', student_name),
                        grade_item_name: score
                    })
                else:
                    # Fallback if user not found
                    writer.writerow({
                        'Username': student_name,
                        'Email': f'{student_name}@example.com',
                        'Full Name': student_name,
                        grade_item_name: score
                    })
        
        self.logger.info(f"Grading results exported to CSV: {output_path}")
        self.logger.info(f"Import this file in Moodle: Course → Grades → Import → CSV file")
        return output_path
    


    @keyword("Complete Auto Grading And Upload Workflow")
    def complete_auto_grading_and_upload_workflow(
        self,
        submissions_folder_id: str,
        question_file_id: str,
        answer_key_file_id: str,
        course_id: int,
        assignment_id: int,
        max_score: float = 10.0
    ) -> Dict[str, Any]:
        """
        Complete workflow: Grade submissions and upload to Moodle.
        
        Args:
            submissions_folder_id: Google Drive folder with submissions
            question_file_id: File ID of questions
            answer_key_file_id: File ID of answer key
            course_id: Moodle course ID
            assignment_id: Moodle assignment ID
            max_score: Maximum score
            
        Returns:
            Complete results including grading and upload status
        """
        # Step 1: Grade all submissions
        self.logger.info("Step 1: Grading all submissions...")
        grading_result = self.complete_auto_grading_workflow(
            submissions_folder_id,
            question_file_id,
            answer_key_file_id,
            max_score
        )
        
        self.logger.info(f"Graded {grading_result['graded']}/{grading_result['total_submissions']} submissions")
        
        # Step 2: Upload grades to Moodle
        self.logger.info("Step 2: Uploading grades to Moodle...")
        upload_result = self.upload_grades_to_moodle(
            course_id,
            assignment_id,
            grading_result['results']
        )
        
        self.logger.info(f"Uploaded {upload_result['uploaded']}/{upload_result['total']} grades")
        
        return {
            'grading': grading_result,
            'upload': upload_result,
            'summary': {
                'total_submissions': grading_result['total_submissions'],
                'graded': grading_result['graded'],
                'uploaded': upload_result['uploaded'],
                'failed_grading': grading_result['failed'],
                'failed_upload': upload_result['failed'],
                'average_score': grading_result['summary']['average_score'],
                'success_rate': (upload_result['uploaded'] / grading_result['total_submissions'] * 100) if grading_result['total_submissions'] > 0 else 0
            }
        }
