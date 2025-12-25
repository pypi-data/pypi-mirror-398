import plotly.express as px

if __name__ == '__main__':
    fig = px.bar(x=["a", "b", "c"], y=[1, 3, 2])
    fig.write_html('/Users/leqee/code/nehushtan/debug/plotly/first_figure.html', auto_open=True)
