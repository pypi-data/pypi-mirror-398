import json
import pandas as pd
import requests
import re
import io
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

@library(scope='GLOBAL', auto_keywords=False)
class MoodleLibrary:
    """
    Thư viện Robot Framework để tương tác với Moodle Web Services API.
    Hỗ trợ tạo khóa học, quiz và quản lý nội dung từ file Excel.
    """
    
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
        
        # Setup Google credentials if provided
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
            
        Expected JSON format:
        {
            "base_url": "https://moodle.example.com",
            "token": "your_moodle_token"
        }
            
        Returns:
            Dictionary với thông tin kết nối
        """
        if not token_file_path:
            raise Exception('Token file path is required')

        with open(token_file_path, 'r') as file:
            data = json.load(file)
            
        base_url = data.get('base_url')
        token = data.get('token')
        
        if not base_url or not token:
            raise Exception('Token file must contain "base_url" and "token"')
        
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
        users = self.call_moodle_api('core_user_get_users_by_field', {
            'field': 'username',
            'values[0]': username
        })
        
        if not users or len(users) == 0:
            raise Exception(f"User not found: {username}")
        
        userid = users[0]['id']
        
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
        
        request = service.files().get_media(fileId=file_id)
        
        with io.FileIO(output_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        self.logger.info(f"File downloaded: {output_path}")
        return output_path

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
        
        Args:
            students: List of student dictionaries
            
        Returns:
            Summary of created students
        """
        created = []
        failed = []
        
        for student in students:
            try:
                user = self.create_user(
                    username=student['username'],
                    password=student['password'],
                    firstname=student['firstname'],
                    lastname=student['lastname'],
                    email=student['email']
                )
                created.append({
                    'username': student['username'],
                    'userid': user['id']  # Fixed: user is already a dict, not a list
                })
                self.logger.info(f"Created user: {student['username']}")
            except Exception as e:
                failed.append({
                    'username': student['username'],
                    'error': str(e)
                })
                self.logger.warning(f"Failed to create {student['username']}: {e}")
        
        return {
            'total': len(students),
            'created': len(created),
            'failed': len(failed),
            'created_users': created,
            'failed_users': failed
        }

    @keyword("Bulk Create Courses And Enrol Students")
    def bulk_create_courses_and_enrol_students(self, courses: List[Dict[str, Any]], 
                                                student_usernames: List[str]) -> Dict[str, Any]:
        """
        Tạo hàng loạt khóa học và enrol tất cả học sinh.
        
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
                
                # Create course
                course = self.create_course(
                    fullname=course_data['fullname'],
                    shortname=course_data['shortname'],
                    categoryid=category['id'],
                    summary=course_data.get('summary', '')
                )
                
                # Enrol all students
                enrolled = 0
                for username in student_usernames:
                    try:
                        self.enrol_user(username, course_data['shortname'])
                        enrolled += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to enrol {username}: {e}")
                
                created_courses.append({
                    'shortname': course_data['shortname'],
                    'courseid': course['id'],
                    'enrolled_count': enrolled
                })
                
                self.logger.info(f"Created course {course_data['shortname']} with {enrolled} students")
                
            except Exception as e:
                failed_courses.append({
                    'shortname': course_data['shortname'],
                    'error': str(e)
                })
                self.logger.warning(f"Failed to create course {course_data['shortname']}: {e}")
        
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
            
            # Get list of created usernames
            created_usernames = [u['username'] for u in students_result['created_users']]
            
            # Create courses and enrol students
            self.logger.info("Creating courses and enrolling students...")
            courses_result = self.bulk_create_courses_and_enrol_students(
                courses, created_usernames
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
