from flask import Flask,render_template

app= Flask(__name__)

import config

import routes

import models

if __name__=='__main__':
    app.run(debug=True)