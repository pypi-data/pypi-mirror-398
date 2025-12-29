import streamlit as st
from polynomials.quadratic.numeric import QuadraticEquation

st.title("Polynomial Visualizer")

a = st.number_input("a", 1.0)
b = st.number_input("b", 0.0)
c = st.number_input("c", 0.0)

q = QuadraticEquation(a, b, c)
st.latex(q.__latex__())
