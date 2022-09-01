from flask import Flask , render_template

app = Flask(__name__)

# Home Page #
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/win")
def email():
    return render_template("win.html")


# Error 404 # 
@app.route('/<string:nome>')
def error(nome):
    error = f'Página ({nome}) não existe!'
    return render_template("404.html", error=error)
# Error 404 #



# colocar o site no ar
if __name__ == "__main__":
    app.run(debug=True)