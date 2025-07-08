from flask import Flask, render_template, request
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import uuid
import socket
import os
from datetime import datetime
from careers import careers_blueprint

app = Flask(__name__)

# Ensure the 'data' folder exists to store uploaded files
os.makedirs('data', exist_ok=True)
app.register_blueprint(careers_blueprint, url_prefix='/careers')

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
        }
    </style>
</head>
<body>

    <!-- Careers Link -->
    <a href="{{ url_for('careers.careers') }}" class="nav-link">Careers</a>

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
    return render_template('home.html', current_date=current_date, system_id=system_id, private_ip=private_ip)

@app.route('/careers', methods=['GET', 'POST'])
def careers():
    if request.method == 'POST':
        # Get the user inputs from the form
        user_name = request.form.get('name')

        # Handle file upload
        if 'file' not in request.files:
            return "No file part", 400

        file = request.files['file']

        if file.filename == '':
            return "No selected file", 400

        # Extract file extension and create the file name
        file_extension = os.path.splitext(file.filename)[1]  # Get the file extension
        file_name = f"{user_name}{file_extension}"  # Combine user name with the file extension

        # Get the current date in ddmmyyyy format
        current_date = datetime.now().strftime('%d%m%Y')

        # Create the S3 folder path based on the current date
        s3_folder = f"{current_date}/{file_name}"

        try:
            # Upload file to S3 within the folder structure
            s3_client.upload_fileobj(file, S3_BUCKET_NAME, s3_folder)

            # Return success message
            return f"File '{file_name}' uploaded successfully to S3 folder '{current_date}'"

        except NoCredentialsError:
            return "Credentials not available", 400
        except Exception as e:
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
            text-align: center;
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
            <div class="form-group">
                <label for="name">Your Name</label>
                <input type="text" name="name" id="name" required>
            </div>

            <div class="form-group">
                <label for="file">Upload Your Resume</label>
                <input type="file" name="file" id="file" required>
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