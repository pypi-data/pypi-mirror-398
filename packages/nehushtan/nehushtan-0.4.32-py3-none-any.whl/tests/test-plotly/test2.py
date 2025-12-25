import plotly.express as px

if __name__ == '__main__':
    fig = px.line(x=["a", "b", "c"], y=[1, 3, 2], title="sample figure")
    print(fig)
    fig.show()
