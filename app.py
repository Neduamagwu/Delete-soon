from flask import Flask, render_template, render_template_string, request
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import uuid
import socket
import os
import json
from datetime import datetime
import psycopg2
from psycopg2 import sql


# Create an instance of the Flask app
app = Flask(__name__)

# Initialize the S3 client using IAM role credentials
s3_client = boto3.client(
    's3',
    region_name=os.getenv('AWS_REGION', 'us-east-2')  # Default to 'us-east-2' if not provided in the environment
)

# Ensure the 'data' folder exists to store uploaded files locally
os.makedirs('data', exist_ok=True)

# S3 bucket name (make sure it's set correctly)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'my-pythonapp-bucket')  # Get bucket name from environment variable or default

# Initialize RDS connection (using IAM Role for credentials)
rds_host = os.getenv('RDS_HOST')  # RDS endpoint URL
rds_db_name = 'polypop'
rds_user = os.getenv('RDS_USER')  # Postgres username
rds_port = '5432'  # Default PostgreSQL port
secret_name = os.getenv('SECRET_NAME') # Secret to Read postgres password from

# Initialize Secrets Manager client
secrets_client = boto3.client('secretsmanager', region_name=os.getenv('AWS_REGION'))

# Function to get RDS password from Secrets Manager
def get_rds_password():
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        return secret_dict['password']
    except ClientError as e:
        print(f"Error retrieving secret from Secrets Manager: {e}")
        return None

# Get the RDS password from Secrets Manager
rds_password = get_rds_password()

if not rds_password:
    raise Exception("Unable to retrieve RDS password from Secrets Manager.")

# Establish connection with the retrieved RDS password
conn = psycopg2.connect(
    host=rds_host,
    database=rds_db_name,
    user=rds_user,
    password=rds_password,
    port=rds_port,
    sslmode='require'  # SSL is recommended for RDS connections
)

# Create the table if it doesn't exist and add new columns if they don't exist
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS careers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        experience INT,
        position VARCHAR(255),
        salary INT,
        resume_url VARCHAR(255),
        phone_number VARCHAR(20),
        expected_salary INT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

# Add new columns if they don't exist
cursor.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='careers' AND column_name='phone_number') THEN
            ALTER TABLE careers ADD COLUMN phone_number VARCHAR(20);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='careers' AND column_name='expected_salary') THEN
            ALTER TABLE careers ADD COLUMN expected_salary INT;
        END IF;
    END $$;
