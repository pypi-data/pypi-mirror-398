# RPA Moodle

Robot Framework library for Moodle LMS automation via Web Services API.

## Installation

```bash
pip install rpa-moodle
```

## Features

- **Course Management**: Create, retrieve, and manage Moodle courses
- **Category Management**: Organize courses into categories
- **Quiz Generation**: Create quizzes from Excel files or Google Docs (GIFT/XML format)
- **User Management**: Create users and enroll them in courses
- **Excel Integration**: Import course and quiz data from Excel
- **Google Docs Integration** (Optional): Read quiz questions directly from Google Docs
- **Robot Framework Support**: Full integration with Robot Framework

## Quick Start

### Python

```python
from RPA.Moodle import MoodleLibrary

# Method 1: Initialize with credentials
moodle = MoodleLibrary(
    base_url="https://your-moodle-site.com",
    token="your_web_service_token"
)

# Method 2: Initialize without credentials, setup from token file
moodle = MoodleLibrary()
moodle.setup_moodle_connection("moodle_token.json")

# Create a course
course = moodle.create_course(
    fullname="Python Programming 101",
    shortname="PYTHON101",
    categoryid=1,
    summary="Learn Python from scratch"
)

# Create quiz from Excel
quiz_file = moodle.create_quiz_from_excel("quiz_data.xlsx", "gift")
```

### Robot Framework

```robot
*** Settings ***
# Method 1: Initialize with credentials
Library    RPA.Moodle    https://your-moodle-site.com    your_token

# Method 2: Initialize without credentials
Library    RPA.Moodle

*** Test Cases ***
Setup Connection From File
    # If initialized without credentials
    Set Up Moodle Connection    moodle_token.json

Create Course
    ${course}=    Create Course
    ...    fullname=Python 101
    ...    shortname=PY101
    ...    categoryid=1
    Log    Course ID: ${course['id']}

Create Quiz From Excel
    ${quiz_file}=    Create Quiz From Excel    quiz_data.xlsx    gift
    Log    Quiz file created: ${quiz_file}
```

## Token File Format

If using `Set Up Moodle Connection`, create a JSON file with your Moodle credentials:

**moodle_token.json:**
```json
{
    "base_url": "https://your-moodle-site.com",
    "token": "your_moodle_web_service_token"
}
```

## Excel Format

The library expects Excel files with specific sheets:

### Sheet: Course
| fullname | shortname | category | summary |
|----------|-----------|----------|---------|
| Python Programming 101 | PYTHON101 | Programming | Learn Python basics |

### Sheet: Quiz
| name | intro | timelimit | grade |
|------|-------|-----------|-------|
| Python Quiz | Test your knowledge | 3600 | 100 |

### Sheet: Questions
| question_number | question_text | question_type | option_a | option_b | option_c | option_d | correct_answer | points |
|----------------|---------------|---------------|----------|----------|----------|----------|----------------|--------|
| 1 | What is Python? | multichoice | A programming language | A snake | A framework | An OS | A | 1 |
| 2 | Python is compiled | truefalse | | | | | FALSE | 1 |

**Question Types:**
- `multichoice`: Multiple choice (A, B, C, D)
- `truefalse`: True/False questions
- `shortanswer`: Short answer questions

## Moodle Setup

### 1. Enable Web Services

1. Go to **Site Administration > Advanced features**
2. Enable **Web services**
3. Save changes

### 2. Enable REST Protocol

1. Go to **Site Administration > Plugins > Web services > Manage protocols**
2. Enable **REST protocol**

### 3. Create External Service

1. Go to **Site Administration > Plugins > Web services > External services**
2. Click **Add**
3. Add required functions:
   - `core_course_create_courses`
   - `core_course_get_courses_by_field`
   - `core_course_get_categories`
   - `core_course_create_categories`
   - `core_user_create_users`
   - `enrol_manual_enrol_users`

### 4. Generate Token

1. Go to **Site Administration > Plugins > Web services > Manage tokens**
2. Click **Add**
3. Select user and service
4. Copy the generated token

## API Reference

### Course Management

#### Create Course
```python
course = moodle.create_course(fullname, shortname, categoryid, summary="")
```

