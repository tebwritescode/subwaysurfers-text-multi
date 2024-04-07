from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/output', methods=['POST'])
def output():
    text_input = request.form['text_input']
    return render_template('output.html', text_input=text_input)

# this code runs the app in "development" mode which makes it easier when developing. 
# comment out for final product
if __name__ == '__main__':
    app.run(debug=True)