""")
conn.commit()


@app.route('/')
def home():
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_id = str(uuid.uuid4())
    private_ip = socket.gethostbyname(socket.gethostname())

    # HTML template with variables
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to Polypop Nigeria Limited</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 20px;
            background-color: #f0f0f0;
        }
        h1 {
            color: #4CAF50;
            margin-bottom: 20px;
        }
        p {
            color: #333;
            font-size: 18px;
        }
        .services {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 30px;
        }
        .service {
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .service h3 {
            color: #4CAF50;
        }
        footer {
            margin-top: 50px;
            font-size: 14px;
            color: #777;
        }
        .system-info {
            position: fixed;
            bottom: 20px;
            right: 20px;
            font-size: 14px;
            color: #333;
            background-color: #fff;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .nav-link {
            position: absolute;
            top: 20px;
            left: 20px;
            font-size: 16px;
            color: #4CAF50;
            text-decoration: none;
        }
        .nav-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

    <!-- Careers Link -->
    <a href="{{ url_for('careers') }}" class="nav-link">Careers</a>

    <h1>Welcome to Polypop Nigeria Limited!</h1>
    <p>We specialize in providing innovative solutions to make your business thrive. Explore our services below:</p>

    <div class="services">
        <div class="service">
            <h3>Web Development</h3>
            <p>Building responsive and functional websites to meet your business needs.</p>
        </div>
        <div class="service">
            <h3>Cloud Solutions</h3>
            <p>Harnessing the power of cloud computing to drive scalability and efficiency.</p>
        </div>
        <div class="service">
            <h3>Mobile Apps</h3>
            <p>Creating user-friendly mobile apps for Android and iOS platforms.</p>
        </div>
    </div>

    <footer>
        <p>From Welcome to Polypop Nigeria Limited</p>
    </footer>

    <!-- Display current date, unique system ID, and private IP -->
    <div class="system-info">
        <p><strong>Current Date:</strong> {{ current_date }}</p>
        <p><strong>System ID:</strong> {{ system_id }}</p>
        <p><strong>Private IP:</strong> {{ private_ip }}</p>
    </div>

</body>
</html>
'''
    return render_template_string(html_content, current_date=current_date, system_id=system_id, private_ip=private_ip)

@app.route('/careers', methods=['GET', 'POST'])
def careers():
    if request.method == 'POST':
        try:
            # Get all form data
            user_name = request.form.get('name')
            phone_number = request.form.get('phone')
            experience = request.form.get('experience')
            position = request.form.get('position')
            salary = request.form.get('salary')
            expected_salary = request.form.get('expected_salary')

            # Handle file upload
            if 'file' not in request.files:
                return "No file part", 400

            file = request.files['file']

            if file.filename == '':
                return "No selected file", 400

            # Extract file extension and create the file name
            file_extension = os.path.splitext(file.filename)[1]  # Get the file extension
            file_name = f"{user_name.replace(' ', '_')}{file_extension}"  # Combine user name with the file extension

            # Get the current date in ddmmyyyy format
            current_date = datetime.now().strftime('%d%m%Y')

            # Create the S3 folder path based on the current date
            s3_folder = f"{current_date}/{file_name}"

            # Upload file to S3 within the folder structure
            s3_client.upload_fileobj(file, S3_BUCKET_NAME, s3_folder)
            resume_url = f"s3://{S3_BUCKET_NAME}/{s3_folder}"

            # Insert into database
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO careers (name, experience, position, salary, resume_url, phone_number, expected_salary)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_name,
                int(experience) if experience else None,
                position,
                int(salary) if salary else None,
                resume_url,
                phone_number,
                int(expected_salary) if expected_salary else None
            ))
            conn.commit()

            # Return success message
            return f"Application submitted successfully! Resume '{file_name}' uploaded to S3 folder '{current_date}' and saved to database."

        except NoCredentialsError:
            conn.rollback()
            return "Credentials not available", 400
        except Exception as e:
            conn.rollback()
            return f"An error occurred: {str(e)}", 500

    # For GET requests, show the careers page
    careers_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Careers - Polypop Nigeria Limited</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 20px;
            background-color: #f8f8f8;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .content-wrapper {
            width: 100%;
            max-width: 600px;
        }
        h1 {
            color: #4CAF50;
            margin-bottom: 20px;
        }
        .upload-form {
            margin: 30px 0;
            background-color: #fff;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .form-group {
            margin-bottom: 25px;
            width: 100%;
        }
        .form-group label {
            display: block;
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 8px;
            color: #333;
            text-align: left;
        }
        .form-group input {
            width: 100%;
            max-width: 400px;
            padding: 12px;
            font-size: 16px;
            border-radius: 5px;
            border: 1px solid #ddd;
            box-sizing: border-box;
            margin: 0 auto;
            display: block;
        }
        .form-group input[type="file"] {
            border: none;
            padding: 10px 0;
        }
        .section-title {
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
            margin: 30px 0 20px;
            text-align: center;
        }
        button {
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            width: 100%;
            max-width: 400px;
            margin: 20px auto 0;
            display: block;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #45a049;
        }
        footer {
            margin-top: 40px;
            font-size: 14px;
            color: #777;
        }
        p {
            color: #555;
            line-height: 1.5;
            max-width: 600px;
            margin: 0 auto 30px;
        }
    </style>
</head>
<body>
    <div class="content-wrapper">
        <h1>Careers at Polypop Nigeria Limited</h1>
        <p>We are always looking for talented individuals to join our team! Please fill in your details and upload your resume below:</p>

        <form method="POST" enctype="multipart/form-data" class="upload-form">
            <!-- Personal Information -->
            <div class="form-group">
                <label for="name">Your Name</label>
                <input type="text" name="name" id="name" required>
            </div>
            
            <div class="form-group">
                <label for="phone">Phone Number:</label>
                <input type="tel" name="phone" id="phone" required placeholder="Enter your phone number">
            </div>

            <!-- Professional Information Section -->
            <div class="section-title">Professional Information</div>
            
            <div class="form-group">
                <label for="experience">Years of Experience:</label>
                <input type="number" name="experience" id="experience" required min="0" max="50">
            </div>

            <div class="form-group">
                <label for="position">Position Applying For:</label>
                <input type="text" name="position" id="position" required placeholder="e.g. Software Developer, Cloud Engineer">
            </div>

            <div class="form-group">
                <label for="salary">Current Salary (Naira):</label>
                <input type="number" name="salary" id="salary" placeholder="Enter your current salary (optional)">
            </div>

            <div class="form-group">
                <label for="expected_salary">Expected Salary (Naira):</label>
                <input type="number" name="expected_salary" id="expected_salary" placeholder="Enter your expected salary (optional)">
            </div>

            <div class="form-group">
                <label for="file">Upload Your Resume</label>
                <input type="file" name="file" id="file" required accept=".pdf,.doc,.docx">
            </div>

            <button type="submit">Submit Application</button>
        </form>

        <footer>
            <p>From Polypop Nigeria Limited</p>
        </footer>
    </div>
</body>
</html>
'''
    return render_template_string(careers_html)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)