#### Get Course
```python
course = moodle.get_course_by_shortname(shortname)
```

#### Ensure Course Exists
```python
course = moodle.ensure_course_exists(fullname, shortname, categoryid)
```

### Category Management

#### Get Categories
```python
categories = moodle.get_course_categories()
```

#### Create Category
```python
category = moodle.create_course_category(name, parent=0, description="")
```

#### Ensure Category Exists
```python
category = moodle.ensure_category_exists(name, parent=0)
```

### Quiz Management

#### Create Quiz from Excel
```python
# GIFT format
quiz_file = moodle.create_quiz_from_excel(excel_path, "gift")

# XML format
quiz_file = moodle.create_quiz_from_excel(excel_path, "xml")
```

#### Generate Quiz Files
```python
# GIFT format
moodle.generate_quiz_gift_file(questions, output_path)

# XML format
moodle.generate_quiz_xml_file(questions, output_path, quiz_name)
```

### User Management

#### Create User
```python
user = moodle.create_user(username, password, firstname, lastname, email)
```

#### Enroll User
```python
# roleid: 5 = Student, 3 = Teacher
moodle.enroll_user_in_course(userid, courseid, roleid=5)
```

### Complete Workflows

#### Create Course from Excel
```python
course = moodle.create_course_from_excel(excel_path)
```

#### Create Course and Quiz
```python
result = moodle.create_course_and_quiz_from_excel(excel_path, quiz_format="gift")
# Returns: {'course': {...}, 'quiz_file': '...', 'message': '...'}
```

## Google Docs Integration (Optional)

### Installation

To use Google Docs integration, install with Google API support:

```bash
pip install rpa-moodle[google]
```

Or install the dependencies manually:

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

### Setup Google API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API and Google Docs API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file

### Usage

#### Python

```python
from RPA.Moodle import MoodleLibrary

# Initialize with Google credentials
moodle = MoodleLibrary(
    base_url="https://your-moodle-site.com",
    token="your_moodle_token",
    google_credentials_path="path/to/google_token.json"
)

# Or setup Google connection later
moodle.setup_google_connection("path/to/google_token.json")

# Create quiz from Google Doc
doc_url = "https://docs.google.com/document/d/YOUR_DOC_ID/edit"
quiz_file = moodle.create_quiz_from_google_doc(doc_url, "quiz_output.txt", "gift")
```

#### Robot Framework

```robot
*** Settings ***
Library    RPA.Moodle    https://moodle.site.com    moodle_token

*** Test Cases ***
Create Quiz From Google Doc
    Setup Google Connection    /path/to/google_token.json
    ${quiz_file}=    Create Quiz From Google Doc
    ...    https://docs.google.com/document/d/DOC_ID/edit
    ...    quiz_output.txt
    ...    gift
    Log    Quiz file: ${quiz_file}
```

### Google Doc Format

Your Google Doc should follow this format:

```
Question 1: What is Python?
A. A programming language
B. A snake
C. A framework
D. An operating system

Question 2: Python is a compiled language
A. True
B. False

---HẾT---

1. A
2. B
```

**Format Rules:**
- Questions start with "Question" or "Câu" followed by number
- Options labeled A, B, C, D
- Delimiter `---HẾT---` separates questions from answers
- Answer key format: `1. A` (question number, dot, answer letter)

### API Methods

#### Setup Google Connection
```python
moodle.setup_google_connection(token_file_path)
```

#### Read Quiz from Google Doc
```python
questions = moodle.read_quiz_from_google_doc(doc_id, delimiter="---HẾT---")
```

#### Create Quiz from Google Doc
```python
quiz_file = moodle.create_quiz_from_google_doc(doc_id_or_url, output_path, format="gift")
```

## Importing Quizzes to Moodle

After generating GIFT or XML files:

1. Go to your course in Moodle
2. Click **More > Question bank > Import**
3. Select format (GIFT or Moodle XML)
4. Upload the generated file
5. Click **Import**
6. Create a Quiz activity and add questions from the Question bank

## Requirements

- Python 3.8+
- requests >= 2.31.0
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- robotframework >= 6.0.0

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on GitHub.
