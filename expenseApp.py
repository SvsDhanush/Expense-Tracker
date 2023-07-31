from flask import Flask, render_template, request
import boto3
import json

app = Flask(__name__, template_folder='templates')
s3 = boto3.client('s3')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'image' not in request.files:
            return 'No image file found', 400

        image = request.files['image']
        image_name = image.filename

        try:
            s3.upload_fileobj(image, 'expense-tracker-project-try', 'receipts/' + image_name)
            total = get_total_from_json()
            return render_template('index.html', total=total, message='Image uploaded successfully')
        except Exception as e:
            return render_template('index.html', total=None, message=str(e))

    total = get_total_from_json()
    return render_template('index.html', total=total, message=None)

def get_total_from_json():
    try:
        response = s3.get_object(Bucket='expense-tracker-project-try', Key='totals.json')
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data['total']
    except Exception as e:
        print(str(e))
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
